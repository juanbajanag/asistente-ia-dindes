from __future__ import annotations

import streamlit as st

from src.cloud_runtime import load_cloud_config


def render_demo_examples() -> str | None:
    cfg = load_cloud_config()
    examples = cfg.get("demo_examples", [])

    if not examples:
        return None

    st.caption("Consultas sugeridas para la evaluación remota")

    selected = st.selectbox(
        "Ejemplo rápido",
        ["Seleccionar..."] + examples,
        index=0,
        key="cloud_demo_example",
    )

    if selected == "Seleccionar...":
        return None

    return selected
