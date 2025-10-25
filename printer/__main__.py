""""""

import base64
import logging
import select
import shutil
import subprocess
import sys
import time
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
    while not select.select([sys.stdin], [], [], 0)[0]:
        if GracefulTerminationHandler.EXIT_NOW:
            return

        time.sleep(0.1)  # TODO: Configure polling rate

    pdf: FPDF = FPDF(format="A4")
    pdf.add_page()
    pdf.set_font("Courier", size=12)
    pdf.write(
        text=base64.standard_b64encode(sys.stdin.buffer.read(1800 * 64)).decode(),
        wrapmode=WrapMode.CHAR,
    )

    completed_print_subprocess_stdout: str = subprocess.run(
        (lp_executable,),
        check=True,
        input=pdf.output(),
        stdout=subprocess.PIPE,
        text=False,
        timeout=None,
    ).stdout.decode()
    if completed_print_subprocess_stdout:
        logger.debug(
            "Subprocess call to 'lp' had stdout: %s", repr(completed_print_subprocess_stdout)
        )


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

    logger.debug("Starting listener loop")

    GracefulTerminationHandler.setup()
    while not GracefulTerminationHandler.EXIT_NOW:
        _print_stdin(lp_executable)

    logger.debug("Ended listener loop")

    logger.debug("Exiting")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
