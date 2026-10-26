from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
text = (ROOT / "src" / "cloud_backend.py").read_text(encoding="utf-8")
checks = {
    "DETALLE DE MODELO": "_special_model_detail_response" in text,
    "FORMATEADOR DE CAMPOS": "_source_detail_lines" in text,
    "IDENTIFICADOR ENRIQUECIDO": "La fuente coincide con el identificador" in text,
    "DETALLE ACTIVADO ANTES DEL RAG GENÉRICO": "model_detail = self._special_model_detail_response" in text,
}
print("=" * 68)
print("FASE 14.5 — VERIFICACIÓN DETALLE CLOUD")
print("=" * 68)
failed = False
for name, ok in checks.items():
    print(("OK   " if ok else "FALTA"), name)
    failed = failed or not ok
print()
print("RESULTADO:", "INCOMPLETO" if failed else "OK")
if failed:
    sys.exit(1)
