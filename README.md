# Asistente IA DINDES

Proyecto académico preparado para ejecutarse en **Visual Studio Code** y alojado en un repositorio público de **GitHub**.

El sistema corresponde al proyecto **“Asistente de IA para Innovación, Desarrollo y Gestión del Conocimiento Técnico — DINDES”**, desarrollado en el marco del curso **Proyecto Integrador en Inteligencia Artificial (MIAR0545)** de la Universidad de Especialidades Espíritu Santo (UEES).

> El proyecto utiliza una arquitectura **RAG (Retrieval-Augmented Generation)** con ejecución local/on-premise. El objetivo es consultar documentación autorizada, recuperar evidencia relevante y generar respuestas sustentadas con trazabilidad hacia las fuentes.

---

## Estado del proyecto

El repositorio ya cuenta con una línea base funcional y con documentación progresiva del proyecto.

### Historial de commits principales

| # | Commit | Descripción |
|---|---|---|
| 1 | `c965e25` | Estructura inicial del proyecto y baseline de Semana 3 |
| 2 | `4cb7700` | Documento de planificación y licencia |
| 3 | `e47edaa` | Análisis de datos, arquitectura y visualizaciones EDA |
| 4 | `7f3bbc6` | Dataset de inventario y documentación de optimización, ética y manual de usuario |

El versionamiento continuará mediante commits pequeños y descriptivos.

---

## Estructura actual del proyecto

```text
Asistente_IA/
├── .vscode/
│   ├── extensions.json
│   └── settings.json
│
├── app/
│   └── .gitkeep
│
├── data/
│   ├── Dataset_1_Documentacion_Tecnica_DINDES_Sample.csv
│   ├── Dataset_2_Inventario_Institucional_DINDES_Sample.csv
│   └── Dataset_3_Evaluacion_QA_Asistente_IA_Sample.csv
│
├── docs/
│   ├── planificacion.md
│   ├── analisis_datos.md
│   ├── arquitectura.md
│   ├── optimizacion.md
│   ├── consideraciones_eticas.md
│   └── manual_usuario.md
│
├── models/
│   └── .gitkeep
│
├── notebooks/
│   └── overfitting_analysis.ipynb
│
├── outputs/
│   └── figures/
│       ├── 01_training_validation_loss.png
│       ├── 02_training_validation_accuracy.png
│       ├── 03_precision_recall_f1_base.png
│       ├── 04_confusion_feature_engineering.png
│       ├── 05_learning_curve_dataset_size.png
│       ├── 06_validation_curve_alpha.png
│       └── 07_comparacion_estrategias_f1.png
│
├── results/
│   ├── .gitkeep
│   └── figures/
│       ├── eda_01_documentos_por_tipo.png
│       ├── eda_02_estado_fuentes.png
│       ├── eda_03_inventario_por_categoria.png
│       ├── eda_04_estado_inventario.png
│       ├── eda_05_qa_por_dificultad.png
│       └── eda_06_desbalance_pares_relevancia.png
│
├── src/
│   └── overfitting_utils.py
│
├── tests/
│   └── .gitkeep
│
├── .gitignore
├── LICENSE
├── README.md
├── requirements.txt
├── setup_windows.bat
└── verificar_entorno.py
```

> La carpeta `.venv/` existe localmente, pero está excluida mediante `.gitignore` y no se publica en GitHub.

---

## Descripción del problema

DINDES gestiona documentación técnica, información de proyectos, inventarios, informes y otros recursos de conocimiento que deben ser consultados de manera eficiente por personal autorizado.

La búsqueda manual puede:

- consumir tiempo;
- dificultar la trazabilidad;
- depender del conocimiento individual;
- complicar la reutilización de antecedentes técnicos.

El proyecto propone un asistente de IA que permita realizar consultas en lenguaje natural y recuperar información relevante desde fuentes autorizadas.

---

## Objetivo general

Desarrollar un prototipo funcional de asistente de inteligencia artificial local, basado en una arquitectura **RAG**, que permita consultar y recuperar conocimiento técnico de DINDES de forma contextualizada, trazable y segura.

---

## Usuarios objetivo

El sistema está orientado a personal autorizado que requiera consultar:

- documentación técnica;
- antecedentes de proyectos;
- inventario institucional;
- informes;
- procedimientos;
- información estructurada de apoyo.

---

## Arquitectura propuesta

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

La estrategia principal del MVP es **RAG**, no fine-tuning del LLM con documentación institucional.

---

## Dataset

El repositorio utiliza únicamente **datasets sample sintéticos** para fines académicos.

### Dataset 1 — Documentación técnica

```text
data/Dataset_1_Documentacion_Tecnica_DINDES_Sample.csv
```

Contiene documentos técnicos sample con:

- identificadores;
- proyectos;
- tipo de documento;
- título;
- versión;
- sección;
- chunk;
- texto;
- estado de fuente;
- nivel de acceso.

### Dataset 2 — Inventario institucional

```text
data/Dataset_2_Inventario_Institucional_DINDES_Sample.csv
```

Contiene:

- código;
- descripción;
- categoría;
- marca;
- modelo;
- cantidad;
- estado;
- ubicación;
- responsable.

### Dataset 3 — Evaluación QA

```text
data/Dataset_3_Evaluacion_QA_Asistente_IA_Sample.csv
```

Contiene preguntas de evaluación, fuente esperada, respuesta esperada, dificultad y criterio de respondibilidad.

> No se publican documentos institucionales reales, datos sensibles ni información operativa no autorizada.

---

## Metodología

### Diagnóstico de Semana 3

Se implementó un clasificador auxiliar de relevancia **pregunta-documento** para estudiar:

- overfitting;
- underfitting;
- desbalance;
- data leakage;
- tracking de métricas;
- feature engineering;
- learning curves;
- validation curves.

El split experimental se realiza por `qa_id` antes de la aumentación y esta se aplica únicamente a training.

### Estrategias evaluadas

1. Modelo base: TF-IDF + SGDClassifier.
2. Balanceo de clases.
3. Feature Engineering.
4. Early stopping como análisis complementario.

---

## Resultados de referencia

| Modelo | Accuracy | Precision | Recall | F1 |
|---|---:|---:|---:|---:|
| Modelo base | 0.8750 | 0.0000 | 0.0000 | 0.0000 |
| Balanceo de clases | 0.5000 | 0.0000 | 0.0000 | 0.0000 |
| Feature Engineering | 0.8125 | 0.4000 | 1.0000 | 0.5714 |

Matriz de confusión del modelo con Feature Engineering:

```text
TN = 11
FP = 3
FN = 0
TP = 2
```

> El `Recall = 1.00` corresponde a 2 de 2 positivos en validation, por lo que no debe interpretarse como desempeño operacional.

---

## Diagnóstico

Los resultados actuales no muestran un patrón clásico de overfitting.

Las principales limitaciones identificadas son:

- fuerte desbalance de clases;
- tamaño reducido del sample;
- alta variabilidad estadística;
- representación insuficiente de la relación pregunta-documento en el modelo base.

La mejora más relevante se obtuvo mediante **Feature Engineering**.

---

## Documentación disponible

La carpeta `docs/` contiene:

| Documento | Estado |
|---|---|
| `planificacion.md` | Inicial completo |
| `analisis_datos.md` | Inicial completo |
| `arquitectura.md` | Inicial completo |
| `optimizacion.md` | Parcial; Workshop S5 pendiente |
| `consideraciones_eticas.md` | Inicial completo |
| `manual_usuario.md` | Estructurado; capturas de la app pendientes |

---

## Visualizaciones

### Semana 3

```text
outputs/figures/
```

Incluye:

- Training vs Validation Loss;
- Training vs Validation Accuracy;
- Precision/Recall/F1;
- matriz de confusión;
- Learning Curve;
- Validation Curve;
- comparación final de estrategias.

### EDA

```text
results/figures/
```

Incluye 6 visualizaciones del análisis exploratorio de datos.

Todas las figuras académicas principales se generan a **300 DPI**.

---

## Interfaz web

La interfaz prevista para el MVP será desarrollada con **Streamlit**.

Flujo esperado:

```text
Usuario
  ↓
Aplicación web
  ↓
Consulta
  ↓
Retrieval híbrido
  ↓
Reranking
  ↓
Top-K fuentes
  ↓
Qwen local
  ↓
Respuesta + fuentes + scores
```

La app se incorporará en:

```text
app/app.py
```

Ejecución prevista:

```powershell
streamlit run app/app.py
```

---

## Indicadores de éxito del MVP

| Indicador | Meta |
|---|---:|
| Precision@5 | ≥ 85 % |
| Grounded Response Rate | ≥ 90 % |
| Tiempo de respuesta | ≤ 10 s |
| Reducción del tiempo de búsqueda | ≥ 50 % |
| Satisfacción del usuario | ≥ 4/5 |

Estas metas deberán validarse con datos suficientes antes de considerarse resultados operacionales.

---

## Instalación rápida en Windows

Abrir la carpeta completa del proyecto en Visual Studio Code.

Desde PowerShell:

```powershell
py -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m ipykernel install --user --name asistente-ia-dindes --display-name "Python (Asistente IA DINDES)"
```

---

## Verificación

```powershell
python verificar_entorno.py
```

---

## Ejecutar el notebook actual

Abrir:

```text
notebooks/overfitting_analysis.ipynb
```

Seleccionar el kernel:

```text
Python (Asistente IA DINDES)
```

Para una primera validación se recomienda ejecutar celda por celda y posteriormente utilizar **Run All**.

---

## Consideraciones éticas

El proyecto incorpora:

- privacidad por diseño;
- supervisión humana;
- trazabilidad;
- abstención cuando no exista evidencia suficiente;
- protección de información institucional;
- análisis de sesgo de cobertura;
- limitaciones claramente documentadas.

El asistente no debe sustituir el criterio de especialistas ni utilizarse como única fuente para decisiones críticas.

Ver:

```text
docs/consideraciones_eticas.md
```

---

## Seguridad

No deben subirse al repositorio público:

- credenciales;
- tokens;
- claves privadas;
- documentos institucionales reales no autorizados;
- bases vectoriales derivadas de información sensible;
- logs con información restringida.

---

## Autores

### Juan Carlos Bajaña Gutiérrez
Participación en planificación, desarrollo técnico, experimentación, documentación y arquitectura.

### José Luis Peñafiel Fernández
Participación en análisis, desarrollo, evaluación y documentación del proyecto.

---

## Licencia

Este repositorio utiliza una versión en español de la **Licencia MIT**, incluida en:

```text
LICENSE
```

---

## Trabajo pendiente

Próximos componentes:

- reorganización de notebooks;
- modularización completa de `src/`;
- pipeline de ingesta;
- embeddings;
- base vectorial;
- BM25;
- recuperación híbrida;
- reranking;
- integración con Qwen local;
- aplicación Streamlit;
- pruebas unitarias;
- Workshop S5;
- métricas end-to-end;
- capturas del manual;
- video pitch;
- video de respuestas.

---

## Repositorio

Repositorio público:

```text
https://github.com/juanbajanag/asistente-ia-dindes
```

---

## Advertencia

Los resultados actuales corresponden a datasets sample y actividades académicas.

No representan desempeño operacional del futuro sistema institucional.
