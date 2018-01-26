from celery import shared_task

from django.core.files.base import ContentFile

from compare.utils import get_html_diff, rewrite_html, calculate_similarity_pair
from compare.models import *
from compare.warc_compare import *

from dashboard.utils import write_to_static


def call_task(fn, *args, **kwargs):
    """
    gets celery signature, executes
    """
    if settings.RUN_ASYNC:
        res = fn.delay(*args, **kwargs)
    else:
        res = fn.apply(*args, **kwargs)
    return res


@shared_task
def count_resources(compare_id):
    comp = Compare.objects.get(id=compare_id)
    sort_resources(comp.id)
    total, unchanged, missing, added, changed = comp.count_resources()
    return total, unchanged, missing, added, changed



@shared_task
def diff_html(compare_id, resource_tuple, html_tuple):
    diffed = diff.HTMLDiffer(html1, html2)
    write_to_static(diffed.deleted_diff, 'deleted.html', compare_id=compare_id)
    write_to_static(diffed.inserted_diff, 'inserted.html', compare_id=compare_id)
    write_to_static(diffed.combined_diff, 'combined.html', compare_id=compare_id)

# @shared_task
# def expand_archive(archive_id):


@shared_task
def expand_warc(archive_id):
    archive = Archive.objects.get(id=archive_id)
    archive.expand_warc_create_resources()


@shared_task
def initial_compare(compare_id):
    # compare just the submitted_url resources (the most-likely html response user will see on request of url)
    # this allows the site to replay in full while showing highlights
    compare_obj = Compare.objects.get(id=compare_id)
    archive1 = compare_obj.archive1
    archive2 = compare_obj.archive2
    archive1.expand_warc_create_resources()
    archive2.expand_warc_create_resources()


@shared_task
def create_html_diffs(compare_id, resource_compare_id):
    comp = Compare.objects.get(id=compare_id)
    rc = ResourceCompare.objects.get(id=resource_compare_id)
    if not rc.html_added:
        payload1 = rewrite_html(rc.resource1.payload, comp.archive1.get_warc_dir())
        payload2 = rewrite_html(rc.resource2.payload, comp.archive2.get_warc_dir())
        deleted, added, combined = get_html_diff(payload1, payload2)

        rc.html_deleted.save('deleted.html', ContentFile(deleted))
        rc.html_added.save('added.html', ContentFile(added))
        rc.html_combined.save('combined.html', ContentFile(combined))

        rc.save()
        # TODO: figure out if need to check existence first:
        comp.resource_compares.add(rc)
        comp.save()
        print("html diffs written!")
    else:
        print("html diffs already written")


@shared_task
def sort_resources(compare_id):
    comp = Compare.objects.get(id=compare_id)
    if not comp.completed:
        resources1 = comp.archive1.resources.all()
        resources1_urls = resources1.values_list('url', flat=True)
        resources2 = comp.archive2.resources.all()
        resources2_urls = resources2.values_list('url', flat=True)
        # for resource in resources:
        for resource in resources1:
            if resource.url not in resources2_urls:
                # resource is missing
                resource.status = 'm'
                rc, created = ResourceCompare.objects.get_or_create(
                    resource1=resource,
                    resource2=None,
                    change=100,
                )
            else:
                # TODO: figure out what to do if there are two
                # or more of the same url
                resource2 = resources2.filter(url=resource.url)[0]
                rc, created = ResourceCompare.objects.get_or_create(
                    resource1=resource,
                    resource2=resource2,
                )

                if resource2.hash == resource.hash:
                    resource2.status = 'u'
                    resource2.save()
                    resource.hash = 'u'
                    rc.change = 0
                else:
                    resource2.status = 'c'
                    resource2.save()
                    resource.status = 'c'
                    # since resource has changed, kick off comparison
                    call_task(compare_resource.s(comp.id, rc.id))

            resource.save()
            # TODO: potential for collision here, investigate
            rc.save()
            comp.resource_compares.add(rc)
        # get all the remaining resources from archive2
        # that have the status of pending
        # at this point they should all be newly added
        # set status to 'a' for added
        for resource in resources2.filter(status='p'):
            if resource.url not in resources1_urls:
                # resource has been added, wasn't present before
                rc, created = ResourceCompare.objects.get_or_create(
                    resource1=None,
                    resource2=resource,
                    change=100,
                )
                resource.status = 'a'
                resource.save()
                rc.save()
                comp.resource_compares.add(rc)
        comp.completed = True
        comp.save()
    else:
        print('comparing is finished')
        return


@shared_task
def compare_resource(compare_id, resource_compare_id):
    rc = ResourceCompare.objects.get(id=resource_compare_id)
    if not rc.resource1.payload or not rc.resource2.payload:
        print("impossible to compare", rc.resource1.id, rc.resource2.id)
        return
    compared = calculate_similarity_pair(rc.resource1.payload, rc.resource2.payload, minhash=True, simhash=False, sequence_match=False)
    rc.change = compared['minhash']
    rc.save()
    comp = Compare.objects.get(id=compare_id)
    comp.resource_compares.add(rc)
    print('calculated change:', rc.id, rc.change )
