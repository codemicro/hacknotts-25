""""""

import base64
import logging
import re
import select
import shutil
import subprocess
import sys
from subprocess import CalledProcessError
from typing import TYPE_CHECKING

from . import pdf, utils
from .utils import GracefulTerminationHandler, PerformGracefulTermination

if TYPE_CHECKING:
    from collections.abc import Sequence
    from logging import Logger
    from typing import Final


__all__: Sequence[str] = ()


logger: Final[Logger] = logging.getLogger("ipops-printer")


def _get_ipops_frames(existing_data: bytes) -> bytes:
    if existing_data:
        if not select.select([sys.stdin], [], [], 10)[0]:  # TODO: Configure timeout
            logger.debug("Timed-out while waiting for further IP packets")
            return existing_data
    else:
        while not select.select([sys.stdin], [], [], 0.15)[0]:  # TODO: Configure polling rate
            if GracefulTerminationHandler.EXIT_NOW:
                raise PerformGracefulTermination

    logger.debug("Ready to accept IP packet from stdin")

    frame_size: int = int.from_bytes(sys.stdin.buffer.read(3), byteorder="big")

    if frame_size == 0:
        logger.info("Skipping packet: size was %d bytes", frame_size)
        return existing_data

    if frame_size < 0:
        NEGATIVE_FRAME_SIZE_MESSAGE: Final[str] = f"Negative packet size: {frame_size} bytes."
        raise ValueError(NEGATIVE_FRAME_SIZE_MESSAGE)

    logger.debug("Reading packet from stdin: size %d bytes", frame_size)

    existing_data += sys.stdin.buffer.read(frame_size)

    logger.debug("Current IPoPS frame buffer size: %d", len(existing_data))

    if len(existing_data) < 2000:  # TODO: Configure max buffer size
        logger.debug("Attempting to add more IP packets into a single IPoPS frame")
        return _get_ipops_frames(existing_data)

    logger.debug("IPoPS frame buffer filled")
    return existing_data


def _run_print_loop(lp_executable: str, starting_page_num: int) -> int:
    try:
        ipops_frames_data: bytes = _get_ipops_frames(existing_data=b"")
    except PerformGracefulTermination:
        return starting_page_num

    logger.debug("Byte reading completed successfully")

    if not ipops_frames_data:
        logger.debug("Skipping printing empty IPoPS frame")
        return starting_page_num

    pdf_bytes: bytearray
    pdf_pages_count: int
    pdf_bytes, pdf_pages_count = pdf.text_to_pdf(
        base64.standard_b64encode(ipops_frames_data).decode(),
        starting_page_num=starting_page_num,
    )

    logger.debug("Formatting PDF completed successfully")

    completed_print_subprocess_stdout: str = subprocess.run(
        (lp_executable,),
        check=True,
        input=pdf_bytes,
        stdout=subprocess.PIPE,
        text=False,
        timeout=None,
    ).stdout.decode()
    if completed_print_subprocess_stdout:
        known_stdout_match: re.Match[str] | None = re.fullmatch(
            r"\Arequest id is (?P<job_id>[\w-]+) \((?P<files_count>\d+) file\(s\)\)\n\Z",
            completed_print_subprocess_stdout,
        )
        if known_stdout_match is not None:
            logger.debug(
                "Printed %s file(s) with job ID '%s'",
                known_stdout_match.group("files_count"),
                known_stdout_match.group("job_id"),
            )
        else:
            logger.warning(
                "Subprocess call to 'lp' had stdout: %s",
                repr(completed_print_subprocess_stdout),
            )

    logger.debug("Printing PDF completed successfully")

    return starting_page_num + pdf_pages_count


def main(argv: Sequence[str] | None = None) -> int:
    """"""
    utils.setup_logging(verbosity=2)  # TODO: Make verbosity configurable

    if argv is None:
        argv = sys.argv[1:]

    if argv:
        logger.error("Command line arguments not recognized")
        return -1

    lp_executable: str | None = shutil.which("lp")
    if lp_executable is None:
        logger.error("The 'lp' executable could not be found.")
        logger.info(
            "Ensure CUPS is installed on your Linux system "
            "and that the 'lp' binary is available on your PATH."
        )
        return 1

    page_count: int = 0

    logger.info("Starting listener loop")

    GracefulTerminationHandler.setup()

    try:
        while not GracefulTerminationHandler.EXIT_NOW:
            page_count = _run_print_loop(lp_executable, page_count)

    except CalledProcessError as e:
        logger.error("Subrocess call to 'lp' failed with exit code %d", e.returncode)
        logger.info("Subprocess call to 'lp' had stderr: %s", repr(e.stderr))
        logger.info("Subprocess call to 'lp' had stdout: %s", repr(e.stdout))
        return 3

    except ValueError as e:
        logger.error(str(e).strip("\n\r\t ."))
        return 2

    logger.info("Ended listener loop")

    logger.info("Exiting")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
