"""Console entry point for IPoPs-scanner."""

import shutil
import string
import subprocess
from typing import TYPE_CHECKING

import platformdirs
import pytesseract
from PIL import Image

from . import utils

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path
    from subprocess import CompletedProcess
    from typing import BinaryIO, Final, Literal

import click

if TYPE_CHECKING:
    from collections.abc import Sequence

__all__: Sequence[str] = ("run",)


INTERMEDIARY_IMAGE_FORMAT: Final[Literal["png", "jpg", "tiff"]] = "tiff"
APP_STATE_PATH: Final[Path] = platformdirs.user_state_path(
    "IPoPS-scanner", roaming=False, ensure_exists=True
)


@click.command(
    name="scanner",
    context_settings={"help_option_names": ["-h", "--help"]},
    help="Ingest an IPoPS frame as a selection of IP packets.",
)
@click.version_option(None, "-V", "--version")
# @click.option(
#     "-v",
#     "--verbose",
#     count=True,
#     callback=_callback_verbose,
#     expose_value=False,
# )
# @click.option(
#     "-q",
#     "--quiet",
#     is_flag=True,
#     callback=_callback_mutually_exclusive_verbose_and_quiet,
#     expose_value=False,
# )
@click.option("--virtual-pipe-file", type=click.File("wb"), default="/var/run/printun")
@click.pass_context
def run(ctx: click.Context, virtual_pipe_file: BinaryIO) -> None:
    """Run cli entry-point."""
    scanimage_executable: str | None = shutil.which("scanimage")
    if scanimage_executable is None:
        click.echo(
            (
                "The 'scanimage' executable could not be found.\n"
                "Ensure SANE-utils is installed on your Linux system "
                "and that the 'scanimage' binary is available on your PATH."
            ),
            err=True,
        )
        ctx.exit(2)

    if shutil.which("tesseract") is None:
        click.echo(
            (
                "The 'tesseract' executable could not be found.\n"
                "Ensure tesseract-ocr is installed on your Linux system "
                "and that the 'tesseract' binary is available on your PATH."
            ),
            err=True,
        )
        ctx.exit(2)

    completed_scanimage_subprocess: CompletedProcess[bytes] = subprocess.run(
        (scanimage_executable, "--format", INTERMEDIARY_IMAGE_FORMAT),
        check=False,
        stdout=subprocess.PIPE,
        text=False,
        timeout=None,
    )
    if completed_scanimage_subprocess.returncode != 0:
        click.echo(
            (
                f"Subrocess call to 'scanimage' failed with exit code {
                    completed_scanimage_subprocess.returncode
                }\nstderr: {completed_scanimage_subprocess.stderr!r}"
            ),
            err=True,
        )
        ctx.exit(3)

    scanned_image: Image.Image = Image.open(
        completed_scanimage_subprocess.stdout, formats=(INTERMEDIARY_IMAGE_FORMAT,)
    )

    data: str
    raw_page_number: str
    data, _, raw_page_number = pytesseract.image_to_string(
        scanned_image,
        output_type="string",
        config=f"--psm 6 -c tessedit_char_whitelist={string.ascii_letters}{string.digits}+/",
    ).partition("\n\n")
    data = data.translate(str.maketrans("", "", "\n\r "))
    raw_page_number = raw_page_number.translate(
        str.maketrans("=_—oOilLzZAbG", "---0011122466", "\n\r ")
    )

    try:
        page_number: int = int(raw_page_number)
    except ValueError:
        click.echo(
            f"Failed to parse page number as an integer: '{raw_page_number}'\n", err=True
        )
        ctx.exit(2)

    previous_page_number: int = utils.load_previous_page_number()

    if page_number == previous_page_number + 1:
        virtual_pipe_file.write(b"hdisajhf83247hfwighfsdh" * 20)
