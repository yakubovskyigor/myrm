import errno
import logging
import os
import sys

# Create a new instance of the preferred reporting system for this program.
logger = logging.getLogger("myrm")

__all__ = (
    "rm",
    "rmdir",
    "mkdir",
    "mv",
    "mvdir",
)


def rm(path: str) -> None:
    try:
        os.remove(path)
    except OSError as err:
        logger.error("The determined path can't be removed from the current machine.")
        logger.debug("An unexpected error occurred at this program runtime:", exc_info=True)
        # Stop this program runtime and return the exit status code.
        sys.exit(getattr(err, "errno", errno.EPERM))
    else:
        logger.info("Item '%s' was removed without errors.", path)


def rmdir(path: str) -> None:
    try:
        content = os.walk(path, topdown=False)
    except OSError as err:
        logger.error("The determined path don't exist on the current machine.")
        logger.debug("An unexpected error occurred at this program runtime:", exc_info=True)
        # Stop this program runtime and return the exit status code.
        sys.exit(getattr(err, "errno", errno.EPERM))

    for top, dirs, nondirs in content:
        # Step — 1.
        for name in nondirs:
            rm(os.path.join(top, name))

        try:
            # Step — 2.
            for name in dirs:
                abspath = os.path.join(top, name)
                os.rmdir(abspath)
                logger.info("Directory '%s' was removed from the current machine.", abspath)
        except OSError as err:
            logger.error("The determined path can't be removed from the current machine.")
            logger.debug("An unexpected error occurred at this program runtime:", exc_info=True)
            # Stop this program runtime and return the exit status code.
            sys.exit(getattr(err, "errno", errno.EPERM))

    try:
        os.rmdir(path)
    except OSError as err:
        logger.error("The determined path can't be removed from the current machine.")
        logger.debug("An unexpected error occurred at this program runtime:", exc_info=True)
        # Stop this program runtime and return the exit status code.
        sys.exit(getattr(err, "errno", errno.EPERM))
    else:
        logger.info("Directory '%s' was removed without errors.", path)


def mkdir(path: str) -> None:
    try:
        # Create a new directory on the current machine.
        os.makedirs(path)
        logger.info("The required directory '%s' was created on the current machine.", path)
    except OSError as err:
        if not (err.errno == errno.EEXIST and os.path.isdir(path)):
            logger.error("It's impossible to create a new directory on the current machine.")
            logger.debug("An unexpected error occurred at this program runtime:", exc_info=True)
            # Stop this program runtime and return the exit status code.
            sys.exit(getattr(err, "errno", errno.EPERM))


def mv(src: str, dst: str) -> None:
    try:
        os.rename(src, dst)
    except OSError as err:
        logger.error("Can't move the determined item to the destination path.")
        logger.debug("An unexpected error occurred at this program runtime:", exc_info=True)
        # Stop this program runtime and return the exit status code.
        sys.exit(getattr(err, "errno", errno.EPERM))
    else:
        logger.info("Item '%s' was moved to '%s' as the destination path.", src, dst)


def mvdir(src: str, dst: str) -> None:
    try:
        content = os.walk(src, topdown=False)
    except OSError as err:
        logger.error("The determined path don't exist on the current machine.")
        logger.debug("An unexpected error occurred at this program runtime:", exc_info=True)
        # Stop this program runtime and return the exit status code.
        sys.exit(getattr(err, "errno", errno.EPERM))

    # Create a destination directory on the current machine.
    mkdir(dst)
    logger.info("The required directory '%s' was created on the current machine.", dst)

    for top, dirs, nondirs in content:
        # Step — 1.
        for name in dirs:
            mkdir(os.path.join(dst, name))

        # Step — 2.
        for name in nondirs:
            mv(os.path.join(top, name), os.path.join(dst, name))

    # Remove determined directory from the current machine.
    rmdir(src)
    logger.info("Directory '%s' was moved to '%s' as a destination path.", src, dst)
