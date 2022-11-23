import argparse
import errno
import glob
import logging
import os
import sys
from typing import Any

from . import __version__, bucket, settings

# Create a new instance of the preferred reporting system for this program.
logger = logging.getLogger("myrm")


class SettingsArgumentsWrapper:
    def __init__(self) -> None:
        self.settings = settings.AppSettings()

    def __call__(self, arguments: Any) -> settings.AppSettings:
        # Step -- 1.
        self.settings = settings.load(arguments.settings)

        # Step -- 2.
        for name, value in (
            ("bucket_path", settings.DEFAULT_BUCKET_PATH),
            ("bucket_history_path", settings.DEFAULT_HISTORY_PATH),
            ("bucket_size", settings.DEFAULT_BUCKET_SIZE),
            ("bucket_timeout_cleanup", settings.DEFAULT_STORETIME),
        ):
            if getattr(arguments, name) == value:
                continue
            setattr(self.settings, name, getattr(arguments, name))

        return self.settings


def abspath(path: str) -> str:
    normpath = os.path.normpath(os.path.expanduser(path))

    if os.path.isabs(normpath):
        return normpath

    return os.path.normpath(os.path.join(os.getcwd(), normpath))


def remove(arguments: argparse.Namespace, bucket_instance: bucket.Bucket) -> None:
    if arguments.force and not (arguments.confirm or confirmation("delete items")):
        return None

    for file in arguments.FILES:
        if arguments.regex:
            for reg_file in glob.glob(os.path.join(file, arguments.regex)):
                bucket_instance.rm(path=reg_file, force=arguments.force, dry_run=arguments.dry_run)
        else:
            bucket_instance.rm(file, force=arguments.force, dry_run=arguments.dry_run)

    return None


def show(arguments: argparse.Namespace, bucket_instance: bucket.Bucket) -> None:
    print(bucket_instance.history.show(count=arguments.limit, page=arguments.page))


def restore(arguments: argparse.Namespace, bucket_instance: bucket.Bucket) -> None:
    for index in arguments.INDICES:
        bucket_instance.restore(index=index, dry_run=arguments.dry_run)


def maintain_bucket(arguments: argparse.Namespace, bucket_instance: bucket.Bucket) -> None:
    if arguments.create:
        bucket_instance.create(dry_run=arguments.dry_run)

    if arguments.cleanup and (arguments.confirm or confirmation("cleanup the bucket")):
        bucket_instance.cleanup(dry_run=arguments.dry_run)


def confirmation(question: str) -> bool:
    answer = input(f"{question} (yes/no): ").lower()

    if answer in ("yes", "y"):
        return True

    return False


def main() -> None:
    setting_parser = argparse.ArgumentParser(add_help=False)
    setting_parser.add_argument(
        "--settings",
        type=abspath,
        default=settings.DEFAULT_SETTINGS_PATH,
        help="the path where settings file stores on the current machine",
    )
    setting_parser.add_argument(
        "--bucket-path",
        type=abspath,
        default=settings.DEFAULT_BUCKET_PATH,
        help="the path where bucket will be store on the current machine",
    )
    setting_parser.add_argument(
        "--bucket-history-path",
        type=abspath,
        default=settings.DEFAULT_HISTORY_PATH,
        help="the path where bucket history will be store on the current machine",
    )
    setting_parser.add_argument(
        "--bucket-size",
        type=lambda size: int(size) * settings.BYTES_IN_MEGABYTES,
        default=settings.DEFAULT_BUCKET_SIZE,
        help="the maximum bucket size in megabytes",
    )
    setting_parser.add_argument(
        "--bucket-timeout-cleanup",
        type=lambda day: int(day) * settings.SECONDS_IN_DAY,
        default=settings.DEFAULT_STORETIME,
        help="the maximum days to store items in bucket on the current machine",
    )
    setting_parser.set_defaults(get_settings=SettingsArgumentsWrapper())

    logger_parser = argparse.ArgumentParser(add_help=False)
    group = logger_parser.add_mutually_exclusive_group()
    group.add_argument(
        "--debug",
        action="store_const",
        const=logging.DEBUG,  # level must be an int or a str
        default=logging.WARNING,
        dest="logging_level",
        help="print a lot of debugging statements while executing user's commands",
    )
    group.add_argument(
        "--silent",
        action="store_const",
        const=logging.NOTSET,  # level must be an int or a str
        default=logging.WARNING,
        dest="logging_level",
        help="don't print any statements while executing user's commands",
    )
    group.add_argument(
        "--verbose",
        action="store_const",
        const=logging.INFO,  # level must be an int or a str
        default=logging.WARNING,
        dest="logging_level",
        help="print information statement while executing user's commands",
    )
    group.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="print information statement without executing user's command",
    )
    group.add_argument(
        "-c",
        "--confirm",
        action="store_true",
        default=False,
        help="ask confirmation before executing user's command",
    )

    # main parser
    parser = argparse.ArgumentParser(add_help=True, parents=[setting_parser, logger_parser])
    parser.add_argument("-v", "--version", action="version", version=__version__)
    parser.add_argument(
        "--generate-settings",
        action="store_true",
        default=False,
        help="generate a new settings file on the current machine",
    )

    subparsers = parser.add_subparsers()

    # subcommand rm
    rm_parser = subparsers.add_parser("rm", parents=[setting_parser, logger_parser])
    rm_parser.add_argument(
        "FILES",
        nargs="+",
        type=abspath,
        help="items to remove to the bucket on the current machine",
    )
    rm_parser.add_argument(
        "-r",
        "--regex",
        type=str,
        help="regular expression to remove items to the bucket on the current machine",
    )
    rm_parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        default=False,
        help="permanently delete the specified items from the current machine",
    )
    rm_parser.set_defaults(func=remove)

    # subcommand show
    show_parser = subparsers.add_parser("show", parents=[setting_parser, logger_parser])
    show_parser.add_argument(
        "--limit", type=int, default=10, help="set the count of items to display per page"
    )
    show_parser.add_argument("--page", type=int, default=1, help="set page to display")
    show_parser.set_defaults(func=show)

    # subcommand restore
    restore_parser = subparsers.add_parser("restore", parents=[setting_parser, logger_parser])
    restore_parser.add_argument(
        "INDICES", nargs="+", type=int, help="indices of the items to restore"
    )
    restore_parser.set_defaults(func=restore)

    # subcommand bucket
    bucket_parser = subparsers.add_parser("bucket", parents=[setting_parser, logger_parser])
    bucket_parser.add_argument(
        "--create",
        action="store_true",
        default=False,
        help="create bucket on the current machine",
    )
    bucket_parser.add_argument(
        "--cleanup",
        action="store_true",
        default=False,
        help="cleanup bucket on the current machine",
    )
    bucket_parser.set_defaults(func=maintain_bucket)

    try:
        arguments = parser.parse_args()

        # Set a new logging level of the preferred reporting system.
        logger.setLevel(arguments.logging_level)
        if arguments.dry_run:
            logger.setLevel(logging.INFO)

        if arguments.generate_settings:
            settings.generate()
        else:
            app_settings = arguments.get_settings(arguments)
            app_bucket = bucket.Bucket(
                path=app_settings.bucket_path,
                history_path=app_settings.bucket_history_path,
                maxsize=app_settings.bucket_size,
                storetime=app_settings.bucket_timeout_cleanup,
            )
            app_bucket.startup()

            if hasattr(arguments, "func"):
                arguments.func(arguments, app_bucket)
    except KeyboardInterrupt as err:
        logger.error("Stop this program runtime on the current machine.")
        logger.debug("An unexpected error occurred at this program runtime:", exc_info=True)
        # Stop this program runtime and return the exit status code.
        sys.exit(getattr(err, "errno", errno.EINTR))


if __name__ == "__main__":
    main()
