import json
import redis
from celery import shared_task, Task

from django.core.files.base import ContentFile

from compare.utils import get_html_diff, rewrite_html, calculate_similarity_pair
from compare.models import *

r = redis.StrictRedis(host='localhost', port=6379, db=0)


class CallbackTask(Task):
    def on_success(self, val, task_id, args, kwargs):
        response = json.dumps({
            "data": val,
            "args": args,
            "kwargs": kwargs
        })
        r.publish('websocket', response)
        print("SUCCESS!", response)
        pass

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        response = json.dumps({
            "error": exc,
            "args": args,
            "kwargs": kwargs
        })
        r.publish('websocket', response)
        pass

def call_task(fn, *args, **kwargs):
    """
    gets celery signature, executes
    """
    if settings.RUN_ASYNC:

        res = fn.delay(*args, **kwargs)
    else:
        res = fn.apply(*args, **kwargs)
    return res


@shared_task(base=CallbackTask, name="count_resources")
def count_resources(compare_id):
    comp = Compare.objects.get(id=compare_id)
    sort_resources(comp.id)
    total, unchanged, missing, added, changed = comp.count_resources()
    return total, unchanged, missing, added, changed


@shared_task(base=CallbackTask, name="expand_warc")
def expand_warc(archive_id):
    archive = Archive.objects.get(id=archive_id)
    archive.expand_warc_create_resources()
    return {
        "task": "expand_warc",
        "archive": archive_id,
    }


@shared_task(base=CallbackTask, name="initial_compare")
def initial_compare(compare_id):
    """
    compare just the submitted_url resources (the most-likely html response user will see on request of url)
    this allows the site to replay in full while showing highlights
    """
    compare_obj = Compare.objects.get(id=compare_id)
    archive1 = compare_obj.archive1
    archive2 = compare_obj.archive2

    archive1.expand_warc_create_resources()
    archive2.expand_warc_create_resources()

    # FIXME: actually handle case where we have two resources with same URL
    resource1 = archive1.resources.filter(submitted_url=True)[0]
    resource2 = archive1.resources.filter(submitted_url=True)[0]
    rc, created = ResourceCompare.objects.get_or_create(resource1=resource1, resource2=resource2)
    print("created new main resource compare: %s" % created)

    create_html_diffs(compare_id, rc.id)

    return {
        "task": "initial_compare",
        "status": "success",
        "compare_id": compare_id,
    }


@shared_task(base=CallbackTask, name="create_html_diffs")
def create_html_diffs(compare_id, resource_compare_id):
    print("calling create_html_diffs", compare_id, resource_compare_id)
    comp = Compare.objects.get(id=compare_id)
    rc = ResourceCompare.objects.get(id=resource_compare_id)
    if "image" in rc.resource1.content_type:
        # TODO: handle image comparisons
        # maybe using imagemagick here
        return {
            "task": "create_html_diffs",
            "status": "error",
            "reason": "image"
        }
    if not rc.html_added or not rc.html_deleted:
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

    if comp.archive1.submitted_url == rc.resource1.url and comp.archive2.submitted_url == rc.resource2.url:
        comp.submitted_url_compare_ready = True
        comp.save()
        rc.is_submitted_url = True
        rc.save()

    return {
        "task": "create_html_diffs",
        "is_submitted_url": rc.is_submitted_url,
        "status": "success",
        "compare_id": compare_id,
        "rc_id": resource_compare_id,
    }


@shared_task(base=CallbackTask, name="sort_resources")
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
                    call_task(compare_resource.s(comp.id, resource.id, resource2.id))

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


@shared_task(base=CallbackTask, name="compare_resources")
def compare_resource(compare_id, resource1_id, resource2_id, is_submitted_url=False):
    rc, created = ResourceCompare.objects.get_or_create(resource1=resource1_id, resource2=resource2_id)
    if not rc.resource1.payload or not rc.resource2.payload:
        print("impossible to compare", rc.resource1.id, rc.resource2.id)
        return
    compared = calculate_similarity_pair(rc.resource1.payload, rc.resource2.payload, minhash=True, simhash=False, sequence_match=False)
    rc.change = compared['minhash']
    create_html_diffs(compare_id, rc.id)
    rc.completed = True
    rc.save()
    comp = Compare.objects.get(id=compare_id)
    comp.resource_compares.add(rc)
    return {
        "compare_id": compare_id,
        "task": "compare_resource",
        "is_submitted_url": is_submitted_url,
        "completed": True,
    }
