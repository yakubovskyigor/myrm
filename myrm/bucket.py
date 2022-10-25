import collections
import datetime
import enum
import errno
import io
import logging
import os
import pickle
import sys
import time
import uuid
from typing import Any, Hashable, List

from tabulate import tabulate

from . import rmlib, settings

# Create a new instance of the preferred reporting system for this program.
logger = logging.getLogger("myrm")

__all__ = (
    "Status",
    "BucketHistory",
    "Bucket",
)


Entry = collections.namedtuple("Entry", ("status", "index", "name", "origin", "date"))


class Status(enum.Enum):
    CORRECT: str = "OK"
    UNKNOWN: str = "UNKNOWN"


class BucketHistory(collections.UserDict):
    def __init__(
        self, *args: Any, path: str = settings.DEFAULT_HISTORY_PATH, **kwargs: Any
    ) -> None:
        super().__init__(*args, **kwargs)

        self.path = path
        # Get the required data and update this container.
        if os.path.isfile(self.path):
            self._read()

    def _read(self) -> None:
        try:
            with io.open(self.path, mode="rb") as stream_in:
                # Load and de-serialize the required data structure.
                self.update(pickle.load(stream_in))
        except (IOError, OSError) as err:
            logger.error("It's impossible to restore the history state on the current machine.")
            logger.debug("An unexpected error occurred at this program runtime:", exc_info=True)
            # Stop this program runtime and return the exit status code.
            sys.exit(getattr(err, "errno", errno.EIO))

    def _write(self) -> None:
        try:
            with io.open(self.path, mode="wb") as stream_out:
                # Serialize the required data structure and save it on the current machine.
                pickle.dump(self.data, stream_out, protocol=pickle.HIGHEST_PROTOCOL)
        except (IOError, OSError) as err:
            logger.error("It's impossible to save the history state on the current machine.")
            logger.debug("An unexpected error occurred at this program runtime:", exc_info=True)
            # Stop this program runtime and return the exit status code.
            sys.exit(getattr(err, "errno", errno.EIO))

    def __getitem__(self, key: Hashable) -> Entry:
        return self.data[key]

    def __setitem__(self, key: Hashable, value: Entry) -> None:
        self.data[key] = value
        # Save the required data on the current machine.
        self._write()

    def __delitem__(self, key: Hashable) -> None:
        del self.data[key]
        # Save the required data on the current machine.
        self._write()

    def show(self, count: int, page: int) -> str:
        values = list(self.values())
        if not values:
            logger.warning("History is empty.")
            # Stop this program runtime and return the exit status code.
            sys.exit(errno.EPERM)

        try:
            res = [values[index : index + count] for index in range(0, len(values), count)][  # noqa
                page - 1
            ]
        except IndexError as err:
            logger.error("It's impossible to show the provided page number.")
            logger.debug("An unexpected error occurred at this program runtime:", exc_info=True)
            # Stop this program runtime and return the exit status code.
            sys.exit(getattr(err, "errno", errno.EPERM))

        header = ("Status", "Index", "Name", "Origin", "Removed on")
        return tabulate(list(map(list, res)), headers=header)

    def get_indexes(self) -> List[int]:
        return [value.index for value in self.values()]

    def get_next_index(self) -> int:
        return max(self.get_indexes(), default=0) + 1

    def cleanup(self) -> None:
        self.data = {}
        # Save the required data on the current machine.
        self._write()


class Bucket:
    def __init__(
        self,
        path: str = settings.DEFAULT_BUCKET_PATH,
        history_path: str = settings.DEFAULT_HISTORY_PATH,
        maxsize: int = settings.DEFAULT_BUCKET_SIZE,
        storetime: int = settings.DEFAULT_STORETIME,
    ) -> None:
        self.path = path
        self.maxsize = maxsize
        self.storetime = storetime
        self.history = BucketHistory(path=history_path)

    def create(self) -> None:
        rmlib.mkdir(self.path)

    def _get_size(self, path: str) -> int:
        size = 0

        if os.path.isfile(path) or os.path.islink(path):
            try:
                return os.path.getsize(path)
            except (OSError, IOError) as err:
                logger.error("It's impossible to calculate size of the determined path.")
                logger.debug("An unexpected error occurred at this program runtime:", exc_info=True)
                # Stop this program runtime and return the exit status code.
                sys.exit(getattr(err, "errno", errno.EIO))

        try:
            for top, _, nondirs in os.walk(self.path):
                for name in nondirs:
                    size += os.path.getsize(os.path.join(top, name))
        except OSError as err:
            logger.error("The determined path don't exist on the current machine.")
            logger.debug("An unexpected error occurred at this program runtime:", exc_info=True)
            # Stop this program runtime and return the exit status code.
            sys.exit(getattr(err, "errno", errno.EPERM))

        return size

    def cleanup(self) -> None:
        rmlib.rmdir(self.path)
        rmlib.mkdir(self.path)
        self.history.cleanup()

    def get_size(self) -> int:
        return self._get_size(self.path)

    def _rm(self, path: str) -> None:
        if os.path.isfile(path):
            rmlib.rm(path)
        else:
            rmlib.rmdir(path)

    def _mv(self, path: str) -> None:
        name = str(uuid.uuid4())

        abspath = os.path.join(self.path, name)
        if os.path.isfile(path):
            rmlib.mv(path, abspath)
        else:
            rmlib.mvdir(path, abspath)

        self.history[name] = Entry(
            status=Status.CORRECT.value,
            index=self.history.get_next_index(),
            name=os.path.basename(path),
            origin=path,
            date=datetime.datetime.now().strftime(settings.DEFAULT_TIME_FORMAT),
        )

    def rm(self, path: str, force: bool = False) -> None:
        if self._get_size(path) + self.get_size() >= self.maxsize * settings.BYTES_IN_MEGABYTES:
            logger.error("It's impossible to move item to bucket because the bucket is full.")
            # Stop this program runtime and return the exit status code.
            sys.exit(errno.EPERM)

        if force:
            self._rm(path)
        else:
            self._mv(path)

    def check(self) -> None:
        try:
            content = os.listdir(self.path)
        except OSError as err:
            logger.error("The determined path don't exist on the current machine.")
            logger.debug("An unexpected error occurred at this program runtime:", exc_info=True)
            # Stop this program runtime and return the exit status code.
            sys.exit(getattr(err, "errno", errno.EPERM))

        items = (name for name in content if name not in self.history.keys())
        # Step - 1.
        for name in items:
            self.history[name] = Entry(
                status=Status.UNKNOWN.value,
                index=self.history.get_next_index(),
                name=os.path.basename(name),
                origin=Status.UNKNOWN.value,
                date=datetime.datetime.now().strftime(settings.DEFAULT_TIME_FORMAT),
            )

        # Step - 2.
        for key in list(self.history):
            if key not in content:
                del self.history[key]

    def timeout_cleanup(self) -> None:
        try:
            content = os.listdir(self.path)
        except OSError as err:
            logger.error("The determined path don't exist on the current machine.")
            logger.debug("An unexpected error occurred at this program runtime:", exc_info=True)
            # Stop this program runtime and return the exit status code.
            sys.exit(getattr(err, "errno", errno.EPERM))

        current_time = time.time()
        for name in content:
            abspath = os.path.join(self.path, name)

            try:
                removed_time = os.stat(abspath).st_mtime
            except OSError as err:
                logger.error("It's impossible to get removed time for the determined path.")
                logger.debug("An unexpected error occurred at this program runtime:", exc_info=True)
                # Stop this program runtime and return the exit status code.
                sys.exit(getattr(err, "errno", errno.EPERM))

            if removed_time > current_time - self.storetime * settings.SECONDS_IN_DAY:
                self._rm(abspath)

    def restore(self, index: int) -> None:
        if index not in self.history.get_indexes():
            logger.error("The determined index don't exist in history.")
            # Stop this program runtime and return the exit status code.
            sys.exit(errno.EPERM)

        for name, entry in self.history.items():
            if entry.index == index:
                # Step - 1.
                if os.path.exists(entry.origin) or entry.origin == Status.UNKNOWN.value:
                    logger.error("The determined path can't be moved on the current machine.")
                    # Stop this program runtime and return the exit status code.
                    sys.exit(errno.EPERM)

                # Step - 2.
                abspath = os.path.join(self.path, name)
                if os.path.isfile(abspath):
                    rmlib.mv(abspath, entry.origin)
                else:
                    rmlib.mvdir(abspath, entry.origin)

        self.check()
