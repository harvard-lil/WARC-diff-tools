import os
import pytest
from compare.models import Compare, Archive
# from gevent import monkey; monkey.patch_all()

@pytest.mark.django_db(transaction=True)
def test_archive():
    archive = Archive.objects.create(
        submitted_url="http://example.com",
        timestamp="01012001",
    )
    archive.save()
    collection_path = archive.get_full_collection_path()
    assert not os.path.exists(collection_path)

    archive.create_collections_dir()
    assert os.path.exists(collection_path)