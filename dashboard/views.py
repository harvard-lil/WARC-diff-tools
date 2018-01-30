from werkzeug.test import Client
from werkzeug.wrappers import BaseResponse
from pywb.apps.frontendapp import FrontEndApp

from django.shortcuts import render, redirect

from dashboard.utils import *

from compare.models import Compare, Archive, ResourceCompare
from compare.tasks import expand_warc, call_task, create_html_diffs, count_resources, compare_resource


def index(request):
    return render(request, "index.html")


def create(request):
    """
    Take requested timestamp and url and create a new archive in a unique directory
    unless one already exists
    """
    submitted_url = request.POST.get('submitted_url')
    old_timestamp = format_date_for_memento(request.POST.get('old_date'))
    new_timestamp = format_date_for_memento(request.POST.get('new_date'))
    archives = []

    archive_requested_urls = []
    for timestamp in (old_timestamp, new_timestamp):
        archive = Archive.objects.create(
            timestamp=timestamp,
            submitted_url=submitted_url)

        archive.save()

        # unique dir for pywb to record warcs
        archive.create_collections_dir()

        # if warc does not exist yet, get record url to record new warc
        # if it does, get warc url
        archive_requested_urls.append(archive.get_record_or_local_url())

        # expand warc in background for later use
        call_task(expand_warc.s(archive.id))

        archives.append(archive)

    compare_obj = Compare.objects.create(archive1=archives[0], archive2=archives[1])
    compare_obj.save()

    return redirect('/view/%s' % compare_obj.id)


def background_compare(request, compare_id):
    comp = Compare.objects.get(id=compare_id)
    call_task(initial_compare.s(comp.id))

    return HttpResponse('ok', status=200)


def view_pair(request, compare_id):
    comp = Compare.objects.get(id=compare_id)
    archive1 = comp.archive1
    archive2 = comp.archive2
    # create initial comparison of submitted_url html for faster display
    submitted_url_resource1 = archive1.resources.get(submitted_url=True)
    submitted_url_resource2 = archive2.resources.get(submitted_url=True)

    rc, created = ResourceCompare.objects.get_or_create(
        resource1=submitted_url_resource1,
        resource2=submitted_url_resource2)
    call_task(create_html_diffs.s(compare_id, rc.id))
    call_task(count_resources.s(comp.id))

    context = {
        "this_page": "view_pair",
        "compare_id": compare_id,
        "request1": archive1.get_record_or_local_url(),
        "request2": archive2.get_record_or_local_url(),
        "timestamp1": archive1.get_friendly_timestamp(),
        "timestamp2": archive2.get_friendly_timestamp(),
        "submitted_url": archive1.submitted_url}

    return render(request, 'compare.html', context)


def single_link(request):
    # full_url = "http://localhost:8082/archives/20000110_example_com/20000110/http://example.com"

    full_url = "/20000110_example_com/20000110/http://example.com"
    application = FrontEndApp(
                config_file='config/config.yaml',
                custom_config={
                    'debug': True,
                    # 'port': '8080',
                    'framed_replay': True})

    # # Set up a werkzeug wsgi client.
    client = Client(application, BaseResponse)
    resp = client.get(full_url, follow_redirects=True)
    return render(resp.response, "single_link.html")


def compare(request, compare_id):
    """
    Given a URL contained in this WARC, return a werkzeug BaseResponse for the URL as played back by pywb.
    """
    compare_obj = Compare.objects.get(id=compare_id)

    # TODO: this is pretty nuts:
    ra = compare_obj.archive1.resources.get(submitted_url=True)
    rb = compare_obj.archive2.resources.get(submitted_url=True)
    # TODO: handle case when not created yet

    rc = ResourceCompare.objects.get(resource1=ra, resource2=rb)
    if not rc.html_added:
        # do synchronously this time
        create_html_diffs(compare_id, rc.id)
        rc.refresh_from_db()

    html_deleted = rc.html_deleted
    html_added = rc.html_added
    # TODO: write temp named files for html highlighting

    total_count, unchanged_count, missing_count, added_count, changed_count = count_resources(compare_id)
    resources = compare_obj.resource_compares.all()

    status_translation = {
        'm': 'missing',
        'a': 'added',
        'c': 'changed',
        'u': 'unchanged',
        'p': 'pending',
    }
    resource_deets = list()

    def flatten_info(resource, change):
        r = dict()
        r['content_type'] = resource.content_type
        r['url'] = resource.url
        r['change'] = change
        r['status'] = status_translation[resource.status]
        return r

    for rc in resources:
        if rc.resource1:
            resource_deets.append(flatten_info(rc.resource1, rc.change))
        if rc.resource2:
            resource_deets.append(flatten_info(rc.resource2, rc.change))

    specific_url = request.GET.get('q', None)
    request1 = compare_obj.archive1.get_record_or_local_url(url=specific_url)
    request2 = compare_obj.archive2.get_record_or_local_url(url=specific_url)

    context = {
        'compare_id': compare_id,
        'request1': request1,
        'request2': request2,
        'this_page': 'compare',
        "timestamp1": compare_obj.archive1.get_friendly_timestamp(),
        "timestamp2": compare_obj.archive2.get_friendly_timestamp(),

        # 'link_url': settings.HOST + '/' + archive1.guid,
        # 'protocol': protocol,
        "submitted_url": compare_obj.archive1.submitted_url,
        'resources': resource_deets,
        'resource_count': {
            'total': total_count[1],
            'unchanged': unchanged_count,
            'missing': missing_count,
            'added': added_count,
            'changed': changed_count,
        },
        'html_deleted': '/media/%s' % html_deleted.name,
        'html_added': '/media/%s' % html_added.name,
    }

    return render(request, 'compare.html', context)

