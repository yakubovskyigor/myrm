import os

import pytest

from myrm import bucket


@pytest.fixture()
def fake_tree(fs):
    paths = []

    # Step -- 1.
    root = "dir"
    fs.create_dir(root)
    paths.append(root)

    # Step -- 2.
    path = os.path.join(root, "test.txt")
    fs.create_file(path)
    paths.append(path)

    # Step -- 3.
    path = os.path.join(root, "inner_dir")
    fs.create_dir(path)
    paths.append(path)

    return paths


@pytest.fixture()
def fake_bucket_history(fs):
    return bucket.BucketHistory(path="history.pkl")


@pytest.fixture()
def fake_entry():
    return bucket.Entry(
        status=bucket.Status.CORRECT.value,
        index=2,
        name="test",
        origin="test",
        date="12:12:2012",
    )


@pytest.fixture()
def fake_bucket(fs):
    return bucket.Bucket(path="bucket", history_path="history.pkl")
