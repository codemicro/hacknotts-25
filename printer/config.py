""""""

import abc
import logging
import os
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Collection, Sequence
    from logging import Logger
    from typing import Any, ClassVar, Final, LiteralString


__all__: Sequence[str] = ()


logger: Final[Logger] = logging.getLogger("ipops-printer")


LOG_LEVEL_VALUES: Final[Collection[LiteralString]] = (
    "DEBUG",
    "INFO",
    "WARNING",
    "ERROR",
    "CRITICAL",
)


class Settings(abc.ABC):
    """
    Settings class that provides access to all settings values.

    Settings values can be accessed via key (like a dictionary) or via class attribute.
    """

    _is_env_variables_setup: ClassVar[bool]
    _settings: ClassVar[dict[str, object]]

    @classmethod
    def get_invalid_settings_key_message(cls, item: str) -> str:
        """Return the message to state that the given settings key is invalid."""
        return f"{item!r} is not a valid settings key."

    def __getattr__(self, item: str) -> Any:  # type: ignore[explicit-any]  # noqa: ANN401
        """Retrieve settings value by attribute lookup."""
        MISSING_ATTRIBUTE_MESSAGE: Final[str] = (
            f"{type(self).__name__!r} object has no attribute {item!r}"
        )

        if (
            "_pytest" in item or item in ("__bases__", "__test__")
        ):  # NOTE: Overriding __getattr__() leads to many edge-case issues where external libraries will attempt to call getattr() with peculiar values
            raise AttributeError(MISSING_ATTRIBUTE_MESSAGE)

        if not self._is_env_variables_setup:
            self._setup_env_variables()

        if item in self._settings:
            return self._settings[item]

        if re.fullmatch(r"\A[A-Z](?:[A-Z_]*[A-Z])?\Z", item):
            INVALID_SETTINGS_KEY_MESSAGE: Final[str] = self.get_invalid_settings_key_message(
                item
            )
            raise AttributeError(INVALID_SETTINGS_KEY_MESSAGE)

        raise AttributeError(MISSING_ATTRIBUTE_MESSAGE)

    def __getitem__(self, item: str) -> Any:  # type: ignore[explicit-any]  # noqa: ANN401
        """Retrieve settings value by key lookup."""
        attribute_not_exist_error: AttributeError
        try:
            return getattr(self, item)
        except AttributeError as attribute_not_exist_error:
            key_error_message: str = item

            if self.get_invalid_settings_key_message(item) in str(attribute_not_exist_error):
                key_error_message = str(attribute_not_exist_error)

            raise KeyError(key_error_message) from None

    @classmethod
    def setup_logging(cls) -> None:
        """Set up a console logger with the output level according to the given verbosity."""
        log_level: str = os.getenv("IPOPS_PRINTER_LOG_LEVEL", "INFO").strip().upper()
        if log_level not in LOG_LEVEL_VALUES:
            INVALID_LOG_LEVEL_MESSAGE: Final[str] = (
                f"Invalid value for IPOPS_PRINTER_LOG_LEVEL: {log_level}"
            )
            raise ValueError(INVALID_LOG_LEVEL_MESSAGE)

        logger.setLevel(getattr(logging, log_level))

        console_logging_handler: logging.Handler = logging.StreamHandler()
        console_logging_handler.setFormatter(
            logging.Formatter(
                "{asctime} | ipops-printer | {levelname:^8} - {message}", style="{"
            ),
        )
        logger.addHandler(console_logging_handler)
        logger.propagate = False

        logger.debug("Logger set up with minimum output level: %s", log_level)

    def _get_max_buffer_size() -> int:
        raw_max_buffer_size: str = os.getenv(
            "IPOPS_PRINTER_MAX_BUFFER_SIZE", default=""
        ).strip()

        if not raw_max_buffer_size:
            raw_max_buffer_size = "2000"

        try:
            return int(raw_max_buffer_size)
        except ValueError as e:
            INVALID_MAX_BUFFER_SIZE_MESSAGE: Final[str] = (
                f"Invalid value for IPOPS_PRINTER_MAX_BUFFER_SIZE: {raw_max_buffer_size}"
            )
            raise ValueError(INVALID_MAX_BUFFER_SIZE_MESSAGE) from e
