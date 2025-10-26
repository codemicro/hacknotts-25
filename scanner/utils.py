""""""

from typing import TYPE_CHECKING

import platformdirs

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path
    from typing import Final

__all__: Sequence[str] = ("load_previous_page_number", "save_previous_page_number")


APP_STATE_PATH: Final[Path] = platformdirs.user_state_path(
    "IPoPS-printer", roaming=False, ensure_exists=True
)
PREVIOUS_PAGE_NUMBER_FILE_PATH: Final[Path] = APP_STATE_PATH / "previous_page_number"


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
