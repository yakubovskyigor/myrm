import errno
import io
import os
import pickle

import pytest

from myrm import bucket


def test_read_bucket_history_with_error(mocker, fake_bucket_history):
    open_mock = mocker.patch("myrm.bucket.io.open")
    open_mock.side_effect = OSError(errno.EPERM, "")
    logger_mock = mocker.patch("myrm.bucket.logger")

    with pytest.raises(SystemExit) as exit_info:
        fake_bucket_history._read()

    assert exit_info.value.code == errno.EPERM
    logger_mock.error.assert_called_with(
        "It's impossible to restore the history state on the current machine."
    )


def test_write_bucket_history_with_error(mocker, fake_bucket_history):
    open_mock = mocker.patch("myrm.bucket.io.open")
    open_mock.side_effect = OSError(errno.EPERM, "")
    logger_mock = mocker.patch("myrm.bucket.logger")

    with pytest.raises(SystemExit) as exit_info:
        fake_bucket_history._write()

    assert exit_info.value.code == errno.EPERM
    logger_mock.error.assert_called_with(
        "It's impossible to save the history state on the current machine."
    )


def test_bucket_history_read(fs):
    path = "test.pkl"
    data = {1: "a", 2: "b"}
    with io.open(path, mode="wb") as stream_out:
        pickle.dump(data, stream_out, protocol=pickle.HIGHEST_PROTOCOL)

    assert bucket.BucketHistory(path=path) == data


def test_bucket_history_write(fake_bucket_history):
    data = {1: "a", 2: "b"}
    fake_bucket_history.update(data)

    with io.open(fake_bucket_history.path, mode="rb") as stream_in:
        assert pickle.load(stream_in) == data


def test_bucket_history_delete_item(fake_bucket_history, fake_entry):
    fake_bucket_history["test"] = fake_entry

    del fake_bucket_history["test"]
    assert "test" not in fake_bucket_history.keys()


def test_bucket_history_get_indexes(fake_bucket_history, fake_entry):
    fake_bucket_history["test"] = fake_entry
    fake_bucket_history.get_indexes()

    assert fake_bucket_history.get_indexes() == [2]


def test_bucket_history_get_next_index(fake_bucket_history, fake_entry):
    fake_bucket_history["test"] = fake_entry
    fake_bucket_history.get_next_index()

    assert fake_bucket_history.get_next_index() == 3


def test_bucket_history_cleanup(fake_bucket_history, fake_entry):
    fake_bucket_history["test"] = fake_entry
    fake_bucket_history.cleanup(dry_run=False)

    assert fake_bucket_history == {}

    with io.open(fake_bucket_history.path, mode="rb") as stream_in:
        assert pickle.load(stream_in) == {}


def test_bucket_history_cleanup_with_dry_run(fake_bucket_history, fake_entry):
    fake_bucket_history["test"] = fake_entry
    fake_bucket_history.cleanup(dry_run=True)

    assert fake_bucket_history["test"] == fake_entry

    with io.open(fake_bucket_history.path, mode="rb") as stream_in:
        assert pickle.load(stream_in) == fake_bucket_history


def test_bucket_history_show(fake_bucket_history, fake_entry):
    fake_bucket_history["test"] = fake_entry
    assert fake_bucket_history.show(1, 1) is not None


def test_bucket_history_show_with_error(mocker, fake_bucket_history, fake_entry):
    fake_bucket_history["test"] = fake_entry
    logger_mock = mocker.patch("myrm.bucket.logger")

    with pytest.raises(SystemExit) as exit_info:
        fake_bucket_history.show(22, 22)

    assert exit_info.value.code == errno.EPERM
    logger_mock.error.assert_called_with("It's impossible to show the provided page number.")


def test_bucket_history_show_with_inner_error(mocker, fake_bucket_history):
    logger_mock = mocker.patch("myrm.bucket.logger")

    with pytest.raises(SystemExit) as exit_info:
        fake_bucket_history.show(1, 1)

    assert exit_info.value.code == errno.EPERM
    logger_mock.warning.assert_called_with("History is empty.")


def test_bucket_create(fake_bucket):
    fake_bucket.create(dry_run=False)
    assert os.path.isdir(fake_bucket.path)


def test_bucket_create_with_dry_run(fake_bucket):
    fake_bucket.create(dry_run=True)
    assert not os.path.exists(fake_bucket.path)


def test_bucket_get_size_with_error(mocker, fake_bucket):
    walk_mock = mocker.patch("myrm.bucket.os.walk")
    walk_mock.side_effect = OSError(errno.EPERM, "")
    logger_mock = mocker.patch("myrm.bucket.logger")

    with pytest.raises(SystemExit) as exit_info:
        fake_bucket._get_size("")

    assert exit_info.value.code == errno.EPERM
    logger_mock.error.assert_called_with("The determined path don't exist on the current machine.")


def test_bucket_get_size_with_inner_error(mocker, fake_bucket, fs):
    path = "test.txt"
    fs.create_file(path)

    get_mock = mocker.patch("myrm.bucket.os.path.getsize")
    get_mock.side_effect = IOError(errno.EIO, "")
    logger_mock = mocker.patch("myrm.bucket.logger")

    with pytest.raises(SystemExit) as exit_info:
        fake_bucket._get_size(path)

    assert exit_info.value.code == errno.EIO
    logger_mock.error.assert_called_with(
        "It's impossible to calculate size of the determined path."
    )


def test_bucket_get_size(fake_bucket, fs):
    fs.create_file(os.path.join(fake_bucket.path, "test.txt"), contents="test")
    assert fake_bucket._get_size(fake_bucket.path) > 0


def test_bucket_get_size_dir(fake_bucket, fs):
    fs.create_file(os.path.join(fake_bucket.path, "test"), contents="test")
    assert fake_bucket._get_size(fake_bucket.path) > 0


def test_bucket_cleanup(fake_bucket, fs):
    fs.create_file(os.path.join(fake_bucket.path, "test"))
    fake_bucket.cleanup(dry_run=False)

    assert fake_bucket.history == {}
    assert os.path.isdir(fake_bucket.path)
    assert not os.listdir(fake_bucket.path)


def test_bucket_cleanup_with_dry_run(fake_bucket, fs, fake_entry):
    fs.create_file(os.path.join(fake_bucket.path, "test"))
    fake_bucket.history["test"] = fake_entry
    fake_bucket.cleanup(dry_run=True)

    assert fake_bucket.history["test"] == fake_entry
    assert os.path.isdir(fake_bucket.path)
    assert os.listdir(fake_bucket.path)


def test_bucket_rm_file(fake_bucket, fs):
    path = "test"
    fs.create_file(path)
    fake_bucket._rm(path, dry_run=False)

    assert not os.path.exists(path)


def test_bucket_rm_file_with_dry_run(fake_bucket, fs):
    path = "test"
    fs.create_file(path)
    fake_bucket._rm(path, dry_run=True)

    assert os.path.exists(path)


def test_bucket_rm_link(fake_bucket, fs):
    path = "test"
    link = "test_lik"
    fs.create_file(path)
    fs.create_link(path, link)
    fake_bucket._rm(link, dry_run=False)

    assert not os.path.exists(link)


def test_bucket_rm_link_with_dry_run(fake_bucket, fs):
    path = "test"
    link = "test_lik"
    fs.create_file(path)
    fs.create_link(path, link)
    fake_bucket._rm(link, dry_run=True)

    assert os.path.exists(link)


def test_bucket_rm_dir(fake_bucket, fs):
    path = "test"
    fs.create_dir(path)
    fake_bucket._rm(path, dry_run=False)

    assert not os.path.exists(path)


def test_bucket_rm_dir_with_dry_run(fake_bucket, fs):
    path = "test"
    fs.create_dir(path)
    fake_bucket._rm(path, dry_run=True)

    assert os.path.exists(path)


def test_bucket_mv_file(fake_bucket, fake_tree, fs):
    fake_bucket.create()

    path = "test"
    fs.create_file(path)
    fake_bucket._mv(path, dry_run=False)

    assert not os.path.exists(path)
    assert os.listdir(fake_bucket.path)
    assert list(fake_bucket.history.values())[0].name == path


def test_bucket_mv_file_with_dry_run(fake_bucket, fake_tree, fs):
    fake_bucket.create()

    path = "test"
    fs.create_file(path)
    fake_bucket._mv(path, dry_run=True)

    assert os.path.exists(path)
    assert not os.listdir(fake_bucket.path)
    assert list(fake_bucket.history.values())[0].name == path


def test_bucket_mv_dir(fake_bucket, fs):
    fake_bucket.create()

    path = "test"
    fs.create_dir(path)
    fake_bucket._mv(path, dry_run=False)

    assert not os.path.exists(path)
    assert os.listdir(fake_bucket.path)
    assert list(fake_bucket.history.values())[0].name == path


def test_bucket_mv_dir_with_dry_run(fake_bucket, fs):
    fake_bucket.create()

    path = "test"
    fs.create_dir(path)
    fake_bucket._mv(path, dry_run=True)

    assert os.path.exists(path)
    assert not os.listdir(fake_bucket.path)
    assert list(fake_bucket.history.values())[0].name == path


def test_bucket_rm_force_file(fake_bucket, fs):
    path = "test"
    fs.create_file(path)
    fake_bucket.rm(path, force=True, dry_run=False)

    assert not os.path.exists(path)


def test_bucket_rm_force_file_with_dry_run(fake_bucket, fs):
    path = "test"
    fs.create_file(path)
    fake_bucket.rm(path, force=True, dry_run=True)

    assert os.path.exists(path)


def test_bucket_rm_not_force_file(fake_bucket, fs):
    fake_bucket.create()

    path = "test"
    fs.create_file(path)
    fake_bucket.rm(path, dry_run=False)

    assert not os.path.exists(path)
    assert os.listdir(fake_bucket.path)


def test_bucket_rm_not_force_file_with_dry_run(fake_bucket, fs):
    fake_bucket.create()

    path = "test"
    fs.create_file(path)
    fake_bucket.rm(path, dry_run=True)

    assert os.path.exists(path)
    assert not os.listdir(fake_bucket.path)


def test_bucket_rm_with_error(fake_bucket, mocker, fake_tree):
    fake_bucket.maxsize = 0
    mocker.patch("myrm.bucket.os.path.getsize").return_value = 1
    logger_mock = mocker.patch("myrm.bucket.logger")

    with pytest.raises(SystemExit) as exit_info:
        fake_bucket.rm(fake_tree[0])

    assert exit_info.value.code == errno.EPERM
    logger_mock.error.assert_called_with(
        "It's impossible to move item to bucket because the bucket is full."
    )


def test_bucket_check(fake_bucket, fs):
    fake_bucket.create()

    path = "test"
    fs.create_dir(os.path.join(fake_bucket.path, path))

    fake_bucket.check()
    assert path in fake_bucket.history


def test_bucket_check_delete_key(fake_bucket, fake_entry):
    fake_bucket.create()

    fake_bucket.history["test"] = fake_entry

    fake_bucket.check()
    assert "test" not in fake_bucket.history


def test_bucket_check_with_error(fake_bucket, mocker):
    listdir_mock = mocker.patch("myrm.bucket.os.listdir")
    listdir_mock.side_effect = OSError(errno.EPERM, "")
    logger_mock = mocker.patch("myrm.bucket.logger")

    with pytest.raises(SystemExit) as exit_info:
        fake_bucket.check()

    assert exit_info.value.code == errno.EPERM
    logger_mock.error.assert_called_with("The determined path don't exist on the current machine.")


def test_bucket_timeout_cleanup_with_error(fake_bucket, mocker):
    listdir_mock = mocker.patch("myrm.bucket.os.listdir")
    listdir_mock.side_effect = OSError(errno.EPERM, "")
    logger_mock = mocker.patch("myrm.bucket.logger")

    with pytest.raises(SystemExit) as exit_info:
        fake_bucket.timeout_cleanup()

    assert exit_info.value.code == errno.EPERM
    logger_mock.error.assert_called_with("The determined path don't exist on the current machine.")


def test_bucket_timeout_cleanup_with_inner_error(fake_bucket, mocker, fs):
    fs.create_file(os.path.join(fake_bucket.path, "test"))

    stat_mock = mocker.patch("myrm.bucket.time.mktime")
    stat_mock.side_effect = OSError(errno.EPERM, "")
    logger_mock = mocker.patch("myrm.bucket.logger")
    fake_bucket.check()

    with pytest.raises(SystemExit) as exit_info:
        fake_bucket.timeout_cleanup()

    assert exit_info.value.code == errno.EPERM
    logger_mock.error.assert_called_with(
        "It's impossible to get removed time for the determined path."
    )


def test_bucket_timeout_cleanup(fake_bucket, mocker, fs):
    path = os.path.join(fake_bucket.path, "test")
    fs.create_file(path)
    fake_bucket.storetime = 1
    mocker.patch("myrm.bucket.time.time").return_value = 100
    mocker.patch("myrm.bucket.time.mktime").return_value = 10

    fake_bucket.check()
    fake_bucket.timeout_cleanup()

    assert not os.path.exists(path)


def test_bucket_restore_with_index_error(fake_bucket, mocker, fake_entry):
    fake_bucket.history["test"] = fake_entry

    logger_mock = mocker.patch("myrm.bucket.logger")

    with pytest.raises(SystemExit) as exit_info:
        fake_bucket.restore(22)

    assert exit_info.value.code == errno.EPERM
    logger_mock.error.assert_called_with("The determined index don't exist in history.")


def test_bucket_restore_with_error(fake_bucket, fs, fake_entry, mocker):
    fake_bucket.history["test"] = fake_entry
    path = fake_entry.name
    fs.create_file(path)

    logger_mock = mocker.patch("myrm.bucket.logger")

    with pytest.raises(SystemExit) as exit_info:
        fake_bucket.restore(2)

    assert exit_info.value.code == errno.EPERM
    logger_mock.error.assert_called_with(
        "The determined path can't be moved on the current machine."
    )


def test_bucket_restore_with_error_unknown_status(fake_bucket, fs, fake_entry, mocker):
    fake_entry = fake_entry._replace(status=bucket.Status.UNKNOWN.value)
    fake_bucket.history["test"] = fake_entry
    fs.create_file(fake_entry.name)

    logger_mock = mocker.patch("myrm.bucket.logger")

    with pytest.raises(SystemExit) as exit_info:
        fake_bucket.restore(2)

    assert exit_info.value.code == errno.EPERM
    logger_mock.error.assert_called_with(
        "The determined path can't be moved on the current machine."
    )


def test_bucket_restore_file(fake_bucket, fake_entry, fs):
    fake_bucket.create()
    fake_bucket.history["test"] = fake_entry

    path = "test"
    fs.create_file(os.path.join(fake_bucket.path, fake_entry.name))

    fake_bucket.restore(2, dry_run=False)

    assert os.path.exists(path)
    assert not os.listdir(fake_bucket.path)
    assert fake_bucket.history == {}


def test_bucket_restore_file_with_dry_run(fake_bucket, fake_entry, fs):
    fake_bucket.create()
    fake_bucket.history["test"] = fake_entry

    path = "test"
    fs.create_file(os.path.join(fake_bucket.path, fake_entry.name))

    fake_bucket.restore(2, dry_run=True)

    assert not os.path.exists(path)
    assert os.listdir(fake_bucket.path)
    assert fake_bucket.history["test"] == fake_entry


def test_bucket_restore_dir(fake_bucket, fake_entry, fs):
    fake_bucket.create()
    fake_bucket.history["test"] = fake_entry

    path = "test"
    fs.create_dir(os.path.join(fake_bucket.path, fake_entry.name))

    fake_bucket.restore(2, dry_run=False)

    assert os.path.exists(path)
    assert not os.listdir(fake_bucket.path)
    assert fake_bucket.history == {}


def test_bucket_restore_dir_with_dry_run(fake_bucket, fake_entry, fs):
    fake_bucket.create()
    fake_bucket.history["test"] = fake_entry

    path = "test"
    fs.create_dir(os.path.join(fake_bucket.path, fake_entry.name))

    fake_bucket.restore(2, dry_run=True)

    assert not os.path.exists(path)
    assert os.listdir(fake_bucket.path)
    assert fake_bucket.history["test"] == fake_entry


def test_bucket_startup(fake_bucket):
    fake_bucket.startup()

    assert os.path.isdir(fake_bucket.path)
    assert fake_bucket.path not in fake_bucket.history
