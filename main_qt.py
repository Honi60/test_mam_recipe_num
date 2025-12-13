"""Compatibility launcher: forward to `QtGUI.main_qt`.

This root `main_qt.py` delegates to `QtGUI/main_qt.py`. Use `run_app.py`
or `python main_qt.py` to launch the application.
"""
import sys
import os

# Ensure project root is on sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from QtGUI.main_qt import main
except Exception as e:
    raise RuntimeError(f"Failed importing QtGUI.main_qt: {e}")


if __name__ == '__main__':
    main()
