#!/usr/bin/env python3
"""
Main entry point for Receipt Tools application
Launches the PyQt5 GUI from the QtGUI module
"""
import sys
import os

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

# Import and run the main application
from QtGUI.main_qt import main

if __name__ == '__main__':
    main()
