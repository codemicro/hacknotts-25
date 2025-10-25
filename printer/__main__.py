""""""

import base64
import logging
import select
import shutil
import subprocess
import sys
from subprocess import CalledProcessError
from typing import TYPE_CHECKING

from . import pdf, utils
from .utils import GracefulTerminationHandler

if TYPE_CHECKING:
    from collections.abc import Sequence
    from logging import Logger
    from typing import Final


__all__: Sequence[str] = ()


logger: Final[Logger] = logging.getLogger("ipops-printer")


def _print_stdin(lp_executable: str, page_count: int) -> None:
    while not select.select([sys.stdin], [], [], 0.15)[0]:  # TODO: Configure polling rate
        if GracefulTerminationHandler.EXIT_NOW:
            return

    logger.debug("Ready to accept data from stdin")

    frame_size: int = int.from_bytes(sys.stdin.buffer.read(3), byteorder="big")

    logger.debug("Reading %d bytes from stdin", frame_size)

    stdin_data: bytes = sys.stdin.buffer.read(frame_size)

    logger.debug("Byte reading completed successfully")

    pdf_bytes: bytes = pdf.text_to_pdf(
        base64.standard_b64encode(stdin_data).decode(), starting_page_num=page_count
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
        logger.warning(
            "Subprocess call to 'lp' had stdout: %s", repr(completed_print_subprocess_stdout)
        )

    logger.debug("Printing PDF completed successfully")


def main(argv: Sequence[str] | None = None) -> int:
    """"""
    utils.setup_logging(verbosity=2)  # TODO: Make verbosity configurable

    if argv is None:
        argv = sys.argv[1:]

    if argv:
        logger.error("ipops-printer command line arguments not recognized")
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
            _print_stdin(lp_executable, page_count)

            page_count += 1

    except CalledProcessError as e:
        logger.error("Subrocess call to 'lp' failed with exit code %d", e.returncode)  # noqa: TRY400
        logger.info("Subprocess call to 'lp' had stderr: %s", repr(e.stderr))
        logger.info("Subprocess call to 'lp' had stdout: %s", repr(e.stdout))
        return 2

    logger.info("Ended listener loop")

    logger.info("Exiting")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
