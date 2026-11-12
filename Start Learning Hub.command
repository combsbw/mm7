#!/bin/bash
# Double-click this file on a Mac to start the Learning Hub with autosave to a SQLite file.
# (The first time, macOS may ask you to allow it: right-click the file, choose Open, then Open.)
cd "$(dirname "$0")"
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is needed. Install it from https://www.python.org/downloads/ (or run: xcode-select --install) and try again."
  read -r -p "Press Return to close." _
  exit 1
fi
exec python3 mm7_helper.py "$@"
