""""""

import base64
from typing import TYPE_CHECKING, override

from fpdf import FPDF
from fpdf.enums import WrapMode
from PIL import Image
from pylibdmtx import pylibdmtx

from .config import PDFDataFormat, settings

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path
    from typing import Final, Literal

__all__: Sequence[str] = ("bytes_into_pdf",)


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
            "dejavu-sans" if settings.PDF_DATA_FORMAT is PDFDataFormat.TEXT else "Courier",
            size=16,
        )
        self.cell(0, 10, str(self.starting_page_number + self.page_no()), align="C")


def bytes_into_pdf(content: bytes, starting_page_number: int) -> tuple[bytearray, int]:
    """"""
    pdf: FPDF = _IPoPS_PDF(format="A4", starting_page_number=starting_page_number)
    pdf.add_page()

    match settings.PDF_DATA_FORMAT:
        case PDFDataFormat.TEXT:
            pdf.add_font("dejavu-sans", fname=_get_font_location("DejaVu Sans"))
            pdf.set_font("dejavu-sans", size=12)
            pdf.write(text=_encode_bytes_base64_for_ocr(content), wrapmode=WrapMode.CHAR)

        case PDFDataFormat.DATA_MATRIX:
            encoded_datamatrix: pylibdmtx.Encoded = pylibdmtx.encode(content)
            pdf.image(
                Image.frombytes(
                    "RGB",
                    (encoded_datamatrix.width, encoded_datamatrix.height),
                    encoded_datamatrix.pixels,
                )
            )

        case _:
            UNKNOWN_PDF_DATA_FORMAT_ERROR: Final[str] = (
                f"Unrecognized PDF data format: {settings.PDF_DATA_FORMAT}"
            )
            raise ValueError(UNKNOWN_PDF_DATA_FORMAT_ERROR)

    return pdf.output(), pdf.pages_count
