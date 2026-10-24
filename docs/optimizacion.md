# Optimización del sistema

## 1. Alcance

La optimización se adaptó a la naturaleza del proyecto. El sistema final es RAG y no entrena de extremo a extremo el LLM con documentos institucionales. Por ello se evaluaron:

1. un clasificador auxiliar pregunta-documento para diagnosticar generalización;
2. sensibilidad de hiperparámetros de dicho clasificador;
3. representación mediante feature engineering;
4. parámetros de recuperación y políticas de evidencia del RAG;
5. estabilidad del runtime cloud.

## 2. Línea base

El clasificador auxiliar utiliza:

```text
Pregunta + documento
        ↓
TF-IDF
        ↓
SGDClassifier(log_loss)
        ↓
Relevante / No relevante
```

El dataset original de pares presentó:
- 42 negativos;
- 6 positivos;
- 87,5 % clase 0;
- 12,5 % clase 1.

## 3. Prevención de leakage

El split se realiza por `qa_id` **antes** de la aumentación. Solo training se aumenta.

Esto evita que variantes de una misma pregunta aparezcan simultáneamente en entrenamiento y validación.

## 4. Métricas

Se analizaron:
- Training Loss;
- Validation Loss;
- Accuracy;
- Precision;
- Recall;
- F1;
- matriz de confusión;
- learning curve;
- validation curve.

## 5. Diagnóstico

El modelo base alcanzó accuracy elevada, pero:
- Precision = 0;
- Recall = 0;
- F1 = 0.

La accuracy resultó engañosa por el desbalance. El patrón observado no correspondió a un overfitting clásico; predominó la insuficiencia de representación y la escasez de positivos.

## 6. Estrategia 1 — balanceo de clases

Se aplicaron pesos balanceados con `sample_weight`.

Resultado:
- la estrategia no recuperó correctamente la clase positiva;
- F1 permaneció en 0.

Conclusión: el desbalance era real, pero no era la única causa.

## 7. Estrategia 2 — Feature Engineering

Se incorporaron:
- similitud coseno;
- overlap de tokens;
- relación de longitudes;
- overlap técnico.

Se utilizó `StandardScaler` + `LogisticRegression(class_weight="balanced")`.

| Métrica | Resultado |
|---|---:|
| Accuracy | 0,8125 |
| Precision | 0,4000 |
| Recall | 1,0000 |
| F1 | 0,5714 |

Matriz de confusión:
- TN = 11
- FP = 3
- FN = 0
- TP = 2

La validación tiene únicamente dos positivos, por lo que el Recall = 1,00 significa literalmente 2/2 y debe interpretarse con cautela.

## 8. Sensibilidad de hiperparámetros

La validation curve del modelo base evaluó `alpha` del SGDClassifier en un rango de `10^-5` a `10^-1`.

El F1 de validación permaneció en 0, mostrando que modificar solo la regularización no resolvía la limitación principal.

El notebook `04_optimizacion.ipynb` complementa esta evidencia con:
- sensibilidad de regularización;
- importancia por permutación del modelo con features;
- partial dependence de features numéricas;
- comparación antes/después.

## 9. Partial dependence e importancia

En este proyecto estos análisis se aplican al **clasificador auxiliar con features numéricas**, no al LLM.

La razón es metodológica: el LLM local no se entrena con hiperparámetros supervisados dentro del proyecto. El análisis interpretable se realiza sobre el componente experimental que sí posee features y parámetros controlables.

Los gráficos se generan reproduciblemente desde `notebooks/04_optimizacion.ipynb`.

## 10. Interacciones

Las interacciones se estudian sobre combinaciones de:
- similitud coseno;
- overlap;
- relación de longitudes.

El objetivo es comprobar si una sola feature explica el desempeño o si la discriminación depende de combinaciones.

## 11. Comparación antes/después

| Modelo | Accuracy | Precision | Recall | F1 |
|---|---:|---:|---:|---:|
| Base | 0,8750 | 0,0000 | 0,0000 | 0,0000 |
| Balanceado | 0,5000 | 0,0000 | 0,0000 | 0,0000 |
| Feature Engineering | 0,8125 | 0,4000 | 1,0000 | 0,5714 |

La mejora principal provino de enriquecer la representación pregunta-documento.

## 12. Optimización del RAG

Para evitar sobreajuste al QA set, parámetros como:
- chunking;
- Top-K;
- pesos de recuperación;
- reranking;
- umbral;
- temperature;

deben ajustarse en desarrollo/validación y comprobarse luego en un conjunto independiente.

La configuración cloud final se mantuvo conservadora:
- Top-K = 5;
- threshold = 0,45;
- temperature = 0,0.

Temperature = 0,0 fue elegida por reproducibilidad en la demo cloud.

## 13. Estabilidad cloud

En pruebas repetidas:
- temperature 0,0 produjo respuesta dominante 100 %;
- mantuvo orden de fuentes estable;
- redujo variabilidad respecto a temperature 0,2.

La política final prioriza reproducibilidad y abstención segura.

## 14. Resultado final

La optimización no consistió en “entrenar más” un LLM. El principal avance fue:

```text
representación más informativa
+ recuperación controlada
+ ruta estructurada determinística
+ evidencia visible
+ abstención
+ runtime cloud reproducible
```

Esta estrategia es coherente con el objetivo del asistente: responder con evidencia y reducir respuestas no sustentadas.
