from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = [
    "README.md",
    "requirements.txt",
    ".gitignore",
    "LICENSE",
    "docs/planificacion.md",
    "docs/analisis_datos.md",
    "docs/arquitectura.md",
    "docs/optimizacion.md",
    "docs/consideraciones_eticas.md",
    "docs/manual_usuario.md",
    "data/README.md",
    "data/raw/README.md",
    "data/processed/README.md",
    "notebooks/01_exploracion.ipynb",
    "notebooks/02_preprocesamiento.ipynb",
    "notebooks/03_modelado.ipynb",
    "notebooks/04_optimizacion.ipynb",
    "notebooks/05_evaluacion.ipynb",
    "src/__init__.py",
    "app/app.py",
    "app/requirements.txt",
    "models/README.md",
    "tests/test_data_processing.py",
    "tests/test_structured_query.py",
    "tests/test_abstention.py",
    "tests/test_cloud_backend.py",
    "tests/test_app.py",
    "results/README.md",
    "streamlit_app.py",
]

missing = [rel for rel in REQUIRED if not (ROOT / rel).exists()]

print("=" * 68)
print("VERIFICACIÓN DE ESTRUCTURA — ENTREGA FINAL")
print("=" * 68)

for rel in REQUIRED:
    status = "OK" if (ROOT / rel).exists() else "FALTA"
    print(f"{status:5} {rel}")

print()
if missing:
    print("RESULTADO: INCOMPLETO")
    print("Faltantes:", len(missing))
    sys.exit(1)

print("RESULTADO: ESTRUCTURA MÍNIMA COMPLETA")
print("Siguiente paso: ejecutar")
print('  python -m unittest discover -s tests -p "test_*.py" -v')
