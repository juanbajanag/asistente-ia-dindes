"""
Construcción de prompts RAG para el Asistente IA DINDES.
"""
from __future__ import annotations

SYSTEM_PROMPT = """
Eres el Asistente de IA para Innovación, Desarrollo y Gestión del Conocimiento Técnico de DINDES.

Reglas obligatorias:
1. Responde únicamente con la evidencia proporcionada.
2. No inventes hechos, nombres, cantidades, fechas, estados ni conclusiones.
3. Si la evidencia es insuficiente, indica:
   "No se encontró evidencia suficiente en las fuentes disponibles para responder esta consulta."
4. Usa referencias [F1], [F2], etc.
5. Si una fuente está marcada como borrador, indícalo.
6. No presentes inferencias como hechos documentados.
7. Sé claro, conciso y técnico.
""".strip()

def build_context(results):
    blocks = []
    for idx, result in enumerate(results, start=1):
        m = result.metadata
        if result.source_type == "document":
            meta = (
                f"document_id={m.get('document_id', result.record_id)}; "
                f"project_id={m.get('project_id','')}; "
                f"section={m.get('section','')}; "
                f"version={m.get('version','')}; "
                f"source_status={m.get('source_status','')}; "
                f"date={m.get('document_date','')}"
            )
        else:
            meta = (
                f"codigo={result.record_id}; "
                f"categoria={m.get('categoria','')}; "
                f"estado={m.get('estado','')}; "
                f"ubicacion={m.get('ubicacion','')}; "
                f"fecha_actualizacion={m.get('fecha_actualizacion','')}"
            )
        blocks.append(
            f"[F{idx}]\n"
            f"Título: {result.title}\n"
            f"Tipo: {result.source_type}\n"
            f"Metadatos: {meta}\n"
            f"Contenido: {result.text}\n"
        )
    return "\n".join(blocks)

def build_user_prompt(question, results):
    context = build_context(results)
    return f"""
PREGUNTA DEL USUARIO:
{question}

CONTEXTO RECUPERADO:
{context}

INSTRUCCIONES:
- Responde directamente.
- Usa exclusivamente el contexto recuperado.
- Cita [F1], [F2], etc. junto a afirmaciones relevantes.
- Finaliza con "Fuentes utilizadas".
- No agregues información no sustentada.
""".strip()
