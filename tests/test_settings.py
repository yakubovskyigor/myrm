import errno
import io
import json
import logging
import os

import pytest

from myrm import settings


def test_positive_integer(fake_positive_number_field):
    number = 10
    fake_positive_number_field.test = number
    assert fake_positive_number_field.test == number


def test_positive_integer_with_error(fake_positive_number_field):
    number = -10

    with pytest.raises(settings.ValidationError) as exc_info:
        fake_positive_number_field.test = number

    assert str(exc_info.value) == "Can't be negative."


def test_positive_integer_with_inner_error(fake_positive_number_field):
    number = ""

    with pytest.raises(settings.ValidationError) as exc_info:
        fake_positive_number_field.test = number

    assert (
        str(exc_info.value) == f"The field must be positive integer but received: {type(number)}."
    )


def test_path_field(fake_path_field):
    path = "~"
    fake_path_field.test = path
    assert fake_path_field.test == os.path.expanduser(path)


def test_path_field_with_error(fake_path_field):
    path = 10

    with pytest.raises(settings.ValidationError) as exc_info:
        fake_path_field.test = path

    assert str(exc_info.value) == f"The path must be string but received: {type(path)}."


def test_bool_field(fake_bool_field):
    flag = False
    fake_bool_field.test = flag
    assert fake_bool_field.test == flag


def test_bool_field_with_error(fake_bool_field):
    flag = 10

    with pytest.raises(settings.ValidationError) as exc_info:
        fake_bool_field.test = flag

    assert str(exc_info.value) == f"The field must be boolean but received: {type(flag)}."


def test_app_settings():
    test_settings = {
        "bucket_path": "test",
        "bucket_history_path": "test",
        "bucket_size": 10,
        "bucket_timeout_cleanup": 10,
    }
    app_settings = settings.AppSettings(**test_settings)
    assert app_settings.dump() == test_settings


def test_app_settings_with_error(caplog):
    test_settings = {
        "bucket_path": 10,
        "bucket_history_path": 10,
        "bucket_size": "",
        "bucket_timeout_cleanup": "",
    }

    with pytest.raises(SystemExit) as exit_info:
        settings.AppSettings(**test_settings)

    record = caplog.records[0]
    assert record.levelno == logging.ERROR
    assert (
        record.message
        == "The validation process was failed: The path must be string but received: <class 'int'>."
    )
    assert exit_info.value.code == errno.EPERM


def test_generate(fs):
    path = "test.json"
    settings.generate(path)
    assert os.path.isfile(path)

    with io.open(path, mode="rt", encoding="utf-8") as stream_in:
        assert json.load(stream_in) == settings.AppSettings().dump()


def test_generate_inside_dir(fs):
    path = "test/test.json"
    settings.generate(path)
    assert os.path.isdir(os.path.dirname(path))


def test_generate_with_error(mocker):
    open_mock = mocker.patch("myrm.settings.io.open")
    open_mock.side_effect = IOError(errno.EIO, "")
    logger_mock = mocker.patch("myrm.settings.logger")

    with pytest.raises(SystemExit) as exit_info:
        settings.generate("")

    assert exit_info.value.code == errno.EIO
    logger_mock.error.assert_called_with(
        "It's impossible to generate the settings on the current machine."
    )


def test_load(fs):
    path = "test.json"
    data = {
        "bucket_path": "test",
        "bucket_history_path": "test",
        "bucket_size": 10,
        "bucket_timeout_cleanup": 101,
    }

    with io.open(path, mode="wt", encoding="utf-8") as stream_out:
        json.dump(data, stream_out)

    assert settings.load(path).dump() == data


def test_load_with_error(mocker):
    open_mock = mocker.patch("myrm.settings.io.open")
    open_mock.side_effect = IOError(errno.EIO, "")
    logger_mock = mocker.patch("myrm.settings.logger")

    with pytest.raises(SystemExit) as exit_info:
        settings.load("")

    assert exit_info.value.code == errno.EIO
    logger_mock.error.assert_called_with(
        "It's impossible to load the settings from the current machine."
    )


def test_load_with_inner_error(mocker):
    open_mock = mocker.patch("myrm.settings.io.open")
    open_mock.side_effect = TypeError(errno.EPERM, "")
    logger_mock = mocker.patch("myrm.settings.logger")

    with pytest.raises(SystemExit) as exit_info:
        settings.load("test.txt")

    assert exit_info.value.code == errno.EPERM
    logger_mock.error.assert_called_with(
        "It's impossible to pars the provided settings or initialise settings class."
    )
