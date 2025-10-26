""""""

import base64
import enum
import json
import time
from typing import TYPE_CHECKING

import platformdirs

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path
    from typing import Final

__all__: Sequence[str] = ("load_previous_page_number", "save_previous_page_number")


APP_STATE_PATH: Final[Path] = platformdirs.user_state_path(
    "IPoPS-scanner", roaming=False, ensure_exists=True
)
PREVIOUS_PAGE_NUMBER_FILE_PATH: Final[Path] = APP_STATE_PATH / "previous_page_number"
SCAN_STATE_FILE_PATH: Final[Path] = APP_STATE_PATH / f"state.{int(time.time())}"


def ansi_red(x: str) -> str:
    return f"\x1b[91m{x}\x1b[0m"


def ansi_green(x: str) -> str:
    return f"\x1b[92m{x}\x1b[0m"


def load_previous_page_number() -> int:
    """"""
    return (
        int.from_bytes(PREVIOUS_PAGE_NUMBER_FILE_PATH.read_bytes(), byteorder="big")
        if PREVIOUS_PAGE_NUMBER_FILE_PATH.exists()
        else -1
    )


def save_previous_page_number(starting_page_number: int, /) -> None:
    """"""
    if starting_page_number < 0:
        INVALID_VALUE_MESSAGE: Final[str] = "Cannot save negative starting_page_number value."
        raise ValueError(INVALID_VALUE_MESSAGE)

    PREVIOUS_PAGE_NUMBER_FILE_PATH.write_bytes(
        starting_page_number.to_bytes(
            length=(starting_page_number.bit_length() + 7) // 8, byteorder="big"
        )
    )


class PageState(enum.Enum):
    UNSEEN = enum.auto()
    SEEN = enum.auto()
    SENT = enum.auto()


def get_page_state() -> list[tuple[int, bool]]:
    fcont = json.loads(SCAN_STATE_FILE_PATH.read_text())
    highest_known = max(map(int, fcont["data"].keys()))
    res = []
    for i in range(1, highest_known + 1):
        res.append((i, PageState.SENT if i in fcont["sent"] else PageState.SEEN if str(i) in fcont["data"] else PageState.UNSEEN))
    return res


def save_data_for_page(page_number: int, data: bytes) -> None:
    if SCAN_STATE_FILE_PATH.exists():
        fcont = json.loads(SCAN_STATE_FILE_PATH.read_text())
    else:
        fcont = {"sent": [], "data": {}}

    fcont["data"][page_number] = base64.standard_b64encode(data).decode()
    
    SCAN_STATE_FILE_PATH.write_text(json.dumps(fcont))


def mark_data_as_sent(page_number: int) -> None:
    fcont = json.loads(SCAN_STATE_FILE_PATH.read_text())
    fcont["sent"].append(page_number)
    SCAN_STATE_FILE_PATH.write_text(json.dumps(fcont))


def send_lowest_contiguous_block() -> bytes | None:
    fcont = json.loads(SCAN_STATE_FILE_PATH.read_text())

    if len(fcont["sent"]) == 0:
        highest_sent = 0
    else:
        highest_sent = max(fcont["sent"])
    
    highest_known = max(map(int, fcont["data"].keys()))

    to_send = []

    i = highest_sent + 1
    while i <= highest_known:
        if i in fcont["sent"]:
            continue
        if str(i) not in fcont["data"]:
            break
        to_send.append(i)
        i += 1

    if not to_send:
        return None

    fcont["sent"] += to_send
    SCAN_STATE_FILE_PATH.write_text(json.dumps(fcont))
    return b"".join(map(base64.standard_b64decode, [fcont["data"][str(x)] for x in to_send]))
