from openpyxl.cell.cell import Cell
from openpyxl.styles import Font, PatternFill, numbers

from .theme import excel_color


def excel_fill(name: str) -> PatternFill:
    """Return a solid fill from the shared payroll review palette."""
    return PatternFill("solid", fgColor=excel_color(name))


def excel_font(name: str = "text", bold: bool = False) -> Font:
    """Return a font from the shared payroll review palette."""
    return Font(bold=bold, color=excel_color(name))


def money_format(cell: Cell) -> None:
    """Apply the standard two-decimal money format."""
    cell.number_format = numbers.FORMAT_NUMBER_00


def fill_row_cells(row, fill: PatternFill) -> None:
    """Apply a fill to every cell in a worksheet row."""
    for cell in row:
        cell.fill = fill
