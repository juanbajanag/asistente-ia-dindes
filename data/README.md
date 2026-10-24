# Datos del proyecto

El repositorio público utiliza únicamente **datos sintéticos y académicos** para demostrar el funcionamiento del Asistente IA DINDES sin publicar información institucional sensible.

## Archivos principales

### Dataset 1 — Documentación técnica
`Dataset_1_Documentacion_Tecnica_DINDES_Sample.csv`

Contiene fragmentos documentales sintéticos con identificadores, proyecto, tipo documental, título, fecha, versión, sección, texto, vigencia y nivel de acceso.

### Dataset 2 — Inventario institucional sample
`Dataset_2_Inventario_Institucional_DINDES_Sample.csv`

Contiene registros sintéticos de equipos y materiales usados para probar consultas de inventario.

### Dataset 3 — Evaluación QA
`Dataset_3_Evaluacion_QA_Asistente_IA_Sample.csv`

Contiene preguntas de prueba, fuente esperada, respuesta esperada, dificultad y condición de respondibilidad.

## Estructura requerida

- `raw/`: reservado para datos originales públicos/sintéticos.
- `processed/`: reservado para derivados reproducibles.
- Los CSV sample se mantienen en `data/` porque el código actual los consume directamente desde esa ubicación.

Moverlos sin actualizar el pipeline rompería compatibilidad, por lo que se conserva la ruta estable y se documenta esta decisión.

## Privacidad

No se deben añadir al repositorio:
- documentos clasificados;
- credenciales;
- información personal innecesaria;
- documentación institucional sin autorización.

## Reproducibilidad

Los notebooks y scripts leen estos datos mediante rutas relativas desde la raíz del proyecto.
