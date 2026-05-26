"""Reset saved UI state (window geometry + last tab).

Audio preset / custom audio settings are preserved.
"""
from PyQt6.QtCore import QSettings


def main() -> None:
    s = QSettings("itunes-library-helper", "itunes-library-helper")
    for key in ("ui/window_geometry", "ui/last_tab"):
        if s.contains(key):
            s.remove(key)
            print(f"removed: {key}")
    print("done.")


if __name__ == "__main__":
    main()
