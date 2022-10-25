import errno
import io
import json
import logging
import os
import sys
from typing import Dict, Union, Any

from myrm import rmlib

# Create a new instance of the preferred reporting system for this program.
logger = logging.getLogger("myrm")

__all__ = (
    "HOME",
    "XDG_CONFIG_HOME",
    "XDG_DATA_HOME",
    "DEFAULT_HISTORY_PATH",
    "DEFAULT_BUCKET_PATH",
    "DEFAULT_SETTINGS_PATH",
    "SECONDS_IN_DAY",
    "BYTES_IN_MEGABYTES",
    "DEFAULT_BUCKET_SIZE",
    "DEFAULT_STORETIME",
    "DEFAULT_TIME_FORMAT",
    "ValidationError",
    "AppSettings",
    "generate",
    "load",
)


HOME: str = os.path.expanduser("~")

# Where user-specific configurations should be written.
XDG_CONFIG_HOME: str = os.path.join(HOME, ".config", "myrm")

# Where user-specific data files should be written.
XDG_DATA_HOME: str = os.path.join(HOME, ".local", "share", "myrm")

DEFAULT_HISTORY_PATH: str = os.path.join(XDG_DATA_HOME, "history.pkl")
DEFAULT_BUCKET_PATH: str = os.path.join(XDG_DATA_HOME, "bucket")
DEFAULT_SETTINGS_PATH: str = os.path.join(XDG_CONFIG_HOME, "settings.json")

SECONDS_IN_DAY: int = 24 * 60 * 60
BYTES_IN_MEGABYTES: int = 1024 * 1024

DEFAULT_BUCKET_SIZE: int = 100 * BYTES_IN_MEGABYTES
DEFAULT_STORETIME: int = 20 * SECONDS_IN_DAY
DEFAULT_TIME_FORMAT: str = "%Y-%m-%d %I:%M:%S %p"


class ValidationError(ValueError):
    """This exception will be raised when the validation path doesn't match the requirements."""


class PathField:
    def __init__(self) -> None:
        self.path = os.path.expanduser("~")

    def __get__(self, instance: Any, owner: Any) -> str:
        return self.path

    def __set__(self, instance: Any, path: str) -> None:
        if not isinstance(path, str):
            raise ValidationError(f"The path must be string but received: {type(path)}.")

        self.path = os.path.expanduser(path)


class PositiveIntegerField:
    def __init__(self) -> None:
        self.number = 0

    def __get__(self, instance: Any, owner: Any) -> int:
        return self.number

    def __set__(self, instance: Any, number: int) -> None:
        if not isinstance(number, int):
            raise ValidationError(
                f"The field must be positive integer but received: {type(number)}."
            )

        if number < 0:
            raise ValidationError("Can't be negative.")

        self.number = number


class BoolField:
    def __init__(self) -> None:
        self.flag = False

    def __get__(self, instance: Any, owner: Any) -> bool:
        return self.flag

    def __set__(self, instance: Any, flag: bool) -> None:
        if not isinstance(flag, bool):
            raise ValidationError(f"The field must be boolean but received: {type(flag)}.")

        self.flag = flag


class AppSettings:
    bucket_path = PathField()
    bucket_history_path = PathField()
    bucket_size = PositiveIntegerField()
    bucket_timeout_cleanup = PositiveIntegerField()

    def __init__(
        self,
        bucket_path: str = DEFAULT_BUCKET_PATH,
        bucket_history_path: str = DEFAULT_HISTORY_PATH,
        bucket_size: int = DEFAULT_BUCKET_SIZE,
        bucket_timeout_cleanup: int = DEFAULT_STORETIME,
    ) -> None:
        try:
            self.bucket_path = bucket_path
            self.bucket_history_path = bucket_history_path
            self.bucket_size = bucket_size
            self.bucket_timeout_cleanup = bucket_timeout_cleanup
        except ValidationError as err:
            logger.error("The validation process was failed: %s", err)
            logger.debug("An unexpected error occurred at this program runtime:", exc_info=True)
            # Stop this program runtime and return the exit status code.
            sys.exit(getattr(err, "errno", errno.EPERM))

    def __str__(self) -> str:
        return json.dumps(self.dump(), indent=2)

    def dump(self) -> Dict[str, Union[str, int]]:
        return {
            "bucket_path": self.bucket_path,
            "bucket_history_path": self.bucket_history_path,
            "bucket_size": self.bucket_size,
            "bucket_timeout_cleanup": self.bucket_timeout_cleanup,
        }


def generate(path: str) -> None:
    dirname = os.path.dirname(path)
    if dirname:
        rmlib.mkdir(dirname)

    try:
        with io.open(path, mode="wt", encoding="utf-8") as stream_out:
            stream_out.write(str(AppSettings()))
    except (OSError, IOError) as err:
        logger.error("It's impossible to generate the settings on the current machine.")
        logger.debug("An unexpected error occurred at this program runtime:", exc_info=True)
        # Stop this program runtime and return the exit status code.
        sys.exit(getattr(err, "errno", errno.EIO))


def load(path: str) -> AppSettings:
    try:
        with io.open(path, mode="rt", encoding="utf-8") as stream_in:
            return AppSettings(**json.load(stream_in))
    except (OSError, IOError) as err:
        logger.error("It's impossible to load the settings from the current machine.")
        logger.debug("An unexpected error occurred at this program runtime:", exc_info=True)
        # Stop this program runtime and return the exit status code.
        sys.exit(getattr(err, "errno", errno.EIO))

    except (json.decoder.JSONDecodeError, TypeError) as err:
        logger.error("It's impossible to pars the provided settings or initialise settings class.")
        logger.debug("An unexpected error occurred at this program runtime:", exc_info=True)
        # Stop this program runtime and return the exit status code.
        sys.exit(getattr(err, "errno", errno.EPERM))
