from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import getFont
from bidi.algorithm import get_display
import json

hebrew_text = "שלום עולם"



pdfmetrics.registerFont(TTFont("Alef", "Alef-Regular.ttf"))
pdfmetrics.registerFont(TTFont("Alef-Bold", "Alef-Bold.ttf"))

TEMPLATE_SVG = "receipt_template_TP.svg"
OUTPUT_PDF = r"c:/tmp/receipt.pdf"
HoniSig = "HoniSigneture.jpg"
PAGE_W, PAGE_H = 125 * mm, 160 * mm

def inkScapeToReplib(
    x_mm: float,
    y_mm: float,
    box_w_mm: float,
    box_h_mm: float,
    page_h_mm: float,
    font_name: str,
    font_size_pt: float
) -> tuple[float, float]:
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
    # print(x,y)
    # 1) Right-edge X in points
    # Inkscape X is the left side of the box; for right-align we move to left+width
    x_pt = (x_mm + box_w_mm) * mm

    # 2) Baseline Y in points, flipping from top-origin to bottom-origin
    y_base_pt = (page_h_mm - y_mm) * mm

    # 3) Get font metrics (ascent/descent), in font units (1000 = em)
    font = getFont(font_name)
    asc  = font.face.ascent  / 1000.0 * font_size_pt   # ascent in points
    desc = font.face.descent / 1000.0 * font_size_pt   # descent in points (usually negative)
    # print('font acc ', asc-desc/mm ,font_height)
    y = y-box_h_mm/2
    
    return x, y

def inkscapToDraw(x_mm, y_mm, w_mm, h_mm, page_h_mm):
  """
  Convert Inkscape (SVG) coordinates to ReportLab drawImage parameters.

  Args:
    x_mm (float): X position (mm, top-left in Inkscape)
    y_mm (float): Y position (mm, top-left in Inkscape)
    w_mm (float): Width (mm)
    h_mm (float): Height (mm)
    page_h_mm (float): Page height (mm)

  Returns:
    (x_pt, y_pt, w_pt, h_pt): Position and size in points for drawImage
  """
  x_pt = x_mm * mm
  y_pt = (page_h_mm - y_mm - h_mm) * mm
  w_pt = w_mm * mm
  h_pt = h_mm * mm
  return x_pt, y_pt, w_pt, h_pt

def create_receipt(data, saveNmae):
    c = canvas.Canvas(saveNmae, pagesize=(PAGE_W, PAGE_H))
    PH = 161
    # Load and draw the SVG template
    drawing = svg2rlg(TEMPLATE_SVG)
    drawing.width, drawing.height = PAGE_W, PAGE_H  # Ensure correct scaling
    renderPDF.draw(drawing, c, 0, 0)
    # Overlay dynamic fields (like invoice number, amounts)
    c.setFont("Helvetica", 10)
    x, y = inkScapeToReplib(60, 26, 15, 5, PH, "Helvetica", 10)
    c.drawRightString(x*mm, y*mm, data["recipeNum"])
    x, y = inkScapeToReplib(11, 5*9+55.75, 13, 3.5, PH, "Helvetica", 10)
    c.drawRightString(x*mm, y*mm, data["payment"])
    x, y = inkScapeToReplib(11, 5*8+55.75, 13, 3.5, PH, "Helvetica", 10)
    c.drawRightString(x*mm, y*mm, data["mamVal"])
    rtl_text = get_display(data["customer"])  # Corrects Hebrew order
    c.setFont("Alef", 12)
    x, y = inkScapeToReplib(32, 55.75, 80, 3.5, PH, "Alef", 12)
    rtl_text = get_display(data["discription"])  # Corrects Hebrew order
    c.drawRightString(x*mm, y*mm, rtl_text)
    x, y = inkScapeToReplib(45, 36, 60, 3.5, PH, "Alef", 12)
    c.drawRightString(x*mm, y*mm, rtl_text)
    c.setFont("Alef", 10)
    x, y = inkScapeToReplib(11, 115, 104, 10, PH, "Alef", 10)
    # Compose optional bank/transfer line. If 'bank_transfer' is present use it directly,
    # otherwise build the line from available fields. If nothing is present, skip drawing.
    bank_text = ''
    if data.get('bank_transfer_referance'):
        bank_text = data.get('bank_transfer_referance')
        transfer_account = data.get('transfer_bankAccount')
        c.drawRightString(x*mm, y*mm,  transfer_account + ' :מחשבון '[::-1] + bank_text + '  העברה בנקאית אסמכתא: '[::-1])
    else:
        parts = []
        # Keep the original visual order but only include existing fields
        if data.get('payment'):
            parts.append(data.get('payment') + ' סכום: '[::-1])
        # Hebrew labels reversed in source: keep original style
        if data.get('bankAccount'):
            parts.append(data.get('bankAccount') + ' חשבון: '[::-1])
        if data.get('BankNumber'):
            parts.append( data.get('BankNumber') + ' בנק: '[::-1])
        if data.get('CheckNumber'):
            parts.append(data.get('CheckNumber')+" מס צ'ק: "[::-1])
        # join without extra separators to match previous formatting
        bank_text = ''.join(parts)
        

    x, y = inkScapeToReplib(80, 130, 24, 6, PH, "Alef", 10)
    c.drawRightString(x*mm, y*mm, f"{data.get('Date', '')}")
    x, y, w, h = inkscapToDraw(11, 131, 24, 6, PH)
    # print(f'sig pos {x} {y} {w} {h}')
    c.drawImage(HoniSig, x, y, w, h)
    c.showPage()
    c.save()
    print("Saved:", saveNmae)

def read_customer_data(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

if __name__ == "__main__":
  # Example data
  cData = read_customer_data(r"G:\My Drive\Rentals\RentalsDB\customers_data.json")
  sample_data = cData["Dalya"]
  sample_data['bank_transfer_referance'] = '1234567890'
  sample_data['transfer_bankAccount'] = '012909912'
  create_receipt(sample_data, 'c:/tmp/receipt.pdf')