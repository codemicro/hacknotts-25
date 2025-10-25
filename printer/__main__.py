""""""

import base64
import logging
import select
import shutil
import subprocess
import sys
from subprocess import CalledProcessError
from typing import TYPE_CHECKING

from fpdf import FPDF
from fpdf.enums import WrapMode

from . import utils
from .utils import GracefulTerminationHandler

if TYPE_CHECKING:
    from collections.abc import Sequence
    from logging import Logger
    from typing import Final

__all__: Sequence[str] = ()


logger: Final[Logger] = logging.getLogger("ipops-printer")


def _print_stdin(lp_executable: str) -> None:
    while not select.select([sys.stdin], [], [], 0.15)[0]:  # TODO: Configure polling rate
        if GracefulTerminationHandler.EXIT_NOW:
            return

    logger.debug("Ready to accept data from stdin")

    frame_size: int = int.from_bytes(sys.stdin.buffer.read(3), byteorder="big")

    logger.debug("Reading %d bytes from stdin", frame_size)

    stdin_data: bytes = sys.stdin.buffer.read(frame_size)

    logger.debug("Byte reading completed successfully")

    pdf: FPDF = FPDF(format="A4")
    pdf.add_page()
    pdf.set_font("Courier", size=12)
    pdf.write(
        text=base64.standard_b64encode(stdin_data).decode(),
        wrapmode=WrapMode.CHAR,
    )

    pdf_bytes: bytes = pdf.output()

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

    logger.info("Starting listener loop")

    GracefulTerminationHandler.setup()

    try:
        while not GracefulTerminationHandler.EXIT_NOW:
            _print_stdin(lp_executable)
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
