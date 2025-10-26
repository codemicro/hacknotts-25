""""""

import io
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING

from PIL import Image
from pylibdmtx import pylibdmtx

from . import utils
from .utils import PageState

if TYPE_CHECKING:
    from collections.abc import Sequence
    from subprocess import CompletedProcess
    from typing import Final, Literal


__all__: Sequence[str] = ()

INTERMEDIARY_IMAGE_FORMAT: Final[Literal["png", "jpeg", "tiff"]] = "jpeg"


def ansi_red(x: str) -> str:
    return f"\x1b[91m{x}\x1b[0m"


def ansi_green(x: str) -> str:
    return f"\x1b[92m{x}\x1b[0m"


def parse_scanned_payload(inp: bytes) -> tuple[int, bytes]:
    assert len(inp) > 1, "input bytes too short to parse payload"
    return int(inp[0]), inp[1:]


def scan_and_send(starting_page_number: int) -> None:
    scanimage_executable: str | None = shutil.which("scanimage")
    if scanimage_executable is None:
        sys.stderr.write(
            "The 'scanimage' executable could not be found.\n"
            "Ensure SANE-utils is installed on your Linux system "
            "and that the 'scanimage' binary is available on your PATH."
        )
        return

    print("[*] Scanning...")

    completed_scanimage_subprocess: CompletedProcess[bytes] = subprocess.run(
        (scanimage_executable, "--format", INTERMEDIARY_IMAGE_FORMAT),
        check=False,
        stdout=subprocess.PIPE,
        text=False,
        timeout=None,
    )
    if completed_scanimage_subprocess.returncode != 0:
        sys.stderr.write(
            f"Subrocess call to 'scanimage' failed with exit code %d\n"
            f"stderr: {completed_scanimage_subprocess.stderr!r}\n"
        )
        return

    print("[*] Parsing...")

    with open(f"tempscan.{int(time.time())}.{INTERMEDIARY_IMAGE_FORMAT}", "wb") as f:
        f.write(completed_scanimage_subprocess.stdout)

    scanned_image: Image.Image = Image.open(
        io.BytesIO(completed_scanimage_subprocess.stdout), formats=(INTERMEDIARY_IMAGE_FORMAT,)
    )

    result = pylibdmtx.decode(scanned_image)
    print(f"[!] {result}")
    assert len(result) == 1
    raw_data = result[0].data

    page_number, payload = parse_scanned_payload(raw_data)
    utils.save_data_for_page(page_number, payload)

    print(f"[*] Got page {page_number}")

    bytes_to_send = utils.send_lowest_contiguous_block(starting_page_number)
    if bytes_to_send is not None:
        with Path(os.environ.get("IPOPS_INBOUND_PATH", "/var/run/printun")).open("wb") as f:
            f.write(payload)


def main(argv: Sequence[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    if argv:
        sys.stderr.write("Command line arguments not recognized\n")
        return -1

    while True:
        first_page_number: int = int(
            input(
                "[?] Place a document on the scanner, "
                "type the starting page number of this batch and press <ENTER>"
            )
        )
        scan_and_send(first_page_number)
        print("[!] Page state: ", end="")

        for i, state in utils.get_page_states(first_page_number).items():
            fmt_fn = str

            if state is PageState.UNSEEN:
                fmt_fn = ansi_red
            elif state is PageState.SENT:
                fmt_fn = ansi_green

            print(fmt_fn(str(i)), end=" ")
        print()

        go = input("[?] Send another? [y/N] ")
        if go != "y":
            break

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
