from pathlib import Path
import ast
import sys

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "app" / "auth.py"

if not TARGET.exists():
    raise FileNotFoundError(TARGET)

text = TARGET.read_text(encoding="utf-8")
tree = ast.parse(text)

def get_function_source(name: str) -> str:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            start = node.lineno - 1
            end = node.end_lineno
            return "\n".join(text.splitlines()[start:end])
    return ""

login_src = get_function_source("login_form")
logout_src = get_function_source("logout_button")
init_src = get_function_source("init_auth_state")

checks = {
    "LOGIN LIMPIA SESSION_STATE": (
        "st.session_state.clear()" in login_src
        and "st.session_state.authenticated = True" in login_src
        and "st.session_state.user = user" in login_src
    ),
    "LOGOUT LIMPIA SESSION_STATE": (
        "st.session_state.clear()" in logout_src
        and "st.rerun()" in logout_src
    ),
    "LOGOUT NO USA LIMPIEZA PARCIAL": (
        "st.session_state.authenticated = False" not in logout_src
        and "st.session_state.user = None" not in logout_src
    ),
    "INIT_AUTH_STATE CONSERVA INICIALIZACIÓN": (
        "st.session_state.authenticated = False" in init_src
        and "st.session_state.user = None" in init_src
    ),
}

print("=" * 72)
print("FASE 14.3 — VERIFICACIÓN DE LIMPIEZA SEGURA DE SESIÓN")
print("=" * 72)

failed = False
for name, ok in checks.items():
    print(("OK   " if ok else "FALTA"), name)
    failed = failed or not ok

if failed:
    print()
    print("RESULTADO: INCOMPLETO")
    sys.exit(1)

print()
print("RESULTADO: OK")
print("El cierre de sesión limpia todo el estado temporal de Streamlit.")
print("La inicialización de una sesión nueva conserva sus valores por defecto.")
