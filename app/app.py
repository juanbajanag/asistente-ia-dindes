from __future__ import annotations

import csv
import re
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st


# ================================================================
# RUTAS DEL PROYECTO
# ================================================================
APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ================================================================
# IMPORTS DEL PROYECTO
# ================================================================
from app.auth import current_user, login_form, logout_button
from app.audit import AuditTimer, write_audit_event
from src.corpus_builder import build_complete_corpus
from src.inventory_analytics import InventoryAnalytics
from src.inventory_replenishment import InventoryReplenishment
from src.inventory_criticality import InventoryCriticality, VALID_CRITICALITIES
from src.inventory_operational_priority import OperationalPriorityMatrix
from src.replenishment_decisions import ReplenishmentDecisionStore, VALID_MANAGEMENT_STATUS
from src.replenishment_decision_audit import ReplenishmentDecisionAuditStore, format_timestamp, transition_label
from src.document_manager import ingest_uploaded_file
from src.ingestion import load_jsonl
from src.rag_pipeline_synthesis import RAGPipeline
from src.runtime_config import get_rag_runtime_settings, is_cloud_runtime
from src.runtime_pipeline_factory import build_runtime_pipeline


# ================================================================
# CONFIGURACIÓN
# ================================================================

# ================================================================
# HOTFIX FASE 13.1 — FORMATEO ROBUSTO DE EVIDENCIA
# ================================================================
def format_evidence_text(source):
    """Devuelve un texto seguro para mostrar la evidencia recuperada."""
    if source is None:
        return ""

    if isinstance(source, str):
        return source.strip()

    if isinstance(source, dict):
        for key in (
            "text",
            "content",
            "chunk",
            "page_content",
            "evidence",
            "description",
        ):
            value = source.get(key)
            if value not in (None, ""):
                return str(value).strip()
        return str(source).strip()

    for attr in (
        "text",
        "content",
        "chunk",
        "page_content",
        "evidence",
        "description",
    ):
        if hasattr(source, attr):
            value = getattr(source, attr)
            if value not in (None, ""):
                return str(value).strip()

    return str(source).strip()


st.set_page_config(
    page_title="Asistente IA DINDES",
    page_icon="⚓",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = PROJECT_ROOT / "results"
RESULTS_DIR.mkdir(exist_ok=True)

FEEDBACK_PATH = RESULTS_DIR / "feedback_usuarios.csv"
AUDIT_PATH = RESULTS_DIR / "audit_log.csv"
CRITICALITY_CATALOG_PATH = PROJECT_ROOT / "config" / "inventory_criticality.csv"
REPLENISHMENT_DECISIONS_PATH = PROJECT_ROOT / "config" / "replenishment_decisions.csv"
REPLENISHMENT_DECISIONS_AUDIT_PATH = PROJECT_ROOT / "config" / "replenishment_decision_audit.csv"


def _format_audit_timestamp(value):
    return format_timestamp(value)


DEFAULT_EMBEDDING_MODEL = "qwen3-embedding:0.6b"
DEFAULT_LLM_MODEL = "qwen3.5:9b"
DEFAULT_DENSE_THRESHOLD = 0.45
DEFAULT_TOP_K = 5
RUNTIME_SETTINGS = get_rag_runtime_settings()
DEFAULT_TEMPERATURE = float(RUNTIME_SETTINGS["temperature"])


# ================================================================
# AUTENTICACIÓN
# ================================================================
if not login_form():
    st.stop()

user = current_user()
permissions = user["permissions"]


# ================================================================
# ESTADO DE SESIÓN
# ================================================================
defaults = {
    "last_response": None,
    "last_question": "",
    "question_input": "",
    "example_selector": "",
    "feedback_saved": False,
    "feedback_choice": "Sin evaluar",
    "feedback_comment": "",
    "query_history": [],
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


def reset_feedback_state() -> None:
    st.session_state.feedback_saved = False
    st.session_state.feedback_choice = "Sin evaluar"
    st.session_state.feedback_comment = ""


def load_selected_example() -> None:
    """Copia el ejemplo al campo solo cuando el usuario cambia el selector."""
    selected = st.session_state.get("example_selector", "")
    if selected:
        st.session_state.question_input = selected


def clear_query_state() -> None:
    """Limpia consulta, respuesta y evaluación sin restaurar preguntas anteriores."""
    st.session_state.question_input = ""
    st.session_state.example_selector = ""
    st.session_state.last_question = ""
    st.session_state.last_response = None
    reset_feedback_state()


# ================================================================
# PIPELINE
# ================================================================
@st.cache_resource(show_spinner=False)
def load_rag_pipeline(
    embedding_model: str,
    llm_model: str,
    dense_threshold: float,
    top_k: int,
    temperature: float,
):
    records = build_complete_corpus(
        DATA_DIR,
        include_sample=True,
    )

    rag = build_runtime_pipeline(


        embedding_model=embedding_model,


        llm_model=llm_model,


        dense_min_score=dense_threshold,


        top_k=top_k,


        temperature=temperature,


    ).fit(records)

    return rag, len(records)


@st.cache_resource(show_spinner=False)
def load_inventory_analytics():
    records = build_complete_corpus(
        DATA_DIR,
        include_sample=True,
    )
    return InventoryAnalytics(records)


# ================================================================
# UTILIDADES GENERALES
# ================================================================
def canonical_source_id(source) -> str:
    if source.source_type == "document":
        return str(
            source.metadata.get(
                "document_id",
                source.record_id,
            )
        )
    return str(source.record_id)


def exact_match_values(source) -> list[str]:
    matches = source.metadata.get(
        "exact_match_identifiers",
        [],
    )

    if not matches:
        return []

    if isinstance(matches, str):
        return [matches]

    return [
        str(item)
        for item in matches
        if str(item).strip()
    ]


def get_abstention_label(response) -> str:
    if not response.abstained:
        return "No"

    stage = getattr(
        response,
        "abstention_stage",
        None,
    )

    if stage == "retrieval":
        return "Sí — Retrieval"

    if stage == "generation":
        return "Sí — Generación"

    return "Sí"


def save_feedback(
    *,
    question: str,
    answer: str,
    feedback_type: str,
    comment: str,
    source_ids: list[str],
):
    exists = FEEDBACK_PATH.exists()

    fields = [
        "timestamp",
        "username",
        "role",
        "question",
        "answer",
        "feedback_type",
        "comment",
        "source_ids",
    ]

    with FEEDBACK_PATH.open(
        "a",
        newline="",
        encoding="utf-8-sig",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fields,
        )

        if not exists:
            writer.writeheader()

        writer.writerow(
            {
                "timestamp": datetime.now().isoformat(
                    timespec="seconds"
                ),
                "username": user["username"],
                "role": user["role"],
                "question": question,
                "answer": answer,
                "feedback_type": feedback_type,
                "comment": comment,
                "source_ids": ";".join(source_ids),
            }
        )


# ================================================================
# UTILIDADES DE VISUALIZACIÓN DE EVIDENCIA
# ================================================================
ASSET_CODE_RE = re.compile(r"^\d{6,9}$")


def clean_evidence_lines(text: str) -> list[str]:
    """
    Limpia líneas sin alterar el contenido sustantivo.
    """
    lines = []

    for raw in str(text).splitlines():
        line = re.sub(
            r"\s+",
            " ",
            raw,
        ).strip()

        if line:
            lines.append(line)

    return lines


def extract_exact_asset_record(
    text: str,
    matches: list[str],
) -> tuple[str | None, list[str]]:
    """
    Si existe un identificador numérico exacto, extrae únicamente el
    bloque comprendido desde ese código hasta el siguiente código de bien.

    Esto evita mostrar varios bienes consecutivos dentro del mismo chunk.
    """
    lines = clean_evidence_lines(
        text
    )

    if not lines:
        return None, []

    numeric_matches = [
        item
        for item in matches
        if item.isdigit()
        and len(item) >= 6
    ]

    if not numeric_matches:
        return None, []

    target = numeric_matches[0]

    start = None

    for idx, line in enumerate(
        lines
    ):
        if line == target:
            start = idx
            break

    if start is None:
        return None, []

    end = len(lines)

    for idx in range(
        start + 1,
        len(lines),
    ):
        if ASSET_CODE_RE.fullmatch(
            lines[idx]
        ):
            end = idx
            break

    return target, lines[
        start:end
    ]


def join_wrapped_description(
    lines: list[str],
) -> list[str]:
    """
    Mejora visual conservadora:
    une fragmentos textuales consecutivos cuando son claramente
    continuación de una descripción larga y no valores cortos/códigos.

    No asigna nombres de campos para evitar inferir columnas.
    """
    if not lines:
        return []

    output = []
    buffer = []

    def flush():
        nonlocal buffer

        if buffer:
            output.append(
                " ".join(buffer)
            )
            buffer = []

    for line in lines:
        # Valores típicos que deben mantenerse separados.
        is_code = bool(
            re.fullmatch(
                r"[A-Z0-9./_-]{1,20}",
                line,
                flags=re.IGNORECASE,
            )
        )

        is_date = bool(
            re.fullmatch(
                r"\d{1,2}/\d{1,2}/\d{4}",
                line,
            )
        )

        is_money = bool(
            re.fullmatch(
                r"[\d,]+\.\d{2}",
                line,
            )
        )

        is_short_status = (
            line.upper()
            in {
                "BUENO",
                "MALO",
                "REGULAR",
                "HABILITADO",
                "INHABILITADO",
                "S",
                "N",
                "S/M",
            }
        )

        # Frases largas o palabras consecutivas: se agrupan.
        looks_textual = (
            len(line) > 12
            and not is_code
            and not is_date
            and not is_money
            and not is_short_status
        )

        if looks_textual:
            buffer.append(line)
        else:
            flush()
            output.append(line)

    flush()

    return output


def render_relevant_evidence(
    source,
    matches: list[str],
):
    """
    Vista amigable:
    - Si existe match exacto numérico, muestra solo ese registro.
    - Si no, muestra una vista limpia del chunk.
    - Siempre conserva el texto original como respaldo.
    """
    target, record_lines = (
        extract_exact_asset_record(
            source.text,
            matches,
        )
    )

    if target and record_lines:
        st.markdown(
            f"#### Registro relacionado con `{target}`"
        )

        cleaned = join_wrapped_description(
            record_lines
        )

        # Encabezado destacado.
        st.markdown(
            f"**Código del bien:** `{target}`"
        )

        remaining = cleaned[1:]

        # Mostrar en un contenedor visual más cómodo.
        with st.container(
            border=True
        ):
            for item in remaining:
                st.markdown(
                    f"- {item}"
                )

        st.caption(
            "Vista enfocada generada a partir del chunk recuperado. "
            "El texto original permanece disponible debajo."
        )

    else:
        st.markdown(
            "#### Fragmento recuperado"
        )

        cleaned = join_wrapped_description(
            clean_evidence_lines(
                source.text
            )
        )

        with st.container(
            border=True
        ):
            for item in cleaned:
                st.markdown(
                    f"- {item}"
                )

    with st.expander(
        "Ver texto original del chunk",
        expanded=False,
    ):
        st.code(
            source.text,
            language=None,
            wrap_lines=True,
        )


# ================================================================
# SIDEBAR
# ================================================================
with st.sidebar:
    st.header("Sesión")
    st.write(
        f"**Usuario:** {user['display_name']}"
    )
    st.write(
        f"**Rol:** {user['role']}"
    )

    logout_button()

    st.divider()
    st.header("Configuración")

    embedding_model = st.text_input(
        "Modelo de embeddings",
        value=DEFAULT_EMBEDDING_MODEL,
    )

    llm_model = st.text_input(
        "Modelo generativo",
        value=DEFAULT_LLM_MODEL,
    )

    dense_threshold = st.slider(
        "Umbral denso",
        min_value=0.30,
        max_value=0.60,
        value=DEFAULT_DENSE_THRESHOLD,
        step=0.01,
    )

    top_k = st.slider(
        "Top-K de evidencias",
        min_value=1,
        max_value=10,
        value=DEFAULT_TOP_K,
        step=1,
    )

    temperature = st.slider(
        "Temperatura",
        min_value=0.0,
        max_value=1.0,
        value=DEFAULT_TEMPERATURE,
        step=0.1,
        disabled=is_cloud_runtime(),
        help=(
            "En la demo cloud la temperatura se fija en 0.0 por estabilidad y reproducibilidad."
            if is_cloud_runtime()
            else "Temperatura del modelo generativo."
        ),
    )


# ================================================================
# CARGA DEL PIPELINE
# ================================================================
try:
    with st.spinner(
        "Inicializando el asistente..."
    ):
        rag, corpus_size = load_rag_pipeline(
            embedding_model=embedding_model,
            llm_model=llm_model,
            dense_threshold=dense_threshold,
            top_k=top_k,
            temperature=temperature,
        )

    pipeline_ready = True

except Exception as exc:
    rag = None
    corpus_size = 0
    pipeline_ready = False

    st.error(
        "No fue posible iniciar el pipeline."
    )

    with st.expander(
        "Detalle técnico"
    ):
        st.exception(exc)


# ================================================================
# ENCABEZADO
# ================================================================
st.title(
    "⚓ Asistente IA DINDES"
)

st.caption(
    "Consulta, recuperación y gestión del conocimiento técnico."
)

c1, c2, c3 = st.columns(3)

c1.metric(
    "Estado",
    (
        "Operativo"
        if pipeline_ready
        else "No disponible"
    ),
)

c2.metric(
    "Registros",
    corpus_size,
)

c3.metric(
    "Top-K",
    top_k,
)

st.info(
    "Herramienta de apoyo. "
    "Verifique las fuentes originales antes de adoptar decisiones."
)


# ================================================================
# PESTAÑAS
# ================================================================
tab_names = [
    "Consulta",
    "Inventario",
]

if permissions["can_view_history"]:
    tab_names.append(
        "Historial"
    )

if permissions["can_view_audit"]:
    tab_names.append(
        "Auditoría"
    )

if permissions.get(
    "can_manage_documents",
    False,
):
    tab_names.append(
        "Documentos"
    )

tabs = st.tabs(
    tab_names
)

tab_map = {
    name: tab
    for name, tab in zip(
        tab_names,
        tabs,
    )
}



# ================================================================
# INVENTARIO — FASE 9
# ================================================================
with tab_map["Inventario"]:

    try:
        inventory = load_inventory_analytics()
        kpis = inventory.kpis()

        # Hotfix Fase 9.3.1:
        # El KPI superior usa la misma política consolidada
        # que la sección "Gestión de reposición".
        replenishment = InventoryReplenishment(
            inventory.rows
        )
        replenishment_summary = replenishment.summary()

        criticality = InventoryCriticality(
            inventory.rows,
            CRITICALITY_CATALOG_PATH,
        )
        criticality_summary = criticality.summary()

        decision_audit_store = ReplenishmentDecisionAuditStore(
            REPLENISHMENT_DECISIONS_AUDIT_PATH
        )
        decision_store = ReplenishmentDecisionStore(
            REPLENISHMENT_DECISIONS_PATH,
            audit_store=decision_audit_store,
        )

        st.header(
            "Dashboard de inventario"
        )

        st.caption(
            "Analítica determinística sobre los registros "
            "estructurados ingeridos. Esta vista no utiliza "
            "el modelo generativo."
        )

        k1, k2, k3, k4 = st.columns(
            4
        )

        k1.metric(
            "Registros",
            kpis.total_records,
        )

        k2.metric(
            "Stock total",
            kpis.total_stock,
        )

        k3.metric(
            "Disponibles",
            kpis.available_records,
        )

        k4.metric(
            "Sin stock",
            kpis.zero_stock_records,
        )

        k5, k6, k7, k8 = st.columns(
            4
        )

        k5.metric(
            "Cantidad total",
            kpis.total_quantity,
        )

        k6.metric(
            "Artículos a reponer",
            replenishment_summary[
                "Artículos a reponer"
            ],
        )

        k7.metric(
            "Marcas",
            kpis.total_brands,
        )

        k8.metric(
            "Calidad alta",
            kpis.high_quality_records,
        )

        if kpis.excluded_records:
            st.info(
                f"Se excluyeron {kpis.excluded_records} fila(s) de encabezado, "
                "título o sin valores cuantitativos del cálculo del inventario."
            )

        if kpis.review_records:
            st.warning(
                f"{kpis.review_records} registro(s) presentan observaciones de calidad. "
                f"Se detectaron {kpis.duplicate_groups} grupo(s) de posibles duplicados."
            )

        st.divider()

        st.subheader(
            "Explorar inventario"
        )

        f1, f2, f3, f4 = st.columns(
            [1, 1, 1, 2]
        )

        with f1:
            selected_brand = st.selectbox(
                "Marca",
                [
                    "Todas",
                    *inventory.brands(),
                ],
                key="inventory_brand_filter",
            )

        with f2:
            selected_status = st.selectbox(
                "Estado",
                [
                    "Todos",
                    "Disponible",
                    "Sin stock",
                    "Reposición",
                ],
                key="inventory_status_filter",
            )

        with f3:
            selected_quality = st.selectbox(
                "Calidad",
                ["Todos", "Alta", "Media", "Revisar"],
                key="inventory_quality_filter",
            )

        with f4:
            inventory_search = st.text_input(
                "Buscar",
                placeholder=(
                    "Descripción, modelo o número de ítem..."
                ),
                key="inventory_search_filter",
            )

        filtered_rows = inventory.rows_filtered(
            brand=selected_brand,
            status=selected_status,
            search=inventory_search,
            quality=selected_quality,
        )

        st.write(
            f"**Registros encontrados:** "
            f"{len(filtered_rows)}"
        )

        if filtered_rows:
            filtered_df = pd.DataFrame(
                filtered_rows
            )

            st.dataframe(
                filtered_df,
                use_container_width=True,
                hide_index=True,
                height=430,
            )

            st.download_button(
                "Descargar inventario filtrado CSV",
                data=filtered_df.to_csv(
                    index=False
                ).encode(
                    "utf-8-sig"
                ),
                file_name=(
                    "inventario_filtrado.csv"
                ),
                mime="text/csv",
                key=(
                    "download_inventory_filtered"
                ),
            )

        else:
            st.info(
                "No existen registros que cumplan "
                "los filtros seleccionados."
            )

        st.divider()

        st.subheader(
            "Calidad de los registros"
        )

        quality_df = pd.DataFrame(
            inventory.quality_distribution()
        )

        if not quality_df.empty:
            st.bar_chart(
                quality_df.set_index("Nivel")["Registros"],
                use_container_width=True,
            )

        review_rows = inventory.quality_review_rows()
        if review_rows:
            with st.expander(
                f"Registros para revisión ({len(review_rows)})"
            ):
                st.dataframe(
                    pd.DataFrame(review_rows),
                    use_container_width=True,
                    hide_index=True,
                    height=360,
                )

        duplicate_rows = inventory.duplicate_groups()
        if duplicate_rows:
            with st.expander(
                f"Posibles duplicados ({len(duplicate_rows)} grupos)"
            ):
                st.dataframe(
                    pd.DataFrame(duplicate_rows),
                    use_container_width=True,
                    hide_index=True,
                    height=320,
                )

        st.divider()


        # ============================================================
        # FASE 9.4 — CRITICIDAD OPERATIVA CONFIGURABLE
        # ============================================================
        st.subheader(
            "Criticidad operativa"
        )

        st.caption(
            "La criticidad no se infiere automáticamente. Debe ser definida "
            "por personal autorizado según el impacto real de la indisponibilidad "
            "del artículo sobre las actividades técnicas u operativas."
        )

        c1, c2, c3, c4 = st.columns(
            4
        )

        c1.metric(
            "Criticidad alta",
            criticality_summary.high,
        )
        c2.metric(
            "Criticidad media",
            criticality_summary.medium,
        )
        c3.metric(
            "Criticidad baja",
            criticality_summary.low,
        )
        c4.metric(
            "No definida",
            criticality_summary.undefined,
        )

        if criticality_summary.undefined:
            st.warning(
                f"{criticality_summary.undefined} artículo(s) todavía no tienen "
                "criticidad operativa definida. Hasta clasificarlos, la app conserva "
                "la prioridad cuantitativa de stock y marca la prioridad operativa "
                "como pendiente."
            )
        else:
            st.success(
                "Todos los artículos válidos tienen criticidad operativa definida."
            )

        catalog_df = pd.DataFrame(
            criticality.catalog_rows()
        )

        if user.get("role") == "administrador":
            with st.expander(
                "Administrar catálogo de criticidad"
            ):
                st.info(
                    "Clasifique únicamente con criterios institucionales autorizados. "
                    "La app no propone criticidad automáticamente."
                )

                admin_catalog_df = catalog_df.copy()

                # -----------------------------------------------------
                # Fase 9.4.1 — filtros prácticos del catálogo
                # -----------------------------------------------------
                f1, f2, f3, f4 = st.columns(
                    [1, 1, 1, 1.7]
                )

                brand_values = sorted(
                    [
                        value
                        for value in admin_catalog_df[
                            "Marca"
                        ].astype(str).unique().tolist()
                        if value.strip()
                    ]
                )

                selected_criticality_catalog = f1.selectbox(
                    "Criticidad",
                    [
                        "Todas",
                        "No definida",
                        "Alta",
                        "Media",
                        "Baja",
                    ],
                    index=0,
                    key="criticality_admin_filter_v2",
                )

                selected_brand_catalog = f2.selectbox(
                    "Marca",
                    ["Todas"] + brand_values,
                    index=0,
                    key="criticality_brand_filter",
                )

                pending_only = f3.checkbox(
                    "Solo pendientes",
                    value=False,
                    key="criticality_pending_only",
                    help=(
                        "Muestra únicamente registros cuya criticidad "
                        "todavía está como No definida."
                    ),
                )

                search_criticality = f4.text_input(
                    "Buscar",
                    placeholder=(
                        "Descripción, modelo, marca o número de ítem..."
                    ),
                    key="criticality_catalog_search",
                )

                filtered_catalog_df = (
                    admin_catalog_df.copy()
                )

                if selected_criticality_catalog != "Todas":
                    filtered_catalog_df = (
                        filtered_catalog_df[
                            filtered_catalog_df[
                                "Criticidad"
                            ]
                            == selected_criticality_catalog
                        ]
                    )

                if selected_brand_catalog != "Todas":
                    filtered_catalog_df = (
                        filtered_catalog_df[
                            filtered_catalog_df[
                                "Marca"
                            ]
                            == selected_brand_catalog
                        ]
                    )

                if pending_only:
                    filtered_catalog_df = (
                        filtered_catalog_df[
                            filtered_catalog_df[
                                "Criticidad"
                            ]
                            == "No definida"
                        ]
                    )

                if search_criticality.strip():
                    needle = (
                        search_criticality
                        .strip()
                        .lower()
                    )

                    searchable = (
                        filtered_catalog_df[
                            [
                                "Ítem",
                                "Descripción",
                                "Marca",
                                "Modelo",
                            ]
                        ]
                        .fillna("")
                        .astype(str)
                        .agg(" ".join, axis=1)
                        .str.lower()
                    )

                    filtered_catalog_df = (
                        filtered_catalog_df[
                            searchable.str.contains(
                                needle,
                                regex=False,
                            )
                        ]
                    )

                m1, m2, m3 = st.columns(3)

                m1.metric(
                    "Registros visibles",
                    len(filtered_catalog_df),
                )

                m2.metric(
                    "Pendientes visibles",
                    int(
                        (
                            filtered_catalog_df[
                                "Criticidad"
                            ]
                            == "No definida"
                        ).sum()
                    ),
                )

                m3.metric(
                    "Clasificados visibles",
                    int(
                        (
                            filtered_catalog_df[
                                "Criticidad"
                            ]
                            != "No definida"
                        ).sum()
                    ),
                )

                if filtered_catalog_df.empty:
                    st.warning(
                        "No hay registros que coincidan con los filtros seleccionados."
                    )
                else:
                    st.caption(
                        "Edite únicamente los registros visibles. Al guardar, "
                        "la aplicación conserva sin cambios los registros que no "
                        "están incluidos en la vista filtrada."
                    )

                    edited_catalog = st.data_editor(
                        filtered_catalog_df,
                        use_container_width=True,
                        hide_index=True,
                        height=430,
                        disabled=[
                            "record_key",
                            "Ítem",
                            "Descripción",
                            "Marca",
                            "Modelo",
                        ],
                        column_config={
                            "record_key": None,
                            "Criticidad": st.column_config.SelectboxColumn(
                                "Criticidad",
                                options=list(
                                    VALID_CRITICALITIES
                                ),
                                required=True,
                            ),
                            "Impacto operativo": st.column_config.TextColumn(
                                "Impacto operativo",
                                help=(
                                    "Describa brevemente qué proceso, capacidad "
                                    "o actividad se afecta por su indisponibilidad."
                                ),
                            ),
                            "Justificación": st.column_config.TextColumn(
                                "Justificación",
                                help=(
                                    "Fundamento para asignar la criticidad."
                                ),
                            ),
                        },
                        key="criticality_catalog_editor_filtered",
                    )

                    save_col, reset_col = st.columns(
                        [1, 4]
                    )

                    if save_col.button(
                        "Guardar criticidad visible",
                        key="save_criticality_catalog_filtered",
                        type="primary",
                    ):
                        full_rows = (
                            catalog_df.to_dict(
                                orient="records"
                            )
                        )

                        edited_rows = (
                            edited_catalog.to_dict(
                                orient="records"
                            )
                        )

                        edited_map = {
                            row["record_key"]: row
                            for row in edited_rows
                        }

                        merged_rows = []

                        for original_row in full_rows:
                            key = original_row[
                                "record_key"
                            ]

                            if key in edited_map:
                                merged_rows.append(
                                    edited_map[key]
                                )
                            else:
                                merged_rows.append(
                                    original_row
                                )

                        criticality.save_catalog(
                            merged_rows
                        )

                        st.success(
                            f"Se guardaron los cambios de "
                            f"{len(edited_rows)} registro(s) visible(s)."
                        )
                        st.rerun()

                    if reset_col.button(
                        "Limpiar filtros",
                        key="reset_criticality_filters",
                    ):
                        keys_to_clear = [
                            "criticality_admin_filter",
                            "criticality_brand_filter",
                            "criticality_pending_only",
                            "criticality_catalog_search",
                        ]

                        for key in keys_to_clear:
                            if key in st.session_state:
                                del st.session_state[key]

                        st.rerun()

        else:
            with st.expander(
                "Ver catálogo de criticidad"
            ):
                st.dataframe(
                    catalog_df.drop(
                        columns=["record_key"],
                        errors="ignore",
                    ),
                    use_container_width=True,
                    hide_index=True,
                    height=360,
                )

        st.divider()

        # ============================================================
        # FASE 9.3 — REPOSICIÓN Y ALERTAS OPERATIVAS
        # ============================================================
        st.subheader(
            "Gestión de reposición"
        )

        st.caption(
            "Política provisional del MVP: la cantidad registrada se usa "
            "como nivel objetivo de referencia. Solo se propone reposición "
            "cuando la cobertura de stock es de 50% o menos. La reposición "
            "sugerida se calcula como Cantidad - Stock."
        )

        r1, r2, r3, r4 = st.columns(
            4
        )

        r1.metric(
            "Sin stock",
            replenishment_summary["Sin stock"],
        )

        r2.metric(
            "Críticos",
            replenishment_summary["Crítico"],
        )

        r3.metric(
            "Stock bajo",
            replenishment_summary["Bajo"],
        )

        r4.metric(
            "Adecuados",
            replenishment_summary["Adecuado"],
        )

        r5, r6 = st.columns(
            2
        )

        r5.metric(
            "Artículos a reponer",
            replenishment_summary[
                "Artículos a reponer"
            ],
        )

        r6.metric(
            "Unidades sugeridas",
            replenishment_summary[
                "Unidades sugeridas"
            ],
        )

        st.info(
            "Criterio provisional: Sin stock = urgente; "
            "cobertura ≤25% = prioridad alta; "
            "cobertura >25% y ≤50% = prioridad media; "
            "cobertura >50% = adecuada."
        )

        proposal_rows = criticality.enrich_rows(
            replenishment.proposal_rows(
                include_medium=True
            )
        )

        operational_matrix = OperationalPriorityMatrix(proposal_rows)
        proposal_rows = operational_matrix.enrich_rows()
        operational_summary = operational_matrix.summary()

        st.subheader("Matriz de prioridad operativa")
        st.caption("Combina la criticidad definida por personal autorizado con la prioridad cuantitativa de stock. Es una ayuda para ordenar la atención y no constituye una orden de compra.")
        p1,p2,p3,p4,p5,p6=st.columns(6)
        p1.metric("Crítica",operational_summary.critical); p2.metric("Muy alta",operational_summary.very_high); p3.metric("Alta",operational_summary.high); p4.metric("Media",operational_summary.medium); p5.metric("Baja",operational_summary.low); p6.metric("Pendiente",operational_summary.pending)
        st.info("Matriz provisional del MVP: Alta+Urgente=Crítica; Alta+Alta=Muy alta; Media+Urgente=Muy alta; Baja+Urgente=Alta. Sin criticidad definida = Pendiente.")
        ranked_rows = operational_matrix.actionable_rows(False)
        ranked_rows = decision_store.enrich_rows(
            ranked_rows
        )

        decision_summary = decision_store.summary(
            ranked_rows
        )

        st.markdown(
            "#### Seguimiento de decisiones de reposición"
        )

        ds1, ds2, ds3, ds4, ds5 = st.columns(5)

        ds1.metric(
            "Pendientes",
            decision_summary.get(
                "Pendiente",
                0,
            ),
        )
        ds2.metric(
            "En revisión",
            decision_summary.get(
                "En revisión",
                0,
            ),
        )
        ds3.metric(
            "Aprobados",
            decision_summary.get(
                "Aprobado",
                0,
            ),
        )
        ds4.metric(
            "No aprobados",
            decision_summary.get(
                "No aprobado",
                0,
            ),
        )
        ds5.metric(
            "Gestionados",
            decision_summary.get(
                "Gestionado",
                0,
            ),
        )

        st.markdown("#### Panel de priorización operativa")

        if ranked_rows:
            ranked_df = pd.DataFrame(ranked_rows)

            ranking_columns = [
                "Ítem",
                "Descripción",
                "Marca",
                "Modelo",
                "Cantidad",
                "Stock",
                "Cobertura stock %",
                "Estado reposición",
                "Prioridad stock",
                "Criticidad",
                "Prioridad operativa",
                "Puntaje prioridad",
                "Reposición sugerida",
                "Impacto operativo",
                "Justificación criticidad",
                "Justificación prioridad",
                "Estado gestión",
                "Responsable",
                "Observación decisión",
                "Última actualización",
            ]
            ranking_columns = [
                c for c in ranking_columns
                if c in ranked_df.columns
            ]

            rf1, rf2, rf3, rf4, rf5, rf6 = st.columns(
                [1, 1, 1, 1, 1, 1.5]
            )

            selected_op = rf1.selectbox(
                "Prioridad operativa",
                [
                    "Todas",
                    "Crítica",
                    "Muy alta",
                    "Alta",
                    "Media",
                    "Baja",
                ],
                index=0,
                key="phase96_priority_filter",
            )

            selected_crit = rf2.selectbox(
                "Criticidad",
                [
                    "Todas",
                    "Alta",
                    "Media",
                    "Baja",
                ],
                index=0,
                key="phase96_criticality_filter",
            )

            replenishment_values = [
                x for x in sorted(
                    ranked_df["Estado reposición"]
                    .fillna("")
                    .astype(str)
                    .unique()
                    .tolist()
                )
                if x.strip()
            ]

            selected_repl = rf3.selectbox(
                "Estado reposición",
                ["Todos"] + replenishment_values,
                index=0,
                key="phase96_replenishment_filter",
            )

            brand_values = [
                x for x in sorted(
                    ranked_df["Marca"]
                    .fillna("")
                    .astype(str)
                    .unique()
                    .tolist()
                )
                if x.strip()
            ]

            selected_brand = rf4.selectbox(
                "Marca",
                ["Todas"] + brand_values,
                index=0,
                key="phase96_brand_filter",
            )

            selected_management = rf5.selectbox(
                "Estado gestión",
                ["Todos"] + VALID_MANAGEMENT_STATUS,
                index=0,
                key="phase97_management_filter",
            )

            search_rank = rf6.text_input(
                "Buscar",
                placeholder="Ítem, descripción, modelo o marca...",
                key="phase96_search_filter",
            )

            filtered_rank = ranked_df.copy()

            if selected_op != "Todas":
                filtered_rank = filtered_rank[
                    filtered_rank["Prioridad operativa"]
                    == selected_op
                ]

            if selected_crit != "Todas":
                filtered_rank = filtered_rank[
                    filtered_rank["Criticidad"]
                    == selected_crit
                ]

            if selected_repl != "Todos":
                filtered_rank = filtered_rank[
                    filtered_rank["Estado reposición"]
                    == selected_repl
                ]

            if selected_brand != "Todas":
                filtered_rank = filtered_rank[
                    filtered_rank["Marca"]
                    == selected_brand
                ]

            if selected_management != "Todos":
                filtered_rank = filtered_rank[
                    filtered_rank["Estado gestión"]
                    == selected_management
                ]

            if search_rank.strip():
                needle = search_rank.strip().lower()
                search_cols = [
                    c for c in [
                        "Ítem",
                        "Descripción",
                        "Marca",
                        "Modelo",
                    ]
                    if c in filtered_rank.columns
                ]
                searchable = (
                    filtered_rank[search_cols]
                    .fillna("")
                    .astype(str)
                    .agg(" ".join, axis=1)
                    .str.lower()
                )
                filtered_rank = filtered_rank[
                    searchable.str.contains(
                        needle,
                        regex=False,
                    )
                ]

            rm1, rm2, rm3, rm4 = st.columns(4)

            rm1.metric(
                "Registros filtrados",
                len(filtered_rank),
            )
            rm2.metric(
                "Críticos",
                int(
                    (
                        filtered_rank["Prioridad operativa"]
                        == "Crítica"
                    ).sum()
                ),
            )
            rm3.metric(
                "Muy alta",
                int(
                    (
                        filtered_rank["Prioridad operativa"]
                        == "Muy alta"
                    ).sum()
                ),
            )
            rm4.metric(
                "Unidades sugeridas",
                int(
                    pd.to_numeric(
                        filtered_rank["Reposición sugerida"],
                        errors="coerce",
                    )
                    .fillna(0)
                    .sum()
                ),
            )

            if not filtered_rank.empty:
                chart_data = (
                    filtered_rank["Prioridad operativa"]
                    .value_counts()
                    .reindex(
                        [
                            "Crítica",
                            "Muy alta",
                            "Alta",
                            "Media",
                            "Baja",
                        ],
                        fill_value=0,
                    )
                    .rename_axis("Prioridad")
                    .reset_index(name="Registros")
                )

                st.markdown(
                    "##### Distribución de la vista filtrada"
                )
                st.bar_chart(
                    chart_data,
                    x="Prioridad",
                    y="Registros",
                    use_container_width=True,
                )

                filtered_rank = filtered_rank.sort_values(
                    by=[
                        "Puntaje prioridad",
                        "Reposición sugerida",
                    ],
                    ascending=[
                        False,
                        False,
                    ],
                )

                st.markdown("##### Ranking consolidado")
                st.dataframe(
                    filtered_rank[ranking_columns],
                    use_container_width=True,
                    hide_index=True,
                    height=380,
                )

                st.download_button(
                    "Descargar vista priorizada CSV",
                    data=(
                        filtered_rank[ranking_columns]
                        .to_csv(index=False)
                        .encode("utf-8-sig")
                    ),
                    file_name=(
                        "panel_priorizacion_operativa_filtrado.csv"
                    ),
                    mime="text/csv",
                    key="download_operational_ranking_filtered",
                )


                st.markdown(
                    "##### Seguimiento de decisiones"
                )

                st.caption(
                    "Edite únicamente los registros visibles. "
                    "Los demás registros conservan su estado actual."
                )

                editable_columns = [
                    c
                    for c in [
                        "Ítem",
                        "Descripción",
                        "Marca",
                        "Modelo",
                        "Prioridad operativa",
                        "Estado gestión",
                        "Responsable",
                        "Observación decisión",
                        "Última actualización",
                    ]
                    if c in filtered_rank.columns
                ]

                editor_df = filtered_rank[
                    editable_columns
                ].copy()

                edited_decisions = st.data_editor(
                    editor_df,
                    use_container_width=True,
                    hide_index=True,
                    num_rows="fixed",
                    disabled=[
                        c
                        for c in [
                            "Ítem",
                            "Descripción",
                            "Marca",
                            "Modelo",
                            "Prioridad operativa",
                            "Última actualización",
                        ]
                        if c in editor_df.columns
                    ],
                    column_config={
                        "Estado gestión": st.column_config.SelectboxColumn(
                            "Estado gestión",
                            options=VALID_MANAGEMENT_STATUS,
                            required=True,
                        ),
                        "Responsable": st.column_config.TextColumn(
                            "Responsable",
                        ),
                        "Observación decisión": st.column_config.TextColumn(
                            "Observación decisión",
                        ),
                    },
                    key="phase97_decision_editor",
                )

                if st.button(
                    "Guardar seguimiento visible",
                    key="phase97_save_decisions",
                    type="primary",
                ):
                    changed = decision_store.upsert_many(
                        edited_decisions.to_dict(
                            orient="records"
                        )
                    )

                    st.success(
                        f"Seguimiento guardado. "
                        f"Registros actualizados: {changed}."
                    )
                    st.rerun()
            else:
                st.warning(
                    "No hay registros que coincidan con los filtros seleccionados."
                )
        else:
            st.warning(
                "Aún no hay artículos clasificados que permitan construir un ranking operativo."
            )

        st.divider()

        st.markdown(
            "#### Propuesta de reposición"
        )

        st.caption(
            "Las unidades sugeridas son una recomendación provisional para "
            "recuperar el nivel objetivo definido por la cantidad registrada. "
            "No constituyen una orden de compra. La prioridad operativa solo "
            "se calcula cuando existe una criticidad institucional definida."
        )

        if proposal_rows:
            proposal_df = pd.DataFrame(
                proposal_rows
            )

            f1, f2, f3, f4, f5, f6 = st.columns(
                [1, 1, 1, 1, 1, 1.4]
            )

            selected_priority = f1.selectbox(
                "Prioridad",
                [
                    "Todas",
                    "Urgente",
                    "Alta",
                    "Media",
                ],
                index=0,
                key="replenishment_priority_filter",
            )

            selected_status = f2.selectbox(
                "Estado de reposición",
                [
                    "Todos",
                    "Sin stock",
                    "Crítico",
                    "Bajo",
                ],
                index=0,
                key="replenishment_status_filter",
            )

            brands = sorted(
                [
                    brand
                    for brand in proposal_df[
                        "Marca"
                    ].dropna().astype(str).unique().tolist()
                    if brand.strip()
                ]
            )

            selected_brand = f3.selectbox(
                "Marca",
                ["Todas"] + brands,
                index=0,
                key="replenishment_brand_filter",
            )

            selected_criticality = f4.selectbox(
                "Criticidad",
                [
                    "Todas",
                    "Alta",
                    "Media",
                    "Baja",
                    "No definida",
                ],
                index=0,
                key="replenishment_criticality_filter",
            )

            selected_operational_priority = f5.selectbox(
                "Prioridad operativa",
                ["Todas","Crítica","Muy alta","Alta","Media","Baja","Normal","Pendiente de criticidad"],
                index=0,
                key="replenishment_operational_priority_filter",
            )

            search_replenishment = f6.text_input(
                "Buscar en propuesta",
                placeholder=(
                    "Descripción, modelo o número de ítem..."
                ),
                key="replenishment_search",
            )

            filtered_proposal_df = proposal_df.copy()

            if selected_priority != "Todas":
                filtered_proposal_df = filtered_proposal_df[
                    filtered_proposal_df[
                        "Prioridad"
                    ] == selected_priority
                ]

            if selected_status != "Todos":
                filtered_proposal_df = filtered_proposal_df[
                    filtered_proposal_df[
                        "Estado reposición"
                    ] == selected_status
                ]

            if selected_brand != "Todas":
                filtered_proposal_df = filtered_proposal_df[
                    filtered_proposal_df[
                        "Marca"
                    ] == selected_brand
                ]

            if selected_criticality != "Todas":
                filtered_proposal_df = filtered_proposal_df[
                    filtered_proposal_df["Criticidad"] == selected_criticality
                ]

            if selected_operational_priority != "Todas":
                filtered_proposal_df = filtered_proposal_df[
                    filtered_proposal_df["Prioridad operativa"] == selected_operational_priority
                ]

            if search_replenishment.strip():
                needle = search_replenishment.strip().lower()
                searchable_columns = [
                    column
                    for column in [
                        "Ítem",
                        "Descripción",
                        "Modelo",
                        "Marca",
                    ]
                    if column in filtered_proposal_df.columns
                ]

                mask = pd.Series(
                    False,
                    index=filtered_proposal_df.index,
                )

                for column in searchable_columns:
                    mask = mask | (
                        filtered_proposal_df[
                            column
                        ]
                        .astype(str)
                        .str.lower()
                        .str.contains(
                            needle,
                            na=False,
                            regex=False,
                        )
                    )

                filtered_proposal_df = (
                    filtered_proposal_df[
                        mask
                    ]
                )

            preferred_columns = [
                "Ítem",
                "Descripción",
                "Marca",
                "Modelo",
                "Cantidad",
                "Stock",
                "Cobertura stock %",
                "Estado reposición",
                "Prioridad stock",
                "Criticidad",
                "Prioridad operativa",
                "Puntaje prioridad",
                "Reposición sugerida",
                "Justificación prioridad",
                "Impacto operativo",
                "Justificación criticidad",
                "Calidad",
                "Nivel calidad",
            ]

            available_columns = [
                column
                for column in preferred_columns
                if column in filtered_proposal_df.columns
            ]

            filtered_units = 0
            if (
                not filtered_proposal_df.empty
                and "Reposición sugerida"
                in filtered_proposal_df.columns
            ):
                filtered_units = (
                    pd.to_numeric(
                        filtered_proposal_df[
                            "Reposición sugerida"
                        ],
                        errors="coerce",
                    )
                    .fillna(0)
                    .sum()
                )

            m1, m2 = st.columns(
                2
            )

            m1.metric(
                "Registros filtrados",
                len(filtered_proposal_df),
            )

            m2.metric(
                "Unidades sugeridas filtradas",
                int(filtered_units),
            )

            if not filtered_proposal_df.empty:
                st.dataframe(
                    filtered_proposal_df[
                        available_columns
                    ],
                    use_container_width=True,
                    hide_index=True,
                    height=420,
                )

                export_scope = st.selectbox(
                    "Exportar",
                    [
                        "Vista filtrada",
                        "Toda la propuesta",
                        "Solo urgentes",
                        "Prioridad alta",
                        "Prioridad media",
                    ],
                    index=0,
                    key="replenishment_export_scope",
                )

                if export_scope == "Vista filtrada":
                    export_df = filtered_proposal_df[
                        available_columns
                    ].copy()
                    export_name = (
                        "propuesta_reposicion_filtrada.csv"
                    )
                elif export_scope == "Toda la propuesta":
                    export_df = proposal_df[
                        available_columns
                    ].copy()
                    export_name = (
                        "propuesta_reposicion_completa.csv"
                    )
                elif export_scope == "Solo urgentes":
                    export_df = proposal_df[
                        proposal_df[
                            "Prioridad"
                        ] == "Urgente"
                    ][available_columns].copy()
                    export_name = (
                        "propuesta_reposicion_urgente.csv"
                    )
                elif export_scope == "Prioridad alta":
                    export_df = proposal_df[
                        proposal_df[
                            "Prioridad"
                        ] == "Alta"
                    ][available_columns].copy()
                    export_name = (
                        "propuesta_reposicion_alta.csv"
                    )
                else:
                    export_df = proposal_df[
                        proposal_df[
                            "Prioridad"
                        ] == "Media"
                    ][available_columns].copy()
                    export_name = (
                        "propuesta_reposicion_media.csv"
                    )

                st.download_button(
                    "Descargar propuesta de reposición CSV",
                    data=export_df.to_csv(
                        index=False
                    ).encode(
                        "utf-8-sig"
                    ),
                    file_name=export_name,
                    mime="text/csv",
                    key=(
                        "download_replenishment_proposal"
                    ),
                )
            else:
                st.warning(
                    "No existen registros que coincidan "
                    "con los filtros seleccionados."
                )

        else:
            st.success(
                "No existen artículos que cumplan los "
                "criterios provisionales de reposición."
            )

        dist_left, dist_right = st.columns(
            2
        )

        with dist_left:
            st.markdown(
                "#### Estados de reposición"
            )

            status_df = pd.DataFrame(
                replenishment.status_distribution()
            )

            if not status_df.empty:
                st.bar_chart(
                    status_df.set_index(
                        "Estado"
                    )[
                        "Registros"
                    ],
                    use_container_width=True,
                )

        with dist_right:
            st.markdown(
                "#### Prioridad operativa"
            )

            priority_df = pd.DataFrame(
                replenishment.priority_distribution()
            )

            if not priority_df.empty:
                st.bar_chart(
                    priority_df.set_index(
                        "Prioridad"
                    )[
                        "Registros"
                    ],
                    use_container_width=True,
                )

        st.divider()

        st.subheader(
            "Análisis por marca"
        )

        stock_brand_df = pd.DataFrame(
            inventory.stock_by_brand()
        )

        count_brand_df = pd.DataFrame(
            inventory.records_by_brand()
        )

        if not stock_brand_df.empty:
            st.markdown(
                "#### Stock total por marca"
            )

            st.bar_chart(
                stock_brand_df.set_index(
                    "Marca"
                )[
                    "Stock total"
                ],
                use_container_width=True,
            )

        if not count_brand_df.empty:
            st.markdown(
                "#### Registros por marca"
            )

            st.bar_chart(
                count_brand_df.set_index(
                    "Marca"
                )[
                    "Registros"
                ],
                use_container_width=True,
            )

        st.divider()

        low_col, high_col = st.columns(
            2
        )

        with low_col:
            st.subheader(
                "10 con menor stock"
            )

            st.dataframe(
                pd.DataFrame(
                    inventory.top_low_stock(
                        10
                    )
                ),
                use_container_width=True,
                hide_index=True,
                height=360,
            )

        with high_col:
            st.subheader(
                "10 con mayor stock"
            )

            st.dataframe(
                pd.DataFrame(
                    inventory.top_high_stock(
                        10
                    )
                ),
                use_container_width=True,
                hide_index=True,
                height=360,
            )

    except Exception as exc:
        st.error(
            "No fue posible construir el dashboard "
            "de inventario."
        )

        with st.expander(
            "Detalle técnico"
        ):
            st.exception(
                exc
            )


# ================================================================
# CONSULTA
# ================================================================
with tab_map["Consulta"]:

    examples = [
        (
            "¿Qué componentes principales integra la arquitectura "
            "del Simulador Táctico Submarino?"
        ),
        (
            "¿Cuántas impresoras 3D Creality K1 están disponibles?"
        ),
        (
            "¿Qué componentes del inventario pueden utilizarse "
            "para procesamiento de IA?"
        ),
        (
            "¿Qué documentos se encuentran vigentes?"
        ),
        (
            "¿Qué información consta en el documento Bienes DINDES "
            "para el bien código 2341766?"
        ),
    ]

    st.selectbox(
        "Ejemplos",
        options=[""] + examples,
        format_func=lambda x: (
            "Seleccione un ejemplo..."
            if not x
            else x
        ),
        key="example_selector",
        on_change=load_selected_example,
    )

    question = st.text_area(
        "Escriba su pregunta",
        key="question_input",
        height=110,
        placeholder="Escriba aquí una nueva consulta...",
    )

    col_a, col_b = st.columns(
        2
    )

    with col_a:
        ask_clicked = st.button(
            "Consultar",
            type="primary",
            use_container_width=True,
            disabled=(
                not pipeline_ready
                or not permissions[
                    "can_query"
                ]
            ),
        )

    with col_b:
        st.button(
            "Limpiar",
            use_container_width=True,
            on_click=clear_query_state,
        )

    if ask_clicked:

        if not question.strip():
            st.session_state.last_response = None
            st.session_state.last_question = ""
            reset_feedback_state()

            st.warning(
                "Ingrese una pregunta."
            )

        else:
            reset_feedback_state()

            st.session_state.last_question = (
                question.strip()
            )

            try:
                with AuditTimer() as timer:
                    with st.spinner(
                        "Recuperando evidencia y generando respuesta..."
                    ):
                        response = rag.ask(
                            question.strip()
                        )

                st.session_state.last_response = (
                    response
                )

                source_ids = [
                    canonical_source_id(
                        source
                    )
                    for source in response.sources
                ]

                exact_matches = []

                for source in response.sources:
                    exact_matches.extend(
                        exact_match_values(
                            source
                        )
                    )

                exact_matches = list(
                    dict.fromkeys(
                        exact_matches
                    )
                )

                st.session_state.query_history.insert(
                    0,
                    {
                        "timestamp": datetime.now().isoformat(
                            timespec="seconds"
                        ),
                        "question": response.question,
                        "answer": response.answer,
                        "abstained": response.abstained,
                        "abstention_stage": getattr(
                            response,
                            "abstention_stage",
                            None,
                        ),
                        "exact_matches": ";".join(
                            exact_matches
                        ),
                        "source_ids": ";".join(
                            source_ids
                        ),
                        "response_mode": getattr(
                            response,
                            "response_mode",
                            "rag",
                        ),
                        "structured_result_count": len(
                            getattr(
                                response,
                                "structured_rows",
                                [],
                            )
                        ),
                        "duration_seconds": round(
                            timer.elapsed,
                            4,
                        ),
                    },
                )

                detail_parts = [
                    (
                        "abstention_stage="
                        f"{getattr(response, 'abstention_stage', None)}"
                    ),
                    (
                        "response_mode="
                        f"{getattr(response, 'response_mode', 'rag')}"
                    ),
                ]

                if exact_matches:
                    detail_parts.append(
                        "exact_match="
                        + ";".join(
                            exact_matches
                        )
                    )

                write_audit_event(
                    AUDIT_PATH,
                    event="query",
                    username=user["username"],
                    role=user["role"],
                    question=response.question,
                    abstained=response.abstained,
                    retrieval_count=response.retrieval_count,
                    source_ids=source_ids,
                    duration_seconds=timer.elapsed,
                    detail=" | ".join(
                        detail_parts
                    ),
                )

            except Exception as exc:
                write_audit_event(
                    AUDIT_PATH,
                    event="query_error",
                    username=user["username"],
                    role=user["role"],
                    question=question.strip(),
                    detail=str(exc),
                )

                st.error(
                    "Error durante la consulta."
                )

                with st.expander(
                    "Detalle técnico"
                ):
                    st.exception(exc)

    response = (
        st.session_state.last_response
    )

    if response is not None:

        st.divider()
        st.subheader(
            "Respuesta"
        )

        response_mode = getattr(
            response,
            "response_mode",
            "rag",
        )

        if response_mode == "structured":
            st.success(
                "Modo de respuesta: **Estructurado** — "
                "resultado obtenido mediante filtros determinísticos "
                "sobre registros tabulares."
            )
        else:
            st.info(
                "Modo de respuesta: **RAG** — "
                "resultado generado a partir de recuperación semántica "
                "y evidencia documental."
            )

        if response.abstained:
            st.warning(
                response.answer
            )

            stage = getattr(
                response,
                "abstention_stage",
                None,
            )

            if stage == "retrieval":
                st.info(
                    "La abstención ocurrió en la etapa de retrieval: "
                    "no se recuperaron fuentes con evidencia suficiente "
                    "para responder."
                )

            elif stage == "generation":
                st.info(
                    "Se recuperaron fuentes candidatas, pero el modelo "
                    "determinó que no contenían evidencia suficiente "
                    "para responder de forma sustentada."
                )

        else:
            st.markdown(
                response.answer
            )

        exact_matches_summary = []

        for source in response.sources:
            exact_matches_summary.extend(
                exact_match_values(
                    source
                )
            )

        exact_matches_summary = list(
            dict.fromkeys(
                exact_matches_summary
            )
        )

        if exact_matches_summary:
            st.success(
                "Coincidencia exacta detectada en las fuentes: "
                + ", ".join(
                    f"`{item}`"
                    for item in exact_matches_summary
                )
            )

        m1, m2, m3 = st.columns(
            3
        )

        m1.metric(
            "Abstención",
            get_abstention_label(
                response
            ),
        )

        m2.metric(
            "Fuentes",
            response.retrieval_count,
        )

        m3.metric(
            "Umbral",
            f"{dense_threshold:.2f}",
        )

        structured_rows = getattr(
            response,
            "structured_rows",
            [],
        )

        if (
            response_mode == "structured"
            and structured_rows
        ):
            st.subheader(
                "Resultados estructurados"
            )

            structured_df = pd.DataFrame(
                structured_rows
            )

            st.dataframe(
                structured_df,
                use_container_width=True,
                hide_index=True,
            )

            csv_bytes = structured_df.to_csv(
                index=False
            ).encode(
                "utf-8-sig"
            )

            st.download_button(
                "Descargar resultados CSV",
                data=csv_bytes,
                file_name="consulta_estructurada_dindes.csv",
                mime="text/csv",
            )

            st.caption(
                f"Registros encontrados: {len(structured_rows)}. "
                "Los valores mostrados provienen directamente "
                "de los registros estructurados."
            )

        if (
            response.sources
            and permissions[
                "can_view_sources"
            ]
        ):
            st.subheader(
                "Fuentes y evidencias"
            )

            if response_mode == "structured":
                # En modo estructurado no tiene sentido mostrar 17, 50 o más
                # expanders idénticos. Se agrupa la procedencia documental.
                grouped_sources = {}

                for source in response.sources:
                    document_id = str(
                        source.metadata.get(
                            "document_id",
                            canonical_source_id(
                                source
                            ),
                        )
                    )

                    key = (
                        document_id,
                        source.title,
                        source.source_file,
                    )

                    grouped_sources.setdefault(
                        key,
                        {
                            "document_id": document_id,
                            "title": source.title,
                            "source_file": source.source_file,
                            "count": 0,
                        },
                    )

                    grouped_sources[
                        key
                    ][
                        "count"
                    ] += 1

                for idx, info in enumerate(
                    grouped_sources.values(),
                    start=1,
                ):
                    label = (
                        f"Fuente {idx} — "
                        f"{info['document_id']} — "
                        f"{info['title']}"
                    )

                    with st.expander(
                        label,
                        expanded=(
                            idx == 1
                        ),
                    ):
                        st.write(
                            f"**Documento:** "
                            f"{info['document_id']}"
                        )

                        if info[
                            "source_file"
                        ]:
                            st.write(
                                f"**Archivo:** "
                                f"{info['source_file']}"
                            )

                        st.write(
                            "**Registros utilizados en la consulta:** "
                            f"{info['count']}"
                        )

                        st.caption(
                            "Los valores de la tabla anterior "
                            "provienen directamente de los registros "
                            "estructurados de esta fuente."
                        )

            else:
                for idx, source in enumerate(
                    response.sources,
                    start=1,
                ):

                    source_id = (
                        canonical_source_id(
                            source
                        )
                    )

                    matches = (
                        exact_match_values(
                            source
                        )
                    )

                    exact_badge = (
                        " 🎯"
                        if matches
                        else ""
                    )

                    label = (
                        f"F{idx} — "
                        f"{source_id} — "
                        f"{source.title}"
                        f"{exact_badge}"
                    )

                    with st.expander(
                        label,
                        expanded=(
                            idx == 1
                        ),
                    ):
                        meta1, meta2, meta3 = st.columns(
                            3
                        )

                        meta1.write(
                            f"**Tipo:** {source.source_type}"
                        )

                        meta2.write(
                            f"**Score:** {source.score:.4f}"
                        )

                        if matches:
                            meta3.success(
                                "🎯 Coincidencia exacta"
                            )
                        else:
                            meta3.caption(
                                "Coincidencia semántica"
                            )

                        metadata = (
                            source.metadata
                            or {}
                        )

                        document_id = metadata.get(
                            "document_id",
                            "",
                        )

                        section = metadata.get(
                            "section",
                            "",
                        )

                        chunk_index = metadata.get(
                            "chunk_index",
                            "",
                        )

                        version = metadata.get(
                            "version",
                            "",
                        )

                        source_status = metadata.get(
                            "source_status",
                            "",
                        )

                        document_date = metadata.get(
                            "document_date",
                            "",
                        )

                        info_cols = st.columns(
                            3
                        )

                        if document_id:
                            info_cols[0].write(
                                f"**Documento:** {document_id}"
                            )

                        if section:
                            info_cols[1].write(
                                f"**Sección:** {section}"
                            )

                        if chunk_index not in (
                            "",
                            None,
                        ):
                            info_cols[2].write(
                                f"**Chunk:** {chunk_index}"
                            )

                        info_cols2 = st.columns(
                            3
                        )

                        if version:
                            info_cols2[0].write(
                                f"**Versión:** {version}"
                            )

                        if source_status:
                            info_cols2[1].write(
                                f"**Estado:** {source_status}"
                            )

                        if document_date:
                            info_cols2[2].write(
                                f"**Fecha:** {document_date}"
                            )

                        if matches:
                            st.success(
                                "Coincidencia exacta detectada: "
                                + ", ".join(
                                    f"`{item}`"
                                    for item in matches
                                )
                            )

                        st.divider()

                        st.markdown(
                            "### Fragmento recuperado"
                        )

                        st.markdown(
                            format_evidence_text(
                                source.text
                            )
                        )

                        with st.expander(
                            "Ver texto original del chunk"
                        ):
                            st.code(
                                source.text
                            )

        if permissions[
            "can_submit_feedback"
        ]:
            st.subheader(
                "Evaluación"
            )

            feedback_choice = st.radio(
                "¿La respuesta fue útil y correcta?",
                options=[
                    "Sin evaluar",
                    "Correcta / útil",
                    "Incorrecta / incompleta",
                ],
                horizontal=True,
                key="feedback_choice",
            )

            feedback_comment = st.text_area(
                "Comentario opcional",
                key="feedback_comment",
            )

            if st.button(
                "Registrar evaluación",
                disabled=(
                    st.session_state.feedback_saved
                ),
            ):

                if (
                    feedback_choice
                    == "Sin evaluar"
                ):
                    st.warning(
                        "Seleccione una opción."
                    )

                else:
                    source_ids = [
                        canonical_source_id(
                            source
                        )
                        for source in response.sources
                    ]

                    save_feedback(
                        question=response.question,
                        answer=response.answer,
                        feedback_type=feedback_choice,
                        comment=feedback_comment,
                        source_ids=source_ids,
                    )

                    write_audit_event(
                        AUDIT_PATH,
                        event="feedback",
                        username=user["username"],
                        role=user["role"],
                        question=response.question,
                        source_ids=source_ids,
                        detail=feedback_choice,
                    )

                    st.session_state.feedback_saved = (
                        True
                    )

                    st.success(
                        "Evaluación registrada."
                    )


# ================================================================
# HISTORIAL
# ================================================================
if "Historial" in tab_map:

    with tab_map["Historial"]:

        st.subheader(
            "Historial de la sesión"
        )

        history = (
            st.session_state.query_history
        )

        if not history:
            st.info(
                "Aún no hay consultas "
                "en esta sesión."
            )
        else:
            st.dataframe(
                pd.DataFrame(
                    history
                ),
                use_container_width=True,
                hide_index=True,
            )


decision_audit_store_global = ReplenishmentDecisionAuditStore(
    REPLENISHMENT_DECISIONS_AUDIT_PATH
)


# ================================================================
# AUDITORÍA
# ================================================================
if "Auditoría" in tab_map:

    with tab_map["Auditoría"]:

        st.subheader(
            "Auditoría"
        )

        if not AUDIT_PATH.exists():
            st.info(
                "Aún no existen registros."
            )
        else:
            try:
                audit_df = pd.read_csv(
                    AUDIT_PATH
                )

                st.dataframe(
                    audit_df.sort_values(
                        "timestamp",
                        ascending=False,
                    ),
                    use_container_width=True,
                    hide_index=True,
                )

            except Exception as exc:
                st.error(
                    "No fue posible leer el log."
                )
                st.exception(
                    exc
                )



        st.divider()

        st.subheader(
            "Auditoría institucional de decisiones de reposición"
        )

        st.caption(
            "Trazabilidad avanzada de cambios de estado. "
            "Permite revisar cuándo cambió una decisión, "
            "quién fue registrado como responsable y cuál fue la transición."
        )

        decision_events = (
            decision_audit_store_global.load()
        )

        if not decision_events:
            st.info(
                "Todavía no hay eventos de decisión registrados. "
                "La bitácora comenzará con el próximo cambio de estado guardado."
            )
        else:
            audit_analytics = (
                ReplenishmentDecisionAuditStore
            )

            decision_audit_df = pd.DataFrame(
                decision_events
            )

            parsed_dates = pd.to_datetime(
                decision_audit_df[
                    "timestamp"
                ],
                errors="coerce",
            )

            valid_dates = parsed_dates.dropna()

            if valid_dates.empty:
                default_start = datetime.now().date()
                default_end = default_start
            else:
                default_start = (
                    valid_dates.min().date()
                )
                default_end = (
                    valid_dates.max().date()
                )

            transition_options = [
                "Todas"
            ] + sorted(
                {
                    transition_label(row)
                    for row in decision_events
                    if transition_label(row)
                }
            )

            status_options = [
                "Todos"
            ] + sorted(
                {
                    str(
                        row.get(
                            "new_status",
                            "",
                        )
                    ).strip()
                    for row in decision_events
                    if str(
                        row.get(
                            "new_status",
                            "",
                        )
                    ).strip()
                }
            )

            responsible_options = [
                "Todos"
            ] + sorted(
                {
                    str(
                        row.get(
                            "responsible",
                            "",
                        )
                    ).strip()
                    for row in decision_events
                    if str(
                        row.get(
                            "responsible",
                            "",
                        )
                    ).strip()
                }
            )

            brand_options = [
                "Todas"
            ] + sorted(
                {
                    str(
                        row.get(
                            "brand",
                            "",
                        )
                    ).strip()
                    for row in decision_events
                    if str(
                        row.get(
                            "brand",
                            "",
                        )
                    ).strip()
                }
            )

            st.markdown(
                "#### Filtros de auditoría"
            )

            df1, df2, df3 = st.columns(
                [1, 1, 1]
            )

            audit_start_date = df1.date_input(
                "Fecha inicial",
                value=default_start,
                key="phase99_start_date",
            )

            audit_end_date = df2.date_input(
                "Fecha final",
                value=default_end,
                key="phase99_end_date",
            )

            audit_transition_filter = (
                df3.selectbox(
                    "Transición",
                    transition_options,
                    key=(
                        "phase99_transition_filter"
                    ),
                )
            )

            ff1, ff2, ff3, ff4 = st.columns(
                [1, 1, 1, 1.4]
            )

            audit_status_filter = ff1.selectbox(
                "Estado nuevo",
                status_options,
                key="phase99_status_filter",
            )

            audit_responsible_filter = (
                ff2.selectbox(
                    "Responsable",
                    responsible_options,
                    key=(
                        "phase99_responsible_filter"
                    ),
                )
            )

            audit_brand_filter = ff3.selectbox(
                "Marca",
                brand_options,
                key="phase99_brand_filter",
            )

            audit_search_filter = ff4.text_input(
                "Buscar en auditoría",
                placeholder=(
                    "Ítem, descripción, modelo, responsable u observación..."
                ),
                key="phase99_search_filter",
            )

            item_filter_col, reset_col = (
                st.columns(
                    [3, 1]
                )
            )

            audit_item_filter = (
                item_filter_col.text_input(
                    "Ítem exacto",
                    placeholder="Ej. 4",
                    key="phase99_item_filter",
                )
            )

            if reset_col.button(
                "Limpiar filtros de auditoría",
                key="phase99_clear_filters",
                use_container_width=True,
            ):
                st.session_state[
                    "phase99_transition_filter"
                ] = "Todas"
                st.session_state[
                    "phase99_status_filter"
                ] = "Todos"
                st.session_state[
                    "phase99_responsible_filter"
                ] = "Todos"
                st.session_state[
                    "phase99_brand_filter"
                ] = "Todas"
                st.session_state[
                    "phase99_search_filter"
                ] = ""
                st.session_state[
                    "phase99_item_filter"
                ] = ""
                st.session_state[
                    "phase99_start_date"
                ] = default_start
                st.session_state[
                    "phase99_end_date"
                ] = default_end
                st.rerun()

            if audit_start_date > audit_end_date:
                st.error(
                    "La fecha inicial no puede ser posterior a la fecha final."
                )
                filtered_events = []
            else:
                filtered_events = (
                    audit_analytics.filter_events(
                        decision_events,
                        start_date=audit_start_date,
                        end_date=audit_end_date,
                        new_status=(
                            audit_status_filter
                        ),
                        responsible=(
                            audit_responsible_filter
                        ),
                        brand=audit_brand_filter,
                        item=audit_item_filter,
                        transition=(
                            audit_transition_filter
                        ),
                        search=(
                            audit_search_filter
                        ),
                    )
                )

            global_summary = (
                audit_analytics.summary(
                    decision_events
                )
            )

            filtered_summary = (
                audit_analytics.summary(
                    filtered_events
                )
            )

            st.markdown(
                "#### Indicadores de auditoría"
            )

            ak1, ak2, ak3, ak4, ak5 = (
                st.columns(5)
            )

            ak1.metric(
                "Eventos registrados",
                global_summary["events"],
            )

            ak2.metric(
                "Eventos visibles",
                filtered_summary["events"],
            )

            ak3.metric(
                "Ítems involucrados",
                filtered_summary[
                    "unique_items"
                ],
            )

            ak4.metric(
                "Aprobaciones",
                filtered_summary[
                    "approvals"
                ],
            )

            ak5.metric(
                "Gestionados",
                filtered_summary[
                    "managed"
                ],
            )

            if filtered_events:
                filtered_audit_df = (
                    pd.DataFrame(
                        filtered_events
                    )
                )

                filtered_audit_df[
                    "Transición"
                ] = [
                    transition_label(row)
                    for row in filtered_events
                ]

                rename_map = {
                    "timestamp": "Fecha/hora",
                    "item": "Ítem",
                    "description": "Descripción",
                    "brand": "Marca",
                    "model": "Modelo",
                    "operational_priority": "Prioridad operativa",
                    "previous_status": "Estado anterior",
                    "new_status": "Estado nuevo",
                    "responsible": "Responsable",
                    "decision_notes": "Observación",
                }

                audit_columns = [
                    "timestamp",
                    "item",
                    "description",
                    "brand",
                    "model",
                    "operational_priority",
                    "previous_status",
                    "new_status",
                    "Transición",
                    "responsible",
                    "decision_notes",
                ]

                audit_view = (
                    filtered_audit_df[
                        audit_columns
                    ].copy()
                )

                audit_view[
                    "timestamp"
                ] = (
                    audit_view[
                        "timestamp"
                    ]
                    .apply(
                        _format_audit_timestamp
                    )
                )

                audit_view = (
                    audit_view.rename(
                        columns=rename_map
                    )
                )

                st.markdown(
                    "#### Eventos de decisión"
                )

                st.dataframe(
                    audit_view,
                    use_container_width=True,
                    hide_index=True,
                    height=360,
                )

                summary_left, summary_right = (
                    st.columns(2)
                )

                with summary_left:
                    st.markdown(
                        "#### Eventos por estado nuevo"
                    )

                    status_summary_df = (
                        pd.DataFrame(
                            [
                                {
                                    "Estado": key,
                                    "Eventos": value,
                                }
                                for key, value
                                in sorted(
                                    filtered_summary[
                                        "new_status"
                                    ].items()
                                )
                            ]
                        )
                    )

                    if not status_summary_df.empty:
                        st.bar_chart(
                            status_summary_df.set_index(
                                "Estado"
                            )["Eventos"],
                            use_container_width=True,
                        )
                    else:
                        st.info(
                            "No existen estados para la vista filtrada."
                        )

                with summary_right:
                    st.markdown(
                        "#### Transiciones registradas"
                    )

                    transition_summary_df = (
                        pd.DataFrame(
                            [
                                {
                                    "Transición": key,
                                    "Eventos": value,
                                }
                                for key, value
                                in sorted(
                                    filtered_summary[
                                        "transitions"
                                    ].items()
                                )
                            ]
                        )
                    )

                    if not transition_summary_df.empty:
                        st.dataframe(
                            transition_summary_df,
                            use_container_width=True,
                            hide_index=True,
                            height=220,
                        )
                    else:
                        st.info(
                            "No existen transiciones para la vista filtrada."
                        )

                export_scope = st.selectbox(
                    "Exportar auditoría",
                    [
                        "Vista filtrada",
                        "Historial completo",
                    ],
                    index=0,
                    key="phase99_export_scope",
                )

                if (
                    export_scope
                    == "Vista filtrada"
                ):
                    export_audit_df = (
                        audit_view.copy()
                    )
                    export_file_name = (
                        "auditoria_decisiones_filtrada.csv"
                    )
                else:
                    all_audit_df = pd.DataFrame(
                        decision_events
                    )
                    all_audit_df[
                        "Transición"
                    ] = [
                        transition_label(row)
                        for row
                        in decision_events
                    ]
                    all_audit_df[
                        "timestamp"
                    ] = (
                        all_audit_df[
                            "timestamp"
                        ].apply(
                            _format_audit_timestamp
                        )
                    )

                    all_columns = [
                        col
                        for col in audit_columns
                        if col
                        in all_audit_df.columns
                    ]

                    export_audit_df = (
                        all_audit_df[
                            all_columns
                        ].rename(
                            columns=rename_map
                        )
                    )
                    export_file_name = (
                        "auditoria_decisiones_completa.csv"
                    )

                st.download_button(
                    "Descargar auditoría de decisiones CSV",
                    data=(
                        export_audit_df
                        .to_csv(
                            index=False
                        )
                        .encode(
                            "utf-8-sig"
                        )
                    ),
                    file_name=(
                        export_file_name
                    ),
                    mime="text/csv",
                    key=(
                        "phase99_download_audit"
                    ),
                )

            else:
                st.warning(
                    "No existen eventos que coincidan "
                    "con los filtros de auditoría seleccionados."
                )


# ================================================================
# DOCUMENTOS
# ================================================================
if "Documentos" in tab_map:

    with tab_map["Documentos"]:

        st.subheader(
            "Gestión documental"
        )

        st.info(
            "Los archivos se procesan localmente y se almacenan en "
            "data/private_ingested/. Este directorio debe permanecer "
            "fuera de GitHub."
        )

        uploaded_file = st.file_uploader(
            "Seleccione un documento o archivo de datos",
            type=[
                "pdf",
                "docx",
                "doc",
                "txt",
                "csv",
                "xlsx",
                "xls",
            ],
            help=(
                "Formatos admitidos: PDF, DOCX, DOC, TXT, CSV, XLSX y XLS. "
                "Los archivos se procesan localmente."
            ),
        )

        st.caption(
            "PDF/DOC/DOCX/TXT se tratan como documentos. "
            "CSV/XLS/XLSX se transforman en texto tabular por hoja "
            "para el RAG."
        )

        col1, col2 = st.columns(
            2
        )

        with col1:
            document_id = st.text_input(
                "ID del documento",
                placeholder=(
                    "Ejemplo: DOC-REAL-001"
                ),
            )
            title = st.text_input(
                "Título"
            )
            document_type = st.text_input(
                "Tipo de documento",
                value="Documento técnico",
            )
            version = st.text_input(
                "Versión",
                value="1.0",
            )

        with col2:
            source_status = st.selectbox(
                "Estado",
                [
                    "vigente",
                    "borrador",
                ],
            )
            access_level = st.selectbox(
                "Nivel de acceso",
                [
                    "autorizado",
                ],
            )
            document_date = st.text_input(
                "Fecha del documento",
                placeholder="YYYY-MM-DD",
            )

        cc1, cc2 = st.columns(
            2
        )

        with cc1:
            chunk_size = st.number_input(
                "Tamaño de chunk",
                min_value=500,
                max_value=3000,
                value=1200,
                step=100,
            )

        with cc2:
            overlap = st.number_input(
                "Solapamiento",
                min_value=0,
                max_value=600,
                value=200,
                step=50,
            )

        if st.button(
            "Ingerir documento",
            type="primary",
        ):

            if not uploaded_file:
                st.warning(
                    "Seleccione un archivo."
                )

            elif (
                not document_id.strip()
                or not title.strip()
            ):
                st.warning(
                    "Complete el ID y el título."
                )

            else:
                try:
                    result = ingest_uploaded_file(
                        uploaded_file=uploaded_file,
                        data_dir=DATA_DIR,
                        document_id=document_id.strip(),
                        title=title.strip(),
                        document_type=document_type.strip(),
                        source_status=source_status,
                        access_level=access_level,
                        document_date=document_date.strip(),
                        version=version.strip(),
                        chunk_size=int(chunk_size),
                        overlap=int(overlap),
                    )

                    if result["ok"]:
                        st.success(
                            result["message"]
                        )

                        write_audit_event(
                            AUDIT_PATH,
                            event="document_ingestion",
                            username=user["username"],
                            role=user["role"],
                            detail=(
                                f"{document_id.strip()} | "
                                f"{uploaded_file.name} | "
                                f"chunks="
                                f"{result['chunk_count']}"
                            ),
                        )

                        st.cache_resource.clear()

                        st.info(
                            "El índice fue invalidado correctamente. "
                            "La próxima consulta reconstruirá el corpus "
                            "incluyendo el documento recién ingerido."
                        )

                    else:
                        st.warning(
                            result["message"]
                        )

                except Exception as exc:
                    st.error(
                        "No fue posible ingerir el documento."
                    )
                    st.exception(
                        exc
                    )

        registry_path = (
            DATA_DIR
            / "private_ingested"
            / "document_registry.jsonl"
        )

        registry = load_jsonl(
            registry_path
        )

        st.divider()
        st.subheader(
            "Documentos ingeridos"
        )

        if registry:
            st.dataframe(
                pd.DataFrame(
                    registry
                ),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info(
                "Todavía no hay documentos ingeridos."
            )


# ================================================================
# PIE
# ================================================================
st.divider()

st.caption(
    "Asistente IA DINDES — MVP académico. "
    "La decisión final permanece bajo responsabilidad humana."
)
