# Fase 11 — Evaluación formal del MVP

## Objetivo

Medir de forma reproducible el desempeño del Asistente IA DINDES sobre:

- consultas estructuradas;
- recuperación RAG;
- respuestas sustentadas;
- abstención ante falta de evidencia;
- latencia de respuesta.

## Métricas

### 1. Exactitud de consultas estructuradas
Porcentaje de consultas estructuradas cuya respuesta contiene los valores
esperados y utiliza el modo `structured`.

### 2. Tasa de respuestas RAG sustentadas
Porcentaje de respuestas RAG no abstencionistas que incluyen al menos una
fuente recuperada.

### 3. Exactitud de abstención
Porcentaje de casos diseñados sin evidencia suficiente en los que el sistema
se abstiene correctamente.

### 4. Latencia
Se registran:
- promedio;
- mediana;
- máximo.

## Archivo de casos

`evaluation/evaluation_cases.csv`

Los casos incluidos son una base inicial. Para el informe final se recomienda
ampliarlos con preguntas reales validadas por los integrantes del proyecto.

## Ejecución

Primero:

```powershell
python scripts/validar_fase11.py
```

Luego:

```powershell
python evaluation/run_evaluation.py
python evaluation/generate_report.py
```

## Resultados

Se generan:

- `evaluation/results/evaluation_results.csv`
- `evaluation/results/evaluation_summary.json`
- `evaluation/results/evaluation_report.md`

## Precaución metodológica

Los resultados obtenidos con un conjunto pequeño de casos no deben presentarse
como desempeño general del sistema.

Los casos utilizados para configurar reglas, prompts, umbrales o recuperación
deben considerarse conjunto de desarrollo. Para la evaluación final académica
conviene mantener un conjunto adicional no utilizado durante los ajustes.
