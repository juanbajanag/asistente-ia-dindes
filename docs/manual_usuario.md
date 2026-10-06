# Manual de usuario

## 1. Propósito

Este documento describe el uso previsto de la aplicación web del proyecto **Asistente de IA para Innovación, Desarrollo y Gestión del Conocimiento Técnico — DINDES**.

> **Estado actual:** la interfaz Streamlit todavía se encuentra en desarrollo. Este manual define el flujo esperado y deberá actualizarse con capturas reales cuando la aplicación esté implementada.

## 2. Requisitos

- Windows 10/11.
- Python.
- Entorno virtual del proyecto.
- Dependencias instaladas.
- Modelo local disponible.
- Índice documental generado.

## 3. Iniciar la aplicación

Desde la raíz del proyecto:

```powershell
.\.venv\Scripts\Activate.ps1
```

Luego:

```powershell
streamlit run app/app.py
```

La aplicación debería abrirse en:

```text
http://localhost:8501
```

> Este comando deberá validarse cuando `app/app.py` esté implementado.

## 4. Pantalla principal prevista

La interfaz incluirá:

1. Título.
2. Campo de consulta.
3. Botón **Consultar**.
4. Ejemplos precargados.
5. Área de respuesta.
6. Fuentes utilizadas.
7. Scores de relevancia.
8. Sección **Acerca de**.
9. Métricas y limitaciones.
10. Mensajes de error o advertencia.

## 5. Realizar una consulta

### Paso 1
Escribir una pregunta.

### Paso 2
Presionar **Consultar**.

### Paso 3
El sistema procesará:

```text
Pregunta
→ retrieval
→ recuperación híbrida
→ reranking
→ selección de fuentes
→ Qwen local
→ respuesta
```

### Paso 4
Revisar respuesta, fuentes, fragmentos recuperados, relevancia y advertencias.

## 6. Interpretación de resultados

El usuario deberá verificar:

- título del documento;
- sección;
- fecha;
- versión;
- estado de la fuente.

Cuando la evidencia sea insuficiente, el sistema deberá indicarlo explícitamente.

## 7. Ejemplos de uso

La versión final incluirá ejemplos precargados de:

- documentación técnica;
- inventario;
- proyectos;
- procedimientos;
- antecedentes.

## 8. Consulta sin evidencia

Mensaje esperado:

> No se encontró evidencia suficiente en las fuentes disponibles para responder esta consulta.

El sistema no debe inventar una respuesta.

## 9. Errores frecuentes

### La aplicación no inicia

```powershell
pip install -r requirements.txt
```

y:

```powershell
streamlit --version
```

### No se encuentra el modelo

Verificar la configuración local.

### No se encuentra el índice

Verificar que el pipeline de ingesta haya sido ejecutado.

## 10. Troubleshooting

| Problema | Acción recomendada |
|---|---|
| `ModuleNotFoundError` | Instalar `requirements.txt` |
| Streamlit no reconocido | Instalar Streamlit en `.venv` |
| Puerto 8501 ocupado | Ejecutar con otro puerto |
| Modelo no carga | Revisar ruta y memoria |
| Índice vacío | Ejecutar ingesta |
| Respuesta sin fuentes | No utilizarla; revisar retrieval |
| Consulta muy amplia | Reformular |

Ejemplo para otro puerto:

```powershell
streamlit run app/app.py --server.port 8502
```

## 11. Buenas prácticas

- formular preguntas específicas;
- revisar fuentes;
- verificar información crítica;
- no ingresar información no autorizada;
- no compartir resultados sensibles;
- reportar errores.

## 12. Limitaciones

La versión MVP:

- trabaja con corpus limitado;
- puede no responder fuera del corpus;
- puede recuperar fuentes incorrectas;
- puede producir errores de generación;
- no sustituye especialistas.

## 13. Seguridad

No ingresar contraseñas, claves, tokens, información clasificada no autorizada o datos personales innecesarios.

## 14. Sección Acerca de

La app deberá mostrar:

- objetivo;
- arquitectura RAG;
- modelo;
- métricas;
- limitaciones;
- versión;
- equipo desarrollador.

## 15. Capturas de pantalla

**Pendiente.**

Cuando la interfaz esté implementada se incorporarán capturas anotadas de:

1. pantalla principal;
2. consulta;
3. respuesta;
4. fuentes;
5. ejemplo precargado;
6. error controlado.

## 16. FAQ

### ¿El asistente conoce todo lo que existe en DINDES?
No. Solo puede utilizar las fuentes cargadas y autorizadas.

### ¿Puede equivocarse?
Sí. Por eso deben revisarse las fuentes.

### ¿El modelo fue entrenado con los documentos?
El MVP utiliza RAG. Los documentos se recuperan y entregan como contexto al modelo; no se plantea fine-tuning del LLM como estrategia principal.

### ¿Necesita Internet?
El objetivo es operar localmente. Algunas tareas de instalación pueden requerir Internet.

### ¿Puedo cargar cualquier documento?
No. Solo documentos autorizados.

### ¿Qué ocurre si no existe información?
El sistema deberá abstenerse y comunicar que no dispone de evidencia suficiente.

## 17. Soporte

Responsables académicos:

- Juan Carlos Bajaña Gutiérrez
- José Luis Peñafiel Fernández

## 18. Pendientes antes de la entrega final

- validar comandos reales;
- incorporar capturas;
- completar ejemplos;
- documentar errores reales;
- agregar instrucciones de carga de documentos;
- actualizar FAQ;
- incorporar métricas finales.
