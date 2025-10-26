"""Console entry point for IPoPs-scanner."""

import io
import shutil
import subprocess
import time
from pathlib import Path
from typing import TYPE_CHECKING

import click
import platformdirs
from PIL import Image
from pylibdmtx import pylibdmtx

from . import utils

if TYPE_CHECKING:
    from collections.abc import Sequence
    from subprocess import CompletedProcess
    from typing import BinaryIO, Final, Literal

__all__: Sequence[str] = ("run",)


INTERMEDIARY_IMAGE_FORMAT: Final[Literal["png", "jpg", "tiff"]] = "tiff"
APP_STATE_PATH: Final[Path] = platformdirs.user_state_path(
    "IPoPS-scanner", roaming=False, ensure_exists=True
)


def scan_and_send(
    ctx: click.Context, scanimage_executable: str, start_page: int, virtual_pipe_file: BinaryIO
) -> None:
    click.echo("[*] Scanning...")

    completed_scanimage_subprocess: CompletedProcess[bytes] = subprocess.run(
        (scanimage_executable, "--format", INTERMEDIARY_IMAGE_FORMAT),
        check=False,
        capture_output=True,
        text=False,
        timeout=None,
    )
    if completed_scanimage_subprocess.returncode != 0:
        click.echo(
            (
                f"Subrocess call to 'scanimage' failed with exit code {
                    completed_scanimage_subprocess.returncode
                }\nstderr: {completed_scanimage_subprocess.stderr.decode()!r}"
            ),
            err=True,
        )
        ctx.exit(3)

    click.echo("[*] Parsing...")

    Path(f"tempscan.{int(time.time())}.{INTERMEDIARY_IMAGE_FORMAT}").write_bytes(
        completed_scanimage_subprocess.stdout
    )

    scanned_image: Image.Image = Image.open(
        io.BytesIO(completed_scanimage_subprocess.stdout), formats=(INTERMEDIARY_IMAGE_FORMAT,)
    )

    result: Sequence[pylibdmtx.Decoded] = pylibdmtx.decode(scanned_image)
    click.echo(f"[!] {result}")
    if len(result) != 1:
        click.echo("Decoding data matrices resulted in multiple outputs.", err=True)
        ctx.exit(3)

    if not result[0].data:
        click.echo("Decoding data matrices resulted in no data.", err=True)
        ctx.exit(3)

    page_number: int = int(result[0].data[0])
    payload: bytes = result[0].data[1:]
    utils.save_data_for_page(page_number, payload)

    click.echo(f"[*] Got page {page_number}")

    if utils.send_lowest_contiguous_block(start_page) is not None:
        virtual_pipe_file.write(payload)


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
@click.argument("start-page", type=int)
@click.option("--virtual-pipe-file", type=click.File("wb"), default="/var/run/printun")
@click.pass_context
def run(ctx: click.Context, start_page: int, virtual_pipe_file: BinaryIO) -> None:
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

    # if shutil.which("tesseract") is None:
    #     click.echo(
    #         (
    #             "The 'tesseract' executable could not be found.\n"
    #             "Ensure tesseract-ocr is installed on your Linux system "
    #             "and that the 'tesseract' binary is available on your PATH."
    #         ),
    #         err=True,
    #     )
    #     ctx.exit(2)

    while True:
        scan_and_send(ctx, scanimage_executable, start_page, virtual_pipe_file)
        click.echo("[!] Page state: ", nl=False)

        for i, state in utils.get_page_states(start_page).items():
            click.echo(f"{click.style(str(i), fg=state.value)} ", nl=False)

        click.echo("", nl=True)

        click.confirm("[?] Send another? [y/N]", abort=True, default=False)
