@echo off
cd /d "%~dp0"
python -m venv .venv
if errorlevel 1 goto fail
.venv\Scripts\python.exe -m pip install -e .
if errorlevel 1 goto fail
.venv\Scripts\python.exe -m football_lab.pipeline
if errorlevel 1 goto fail
.venv\Scripts\python.exe -m football_lab.analysis
if errorlevel 1 goto fail
.venv\Scripts\python.exe -m streamlit run app.py
goto end
:fail
echo No se pudo completar. Revisa el mensaje anterior.
pause
:end
