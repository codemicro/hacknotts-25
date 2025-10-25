""""""

from typing import TYPE_CHECKING, override

from fpdf import FPDF
from fpdf.enums import WrapMode

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Literal

__all__: Sequence[str] = ("text_to_pdf",)


class _IPOPS_PDF(FPDF):
    @override
    def __init__(
        self,
        starting_page_num: int,
        orientation: Literal["", "portrait", "p", "P", "landscape", "l", "L"] = "portrait",
        unit: Literal["pt", "mm", "cm", "in"] | float = "mm",
        format: Literal[
            "", "a3", "A3", "a4", "A4", "a5", "A5", "letter", "Letter", "legal", "Legal"
        ]
        | tuple[float, float] = "A4",
    ) -> None:
        self.starting_page_num: int = starting_page_num
        super().__init__(orientation=orientation, unit=unit, format=format)

    @override
    def footer(self) -> None:
        self.set_y(-15)
        self.set_x(-15)
        self.set_font("Courier", size=16)
        self.cell(0, 10, str(self.starting_page_num + self.page_no()), align="C")


def text_to_pdf(text: str, starting_page_num: int) -> bytearray:
    """"""
    pdf: FPDF = _IPOPS_PDF(format="A4", starting_page_num=starting_page_num)

    pdf.add_page()
    pdf.set_font("Courier", size=12)
    pdf.write(text=text, wrapmode=WrapMode.CHAR)

    return pdf.output()
