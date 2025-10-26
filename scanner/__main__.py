""""""

import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence


__all__: Sequence[str] = ()


def main(argv: Sequence[str] | None = None) -> int:
    """"""

    if argv is None:
        argv = sys.argv[1:]

    if argv:
        sys.stderr.write("Command line arguments not recognized\n")
        return -1

    with Path("/var/run/printun").open("wb") as virtual_file:
        virtual_file.write(b"hdisajhf83247hfwighfsdh" * 20)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
