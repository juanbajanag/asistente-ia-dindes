from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

required = [
    "README.md",
    "docs/images/README.md",
    "docs/planificacion_final.md",
    "results/figures/comparacion_f1.png",
    "results/metrics/metricas_finales.csv",
    "results/reports/resumen_evaluacion.md",
]

screenshots = [
    "docs/images/01_interfaz_principal.png",
    "docs/images/02_consulta_estructurada_dewalt.png",
    "docs/images/03_consulta_cuantitativa_creality.png",
    "docs/images/04_consulta_rag_simulador.png",
    "docs/images/05_abstencion_sin_evidencia.png",
]

print("=" * 70)
print("FASE 14.1 — VERIFICACIÓN DE PRESENTACIÓN FINAL")
print("=" * 70)

missing_required = []
for rel in required:
    ok = (ROOT / rel).exists()
    print(("OK   " if ok else "FALTA"), rel)
    if not ok:
        missing_required.append(rel)

print()
print("CAPTURAS")
missing_screenshots = []
for rel in screenshots:
    ok = (ROOT / rel).exists()
    print(("OK   " if ok else "PEND "), rel)
    if not ok:
        missing_screenshots.append(rel)

print()
if missing_required:
    print("RESULTADO: INCOMPLETO")
    sys.exit(1)

print("RESULTADO BASE: OK")
print(f"Capturas pendientes: {len(missing_screenshots)}")
print("Antes de la entrega final:")
print("1. agregar capturas reales;")
print("2. ejecutar y guardar los 5 notebooks con outputs;")
print("3. incorporar enlaces de los dos videos.")
