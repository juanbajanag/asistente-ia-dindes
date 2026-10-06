# Asistente IA DINDES

Proyecto preparado para ejecutar en **Visual Studio Code**.

Este repositorio contiene la implementación académica de la actividad **Diagnóstico de Overfitting/Underfitting — Semana 3** aplicada al proyecto **Asistente de IA para Innovación, Desarrollo y Gestión del Conocimiento Técnico — DINDES**.

> **Nota metodológica:** el MVP del Asistente utiliza una arquitectura RAG y no realiza fine-tuning de Qwen con los documentos institucionales. Para esta actividad se analiza un **clasificador auxiliar de relevancia pregunta-documento**, asociado conceptualmente al proceso de retrieval/reranking.

## Estructura

```text
Asistente_IA/
├── .vscode/
│   ├── extensions.json
│   └── settings.json
├── data/
│   ├── Dataset_1_Documentacion_Tecnica_DINDES_Sample.csv
│   └── Dataset_3_Evaluacion_QA_Asistente_IA_Sample.csv
├── notebooks/
│   └── overfitting_analysis.ipynb
├── outputs/
│   └── figures/
│       ├── 01_training_validation_loss.png
│       ├── 02_training_validation_accuracy.png
│       ├── 03_precision_recall_f1_base.png
│       ├── 04_confusion_feature_engineering.png
│       ├── 05_learning_curve_dataset_size.png
│       ├── 06_validation_curve_alpha.png
│       └── 07_comparacion_estrategias_f1.png
├── src/
│   └── overfitting_utils.py
├── .gitignore
├── requirements.txt
├── setup_windows.bat
├── verificar_entorno.py
└── README.md
```

## Instalación rápida en Windows

1. Abra la carpeta completa del proyecto en VS Code mediante **File > Open Folder**.
2. Abra una terminal integrada.
3. Ejecute:

```bat
.\setup_windows.bat
```

El script crea el entorno virtual `.venv`, instala las dependencias y registra el kernel:

```text
Python (Asistente IA DINDES)
```

## Instalación manual

En PowerShell:

```powershell
py -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m ipykernel install --user --name asistente-ia-dindes --display-name "Python (Asistente IA DINDES)"
```

La modificación de `ExecutionPolicy` con `-Scope Process` solo afecta a la sesión actual de PowerShell.

## Verificación del entorno

Con el entorno virtual activo:

```powershell
python verificar_entorno.py
```

La salida debe confirmar la presencia de los datasets, el notebook y las librerías principales.

## Ejecutar el notebook

Abra:

```text
notebooks/overfitting_analysis.ipynb
```

En la esquina superior derecha seleccione:

```text
Python (Asistente IA DINDES)
```

Para revisión académica se recomienda ejecutar inicialmente **celda por celda**. Una vez validado el flujo completo puede utilizarse **Run All**.

## Metodología del experimento

El notebook implementa los siguientes controles para reducir errores metodológicos:

1. Construcción de pares **pregunta-documento** con etiqueta binaria de relevancia.
2. Separación de training y validation por `qa_id` **antes de realizar aumentación de datos**.
3. Aumentación aplicada exclusivamente al conjunto de training.
4. Validación sin datos aumentados.
5. Tracking por época de:
   - Training Loss
   - Validation Loss
   - Training Accuracy
   - Validation Accuracy
   - Precision
   - Recall
   - F1-Score
6. Curvas avanzadas con `learning_curve` y `validation_curve` de Scikit-learn.
7. Validación cruzada agrupada mediante `GroupKFold` para mantener separados los `qa_id`.

Este diseño evita que variantes de una misma pregunta aparezcan simultáneamente en training y validation, reduciendo el riesgo de **data leakage**.

## Estrategias evaluadas

### Modelo base

Se utiliza:

```text
TF-IDF + SGDClassifier (log_loss)
```

El modelo base puede obtener una accuracy aparentemente elevada debido al desbalance de clases, pero no identifica adecuadamente los documentos relevantes.

### Mejora 1 — Balanceo de clases

Se calculan pesos de clase y se aplican mediante `sample_weight` durante el entrenamiento.

En el dataset sample, esta estrategia no fue suficiente para mejorar el F1 de la clase relevante.

### Mejora 2 — Feature Engineering

Se incorporan características explícitas de la relación pregunta-documento:

- similitud coseno TF-IDF;
- solapamiento de términos;
- relación de longitud;
- coincidencia de términos técnicos (`technical_overlap`).

El modelo de esta etapa utiliza `LogisticRegression` con clases balanceadas.

## Resultados de referencia

Sobre el conjunto sample utilizado en la actividad se obtuvieron los siguientes resultados:

| Modelo | Accuracy | Precision | Recall | F1 |
|---|---:|---:|---:|---:|
| Modelo base | 0.8750 | 0.0000 | 0.0000 | 0.0000 |
| Balanceo de clases | 0.5000 | 0.0000 | 0.0000 | 0.0000 |
| Feature Engineering | 0.8125 | 0.4000 | 1.0000 | 0.5714 |

La matriz de confusión del modelo con Feature Engineering fue:

```text
TN = 11
FP = 3
FN = 0
TP = 2
```

> El `Recall = 1.00` debe interpretarse con cautela porque validation contiene únicamente **2 ejemplos positivos**. Significa 2 de 2 positivos detectados, no desempeño operacional del sistema.

## Diagnóstico

Los resultados no muestran un patrón clásico de **overfitting**. La evidencia apunta principalmente a:

- fuerte desbalance de clases;
- reducido tamaño del dataset;
- alta variabilidad del conjunto de validation;
- representación insuficiente de la relación pregunta-documento en el modelo base.

El **Feature Engineering** fue la estrategia que produjo la mejora más significativa.

## Curvas y visualizaciones

Al ejecutar el notebook, los gráficos se almacenan automáticamente en:

```text
outputs/figures/
```

Las figuras se guardan a **300 DPI** e incluyen títulos, etiquetas de ejes, leyendas, grid y anotaciones en puntos críticos cuando corresponde.

Se generan:

1. Training vs Validation Loss.
2. Training vs Validation Accuracy.
3. Precision, Recall y F1 del modelo base.
4. Matriz de confusión del Feature Engineering.
5. Learning Curve por tamaño de dataset.
6. Validation Curve para el hiperparámetro `alpha`.
7. Comparación final del F1 entre estrategias.

## Código modular

El archivo:

```text
src/overfitting_utils.py
```

contiene funciones reutilizables para:

- construir pares pregunta-documento;
- dividir por `qa_id` sin data leakage;
- aplicar aumentación solo sobre training;
- entrenar un `SGDClassifier` con tracking de métricas;
- aplicar balanceo de clases;
- calcular features de similitud;
- obtener métricas de clasificación.

## Consideraciones para el Asistente RAG real

Este experimento se realizó sobre datasets sample y no constituye una evaluación operacional del Asistente DINDES.

En la implementación RAG real debe evitarse ajustar repetidamente parámetros como:

- chunking;
- Top-K;
- pesos dense/BM25;
- reranking;

sobre el mismo conjunto QA utilizado para reportar métricas finales.

Se recomienda separar:

```text
Desarrollo / validación
        ↓
Ajuste de parámetros
        ↓
Conjunto de prueba final independiente
```

Esto permitirá evaluar de forma más confiable la capacidad de generalización del sistema.
