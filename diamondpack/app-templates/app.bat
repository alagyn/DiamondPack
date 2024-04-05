@echo off
SETLOCAL

: get script directory
SET home=%~dp0

SET PYTHONHOME=%home%venv\
"%home%venv\Scripts\python.exe" @@COMMAND@@ %*

