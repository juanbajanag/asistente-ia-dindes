# Banco de regresión cloud — Fase 14.4

Configuración esperada:

- Threshold: 0.45
- Top-K: 5
- Temperatura cloud: 0.0

| # | Pregunta | Resultado esperado |
|---:|---|---|
| 1 | ¿Cuál es el stock del taladro DEWALT modelo DWD024-B3? | Structured; stock 1; no abstiene |
| 2 | ¿Cuántos taladros DEWALT DWD024-B3 están disponibles? | Structured; stock 1; no abstiene |
| 3 | ¿Qué información existe del modelo DWD024-B3? | RAG; detalle útil; no abstiene |
| 4 | ¿Cuántas impresoras 3D Creality K1 están disponibles? | RAG; 1 unidad; estado Operativo |
| 5 | ¿Cuál es el estado de la impresora Creality K1? | RAG; estado Operativo |
| 6 | ¿Qué componentes principales integra la arquitectura del Simulador Táctico Submarino? | RAG correcto |
| 7 | ¿Cómo está organizada la arquitectura del Simulador Táctico Submarino? | RAG correcto |
| 8 | ¿Qué componentes del inventario pueden utilizarse para procesamiento de IA? | Debe identificar workstation/GPU/Jetson |
| 9 | ¿Qué documentos se encuentran vigentes? | Debe listar documentos vigentes |
| 10 | ¿Qué información consta en el documento Bienes DINDES para el bien código 2341766? | Coincidencia exacta si el código está presente en el corpus |
| 11 | cual es el stock del taladro dewalt dwd024 b3 | Structured; stock 1 |
| 12 | componentes principales simulador tactico submarino | Limitación conocida; puede abstenerse |
| 13 | creality k1 disponibles | RAG; 1 unidad |
| 14 | ¿Cuál es el número de serie del generador principal de la fragata inexistente? | Abstención |
| 15 | ¿Qué motores utiliza el submarino clase Atlantis X99? | Abstención |
| 16 | ¿Cuántos drones DJI Phantom 99 hay disponibles? | Abstención; nunca debe contar todo el inventario |
| 17 | ¿Quién es el comandante actual de la Armada? | Abstención |
| 18 | ¿Cuál será el precio del dólar mañana? | Abstención |
| 19 | Consulta vacía | Debe mostrar “Ingrese una pregunta” y no dejar visible la respuesta anterior |
| 20 | ¿Qué sabes de todo lo que tiene DINDES? | Abstención prudente |

## Casos críticos de regresión

Los casos 1, 4, 5, 6, 8, 9, 14, 15, 16, 17, 18 y 19 se consideran críticos.

Especialmente:

- **Caso 16:** una entidad inexistente no puede convertirse en un conteo global del inventario.
- **Caso 5:** el estado de Creality K1 debe recuperarse porque el dato existe en la evidencia.
- **Casos 8 y 9:** son ejemplos visibles en la interfaz y deben ser respondibles.
- **Caso 19:** una entrada inválida no debe conservar visualmente la respuesta anterior.

## Limitación conocida

El caso 12:

`componentes principales simulador tactico submarino`

permanece documentado como consulta telegráfica de baja cobertura. No debe corregirse bajando globalmente el threshold, porque eso puede perjudicar la abstención responsable.

## Registro recomendado

Para cada prueba anotar:

| Campo | Valor |
|---|---|
| Pregunta | Texto exacto |
| Modo | Structured / RAG |
| Abstención | Sí / No |
| Fuentes | Cantidad |
| Resultado | PASS / PARCIAL / FAIL |
| Observación | Comentario breve |
