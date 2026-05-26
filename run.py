"""Top-level launcher.

Exists so that PyInstaller (and `python run.py`) can start the app while
keeping `src/` as a proper package — i.e. the relative imports inside
src/main.py and src/gui/main_window.py keep working.
"""
import sys

from src.main import main


if __name__ == "__main__":
    sys.exit(main())
