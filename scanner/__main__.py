""""""

import shutil
import string
import subprocess
import sys
from typing import TYPE_CHECKING

import platformdirs
import pytesseract
from PIL import Image

from . import utils

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path
    from subprocess import CompletedProcess
    from typing import Final, Literal


__all__: Sequence[str] = ()


INTERMEDIARY_IMAGE_FORMAT: Final[Literal["png", "jpg", "tiff"]] = "tiff"
APP_STATE_PATH: Final[Path] = platformdirs.user_state_path(
    "IPoPS-scanner", roaming=False, ensure_exists=True
)


def main(argv: Sequence[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    if argv:
        sys.stderr.write("Command line arguments not recognized\n")
        return -1

    scanimage_executable: str | None = shutil.which("scanimage")
    if scanimage_executable is None:
        sys.stderr.write(
            "The 'scanimage' executable could not be found.\n"
            "Ensure SANE-utils is installed on your Linux system "
            "and that the 'scanimage' binary is available on your PATH."
        )
        return 1

    if shutil.which("tesseract") is None:
        sys.stderr.write(
            "The 'tesseract' executable could not be found.\n"
            "Ensure tesseract-ocr is installed on your Linux system "
            "and that the 'tesseract' binary is available on your PATH."
        )
        return 1

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
        return 3

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
        sys.stderr.write(f"Failed to parse page number as an integer: '{raw_page_number}'\n")
        return 2

    previous_page_number: int = utils.load_previous_page_number()

    if page_number == previous_page_number + 1:
    # with Path(os.environ.get("IPOPS_INBOUND_PATH", "/var/run/printun")).open(
    #     "wb"
    # ) as virtual_file:
    #     virtual_file.write(b"hdisajhf83247hfwighfsdh" * 20)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
