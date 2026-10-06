from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib
import sklearn

ROOT = Path(__file__).resolve().parent
files = [
    ROOT / "data" / "Dataset_1_Documentacion_Tecnica_DINDES_Sample.csv",
    ROOT / "data" / "Dataset_3_Evaluacion_QA_Asistente_IA_Sample.csv",
    ROOT / "notebooks" / "overfitting_analysis.ipynb",
]
print("=== Verificación del proyecto ===")
for f in files:
    print(("OK  " if f.exists() else "FALTA"), f.relative_to(ROOT))
print("pandas:", pd.__version__)
print("numpy:", np.__version__)
print("matplotlib:", matplotlib.__version__)
print("scikit-learn:", sklearn.__version__)
print("\nEntorno listo para ejecutar el notebook." if all(f.exists() for f in files) else "\nRevise los archivos faltantes.")
