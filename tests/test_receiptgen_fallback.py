import os
import builtins
from types import SimpleNamespace

def test_create_receipt_uses_fallback_font(monkeypatch, tmp_path):
    # Monkeypatch svg2rlg and renderPDF.draw to avoid heavy deps
    import logic.receiptGen as rg

    monkeypatch.setattr(rg, 'svg2rlg', lambda p: SimpleNamespace(width=100, height=100))
    monkeypatch.setattr(rg.renderPDF, 'draw', lambda drawing, c, x, y: None)

    saved = {}

    class FakeCanvas:
        def __init__(self, fname, pagesize=None):
            self.fname = fname
        def setFont(self, *a, **k):
            pass
        def drawRightString(self, *a, **k):
            pass
        def drawImage(self, *a, **k):
            pass
        def showPage(self):
            pass
        def save(self):
            # Create a small file to simulate a saved PDF
            with open(self.fname, 'wb') as f:
                f.write(b'%PDF-1.4')
            saved['path'] = self.fname

    monkeypatch.setattr(rg.canvas, 'Canvas', FakeCanvas)

    data = {
        'recipeNum': '123',
        'payment': '100',
        'mamVal': '100',
        'customer': 'Test',
        'discription': 'desc',
        'Date': '2025-12-13'
    }

    out = str(tmp_path / 'r.pdf')
    rg.create_receipt(data, out)

    assert 'path' in saved
    assert os.path.exists(saved['path'])