# Arquitectura del sistema

## 1. Propósito

Este documento describe la arquitectura técnica del **Asistente de IA para Innovación, Desarrollo y Gestión del Conocimiento Técnico — DINDES**, incluyendo los controles incorporados a partir del análisis ético y de responsabilidad de Semana 4.

---

## 2. Arquitectura general

```text
Documentos autorizados
        ↓
Clasificación y control de acceso
        ↓
Extracción y limpieza
        ↓
Chunking + metadatos
        ↓
Embeddings ───────────────┐
        ↓                  │
Base vectorial            │
                           ├──→ Recuperación híbrida → Reranking → Top-K
BM25 / búsqueda léxica ───┘                               ↓
                                                     Validación ética
                                             (permisos + umbral + vigencia)
                                                           ↓
                                                     Qwen local
                                                           ↓
                                              Respuesta + evidencias
                                                           ↓
                                                   Aplicación web
```

---

## 3. Principio local/on-premise

El sistema se diseña para operación local o dentro de una red institucional restringida. El repositorio público contiene únicamente código, documentación y datasets sintéticos/autorizados.

---

## 4. Pipeline de ingesta

```text
Archivo autorizado
→ validación de acceso
→ extracción
→ limpieza
→ chunking
→ metadatos
→ embeddings
→ índice vectorial
→ índice BM25
```

Metadatos mínimos recomendados:

- `document_id`
- `project_id`
- título
- sección
- versión
- fecha
- unidad responsable
- estado de fuente
- nivel de acceso
- `chunk_id`

---

## 5. Control de acceso antes del retrieval

La autorización debe evaluarse **antes de recuperar contenido**.

```text
Usuario autenticado
      ↓
Rol / permisos
      ↓
Filtro de corpus autorizado
      ↓
Retrieval
```

Esto evita que un contenido no autorizado llegue al prompt del modelo, aunque posteriormente no se muestre en pantalla.

---

## 6. Recuperación híbrida

El sistema combinará:

- recuperación semántica con embeddings;
- recuperación léxica BM25;
- fusión de resultados;
- reranking;
- selección Top-K.

Los pesos y Top-K deberán ajustarse con un conjunto de desarrollo y validarse con un test independiente.

---

## 7. Validación de evidencia

Antes de generar la respuesta se verificará:

- autorización;
- score mínimo;
- vigencia;
- estado de la fuente;
- cantidad mínima de evidencia.

Si no se cumple el criterio:

```text
No existe evidencia suficiente
→ abstención
→ no generar afirmación categórica
```

---

## 8. Generación con Qwen local

El modelo debe:

- responder usando el contexto recuperado;
- evitar afirmar información no sustentada;
- indicar incertidumbre;
- abstenerse cuando corresponda;
- mantener referencia a las fuentes.

El LLM no se considera repositorio primario de conocimiento institucional.

---

## 9. Panel de evidencias

La interfaz deberá mostrar, cuando esté disponible:

- fuente;
- título;
- sección;
- fragmento;
- fecha;
- versión;
- estado de la fuente;
- score de relevancia.

La respuesta generativa y la evidencia deben diferenciarse visualmente.

---

## 10. Monitoreo por categoría

Además de métricas globales, se registrarán métricas por categoría/área:

- Precision@K;
- Recall@K;
- Grounded Response Rate;
- tasa de abstención;
- latencia;
- consultas sin respuesta.

Esto permitirá detectar sesgo de cobertura documental.

---

## 11. Logging y trazabilidad

El logging deberá ser mínimo y proporcional.

Eventos recomendados:

- versión del sistema;
- fecha/hora;
- categoría de consulta;
- fuentes recuperadas;
- estado de abstención;
- errores;
- incidentes de acceso.

No se deben registrar datos sensibles innecesarios.

---

## 12. Reporte, apelación y escalamiento

La aplicación deberá ofrecer un mecanismo para:

1. reportar una respuesta incorrecta;
2. reportar una fuente inapropiada;
3. solicitar revisión;
4. escalar al responsable funcional, custodio de información o autoridad competente;
5. registrar la resolución del caso.

---

## 13. Seguridad

Controles previstos:

- autenticación;
- autorización por rol;
- filtros antes del retrieval;
- cifrado;
- hardening;
- límites de consulta;
- auditoría;
- threat modeling;
- pruebas de abuso;
- revocación de acceso;
- plan de incidentes.

---

## 14. Arquitectura de software objetivo

```text
src/
├── __init__.py
├── data_processing.py
├── model.py
├── retrieval.py
├── security.py
├── evaluate.py
└── utils.py

app/
├── app.py
└── assets/
```

### `security.py`

Responsabilidades previstas:

- validación de permisos;
- filtros de corpus;
- logging seguro;
- controles de entrada;
- soporte para auditoría.

---

## 15. Componentes pendientes de implementación

- autenticación y roles;
- filtros previos al retrieval;
- abstención automática;
- panel de evidencias;
- mecanismo de reporte/apelación;
- logging de auditoría;
- métricas por categoría;
- pruebas de seguridad y abuso.

---

## 16. Documentos relacionados

- `docs/consideraciones_eticas.md`
- `docs/gobernanza_responsabilidad.md`
- `docs/compliance.md`
- `docs/manual_usuario.md`
