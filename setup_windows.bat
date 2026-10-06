@echo off
echo ============================================
echo Asistente IA DINDES - Preparacion entorno
echo ============================================
py -m venv .venv
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m ipykernel install --user --name asistente-ia-dindes --display-name "Python (Asistente IA DINDES)"
echo.
echo Entorno preparado.
echo Abra VS Code y seleccione: Python (Asistente IA DINDES)
pause
