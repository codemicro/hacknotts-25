""""""

import abc
import logging
import signal
from typing import TYPE_CHECKING, override

import platformdirs
from typed_classproperties import classproperty

if TYPE_CHECKING:
    from collections.abc import Sequence
    from logging import Logger
    from pathlib import Path
    from types import FrameType
    from typing import ClassVar, Final, Self

__all__: Sequence[str] = (
    "GracefulTerminationHandler",
    "PerformGracefulTermination",
    "load_starting_page_number",
    "save_starting_page_number",
)


logger: Final[Logger] = logging.getLogger("ipops-printer")


APP_STATE_PATH: Final[Path] = platformdirs.user_state_path(
    "IPoPS-printer", roaming=False, ensure_exists=True
)
STARTING_PAGE_NUMBER_FILE_PATH: Final[Path] = APP_STATE_PATH / "starting_page_number"


class PerformGracefulTermination(RuntimeError):  # noqa: N818
    """"""


class GracefulTerminationHandler(abc.ABC):  # noqa: B024
    """"""

    _exit_now: ClassVar[bool] = False

    @override
    def __new__(cls) -> Self:  # NOTE: This cannot be statically type-checked
        CANNOT_INSTANTIATE_MESSAGE: Final[str] = (
            f"Cannot instantiate objects of type '{cls.__name__}'."
        )
        raise RuntimeError(CANNOT_INSTANTIATE_MESSAGE)

    @classproperty
    def EXIT_NOW(cls) -> bool:  # noqa: D102
        return cls._exit_now

    @classmethod
    def _handle_termination(cls, _signum: int, _frame: FrameType | None, /) -> None:
        cls._exit_now = True

    @classmethod
    def setup(cls) -> None:
        """"""
        signal.signal(signal.SIGINT, cls._handle_termination)
        signal.signal(signal.SIGTERM, cls._handle_termination)


def load_starting_page_number() -> int:
    """"""
    if not STARTING_PAGE_NUMBER_FILE_PATH.exists():
        logger.debug("Starting page number file not found, using default value: 0")
        return 0

    logger.debug("Loading starting page number value from file")

    starting_page_number: int = int.from_bytes(
        STARTING_PAGE_NUMBER_FILE_PATH.read_bytes(), byteorder="big"
    )

    logger.debug("Loaded starting page number value: %d", starting_page_number)

    return starting_page_number


def save_starting_page_number(starting_page_number: int, /) -> None:
    """"""
    if starting_page_number < 0:
        INVALID_VALUE_MESSAGE: Final[str] = "Cannot save negative starting_page_number value."
        raise ValueError(INVALID_VALUE_MESSAGE)

    logger.debug("Saving next starting page number value to file: %d", starting_page_number)

    STARTING_PAGE_NUMBER_FILE_PATH.write_bytes(
        starting_page_number.to_bytes(
            length=(starting_page_number.bit_length() + 7) // 8, byteorder="big"
        )
    )
