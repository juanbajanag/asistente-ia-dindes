from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
structured = (ROOT / 'src' / 'structured_query.py').read_text(encoding='utf-8')
cloud = (ROOT / 'src' / 'cloud_backend.py').read_text(encoding='utf-8')
app = (ROOT / 'app' / 'app.py').read_text(encoding='utf-8')

checks = {
    'ENTIDAD DESCONOCIDA USA description_contains': 'description_contains=description_contains' in structured and '_matches_description' in structured,
    'CLOUD RESPONDE ESTADO DE INVENTARIO': '_synthesize_inventory_status' in cloud,
    'CLOUD RESPONDE DETALLE DE INVENTARIO': '_synthesize_inventory_detail' in cloud,
    'CLOUD RESPONDE COMPONENTES IA': '_special_ai_inventory_response' in cloud,
    'CLOUD RESPONDE ESTADO DOCUMENTAL': '_special_document_status_response' in cloud,
    'CLOUD SOPORTA IDENTIFICADORES EXACTOS': '_special_exact_identifier_response' in cloud,
    'CONSULTA VACÍA LIMPIA RESPUESTA': 'st.session_state.last_response = None' in app[app.index('if not question.strip():'):app.index('if not question.strip():') + 700],
}

print('=' * 72)
print('FASE 14.4 — VERIFICACIÓN HOTFIX CLOUD')
print('=' * 72)
failed = False
for name, ok in checks.items():
    print(('OK   ' if ok else 'FALTA'), name)
    failed = failed or not ok
print()
if failed:
    print('RESULTADO: INCOMPLETO')
    sys.exit(1)
print('RESULTADO: OK')
