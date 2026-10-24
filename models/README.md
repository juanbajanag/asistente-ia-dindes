# Modelos

El proyecto utiliza una arquitectura RAG y **no requiere publicar un modelo entrenado principal en formato `.pkl`**.

## Runtime local

La versión local puede utilizar modelos Qwen y embeddings instalados localmente. Los pesos no se versionan en GitHub por:
- tamaño;
- reproducibilidad del repositorio;
- licencias y condiciones del proveedor;
- seguridad operacional.

`.gitignore` excluye formatos pesados como `.gguf`, `.safetensors` y otros pesos locales.

## Modelo auxiliar académico

El diagnóstico de overfitting/underfitting usa un clasificador auxiliar pregunta-documento. Su objetivo es estudiar representación, desbalance y generalización; no sustituye el pipeline RAG final.

## Reproducción

Los experimentos están en:
- `notebooks/03_modelado.ipynb`
- `notebooks/04_optimizacion.ipynb`
- `notebooks/05_evaluacion.ipynb`

No se publican pesos artificiales solo para satisfacer una estructura típica de ML; la ausencia de `best_model.pkl` es deliberada y coherente con la arquitectura del proyecto.
