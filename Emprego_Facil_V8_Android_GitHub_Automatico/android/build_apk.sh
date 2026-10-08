#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
python3 -m pip install --user buildozer cython
buildozer -v android debug
echo "APK em android/bin/"
