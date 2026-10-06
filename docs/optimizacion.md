# Optimización del sistema

## 1. Propósito

Este documento registra el proceso de optimización del proyecto **Asistente de IA para Innovación, Desarrollo y Gestión del Conocimiento Técnico — DINDES**.

La optimización se desarrolla de forma progresiva y comprende diagnóstico del comportamiento de modelos auxiliares, análisis de desbalance, selección de features, evaluación de hiperparámetros, comparación antes/después y optimización futura de retrieval, reranking y generación.

> **Importante:** la actividad de Semana 3 aporta evidencia experimental útil, pero el instructivo final exige además el contenido específico del **Workshop S5**: análisis de sensibilidad, partial dependence plots, ranking de importancia de hiperparámetros, interacciones y configuración final. Esos apartados quedan marcados como **pendientes** hasta contar con resultados reales del Workshop S5.

## 2. Línea base analizada

Para estudiar overfitting/underfitting se implementó un clasificador auxiliar de relevancia **pregunta-documento**.

```text
Pregunta + documento
        ↓
TF-IDF
        ↓
SGDClassifier (log_loss)
        ↓
Relevante / No relevante
```

## 3. Problema identificado

El dataset de pares pregunta-documento presentó fuerte desbalance:

- 42 pares no relevantes.
- 6 pares relevantes.
- 87,5 % clase 0.
- 12,5 % clase 1.

El modelo base alcanzó una accuracy aparentemente aceptable, pero con `Precision = 0`, `Recall = 0` y `F1 = 0`. Por ello, la accuracy no se utilizó como única métrica.

## 4. Control de data leakage

La corrección metodológica principal fue realizar el split por `qa_id` antes de la aumentación:

```text
Pares originales
      ↓
Split por qa_id
   ↙          ↘
Train       Validation
   ↓
Aumentación
solo Train
```

Esto evita que variantes de una misma pregunta aparezcan simultáneamente en training y validation.

## 5. Tracking de métricas

Durante el entrenamiento se registraron:

- Training Loss.
- Validation Loss.
- Training Accuracy.
- Validation Accuracy.
- Precision.
- Recall.
- F1.

También se generaron Training vs Validation Loss, Training vs Validation Accuracy, Precision/Recall/F1 por época, Learning Curve y Validation Curve.

## 6. Estrategia 1 — Balanceo de clases

Se utilizaron pesos balanceados mediante `sample_weight`.

Pesos de referencia:

- clase 0: 0,5714.
- clase 1: 4,0000.

Resultado: no se logró recuperar correctamente la clase relevante y `F1 = 0`.

**Interpretación:** el desbalance era un problema real, pero no era la única limitación.

## 7. Estrategia 2 — Feature Engineering

Se incorporaron:

1. `cosine_similarity`
2. `overlap_ratio`
3. `length_ratio`
4. `technical_overlap`

Modelo:

```text
Features de similitud
        ↓
StandardScaler
        ↓
LogisticRegression
class_weight = balanced
```

Resultados de referencia:

| Métrica | Resultado |
|---|---:|
| Accuracy | 0,8125 |
| Precision | 0,4000 |
| Recall | 1,0000 |
| F1 | 0,5714 |

Matriz de confusión:

```text
TN = 11
FP = 3
FN = 0
TP = 2
```

El `Recall = 1,00` debe interpretarse con cautela porque validation contiene únicamente **2 ejemplos positivos**.

## 8. Early stopping

Se analizó como estrategia complementaria usando el mínimo de Validation Loss. Permitió identificar el punto de menor pérdida, pero no corrigió la incapacidad del modelo balanceado para identificar positivos.

## 9. Learning Curve

Se implementó `learning_curve` de Scikit-learn con `GroupKFold` agrupado por `qa_id`.

Hallazgo: el F1 de validation permaneció en 0 en los tamaños de entrenamiento evaluados.

## 10. Validation Curve

Se evaluó `alpha` del `SGDClassifier` en el rango:

```text
10^-5 → 10^-1
```

El F1 de validation permaneció en 0, por lo que ajustar únicamente la regularización no resolvió el problema del modelo base.

## 11. Comparación antes/después

| Modelo | Accuracy | Precision | Recall | F1 |
|---|---:|---:|---:|---:|
| Modelo base | 0,8750 | 0,0000 | 0,0000 | 0,0000 |
| Balanceo de clases | 0,5000 | 0,0000 | 0,0000 | 0,0000 |
| Feature Engineering | 0,8125 | 0,4000 | 1,0000 | 0,5714 |

La mejora cuantificable principal provino de **Feature Engineering**.

## 12. Diagnóstico actual

No se observó un patrón clásico de overfitting. La evidencia apunta principalmente a:

- desbalance de clases;
- muestra pequeña;
- alta variabilidad estadística;
- representación insuficiente de la relación pregunta-documento;
- necesidad de ampliar el dataset QA.

## 13. Optimización futura del RAG

Se evaluarán experimentalmente:

- tamaño de chunk;
- overlap;
- Top-K dense;
- Top-K BM25;
- pesos dense/BM25;
- modelo de embeddings;
- Top-N de entrada al reranker;
- Top-K final;
- umbral de relevancia;
- temperature;
- max tokens;
- estructura del prompt.

## 14. Workshop S5 — Pendiente

El instructivo final exige completar con resultados reales:

- hiperparámetros explorados y rangos;
- análisis de sensibilidad;
- partial dependence plots;
- ranking de importancia de hiperparámetros;
- análisis de interacciones;
- configuración final seleccionada;
- comparación antes/después de la optimización.

Estos apartados no deben completarse con valores inventados.

## 15. Criterios de selección final

La configuración final se evaluará mediante:

- Precision@K;
- Recall@K;
- F1;
- Grounded Response Rate;
- latencia;
- estabilidad;
- costo computacional;
- consumo de memoria.

## 16. Riesgo de sobreajuste al QA set

No se deberán ajustar repetidamente chunking, Top-K, pesos dense/BM25, reranking o thresholds sobre el mismo conjunto usado para reportar resultados finales.

```text
Development
    ↓
Tuning
    ↓
Validation
    ↓
Test final independiente
```

## 17. Conclusión

La optimización realizada hasta el momento demuestra que mejorar la representación de la relación pregunta-documento genera más impacto que ajustar únicamente pesos o regularización. La siguiente etapa deberá trasladar estos aprendizajes al pipeline RAG y completar el análisis específico del Workshop S5.
