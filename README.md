# ⚓ Asistente IA DINDES

![Python](https://img.shields.io/badge/Python-3.14-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Estado-MVP%20funcional-success)

**Asistente de IA para Innovación, Desarrollo y Gestión del Conocimiento Técnico — DINDES**

Proyecto académico del curso **Proyecto Integrador en Inteligencia Artificial (MIAR0545)** de la Universidad de Especialidades Espíritu Santo (UEES).

El sistema implementa un asistente basado en **RAG (Retrieval-Augmented Generation)** para recuperar conocimiento técnico, responder consultas con evidencia visible, consultar inventario estructurado y abstenerse cuando no existe evidencia suficiente. La arquitectura principal se diseñó para operación local/on-premise y se creó además una **versión cloud académica** en Streamlit Community Cloud para permitir evaluación remota con datos sintéticos o autorizados.

> **Aplicación pública:** [https://asistente-ia-dindes.streamlit.app/]

---

## Tabla de contenidos

1. [Problema](#problema)
2. [Usuarios objetivo](#usuarios-objetivo)
3. [Datos](#datos)
4. [Metodología](#metodología)
5. [Arquitectura](#arquitectura)
6. [Resultados](#resultados)
7. [Instalación y ejecución](#instalación-y-ejecución)
8. [Interfaz de usuario](#interfaz-de-usuario)
9. [Estructura del proyecto](#estructura-del-proyecto)
10. [Consideraciones éticas](#consideraciones-éticas)
11. [Limitaciones](#limitaciones)
12. [Autores y contribuciones](#autores-y-contribuciones)
13. [Licencia](#licencia)
14. [Referencias](#referencias)
15. [Videos](#videos)

---

## Problema

DINDES gestiona documentación técnica, antecedentes de proyectos, inventarios e información de apoyo que debe ser consultada de forma eficiente y trazable. La búsqueda manual puede consumir tiempo, fragmentar el conocimiento y dificultar la identificación de la fuente exacta que sustenta una respuesta.

El proyecto busca reducir ese problema mediante recuperación de información, consultas estructuradas y generación asistida con evidencia.

### ¿Por qué es importante?

- Reduce tiempo de búsqueda de antecedentes.
- Facilita reutilización del conocimiento técnico.
- Mantiene trazabilidad hacia documentos y registros.
- Disminuye dependencia del conocimiento tácito.
- Introduce abstención explícita cuando la evidencia es insuficiente.

---

## Usuarios objetivo

El MVP está dirigido principalmente a:

- personal técnico y administrativo autorizado;
- responsables de proyectos;
- analistas y especialistas;
- administradores del conocimiento;
- personal que requiera consultar inventario o antecedentes técnicos.

La aplicación es una **herramienta de apoyo** y no sustituye decisiones técnicas, administrativas u operativas.

---

## Datos

El repositorio público utiliza datasets **sintéticos y académicos**, empleados para demostrar el funcionamiento sin publicar información institucional sensible.

| Dataset | Propósito |
|---|---|
| `Dataset_1_Documentacion_Tecnica_DINDES_Sample.csv` | Conocimiento documental de prueba |
| `Dataset_2_Inventario_Institucional_DINDES_Sample.csv` | Inventario sample |
| `Dataset_3_Evaluacion_QA_Asistente_IA_Sample.csv` | Preguntas y respuestas de evaluación |

La descripción ampliada se encuentra en [`data/README.md`](data/README.md) y [`docs/analisis_datos.md`](docs/analisis_datos.md).

### Fuente y licencia

Los datos publicados forman parte del material sintético elaborado para el proyecto académico. No corresponden a un dataset público de terceros. El código se publica bajo licencia MIT; los datos sample se incluyen únicamente para fines académicos y demostrativos.

---

## Metodología

El proyecto no realiza fine-tuning del LLM con documentación institucional. Se utiliza una arquitectura RAG:

1. carga y normalización de datos;
2. segmentación y metadatos;
3. recuperación léxica/semántica;
4. selección de evidencia;
5. respuesta con citas;
6. abstención si no se supera la política de evidencia.

Además existe una ruta **estructurada determinística** para inventario tabular.

Para estudiar overfitting/underfitting se utilizó un clasificador auxiliar pregunta-documento. La metodología y sus limitaciones se documentan en [`docs/optimizacion.md`](docs/optimizacion.md).

---

## Arquitectura

```text
                         ┌──────────────────────────┐
                         │      Pregunta usuario     │
                         └─────────────┬────────────┘
                                       ↓
                         ┌──────────────────────────┐
                         │ Enrutamiento de consulta │
                         └───────┬──────────┬───────┘
                                 │          │
                    estructurada │          │ documental
                                 ↓          ↓
                     Motor tabular       Retrieval
                                 │          │
                                 │       Top-K / evidencia
                                 │          │
                                 └────┬─────┘
                                      ↓
                              Respuesta + fuentes
                                      ↓
                                 Streamlit UI
```

La versión local puede integrar el modelo generativo local. La versión cloud utiliza un backend ligero y reproducible para evaluación remota, evitando depender de Ollama o de pesos locales no disponibles en Streamlit Community Cloud.

Más detalle: [`docs/arquitectura.md`](docs/arquitectura.md).

---

## Resultados

### Clasificador auxiliar de relevancia

| Modelo | Accuracy | Precision | Recall | F1 |
|---|---:|---:|---:|---:|
| Modelo base | 0.8750 | 0.0000 | 0.0000 | 0.0000 |
| Balanceo de clases | 0.5000 | 0.0000 | 0.0000 | 0.0000 |
| Feature Engineering | 0.8125 | 0.4000 | 1.0000 | 0.5714 |

El conjunto de validación contiene únicamente dos positivos; por ello estas métricas son demostrativas y no deben interpretarse como desempeño operacional.

### Validación funcional del MVP

Se verificaron cuatro comportamientos de extremo a extremo:

| Caso | Resultado esperado |
|---|---|
| Consulta tabular de inventario | Respuesta estructurada determinística |
| Consulta cuantitativa sample | Respuesta RAG con cantidad explícita |
| Consulta documental | Recuperación y respuesta con fuente |
| Consulta sin evidencia | Abstención en retrieval |

Ejemplos usados en la validación:

```text
¿Cuál es el stock del taladro DEWALT modelo DWD024-B3?
¿Cuántas impresoras 3D Creality K1 están disponibles?
¿Qué componentes principales integra la arquitectura del Simulador Táctico Submarino?
¿Cuál es el número de serie del generador principal de la fragata inexistente?
```

---

## Instalación y ejecución

### Requisitos

- Python 3.14.x validado en el entorno de desarrollo
- Windows 10/11 para la configuración local utilizada durante el proyecto
- Dependencias de `requirements.txt`

### Instalación

```powershell
py -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python verificar_entorno.py
```

### Aplicación local principal

```powershell
streamlit run app/app.py
```

### Entrypoint cloud

```powershell
streamlit run streamlit_app.py
```

`streamlit_app.py` activa el runtime cloud y ejecuta la interfaz existente desde `app/app.py`.

### Pruebas

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

### Verificación de estructura final

```powershell
python scripts/check_final_repository.py
```

---

## Interfaz de usuario

La interfaz incluye:

- autenticación y roles;
- consulta en lenguaje natural;
- ejemplos precargados;
- respuestas con evidencia;
- abstención explícita;
- consulta estructurada de inventario;
- dashboard y filtros;
- descarga CSV;
- historial y auditoría;
- evaluación de respuestas;
- administración de criticidad y reposición, según permisos.

La app muestra advertencias de uso y mantiene la decisión final bajo responsabilidad humana.

> Antes de entregar, agregue aquí 2–4 capturas finales o enlaces a imágenes del repositorio.

---

## Estructura del proyecto

```text
asistente-ia-dindes/
├── README.md
├── requirements.txt
├── .gitignore
├── LICENSE
├── streamlit_app.py
├── docs/
├── data/
│   ├── raw/
│   ├── processed/
│   └── README.md
├── notebooks/
│   ├── 01_exploracion.ipynb
│   ├── 02_preprocesamiento.ipynb
│   ├── 03_modelado.ipynb
│   ├── 04_optimizacion.ipynb
│   └── 05_evaluacion.ipynb
├── src/
├── models/
│   └── README.md
├── app/
│   ├── app.py
│   └── requirements.txt
├── tests/
└── results/
    ├── figures/
    ├── metrics/
    └── reports/
```

---

## Consideraciones éticas

El sistema incorpora:

- abstención ante evidencia insuficiente;
- trazabilidad de fuentes;
- revisión humana;
- control de acceso;
- separación entre datos públicos de demostración y datos institucionales;
- advertencias contra sobreconfianza;
- auditoría y mecanismos de reporte;
- análisis de privacidad, fairness, transparencia, impacto y uso dual.

Documentación: [`docs/consideraciones_eticas.md`](docs/consideraciones_eticas.md).

---

## Limitaciones

- Los datasets publicados son pequeños y sintéticos.
- Las métricas académicas no representan desempeño operacional.
- La calidad depende de cobertura y vigencia del corpus.
- La versión cloud no replica todo el costo computacional del runtime local.
- Una respuesta con evidencia debe ser verificada antes de decisiones relevantes.
- La aplicación no debe utilizarse como sistema autónomo de decisión.

---

## Autores y contribuciones

### Juan Carlos Bajaña Gutiérrez
- arquitectura y desarrollo del MVP;
- integración RAG e inventario;
- interfaz y despliegue;
- evaluación y documentación.

### José Luis Peñafiel Fernández
- análisis y desarrollo del proyecto integrador;
- revisión metodológica;
- documentación y evaluación académica.

Las contribuciones pueden ajustarse antes de la entrega final para reflejar con exactitud la distribución real del trabajo.

---

## Licencia

Código publicado bajo **MIT License**. Consulte [`LICENSE`](LICENSE).

---

## Referencias

- Streamlit
- Scikit-learn
- Pandas
- NumPy
- Matplotlib
- Qwen
- documentación técnica citada en los informes del proyecto

Las referencias académicas detalladas se mantienen en los documentos e informes del proyecto.

---

## Videos

Los dos videos son obligatorios para la entrega final.

- **Video pitch (máximo 5 minutos):** agregar enlace final.
- **Video de respuestas a preguntas:** agregar enlace final.

Antes de entregar, sustituya estos textos por enlaces accesibles para la docente.
