@echo off
SETLOCAL

: get script directory
SET home=%~dp0

SET PYTHONHOME=%home%venv\
SET PATH=%home%\venv\Lib;%PATH%
"%home%venv\Scripts\python.exe" @@COMMAND@@ %*

