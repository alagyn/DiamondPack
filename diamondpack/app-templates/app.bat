@echo off
SETLOCAL

: get script directory
SET home=%~dp0

SET PYTHONHOME=%home%venv\stdlib
SET PYTHONPATH=%home%venv\Lib\site-packages
"%home%venv\Scripts\python.exe" @@COMMAND@@ %*

