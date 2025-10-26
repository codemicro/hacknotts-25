""""""

import base64
import enum
import json
import time
from typing import TYPE_CHECKING, cast

import platformdirs

if TYPE_CHECKING:
    from collections.abc import Iterable, MutableMapping, MutableSequence, Sequence
    from pathlib import Path
    from typing import Final, TypedDict

__all__: Sequence[str] = (
    "PageState",
    "get_page_states",
    "load_previous_page_number",
    "save_previous_page_number",
)


if TYPE_CHECKING:

    class StateFileData(TypedDict):
        data: MutableMapping[str, str]
        sent: MutableSequence[int]


APP_STATE_PATH: Final[Path] = platformdirs.user_state_path(
    "IPoPS-scanner", roaming=False, ensure_exists=True
)
PREVIOUS_PAGE_NUMBER_FILE_PATH: Final[Path] = APP_STATE_PATH / "previous_page_number"
SCAN_STATE_FILE_PATH: Final[Path] = APP_STATE_PATH / f"state.{int(time.time())}"


class PageState(enum.Enum):
    """"""

    UNSEEN = "red"
    SEEN = "yellow"
    SENT = "green"


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


def _get_highest_known_page_number(page_numbers: Iterable[int | str]) -> int:
    return max(int(page_number) for page_number in page_numbers)


def get_page_states(starting_page_number: int) -> MutableMapping[int, PageState]:
    """"""
    state_file_data: StateFileData = (
        cast("StateFileData", json.loads(SCAN_STATE_FILE_PATH.read_text()))
        if SCAN_STATE_FILE_PATH.exists()
        else {"sent": [], "data": {}}
    )
    return {
        page_number: (
            PageState.SENT
            if page_number in state_file_data["sent"]
            else PageState.SEEN
            if str(page_number) in state_file_data["data"]
            else PageState.UNSEEN
        )
        for page_number in range(
            starting_page_number, _get_highest_known_page_number(state_file_data["data"]) + 1
        )
    }


def save_data_for_page(page_number: int, data: bytes) -> None:
    state_file_data: StateFileData = (
        cast("StateFileData", json.loads(SCAN_STATE_FILE_PATH.read_text()))
        if SCAN_STATE_FILE_PATH.exists()
        else {"sent": [], "data": {}}
    )

    state_file_data["data"][str(page_number)] = base64.standard_b64encode(data).decode()

    SCAN_STATE_FILE_PATH.write_text(json.dumps(state_file_data))


def mark_data_as_sent(page_number: int) -> None:
    state_file_data: StateFileData = (
        cast("StateFileData", json.loads(SCAN_STATE_FILE_PATH.read_text()))
        if SCAN_STATE_FILE_PATH.exists()
        else {"sent": [], "data": {}}
    )

    state_file_data["sent"].append(page_number)

    SCAN_STATE_FILE_PATH.write_text(json.dumps(state_file_data))


def send_lowest_contiguous_block(starting_page_number: int) -> bytes | None:
    state_file_data: StateFileData = (
        cast("StateFileData", json.loads(SCAN_STATE_FILE_PATH.read_text()))
        if SCAN_STATE_FILE_PATH.exists()
        else {"sent": [], "data": {}}
    )

    to_send = []
    i = (
        max(state_file_data["sent"]) + 1
        if len(state_file_data["sent"]) > 0
        else starting_page_number
    )
    while i <= _get_highest_known_page_number(state_file_data["data"]):
        if i in state_file_data["sent"]:
            continue
        if str(i) not in state_file_data["data"]:
            break
        to_send.append(i)
        i += 1

    if not to_send:
        return None

    state_file_data["sent"].extend(to_send)

    SCAN_STATE_FILE_PATH.write_text(json.dumps(state_file_data))

    return b"".join(
        base64.standard_b64decode(state_file_data["data"][str(x)]) for x in to_send
    )
