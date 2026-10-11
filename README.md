# Asistente IA DINDES

Proyecto académico **“Asistente de IA para Innovación, Desarrollo y Gestión del Conocimiento Técnico — DINDES”**, desarrollado en el curso Proyecto Integrador en Inteligencia Artificial de la Universidad de Especialidades Espíritu Santo (UEES).

El sistema se diseña como un asistente local/on-premise basado en **RAG (Retrieval-Augmented Generation)** para consultar documentación autorizada, recuperar evidencia y generar respuestas trazables hacia sus fuentes.

---

## Objetivo

Desarrollar un MVP que permita:

- consultar conocimiento técnico en lenguaje natural;
- recuperar información relevante;
- mostrar fuentes y evidencias;
- operar localmente;
- mantener control de acceso y trazabilidad;
- abstenerse cuando la evidencia sea insuficiente.

---

## Arquitectura

```text
Documentos autorizados
        ↓
Control de acceso
        ↓
Extracción / limpieza / chunking
        ↓
Embeddings + BM25
        ↓
Recuperación híbrida
        ↓
Reranking
        ↓
Validación de permisos, relevancia y vigencia
        ↓
Qwen local
        ↓
Respuesta + fuentes + metadatos
        ↓
Aplicación web
```

---

## Estructura del repositorio

```text
Asistente_IA/
├── app/
├── data/
├── docs/
│   ├── planificacion.md
│   ├── analisis_datos.md
│   ├── arquitectura.md
│   ├── optimizacion.md
│   ├── consideraciones_eticas.md
│   ├── gobernanza_responsabilidad.md
│   ├── compliance.md
│   └── manual_usuario.md
├── models/
├── notebooks/
├── outputs/
├── results/
├── src/
├── tests/
├── .gitignore
├── LICENSE
├── README.md
├── requirements.txt
├── setup_windows.bat
└── verificar_entorno.py
```

---

## Datasets sample

```text
data/
├── Dataset_1_Documentacion_Tecnica_DINDES_Sample.csv
├── Dataset_2_Inventario_Institucional_DINDES_Sample.csv
└── Dataset_3_Evaluacion_QA_Asistente_IA_Sample.csv
```

Los datasets publicados son sintéticos y académicos. No deben subirse documentos institucionales reales sin autorización.

---

## Ética, seguridad y responsabilidad

El análisis de Semana 4 reforzó los siguientes requisitos:

1. **El asistente informa, no decide.**
2. **Control de acceso antes del retrieval.**
3. **Abstención ante evidencia insuficiente.**
4. **Fuentes visibles con fecha, versión y estado.**
5. **Monitoreo por categoría para detectar sesgo de cobertura.**
6. **Logging mínimo y trazable.**
7. **Mecanismo de reporte y apelación.**
8. **Plan de respuesta a incidentes.**
9. **Revisión humana en decisiones críticas.**

Documentación:

- [`docs/consideraciones_eticas.md`](docs/consideraciones_eticas.md)
- [`docs/gobernanza_responsabilidad.md`](docs/gobernanza_responsabilidad.md)
- [`docs/compliance.md`](docs/compliance.md)
- [`docs/arquitectura.md`](docs/arquitectura.md)
- [`docs/manual_usuario.md`](docs/manual_usuario.md)

---

## Principales riesgos identificados

- privacidad y confidencialidad;
- respuestas no sustentadas;
- información desactualizada;
- sesgo de cobertura documental;
- falta de transparencia;
- sobreconfianza;
- seguridad y uso indebido.

---

## Compliance

Para un despliegue real en Ecuador deberán revisarse:

- Ley Orgánica de Protección de Datos Personales;
- Reglamento General a la LOPDP;
- normativa institucional aplicable;
- políticas de clasificación, acceso y ciberseguridad.

Normas internacionales como GDPR, CCPA, HIPAA o EU AI Act no se consideran aplicables por defecto al alcance actual y deberán reevaluarse si cambia el contexto de uso.

---

## Resultados de Semana 3

| Modelo | Accuracy | Precision | Recall | F1 |
|---|---:|---:|---:|---:|
| Modelo base | 0.8750 | 0.0000 | 0.0000 | 0.0000 |
| Balanceo de clases | 0.5000 | 0.0000 | 0.0000 | 0.0000 |
| Feature Engineering | 0.8125 | 0.4000 | 1.0000 | 0.5714 |

Estos resultados corresponden a un sample académico pequeño y no representan desempeño operacional.

---

## Metas del MVP

| Indicador | Meta |
|---|---:|
| Precision@5 | ≥ 85 % |
| Grounded Response Rate | ≥ 90 % |
| Tiempo de respuesta | ≤ 10 s |
| Reducción del tiempo de búsqueda | ≥ 50 % |
| Satisfacción del usuario | ≥ 4/5 |

---

## Instalación rápida en Windows

```powershell
py -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python verificar_entorno.py
```

---

## Repositorio

```text
https://github.com/juanbajanag/asistente-ia-dindes
```

---

## Autores

- Juan Carlos Bajaña Gutiérrez
- José Luis Peñafiel Fernández

---

## Advertencia

Este proyecto se encuentra en desarrollo académico. El sistema futuro no debe utilizarse como única fuente para decisiones críticas y siempre deberá permitir revisión de la evidencia original.
