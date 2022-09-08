import errno
import logging
import os

import pytest
from myrm import rmlib


def test_rm_with_error(mocker):
    remove_mock = mocker.patch("myrm.rmlib.os.remove")
    remove_mock.side_effect = OSError(errno.EPERM, "")
    logger_mock = mocker.patch("myrm.rmlib.logger")

    with pytest.raises(SystemExit) as exit_info:
        rmlib.rm("")

    assert exit_info.value.code == errno.EPERM
    logger_mock.error.assert_called_with(
        "The determined path can't be removed from the current machine."
    )


def test_rm(fake_tree, caplog, mocker):
    logger_mock = mocker.patch("myrm.rmlib.logger")
    path = fake_tree[1]

    with caplog.at_level(logging.INFO):
        rmlib.rm(path)

    logger_mock.info.assert_called_with("Item '%s' was removed without errors.", path)
    assert not os.path.exists(path)


def test_rmdir_with_error(mocker):
    walk_mock = mocker.patch("myrm.rmlib.os.walk")
    walk_mock.side_effect = OSError(errno.EPERM, "")
    logger_mock = mocker.patch("myrm.rmlib.logger")

    with pytest.raises(SystemExit) as exit_info:
        rmlib.rmdir("")

    assert exit_info.value.code == errno.EPERM
    logger_mock.error.assert_called_with("The determined path don't exist on the current machine.")


def test_rmdir(fake_tree, mocker, caplog):
    logger_mock = mocker.patch("myrm.rmlib.logger")
    path = fake_tree[0]

    with caplog.at_level(logging.INFO):
        rmlib.rmdir(path)

    logger_mock.info.assert_called_with("Directory '%s' was removed without errors.", path)
    assert not os.path.exists(path)


def test_rmdir_inner_with_error(fake_tree, mocker):
    rmdir_mock = mocker.patch("myrm.rmlib.os.rmdir")
    rmdir_mock.side_effect = OSError(errno.EPERM, "")
    logger_mock = mocker.patch("myrm.rmlib.logger")

    with pytest.raises(SystemExit) as exit_info:
        rmlib.rmdir(fake_tree[0])

    assert exit_info.value.code == errno.EPERM
    logger_mock.error.assert_called_with(
        "The determined path can't be removed from the current machine."
    )


def test_rmdir_root_with_error(fake_tree, mocker):
    rmdir_mock = mocker.patch("myrm.rmlib.os.rmdir")
    rmdir_mock.side_effect = OSError(errno.EPERM, "")
    logger_mock = mocker.patch("myrm.rmlib.logger")

    with pytest.raises(SystemExit) as exit_info:
        rmlib.rmdir(fake_tree[2])

    assert exit_info.value.code == errno.EPERM
    logger_mock.error.assert_called_with(
        "The determined path can't be removed from the current machine."
    )


def test_mkdir_with_error(mocker):
    makedirs_mock = mocker.patch("myrm.rmlib.os.makedirs")
    makedirs_mock.side_effect = OSError(errno.EPERM, "")
    logger_mock = mocker.patch("myrm.rmlib.logger")

    with pytest.raises(SystemExit) as exit_info:
        rmlib.mkdir("")

    assert exit_info.value.code == errno.EPERM
    logger_mock.error.assert_called_with(
        "It's impossible to create a new directory on the current machine."
    )


def test_mkdir(caplog, mocker, fs):
    logger_mock = mocker.patch("myrm.rmlib.logger")
    path = "dir"

    with caplog.at_level(logging.INFO):
        rmlib.mkdir(path)

    logger_mock.info.assert_called_with(
        "The required directory '%s' was created on the current machine.", path
    )
    assert os.path.exists(path)


def test_mv_with_error(mocker):
    rename_mock = mocker.patch("myrm.rmlib.os.rename")
    rename_mock.side_effect = OSError(errno.EPERM, "")
    logger_mock = mocker.patch("myrm.rmlib.logger")

    with pytest.raises(SystemExit) as exit_info:
        rmlib.mv("", "")

    assert exit_info.value.code == errno.EPERM
    logger_mock.error.assert_called_with("Can't move the determined item to the destination path.")


def test_mv(caplog, mocker, fs):
    logger_mock = mocker.patch("myrm.rmlib.logger")
    src = "1.txt"
    fs.create_file(src)
    dst = "2.txt"

    with caplog.at_level(logging.INFO):
        rmlib.mv(src, dst)

    logger_mock.info.assert_called_with(
        "Item '%s' was moved to '%s' as the destination path.", src, dst
    )
    assert os.path.exists(dst)
    assert not os.path.exists(src)


def test_mvdir_with_error(mocker):
    walk_mock = mocker.patch("myrm.rmlib.os.walk")
    walk_mock.side_effect = OSError(errno.EPERM, "")
    logger_mock = mocker.patch("myrm.rmlib.logger")

    with pytest.raises(SystemExit) as exit_info:
        rmlib.mvdir("", "")

    assert exit_info.value.code == errno.EPERM
    logger_mock.error.assert_called_with("The determined path don't exist on the current machine.")


def test_mvdir(fake_tree, mocker, caplog):
    logger_mock = mocker.patch("myrm.rmlib.logger")
    src = fake_tree[0]
    dst = "test_dir"

    with caplog.at_level(logging.INFO):
        rmlib.mvdir(src, dst)

    logger_mock.info.assert_called_with(
        "Directory '%s' was moved to '%s' as a destination path.", src, dst
    )
    assert os.path.exists(dst)
    assert not os.path.exists(src)
