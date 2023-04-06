@echo off
CALL Z:\Code\pythons\persistent-playlist\env\Scripts\activate.bat
py "Z:\Code\pythons\persistent-playlist\playlist.py" "%cd%" %*
deactivate
