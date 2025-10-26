""""""

import base64
import itertools
import logging
from typing import TYPE_CHECKING, override

from fpdf import FPDF
from fpdf.enums import WrapMode
from PIL import Image
from pylibdmtx import pylibdmtx

from .config import PDFDataFormat, settings

if TYPE_CHECKING:
    from collections.abc import Sequence
    from logging import Logger
    from pathlib import Path
    from typing import Final, Literal

__all__: Sequence[str] = ("bytes_into_pdf",)


logger: Final[Logger] = logging.getLogger("ipops-printer")


def _encode_bytes_base64_for_ocr(content: bytes) -> str:
    return base64.standard_b64encode(content).decode()


def _get_font_location(font_name: str) -> Path:
    raise NotImplementedError


class _IPoPS_PDF(FPDF):
    @override
    def __init__(
        self,
        starting_page_number: int,
        orientation: Literal["", "portrait", "p", "P", "landscape", "l", "L"] = "portrait",
        unit: Literal["pt", "mm", "cm", "in"] | float = "mm",
        format: Literal[
            "", "a3", "A3", "a4", "A4", "a5", "A5", "letter", "Letter", "legal", "Legal"
        ]
        | tuple[float, float] = "A4",
    ) -> None:
        self.starting_page_number: int = starting_page_number
        super().__init__(orientation=orientation, unit=unit, format=format)

    @override
    def footer(self) -> None:
        self.set_y(-15)
        self.set_x(-15)
        self.set_font(
            "IPoPS-custom-font"
            if settings.PDF_DATA_FORMAT is PDFDataFormat.TEXT
            else "Courier",
            size=16,
        )
        self.cell(0, 10, str(self.starting_page_number + self.page_no()), align="C")


def bytes_into_pdf(content: bytes, starting_page_number: int) -> tuple[bytearray, int]:
    """"""
    pdf: FPDF = _IPoPS_PDF(format="A4", starting_page_number=starting_page_number)

    match settings.PDF_DATA_FORMAT:
        case PDFDataFormat.TEXT:
            pdf.add_font(
                "IPoPS-custom-font",
                fname=_get_font_location("DejaVu Sans"),  # Allow configuration
            )
            pdf.set_font("IPoPS-custom-font", size=12)
            pdf.write(text=_encode_bytes_base64_for_ocr(content), wrapmode=WrapMode.CHAR)

        case PDFDataFormat.DATA_MATRIX:
            logger.debug("Generating PDF with data matrix")

            page_index: int = starting_page_number
            content_chunk: Sequence[int]
            for content_chunk in itertools.batched(
                content, settings.MAX_BUFFER_SIZE, strict=False
            ):
                pdf.add_page()
                encoded_datamatrix: pylibdmtx.Encoded = pylibdmtx.encode(
                    page_index.to_bytes(length=1, byteorder="big")
                    + base64.b85encode(bytes(content_chunk))
                )
                pdf.image(
                    Image.frombytes(
                        "RGB",
                        (encoded_datamatrix.width, encoded_datamatrix.height),
                        encoded_datamatrix.pixels,
                    ),
                    w=0 if encoded_datamatrix.width < 550 else 550,
                )
                page_index += 1

        case _:
            UNKNOWN_PDF_DATA_FORMAT_ERROR: Final[str] = (
                f"Unrecognized PDF data format: {settings.PDF_DATA_FORMAT}"
            )
            raise ValueError(UNKNOWN_PDF_DATA_FORMAT_ERROR)

    return pdf.output(), pdf.pages_count
