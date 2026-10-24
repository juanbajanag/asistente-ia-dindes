from __future__ import annotations

import hmac
import streamlit as st


ROLE_PERMISSIONS = {
    "administrador": {
        "can_query": True,
        "can_view_sources": True,
        "can_view_history": True,
        "can_view_audit": True,
        "can_submit_feedback": True,
        "can_manage_documents": True,
    },
    "analista": {
        "can_query": True,
        "can_view_sources": True,
        "can_view_history": True,
        "can_view_audit": False,
        "can_submit_feedback": True,
        "can_manage_documents": False,
    },
    "consulta": {
        "can_query": True,
        "can_view_sources": True,
        "can_view_history": False,
        "can_view_audit": False,
        "can_submit_feedback": True,
        "can_manage_documents": False,
    },
}


def _load_users() -> dict:
    try:
        users = st.secrets["users"]
    except Exception as exc:
        raise RuntimeError(
            "No se encontró la sección [users] en .streamlit/secrets.toml."
        ) from exc

    result = {}

    for username, data in users.items():
        result[str(username)] = {
            "password": str(data.get("password", "")),
            "role": str(data.get("role", "consulta")).lower(),
            "display_name": str(data.get("display_name", username)),
        }

    return result


def authenticate(username: str, password: str) -> dict | None:
    users = _load_users()
    user = users.get(username.strip())

    if not user:
        return None

    if not hmac.compare_digest(password, user["password"]):
        return None

    role = user["role"]

    if role not in ROLE_PERMISSIONS:
        role = "consulta"

    return {
        "username": username.strip(),
        "display_name": user["display_name"],
        "role": role,
        "permissions": ROLE_PERMISSIONS[role],
    }


def init_auth_state() -> None:
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if "user" not in st.session_state:
        st.session_state.user = None


def login_form() -> bool:
    init_auth_state()

    if st.session_state.authenticated:
        return True

    st.markdown("<br><br>", unsafe_allow_html=True)

    _, center, _ = st.columns([1.35, 2.3, 1.35])

    with center:
        st.markdown(
            """
            <div style="text-align:center; margin-bottom:1.1rem;">
                <div style="font-size:2.35rem; font-weight:700; line-height:1.2;">
                    ⚓ Asistente IA DINDES
                </div>
                <div style="margin-top:0.55rem; color:#9ca3af; font-size:1rem;">
                    Acceso al sistema
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form("login_form", border=True):
            username = st.text_input(
                "Usuario",
                autocomplete="username",
                placeholder="Ingrese su usuario",
            )

            password = st.text_input(
                "Contraseña",
                type="password",
                autocomplete="current-password",
                placeholder="Ingrese su contraseña",
            )

            submitted = st.form_submit_button(
                "Ingresar",
                type="primary",
                use_container_width=True,
            )

        st.info(
            "MVP académico. El acceso local de esta fase es demostrativo "
            "y deberá reemplazarse por autenticación institucional en producción."
        )

        if submitted:
            user = authenticate(username, password)

            if user:
                st.session_state.authenticated = True
                st.session_state.user = user
                st.rerun()

            st.error("Credenciales incorrectas.")

    return False


def logout_button() -> None:
    if st.button("Cerrar sesión", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.user = None
        st.rerun()


def current_user() -> dict:
    init_auth_state()

    user = st.session_state.user

    if not user:
        raise RuntimeError("No existe una sesión autenticada.")

    return user
