from __future__ import annotations

import streamlit as st

from src.cloud_runtime import is_cloud_runtime


def render_cloud_banner() -> None:
    if not is_cloud_runtime():
        return

    st.info(
        "☁️ **Versión Cloud Demo para evaluación académica.** "
        "Usa datos demostrativos y una generación ligera basada en evidencia. "
        "La versión institucional/local conserva el modelo Qwen ejecutado "
        "en infraestructura propia."
    )
