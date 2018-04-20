import os
from datetime import datetime
from werkzeug.test import Client
from werkzeug.wrappers import BaseResponse
from pywb.apps.frontendapp import FrontEndApp
from warcio.archiveiterator import ArchiveIterator

from django.db import models
from django.conf import settings

from compare import utils


class Compare(models.Model):
    id = models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')
    archive1 = models.ForeignKey('Archive', related_name='compare_archive1', null=True, on_delete=models.CASCADE)
    archive2 = models.ForeignKey('Archive', related_name='compare_archive2', null=True, on_delete=models.CASCADE)
    resource_compares = models.ManyToManyField('ResourceCompare')
    # TODO:
    submitted_url_compare_ready = models.BooleanField(default=False)
    # TODO: figure out if completed is actually useful
    # used to note that expanding archive + parsing records is completed
    completed = models.BooleanField(default=False)

    def __str__(self):
        return 'Compare %s + %s' % (self.archive1.id, self.archive2.id)

    def count_resources(self):
        old_total = self.archive1.resources.count()
        new_total = self.archive2.resources.count()
        total = (old_total, new_total)
        # arbitrarily choosing archive1, nums should be the same
        unchanged = self.archive1.resources.filter(status='u').count()
        missing = self.archive1.resources.filter(status='m').count()
        added = self.archive2.resources.filter(status='a').count()
        # arbitrarily choosing archive2, nums should be the same
        changed = self.archive2.resources.filter(status='c').count()
        return total, unchanged, missing, added, changed


class Archive(models.Model):
    # file name ending with warc.gz
    warc_name = models.TextField()

    # user inputted timestamp, not a django timestamp object
    requested_date = models.CharField(max_length=255, db_index=True)

    # actual timestamp of the creation of the archive
    actual_timestamp = models.DateTimeField(null=True)
    submitted_url = models.URLField(max_length=2000, db_index=True)
    resources = models.ManyToManyField('Resource')
    completed = models.BooleanField(default=False)

    def __str__(self):
        return self.submitted_url

    def create(self, *args, **kwargs):
        self.create_collections_dir()
        super(Archive, self).create(*args, **kwargs)

    def reset(self):
        """
        delete all resources to make way for new comparison
        """
        self.resources.all().delete()
        self.completed = False
        self.save()

    def get_warc_dir(self):
        return settings.ARCHIVES_DIR_STRING + str(self.id)

    def get_recording_url(self, url=None):
        base = settings.ARCHIVES_ROUTE + '/' + self.get_warc_dir() + '/' + 'record' + '/' + self.requested_date
        if not url:
            return base + '/' + self.submitted_url
        else:
            raise NotImplemented('should return recording url then redirect to url')

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

    def get_local_url(self, url=None):
        base = settings.ARCHIVES_ROUTE + '/' + self.get_warc_dir() + '/' + self.requested_date
        if not url:
            return base + '/' + self.submitted_url
        else:
            # TODO: figure out what to do with multiple urls
            if self.resources.filter(url=url):
                return base + '/' + url
            else:
                return 'warcdiff-404.html'

    def get_full_local_url(self):
        return settings.BASE_URL + self.get_local_url()

    def get_replay_url(self, url=None):
        url = url if url else self.submitted_url
        base_url = '/' + self.get_warc_dir() + '/' + self.requested_date
        return base_url + '/' + url

    def replay_url(self, url=None):
        application = FrontEndApp(
            config_file='config/config.yaml',
            custom_config={
                'debug': True,
                'framed_replay': False})

        client = Client(application, BaseResponse)
        return client.get(self.get_replay_url(url=url), follow_redirects=True)

    def create_collections_dir(self):
        collection_path = self.get_full_collection_path()
        if not os.path.exists(collection_path):
            os.mkdir(collection_path)

    def warc_exists(self):
        try:
            return os.path.exists(self.get_full_warc_path())
        except FileNotFoundError:
            return False

    def get_record_or_local_url(self, url=None):
        if self.warc_exists():
            return self.get_local_url(url=url)
        else:
            return self.get_recording_url(url=url)

    def get_friendly_timestamp(self):
        d = datetime.strptime(self.requested_date, "%Y%m%d")
        return str(d.date())

    def get_replayed_rewritten_resource_response(self, url):
        # TODO: figure out what to do if two matching urls present
        try:
            data = self.replay_url(url=url).data.decode()
        except UnicodeDecodeError:
            data = self.replay_url(url=url).data.decode('latin-1')
        # TODO: rewrite response here
        return data

    def expand_warc_create_resources(self):
        """
        expand warcs into dicts with compressed responses
        organized by content type
        Each response obj consists of compressed payload and SHA1
        """
        if self.completed:
            return
        with open(self.get_full_warc_path(), 'rb') as stream:
            for record in ArchiveIterator(stream):
                if record.rec_type != 'response':
                    continue

                url = record.rec_headers.get_header('WARC-Target-URI')
                print('saving url', url)
                headers = record.http_headers
                try:
                    # content_type = format_content_type(headers['Content-Type'])
                    content_type = headers.get_header('Content-Type')
                except KeyError:
                    # HACK: figure out a better solution for unknown content types
                    content_type = "unknown"
                try:
                    payload = utils.decode_data(record.content_stream().read())
                except UnicodeDecodeError as e:
                    if 'image' in content_type:
                        payload = ''
                    else:
                        print("something went wrong", url, e)
                        print(content_type)
                        payload = ''
                # TODO: figure out what to do with headers
                try:
                    res = Resource.objects.create(
                        url=url,
                        content_type=content_type,
                        payload=payload,
                        headers=str(record.rec_headers),
                        hash=record.rec_headers.get('warc-payload-digest')
                    )
                    self.resources.add(res)
                except Exception as e:
                    print("expand_warc_create_resources exception", self.id, url, record, record.rec_headers, e)
        # treat submitted_url as special because there might be redirects
        # TODO: is this the right place for it? should it be done?
        response = self.replay_url(self.submitted_url)
        payload = utils.decode_data(response.data)
        res = Resource.objects.create(
            url=self.submitted_url,
            content_type=response.headers.get('content-type'),
            payload=payload,
            headers=str(response.headers),
            submitted_url=True,
        )
        self.resources.add(res)
        self.completed = True
        self.save()


class Resource(models.Model):
    # TODO: maybe remove these, not needed
    STATUS_CHOICES = (
        ('m', 'missing'),
        ('a', 'added'),
        ('c', 'changed'),
        ('u', 'unchanged'),
        ('p', 'pending'),
    )
    url = models.URLField(max_length=3000)
    content_type = models.CharField(max_length=1000)
    status = models.CharField(choices=STATUS_CHOICES, default='p', max_length=1)
    payload = models.TextField()
    hash = models.CharField(max_length=1000)
    headers = models.TextField()
    submitted_url = models.BooleanField(default=False)

    def __str__(self):
        return self.url


def compare_file_dir_path(instance, filename):
    return "{0}/{1}".format(instance.id, filename)


class ResourceCompare(models.Model):
    resource1 = models.ForeignKey('Resource', related_name='resource1', null=True, on_delete=models.CASCADE)
    resource2 = models.ForeignKey('Resource', related_name='resource2', null=True, on_delete=models.CASCADE)
    change = models.FloatField(null=True)
    html_deleted = models.FileField(upload_to=compare_file_dir_path, null=True)
    html_added = models.FileField(upload_to=compare_file_dir_path, null=True)
    html_combined = models.FileField(upload_to=compare_file_dir_path, null=True)
    submitted_url = models.BooleanField(default=False)

    def __str__(self):
        return 'Compare %s + %s' % (self.resource1.id, self.resource2.id)

