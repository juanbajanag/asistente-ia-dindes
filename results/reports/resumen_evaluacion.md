# Resumen de evaluación final

## Clasificador auxiliar pregunta-documento

| Modelo | Accuracy | Precision | Recall | F1 |
|---|---:|---:|---:|---:|
| Modelo base | 0.8750 | 0.0000 | 0.0000 | 0.0000 |
| Balanceo de clases | 0.5000 | 0.0000 | 0.0000 | 0.0000 |
| Feature Engineering | 0.8125 | 0.4000 | 1.0000 | 0.5714 |

La accuracy del modelo base resulta engañosa debido al fuerte desbalance. La mejora principal se obtiene mediante feature engineering. La validación contiene solo dos positivos, por lo que Recall = 1.00 significa 2/2 y no debe interpretarse como desempeño operacional.

## Validación funcional del MVP

- DEWALT DWD024-B3: respuesta estructurada, stock = 1.
- Creality K1: RAG cuantitativo, cantidad = 1, estado Operativo.
- Simulador Táctico Submarino: RAG documental con fuente.
- Fragata inexistente: abstención en retrieval.

## Configuración cloud validada

- Top-K = 5
- Umbral = 0.45
- Temperatura = 0.0

Los datos públicos son sintéticos y académicos.
