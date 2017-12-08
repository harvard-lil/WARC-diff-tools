import os
from django.db import models
from django.conf import settings
from werkzeug.test import Client
from werkzeug.wrappers import BaseResponse
from pywb.apps.frontendapp import FrontEndApp

# from dashboard.utils import

class Compare(models.Model):
    id = models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')
    warc1 = models.ForeignKey('WDTArchive', related_name='compare_warc1', null=True)
    warc2 = models.ForeignKey('WDTArchive', related_name='compare_warc2', null=True)


class WDTArchive(models.Model):
    # file name ending with warc.gz
    warc_name = models.TextField()
    # parent directory where warc.gz is contained
    warc_dir = models.TextField()
    # user inputted timestamp, not a django timestamp object
    timestamp = models.CharField(max_length=255)
    submitted_url = models.URLField(max_length=1000)

    def get_recording_url(self):
        return settings.BASE_URL + settings.ARCHIVES_ROUTE + '/' + self.warc_dir + '/' + 'record' + '/' + self.timestamp + "/" + self.submitted_url

    def get_full_collection_path(self):
        return settings.COLLECTIONS_DIR + '/' + self.warc_dir

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
        return '/' + self.warc_dir + '/' + self.timestamp + '/' + self.submitted_url

    def get_full_local_url(self):
        return settings.BASE_URL + settings.ARCHIVES_ROUTE + '/' + self.warc_dir + '/' + self.timestamp + '/' + self.submitted_url

    def replay_url(self, url=None):
        application = FrontEndApp(
            config_file='config/config.yaml',
            custom_config={
                'debug': True,
                'framed_replay': False})

        client = Client(application, BaseResponse)
        return client.get(self.get_local_url(), follow_redirects=True)

    def create_collections_dir(self):
        collection_path = self.get_full_collection_path()
        if not os.path.exists(collection_path):
            os.mkdir(collection_path)

    def warc_exists(self):
        try:
            full_warc_path = self.get_full_warc_path()
            return os.path.exists(full_warc_path)
        except FileNotFoundError:
            return False

    def get_record_or_local_url(self):
        if self.warc_exists():
            return self.get_full_local_url()
        else:
            return self.get_recording_url()