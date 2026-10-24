"""
Punto de entrada para Streamlit Community Cloud.

No reemplaza app/app.py. Activa el modo cloud y ejecuta la aplicación
existente desde app/app.py.
"""
from __future__ import annotations

import os
from pathlib import Path
import runpy
import sys

PROJECT_ROOT = Path(__file__).resolve().parent
APP_PATH = PROJECT_ROOT / "app" / "app.py"

os.environ.setdefault("DINDES_RUNTIME", "cloud")
os.environ.setdefault("DINDES_CLOUD_MODE", "1")
os.environ.setdefault("DINDES_DISABLE_LOCAL_LLM", "1")

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if not APP_PATH.exists():
    raise FileNotFoundError(
        "No se encontró app/app.py. "
        "Verifique que streamlit_app.py esté en la raíz del proyecto."
    )

runpy.run_path(str(APP_PATH), run_name="__main__")
