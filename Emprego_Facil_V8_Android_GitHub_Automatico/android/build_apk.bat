@echo off
wsl bash -lc "cd \"$(wslpath -a '%~dp0')\" && bash build_apk.sh"
pause
