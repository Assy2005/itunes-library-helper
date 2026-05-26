"""Dump the saved QSettings for the app — used to diagnose UI state issues."""
from PyQt6.QtCore import QSettings


def main() -> None:
    s = QSettings("itunes-library-helper", "itunes-library-helper")
    keys = s.allKeys()
    if not keys:
        print("(no settings stored yet)")
        return
    for key in sorted(keys):
        v = s.value(key)
        if isinstance(v, (bytes, bytearray)):
            v = f"<binary, {len(v)} bytes>"
        print(f"  {key} = {v}")


if __name__ == "__main__":
    main()
