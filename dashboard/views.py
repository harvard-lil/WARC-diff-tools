import os
import requests

from django.shortcuts import render, render_to_response
from django.conf import settings

from dashboard.utils import format_date_for_memento, url_to_dirname


def index(request):
    return render(request, "index.html")


def record(request):
    """
    Take requested timestamp and url and create a new archive in a unique directory
    unless one already exists
    """
    request_data = request.POST.dict()
    submitted_url = request_data['submitted_url']
    old_timestamp = format_date_for_memento(request_data['old_date'])
    new_timestamp = format_date_for_memento(request_data['new_date'])

    archive_paths = []

    url_dirname = url_to_dirname(submitted_url)

    for timestamp in (old_timestamp, new_timestamp):
        collection_name = timestamp + '_' + url_dirname
        collection_path = settings.COLLECTIONS_DIR + '/' + collection_name
        archive_paths.append(settings.ARCHIVES_ROUTE + '/' + collection_name + '/' + timestamp + '/' + submitted_url)

        if not os.path.exists(collection_path):
            os.mkdir(collection_path)
            archiving_request = settings.BASE_URL + settings.ARCHIVES_ROUTE + '/' + collection_name + '/record/' + timestamp + '/' + submitted_url
            requests.get(archiving_request)

    data = {
        'old_archive': archive_paths[0],
        'new_archive': archive_paths[1]
    }

    return render_to_response("compare.html", data)

