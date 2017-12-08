import requests

from django.shortcuts import render, redirect, reverse
from django.http import HttpResponseRedirect

from dashboard.utils import *

from compare.warc_compare import *
from compare.models import Compare, WDTArchive

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
    # http://localhost:8082/archives/20130110_twitter_com/record/20130110/http://twitter.com
    archives = []
    url_dirname = url_to_dirname(submitted_url)

    # create new comparison object
    archive_requested_urls = []
    for timestamp in (old_timestamp, new_timestamp):
        wdtarchive = WDTArchive.objects.create(
            timestamp=timestamp,
            submitted_url=submitted_url,
            warc_dir=timestamp + '_' + url_dirname)

        wdtarchive.save()
        # TODO: assuming faultless recording here for now, should fix

        wdtarchive.create_collections_dir()
        import ipdb; ipdb.set_trace()

        # if warc does not exist yet, get record url to record new warc
        # if it does, get warc url
        archive_requested_urls.append(wdtarchive.get_record_or_local_url())

        archives.append(wdtarchive)

    compare_obj = Compare.objects.create(warc1=archives[0], warc2=archives[1])
    compare_obj.save()

    data = {
        'request1': archive_requested_urls[0],
        'request2': archive_requested_urls[1],
        'old_archive_url': archives[0].get_full_local_url(),
        'new_archive_url': archives[1].get_full_local_url(),
    }
    # return redirect('%s/compare/%s' % (settings.BASE_URL, compare_obj.id))
    # return redirect('/compare/%s' % compare_obj.id, context=data)
    return render(request, 'compare.html', data)

def single_link(request):
    from werkzeug.test import Client
    from werkzeug.wrappers import BaseResponse
    from pywb.apps.frontendapp import FrontEndApp
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
    # import ipdb; ipdb.set_trace()
    return render(resp.response, "single_link.html")


def compare(request, compare_obj_id):
    """
        Given a URL contained in this WARC, return a werkzeug BaseResponse for the URL as played back by pywb.
    """
    compare_obj = Compare.objects.get(id=compare_obj_id)
    archive1 = compare_obj.warc1
    archive2 = compare_obj.warc2

    # replay archive to get HTML data
    html1 = archive1.replay_url().data.decode()
    html2 = archive2.replay_url().data.decode()
    # import ipdb; ipdb.set_trace()

    # ignore guids in html
    # diff_settings.EXCLUDE_STRINGS_A.append(str(old_guid))
    # diff_settings.EXCLUDE_STRINGS_A.append(str(old_guid))
    # diff_settings.EXCLUDE_STRINGS_B.append(str(new_guid))

    # add own style string
    # diff_settings.STYLE_STR = settings.DIFF_STYLE_STR

    wc = WARCCompare(archive1.get_full_warc_path(), archive2.get_full_warc_path())
    # import ipdb; ipdb.set_trace()
    if not os.path.exists(get_compare_dir_path(compare_obj_id)):
        diffed = diff.HTMLDiffer(html1, html2)
        write_to_static(diffed.deleted_diff, 'deleted.html', compare_id=compare_obj_id)
        write_to_static(diffed.inserted_diff, 'inserted.html', compare_id=compare_obj_id)
        write_to_static(diffed.combined_diff, 'combined.html', compare_id=compare_obj_id)

    # # TODO: change all '/' in url to '_' to save
    total_count, unchanged_count, missing_count, added_count, modified_count = wc.count_resources()
    resources = []
    old_archive = archive1
    new_archive = archive2
    for status in wc.resources:
        for content_type in wc.resources[status]:
            if "javascript" in content_type:
                content_type_str = "script"
            elif "image" in content_type:
                content_type_str = "img"
            elif "html" in content_type:
                content_type_str = "html"
            else:
                content_type_str = content_type
            for url in wc.resources[status][content_type]:
                resource = {
                    'url': url,
                    'content_type': content_type_str,
                    'status': status,
                }
                if url == old_archive.submitted_url:
                    resources = [resource] + resources
                else:
                    resources.append(resource)

    context = {
        'compare_id': compare_obj_id,
        'old_archive_url': old_archive.get_full_local_url(),
        'new_archive_url': new_archive.get_full_local_url(),
        'this_page': 'comparison',
        # 'link_url': settings.HOST + '/' + old_archive.guid,
        # 'protocol': protocol,
        'resources': resources,
        'resource_count': {
            'total': total_count[1],
            'unchanged': unchanged_count,
            'missing': missing_count,
            'added': added_count,
            'modified': modified_count,
        },
    }

    return render(request, 'compare.html', context)

