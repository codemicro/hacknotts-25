""""""

import abc
import enum
import logging
import os
import re
from enum import Enum
from typing import TYPE_CHECKING, cast, final, override

if TYPE_CHECKING:
    from collections.abc import Collection, Sequence
    from logging import Logger
    from typing import Any, ClassVar, Final, LiteralString


__all__: Sequence[str] = (
    "ImproperlyConfiguredError",
    "PDFDataFormat",
    "run_setup",
    "settings",
)


logger: Final[Logger] = logging.getLogger("ipops-printer")


LOG_LEVEL_VALUES: Final[Collection[LiteralString]] = (
    "DEBUG",
    "INFO",
    "WARNING",
    "ERROR",
    "CRITICAL",
)
ENVIRONMENT_VARIABLE_PREFIX: Final[LiteralString] = "IPOPS_PRINTER_"


class ImproperlyConfiguredError(Exception):
    """Exception class to raise when environment variables are not correctly provided."""

    @override
    def __init__(self, message: str | None = None) -> None:
        """Initialise a new exception with the given error message."""
        self.message: str = (
            message or "One or more provided environment variable values are invalid."
        )

        super().__init__(self.message)


class PDFDataFormat(Enum):
    """"""

    TEXT = enum.auto()
    DATA_MATRIX = enum.auto()


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
    def _setup_logging(cls) -> None:
        """Set up a console logger with the output level according to the given verbosity."""
        log_level: str = os.getenv("IPOPS_PRINTER_LOG_LEVEL", "INFO").strip().upper()
        if log_level not in LOG_LEVEL_VALUES:
            INVALID_LOG_LEVEL_MESSAGE: Final[str] = (
                f"Invalid value for IPOPS_PRINTER_LOG_LEVEL: {log_level}"
            )
            raise ImproperlyConfiguredError(INVALID_LOG_LEVEL_MESSAGE)

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

    @classmethod
    def _setup_max_buffer_size(cls) -> None:
        raw_max_buffer_size: str = os.getenv(
            f"{ENVIRONMENT_VARIABLE_PREFIX}MAX_BUFFER_SIZE", default=""
        ).strip()

        if not raw_max_buffer_size:
            cls._settings["MAX_BUFFER_SIZE"] = 1500
            return

        INVALID_MAX_BUFFER_SIZE_MESSAGE: Final[str] = f"{
            ENVIRONMENT_VARIABLE_PREFIX
        }MAX_BUFFER_SIZE must be an integer between & including 2 to 10000."

        try:
            max_buffer_size: int = int(raw_max_buffer_size)
        except ValueError as e:
            raise ImproperlyConfiguredError(INVALID_MAX_BUFFER_SIZE_MESSAGE) from e

        if not 2 <= max_buffer_size <= 10000:
            raise ImproperlyConfiguredError(INVALID_MAX_BUFFER_SIZE_MESSAGE)

        cls._settings["MAX_BUFFER_SIZE"] = max_buffer_size

    @classmethod
    def _setup_contiguous_min_buffer_size(cls) -> None:
        if "MAX_BUFFER_SIZE" not in cls._settings:
            INVALID_SETUP_ORDER_MESSAGE: Final[str] = (
                "Invalid setup order: MAX_BUFFER_SIZE must be set up "
                "before CONTIGUOUS_MIN_BUFFER_SIZE can be set up."
            )
            raise RuntimeError(INVALID_SETUP_ORDER_MESSAGE)

        raw_contiguous_min_buffer_size: str = os.getenv(
            f"{ENVIRONMENT_VARIABLE_PREFIX}CONTIGUOUS_MIN_BUFFER_SIZE", default=""
        ).strip()

        if not raw_contiguous_min_buffer_size:
            cls._settings["CONTIGUOUS_MIN_BUFFER_SIZE"] = 1400
            return

        INVALID_CONTIGUOUS_MIN_BUFFER_SIZE_MESSAGE: Final[str] = f"{
            ENVIRONMENT_VARIABLE_PREFIX
        }CONTIGUOUS_MIN_BUFFER_SIZE must be an integer between & including 1 to {
            cast('int', cls._settings['MAX_BUFFER_SIZE']) - 1
        }."

        try:
            contiguous_min_buffer_size: int = int(raw_contiguous_min_buffer_size)
        except ValueError as e:
            raise ImproperlyConfiguredError(INVALID_CONTIGUOUS_MIN_BUFFER_SIZE_MESSAGE) from e

        if not 1 <= contiguous_min_buffer_size < cast("int", cls._settings["MAX_BUFFER_SIZE"]):
            raise ImproperlyConfiguredError(INVALID_CONTIGUOUS_MIN_BUFFER_SIZE_MESSAGE)

        cls._settings["CONTIGUOUS_MIN_BUFFER_SIZE"] = contiguous_min_buffer_size

    @classmethod
    def _setup_contiguous_data_timeout(cls) -> None:
        raw_contiguous_data_timeout: str = os.getenv(
            f"{ENVIRONMENT_VARIABLE_PREFIX}CONTIGUOUS_DATA_TIMEOUT", default=""
        ).strip()

        if not raw_contiguous_data_timeout:
            cls._settings["CONTIGUOUS_DATA_TIMEOUT"] = 10.0
            return

        INVALID_CONTIGUOUS_DATA_TIMEOUT_MESSAGE: Final[str] = f"{
            ENVIRONMENT_VARIABLE_PREFIX
        }CONTIGUOUS_DATA_TIMEOUT must be a float between & including 0.01 to 1000."

        try:
            contiguous_data_timeout: float = float(raw_contiguous_data_timeout)
        except ValueError as e:
            raise ImproperlyConfiguredError(INVALID_CONTIGUOUS_DATA_TIMEOUT_MESSAGE) from e

        if not 0.01 <= contiguous_data_timeout < 1000:  # noqa: PLR2004
            raise ImproperlyConfiguredError(INVALID_CONTIGUOUS_DATA_TIMEOUT_MESSAGE)

        cls._settings["CONTIGUOUS_DATA_TIMEOUT"] = contiguous_data_timeout

    @classmethod
    def _setup_new_frame_polling_rate(cls) -> None:
        raw_new_frame_polling_rate: str = os.getenv(
            f"{ENVIRONMENT_VARIABLE_PREFIX}NEW_FRAME_POLLING_RATE", default=""
        ).strip()

        if not raw_new_frame_polling_rate:
            cls._settings["NEW_FRAME_POLLING_RATE"] = 0.15
            return

        INVALID_NEW_FRAME_POLLING_RATE_MESSAGE: Final[str] = f"{
            ENVIRONMENT_VARIABLE_PREFIX
        }NEW_FRAME_POLLING_RATE must be a float between & including 0.01 to 10."

        try:
            new_frame_polling_rate: float = float(raw_new_frame_polling_rate)
        except ValueError as e:
            raise ImproperlyConfiguredError(INVALID_NEW_FRAME_POLLING_RATE_MESSAGE) from e

        if not 0.01 <= new_frame_polling_rate < 10:  # noqa: PLR2004
            raise ImproperlyConfiguredError(INVALID_NEW_FRAME_POLLING_RATE_MESSAGE)

        cls._settings["NEW_FRAME_POLLING_RATE"] = new_frame_polling_rate

    @classmethod
    def _setup_pdf_data_format(cls) -> None:
        pdf_data_format: str = (
            os.getenv(f"{ENVIRONMENT_VARIABLE_PREFIX}PDF_DATA_FORMAT", default="")
            .strip()
            .lower()
            .replace("_", "-")
            .replace(" ", "-")
        )

        if not pdf_data_format:
            cls._settings["PDF_DATA_FORMAT"] = PDFDataFormat.DATA_MATRIX
            return

        if pdf_data_format in ("text", "txt", "raw", "string", "str", "base64"):
            cls._settings["PDF_DATA_FORMAT"] = PDFDataFormat.TEXT
            return

        if pdf_data_format in ("matrix", "qr-code", "qrcode", "data-matrix"):
            cls._settings["PDF_DATA_FORMAT"] = PDFDataFormat.DATA_MATRIX
            return

        INVALID_PDF_DATA_FORMAT_MESSAGE: Final[str] = f"{
            ENVIRONMENT_VARIABLE_PREFIX
        }PDF_DATA_FORMAT must be either 'data-matrix' or 'text'."
        raise ImproperlyConfiguredError(INVALID_PDF_DATA_FORMAT_MESSAGE)

    @classmethod
    def _setup_env_variables(cls) -> None:
        """
        Load environment values into the settings dictionary.

        Environment values are loaded from the .env file/the current environment variables and
        are only stored after the input values have been validated.
        """
        if cls._is_env_variables_setup:
            logger.warning("Environment variables have already been set up.")
            return

        cls._setup_logging()
        cls._setup_max_buffer_size()
        cls._setup_contiguous_min_buffer_size()
        cls._setup_contiguous_data_timeout()
        cls._setup_new_frame_polling_rate()
        cls._setup_pdf_data_format()

        cls._is_env_variables_setup = True


def _settings_class_factory() -> type[Settings]:
    @final
    class RuntimeSettings(Settings):  # noqa: CAR160
        """
        Settings class that provides access to all settings values.

        Settings values can be accessed via key (like a dictionary) or via class attribute.
        """

        _is_env_variables_setup: ClassVar[bool] = False
        _settings: ClassVar[dict[str, object]] = {}

    return RuntimeSettings


settings: Final[Settings] = _settings_class_factory()()


def run_setup() -> None:
    """Execute the required setup functions."""
    settings._setup_env_variables()  # noqa: SLF001
