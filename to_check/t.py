from svglib.svglib import svg2rlg
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import getFont


pdfmetrics.registerFont(TTFont("Alef", "Alef-Regular.ttf"))
pdfmetrics.registerFont(TTFont("Alef-Bold", "Alef-Bold.ttf"))


def inkScapeToReplib(
    x_mm: float,
    y_mm: float,
    box_w_mm: float,
    box_h_mm: float,
    page_h_mm: float,
    font_name: str,
    font_size_pt: float
) -> (float, float):
    """
    Convert Inkscape coords to ReportLab points for drawRightString.

    Args:
      x_mm, y_mm       : top-left corner of your text-box in mm
      box_w_mm         : width of the text-box in mm
      box_h_mm         : height of the text-box in mm
      page_h_mm        : total page height in mm
      font_name        : e.g. "Alef", must be registered
      font_size_pt     : e.g. 12

    Returns:
      (x, y)     : coordinates in mm for drawRightString
    """
    font_height = font_size_pt/mm
    y = page_h_mm-y_mm -font_height
    x = x_mm + box_w_mm
    print(x,y)
    # 1) Right-edge X in points
    # Inkscape X is the left side of the box; for right-align we move to left+width
    x_pt = (x_mm + box_w_mm) * mm

    # 2) Baseline Y in points, flipping from top-origin to bottom-origin
    y_base_pt = (page_h_mm - y_mm) * mm

    # 3) Get font metrics (ascent/descent), in font units (1000 = em)
    font = getFont(font_name)
    asc  = font.face.ascent  / 1000.0 * font_size_pt   # ascent in points
    desc = font.face.descent / 1000.0 * font_size_pt   # descent in points (usually negative)
    print(asc/mm,desc/mm )
    y = y+0*desc/mm/2+box_h_mm/2
    
    return x, y

# ─── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Your Inkscape box: x=45 mm from left, y=36 mm from top; w=60 mm; h=3.5 mm
    # Page is 125×160 mm, so page_h_mm = 160
    x, y = inkScapeToReplib(
        x_mm=45,
        y_mm=36,
        box_w_mm=60,
        box_h_mm=3.5,
        page_h_mm=160,
        font_name="Alef",
        font_size_pt=12
    )

    # Convert back to mm for easy reading:
    print(f"Converted coordinates: X={x:.2f} mm, Y={y:.2f} mm")