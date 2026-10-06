# Planificación del proyecto

## 1. Identificación

**Proyecto:** Asistente de IA para Innovación, Desarrollo y Gestión del Conocimiento Técnico — DINDES  
**Curso:** Proyecto Integrador en Inteligencia Artificial (MIAR0545)  
**Institución académica:** Universidad de Especialidades Espíritu Santo (UEES)  
**Docente:** Gladys María Villegas Rugel  
**Integrantes:**  
- Juan Carlos Bajaña Gutiérrez  
- José Luis Peñafiel Fernández  

> Este documento corresponde a la planificación inicial del proyecto y será actualizado a medida que avance el desarrollo.

---

## 2. Definición del problema

La Dirección de Innovación y Desarrollo (DINDES) gestiona documentación técnica, información de proyectos, inventarios, informes y otros recursos de conocimiento que deben ser consultados de manera eficiente por personal autorizado.

La búsqueda manual de información en múltiples documentos y repositorios puede consumir tiempo, dificultar la trazabilidad de las fuentes y generar dependencia del conocimiento individual de las personas que conocen dónde se encuentra cada antecedente.

El proyecto propone desarrollar un **Asistente de IA local** que permita realizar consultas en lenguaje natural y recuperar información relevante desde documentación previamente autorizada, manteniendo trazabilidad hacia las fuentes utilizadas.

---

## 3. Objetivo general

Desarrollar un prototipo funcional de asistente de inteligencia artificial local, basado en una arquitectura **RAG (Retrieval-Augmented Generation)**, que permita consultar y recuperar conocimiento técnico de DINDES de forma contextualizada, trazable y segura.

---

## 4. Objetivos específicos

1. Preparar y estructurar un corpus documental de prueba con metadatos.
2. Implementar un proceso de extracción, limpieza y segmentación de documentos.
3. Generar representaciones vectoriales mediante embeddings.
4. Implementar recuperación híbrida de información mediante búsqueda semántica y léxica.
5. Integrar un modelo de lenguaje local Qwen para generar respuestas basadas en contexto recuperado.
6. Mostrar al usuario las fuentes utilizadas para sustentar cada respuesta.
7. Implementar una interfaz web funcional para realizar consultas.
8. Evaluar el sistema mediante métricas de recuperación, calidad de respuesta, latencia y satisfacción del usuario.
9. Mantener el procesamiento y la información del prototipo en un entorno local/on-premise.

---

## 5. Justificación de la relevancia del proyecto

El proyecto busca reducir el tiempo requerido para localizar información técnica y mejorar la gestión del conocimiento institucional.

El uso de una arquitectura RAG permite mantener separada la información documental del modelo generativo, evitando la necesidad de realizar fine-tuning del LLM con los documentos institucionales durante el MVP.

La ejecución local permite desarrollar y demostrar el sistema sin depender de servicios externos para procesar el contenido utilizado en las pruebas, lo cual resulta coherente con las necesidades de privacidad, control y trazabilidad del entorno institucional.

---

## 6. Alcance

### 6.1 Incluye

- Procesamiento de documentos autorizados para el prototipo.
- Limpieza y segmentación del contenido.
- Generación de embeddings.
- Índice vectorial local.
- Recuperación semántica.
- Recuperación léxica tipo BM25 o equivalente.
- Recuperación híbrida.
- Reranking como componente evaluable.
- Generación de respuestas mediante Qwen ejecutado localmente.
- Visualización de fuentes y evidencias.
- Interfaz web para consultas.
- Evaluación mediante datasets QA y métricas definidas.
- Documentación técnica y manual de usuario.
- Código modular, pruebas unitarias y control de versiones con GitHub.

### 6.2 No incluye en el MVP

- Fine-tuning del modelo Qwen con documentación institucional.
- Despliegue público de documentación real de DINDES.
- Integración directa con sistemas institucionales productivos.
- Automatización de decisiones operativas.
- Sustitución del criterio de especialistas o autoridades.
- Publicación en GitHub de información clasificada, sensible, reservada o no autorizada.

---

## 7. Arquitectura conceptual prevista

```text
Documentos autorizados
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
                                                        Qwen local
                                                           ↓
                                               Respuesta + fuentes
                                                           ↓
                                                   Aplicación web
```

---

## 8. Datos

Durante las fases académicas iniciales se utilizan **datasets sample sintéticos**, diseñados para demostrar la metodología sin publicar información institucional sensible.

Los conjuntos de datos de prueba considerados incluyen:

- documentación técnica sample;
- inventario institucional sample;
- preguntas y respuestas para evaluación QA.

Antes de incorporar información real, deberá verificarse su autorización de uso, tratamiento y publicación.

---

## 9. Recursos necesarios

### 9.1 Hardware principal

- CPU: Intel Core Ultra 9 285K
- RAM: 96 GB DDR5 5600
- GPU: NVIDIA GeForce RTX 5080 16 GB
- Almacenamiento: SSD M.2 de 1 TB
- Fuente de poder: 1000 W 80+ Gold

### 9.2 Software y tecnologías previstas

- Python
- Visual Studio Code
- Jupyter
- Scikit-learn
- Qwen local
- Qwen3-Embedding o alternativa validada
- BGE-M3 como alternativa de comparación
- FAISS, Chroma o Qdrant para almacenamiento vectorial
- BM25 para recuperación léxica
- Streamlit para la interfaz web
- Git y GitHub para control de versiones

---

## 10. Indicadores de éxito

| Indicador | Meta inicial |
|---|---:|
| Precision@5 de recuperación | ≥ 85 % |
| Grounded Response Rate | ≥ 90 % |
| Tiempo de respuesta | ≤ 10 s |
| Reducción del tiempo de búsqueda | ≥ 50 % |
| Satisfacción del usuario | ≥ 4/5 |

Estos objetivos deberán validarse con un conjunto de evaluación suficientemente representativo antes de considerarse resultados operacionales.

---

## 11. Cronograma inicial

El MVP académico está planificado para cinco semanas.

| Semana | Actividades principales | Resultado esperado |
|---|---|---|
| 1 | Preparación de datos, baseline, definición de métricas y validación del entorno | Corpus sample preparado y línea base |
| 2 | Procesamiento, embeddings, índice vectorial y recuperación inicial | Retrieval funcional |
| 3 | Evaluación de overfitting/underfitting y mejoras del modelo auxiliar | Diagnóstico y estrategias documentadas |
| 4 | Integración RAG, recuperación híbrida, reranking e interfaz web | Prototipo integral consultable |
| 5 | Evaluación final, pruebas, documentación, ética y preparación de presentación | MVP validado y entregables finales |

### 11.1 Planificado vs. real

El avance real se actualizará progresivamente en este documento mediante commits posteriores.

---

## 12. Riesgos identificados y mitigación

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Dataset pequeño o poco representativo | Métricas poco confiables | Ampliar QA y separar desarrollo, validación y test |
| Desbalance de clases | Accuracy engañosa | Utilizar Precision, Recall, F1 y balanceo |
| Data leakage | Sobreestimación del rendimiento | Separar por `qa_id` antes de aumentación |
| Respuestas no sustentadas | Riesgo de alucinaciones | Grounding, fuentes visibles y umbral de recuperación |
| Documentación sensible | Riesgo de exposición | Procesamiento local y publicación exclusiva de samples autorizados |
| Latencia elevada | Baja usabilidad | Optimizar Top-K, embeddings, reranking y modelo |
| Ajuste reiterado sobre el mismo QA set | Pobre generalización | Separar desarrollo/validación de prueba final |
| Complejidad del despliegue | Dificultad de reproducción | `requirements.txt`, scripts de instalación y documentación |

---

## 13. Seguridad y privacidad

El proyecto prioriza una arquitectura local/on-premise.

El repositorio público de GitHub deberá contener únicamente código fuente, configuraciones no sensibles, datasets sintéticos o autorizados, documentación académica y resultados que no revelen información restringida.

No deberán publicarse credenciales, claves o tokens, documentos institucionales reales no autorizados, datos personales, información clasificada ni información operativa sensible.

---

## 14. Estrategia de versionamiento

Se utilizará Git y GitHub con:

- rama principal `main`;
- commits pequeños y descriptivos;
- ramas de desarrollo para cambios relevantes;
- tags para versiones importantes del prototipo;
- `.gitignore` para excluir entornos virtuales, secretos, modelos grandes y archivos temporales.

---

## 15. Entregables previstos

- Repositorio público de GitHub.
- Documentación completa en `docs/`.
- Notebooks de exploración, preprocesamiento, modelado, optimización y evaluación.
- Código fuente modular en `src/`.
- Modelos y artefactos documentados.
- Aplicación web funcional.
- Pruebas unitarias.
- Resultados, métricas y visualizaciones.
- Video pitch.
- Video de respuestas a preguntas.
- Manual de usuario.
- Consideraciones éticas y limitaciones del sistema.

---

## 16. Estado actual

A la fecha de creación de este documento:

- el repositorio GitHub ya se encuentra inicializado;
- existe una línea base correspondiente a la Semana 3;
- se dispone de un notebook ejecutado para diagnóstico de overfitting/underfitting;
- se ha implementado tracking de métricas;
- se han evaluado balanceo de clases y Feature Engineering;
- se dispone de visualizaciones a 300 DPI;
- se cuenta con código modular inicial;
- la interfaz RAG y los documentos finales del repositorio continúan en desarrollo.

---

## 17. Próximos pasos

1. Completar la documentación restante en `docs/`.
2. Reorganizar los notebooks de acuerdo con la estructura final exigida.
3. Implementar el pipeline RAG funcional.
4. Implementar la interfaz web con Streamlit.
5. Incorporar pruebas unitarias.
6. Documentar la optimización de hiperparámetros.
7. Desarrollar el análisis de consideraciones éticas.
8. Completar el manual de usuario.
9. Preparar la evaluación final, videos y presentación.
