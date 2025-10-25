""""""

import logging
import signal
from typing import TYPE_CHECKING, override

from typed_classproperties import classproperty

if TYPE_CHECKING:
    from collections.abc import Sequence
    from logging import Logger
    from types import FrameType
    from typing import ClassVar, Final, Literal, Self, TextIO

__all__: Sequence[str] = ("setup_logging",)


logger: Final[Logger] = logging.getLogger("ipops-printer")


def setup_logging(*, verbosity: Literal[0, 1, 2, 3] = 1) -> None:
    """Set up a console logger with the output level according to the given verbosity."""
    logger.setLevel(1)
    logger.propagate = False

    if verbosity < 1:
        return

    VERBOSITY_STRING: Final[str] = "DEBUG" if verbosity > 1 else "INFO"

    console_logging_handler: logging.StreamHandler[TextIO] = logging.StreamHandler()
    console_logging_handler.setFormatter(
        logging.Formatter("{asctime} | ipops-printer | {levelname:^8} - {message}", style="{"),
    )
    console_logging_handler.setLevel(VERBOSITY_STRING)
    logger.addHandler(console_logging_handler)

    logger.debug("Logger set up with minimum output level: %s", VERBOSITY_STRING)


class GracefulTerminationHandler:
    """"""

    _exit_now: ClassVar[bool] = False

    @override
    def __new__(cls) -> Self:  # NOTE: This cannot be statically type-checked
        CANNOT_INSTANTIATE_MESSAGE: Final[str] = (
            f"Cannot instantiate objects of type '{cls.__name__}'."
        )
        raise RuntimeError(CANNOT_INSTANTIATE_MESSAGE)

    @classproperty
    def EXIT_NOW(cls) -> bool:
        return cls._exit_now

    @classmethod
    def _handle_termination(cls, _signum: int, _frame: FrameType | None, /) -> None:
        cls._exit_now = True

    @classmethod
    def setup(cls) -> None:
        """"""
        signal.signal(signal.SIGINT, cls._handle_termination)
        signal.signal(signal.SIGTERM, cls._handle_termination)
