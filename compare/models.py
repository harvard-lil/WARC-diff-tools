import os
import json
from datetime import datetime
from werkzeug.test import Client
from werkzeug.wrappers import BaseResponse
from pywb.apps.frontendapp import FrontEndApp
from warcio.archiveiterator import ArchiveIterator

from django.db import models
from django.conf import settings


class Compare(models.Model):
    id = models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')
    archive1 = models.ForeignKey('Archive', related_name='compare_archive1', null=True)
    archive2 = models.ForeignKey('Archive', related_name='compare_archive2', null=True)
    completed = models.BooleanField(default=False)

    def __str__(self):
        return 'Compare %s + %s' % (self.archive1.id, self.archive2.id)



class Archive(models.Model):
    # file name ending with warc.gz
    warc_name = models.TextField()
    # user inputted timestamp, not a django timestamp object
    timestamp = models.CharField(max_length=255, db_index=True)
    submitted_url = models.URLField(max_length=2000, db_index=True)
    resources = models.ManyToManyField('Resource')
    completed = models.BooleanField(default=False)

    def __str__(self):
        return self.submitted_url

    def get_warc_dir(self):
        return settings.ARCHIVES_DIR_STRING + str(self.id)

    def get_recording_url(self):
        return settings.ARCHIVES_ROUTE + '/' + self.get_warc_dir() + '/' + 'record' + '/' + self.timestamp + "/" + self.submitted_url

    def get_full_collection_path(self):
        tmp_path = os.path.join(settings.COLLECTIONS_DIR,  self.get_warc_dir())
        return os.path.join(settings.PROJECT_ROOT, tmp_path)

    def get_full_warc_path(self):
        full_archive_parent_path = self.get_full_collection_path() + settings.WARC_ARCHIVE_DIR
        if not os.path.exists(full_archive_parent_path):
            raise FileNotFoundError("Collection not found")
        dir_contents = os.listdir(full_archive_parent_path)
        if not self.warc_name:
            for f in dir_contents:
                if 'warc.gz' in f:
                    self.warc_name = f
                    self.save()
                    break

        return full_archive_parent_path + "/" + self.warc_name

    def get_local_url(self):
        return settings.ARCHIVES_ROUTE + '/' + self.get_warc_dir() + '/' + self.timestamp + '/' + self.submitted_url

    def get_full_local_url(self):
        return settings.BASE_URL + self.get_local_url()

    def get_replay_url(self):
        return '/' + self.get_warc_dir() + '/' + self.timestamp + '/' + self.submitted_url

    def replay_url(self, url=None):
        application = FrontEndApp(
            config_file='config/config.yaml',
            custom_config={
                'debug': True,
                'framed_replay': False})

        client = Client(application, BaseResponse)
        if url:
            return client.get(url, follow_redirects=True)
        else:
            return client.get(self.get_replay_url(), follow_redirects=True)

    def create_collections_dir(self):
        collection_path = self.get_full_collection_path()
        if not os.path.exists(collection_path):
            os.mkdir(collection_path)

    def warc_exists(self):
        try:
            return os.path.exists(self.get_full_warc_path())
        except FileNotFoundError:
            return False

    def get_record_or_local_url(self):
        if self.warc_exists():
            return self.get_local_url()
        else:
            return self.get_recording_url()

    def get_friendly_timestamp(self):
        d = datetime.strptime(self.timestamp, "%Y%m%d")
        return str(d.date())

    def expand_warc_create_resources(self):
        """
        expand warcs into dicts with compressed responses
        organized by content type
        Each response obj consists of compressed payload and SHA1
        """
        with open(self.get_full_warc_path(), 'rb') as stream:
            for record in ArchiveIterator(stream):
                if record.rec_type != 'response':
                    continue

                url = record.rec_headers.get_header('WARC-Target-URI')
                headers = record.http_headers
                try:
                    # content_type = format_content_type(headers['Content-Type'])
                    content_type = headers.get_header('Content-Type')
                except KeyError:
                    # HACK: figure out a better solution for unknown content types
                    content_type = "unknown"
                try:
                    payload = record.content_stream().read().decode()
                except UnicodeDecodeError as e:
                    if 'image' in content_type:
                        payload = ''
                    else:
                        print("something went wrong", url)
                        print(content_type)



                # TODO: figure out what to do with headersw
                if not self.completed:
                    res = Resource.objects.create(
                        url=url,
                        content_type=content_type,
                        payload=payload,
                        hash=record.rec_headers.get('warc-payload-digest')
                    )
                    self.resources.add(res)
                    self.save()

            if not self.completed:
                self.completed = True
                self.save()
                self.refresh_from_db(fields=['completed', 'resources'])




class Resource(models.Model):
    STATUS_CHOICES = (
        ('m', 'missing'),
        ('a', 'added'),
        ('c', 'changed'),
        ('u', 'unchanged'),
        ('p', 'pending'),
    )
    url = models.URLField(max_length=2000)
    content_type = models.CharField(max_length=1000)
    status = models.CharField(choices=STATUS_CHOICES, default='p', max_length=1)
    payload = models.TextField()
    hash = models.CharField(max_length=1000)
    headers = models.TextField()

    def __str__(self):
        return self.url


class ResourceCompare(models.Model):
    resource1 = models.ForeignKey('Resource', related_name='resource1',  null=True)
    resource2 = models.ForeignKey('Resource', related_name='resource2', null=True)
    minhash = models.FloatField()
    simhash = models.FloatField()
    sequence_match = models.FloatField()
    html_deleted = models.TextField()
    html_added = models.TextField()
    html_combined = models.TextField()

    def __str__(self):
        return 'Compare %s + %s' % (self.resource1.id, self.resource2.id)

