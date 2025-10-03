from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import getFont
from bidi.algorithm import get_display

hebrew_text = "שלום עולם"



pdfmetrics.registerFont(TTFont("Alef", "Alef-Regular.ttf"))
pdfmetrics.registerFont(TTFont("Alef-Bold", "Alef-Bold.ttf"))

TEMPLATE_SVG = "recipt_template_TP.svg"
OUTPUT_PDF = r"c:/tmp/receipt.pdf"
PAGE_W, PAGE_H = 125 * mm, 160 * mm


from reportlab.pdfbase.pdfmetrics import getFont
from reportlab.lib.units import mm

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
    y = page_h_mm-y_mm - font_height/2
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
    print('font acc ', asc-desc/mm ,font_height)
    y = y-box_h_mm/2
    
    return x, y

def create_receipt(data):
    c = canvas.Canvas(OUTPUT_PDF, pagesize=(PAGE_W, PAGE_H))
    PH = 161
    # Load and draw the SVG template
    drawing = svg2rlg(TEMPLATE_SVG)
    drawing.width, drawing.height = PAGE_W, PAGE_H  # Ensure correct scaling
    renderPDF.draw(drawing, c, 0, 0)

    # Overlay dynamic fields (like invoice number, amounts)
    c.setFont("Helvetica", 12)
    x, y = inkScapeToReplib(11, 5*9+55.75, 13, 3.5, PH, "Helvetica", 12)
    c.drawRightString(x*mm, y*mm, data["invoice_no"])
    rtl_text = get_display(data["customer"])  # Corrects Hebrew order
    c.setFont("Alef", 12)
    x, y = inkScapeToReplib(45, 36, 60, 3.5, PH, "Alef", 12)
    c.drawRightString(x*mm, y*mm, rtl_text)
    c.setFont("Alef", 16)
    x, y = inkScapeToReplib(11, 115, 104, 10, PH, "Alef", 16)
    c.drawRightString(x*mm, y*mm, '6789'+' סכום '[::-1]+'123456'+' חשבון '[::-1]+' 12 '+'בנק'[::-1]+' 45321 '+'צק מס'[::-1])
    c.showPage()
    c.save()
    print("Saved:", OUTPUT_PDF)

# Example data
sample_data = {"invoice_no": "1234", "customer": "גזוז בתי קפה בראשון"}
create_receipt(sample_data)