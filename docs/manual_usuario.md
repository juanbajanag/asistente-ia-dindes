# Manual de usuario

## 1. Propósito

Este manual describe el uso de la aplicación **Asistente IA DINDES**, implementada en Streamlit.

El sistema es una herramienta de apoyo para consulta, recuperación y gestión del conocimiento. **Informa y apoya; no decide.**

## 2. Versiones disponibles

### Versión local/on-premise

Ejecuta la aplicación principal desde:

```powershell
streamlit run app/app.py
```

Puede utilizar el runtime local y, cuando esté disponible, modelos instalados en el equipo.

### Versión cloud académica

Se creó una versión específica para evaluación remota en Streamlit Community Cloud:

```powershell
streamlit run streamlit_app.py
```

El entrypoint cloud activa un backend ligero que no depende de Ollama ni de pesos locales. Está destinado a demostración con datos sintéticos/autorizados.

## 3. Acceso

La aplicación incorpora autenticación y permisos por rol. Las credenciales no deben almacenarse en el repositorio; deben configurarse mediante secretos de Streamlit o mecanismos equivalentes.

## 4. Consulta general

1. Ingrese al sistema.
2. Abra la pestaña **Consulta**.
3. Seleccione un ejemplo o escriba una pregunta.
4. Presione **Consultar**.
5. Revise la respuesta.
6. Revise siempre **Fuentes y evidencias**.

## 5. Modos de respuesta

### Estructurado

Se utiliza para consultas tabulares determinísticas, por ejemplo:

```text
¿Cuál es el stock del taladro DEWALT modelo DWD024-B3?
```

El resultado se obtiene directamente de registros estructurados y puede mostrarse en tabla.

### RAG

Se utiliza cuando la consulta requiere recuperación documental o semántica.

Ejemplo:

```text
¿Qué componentes principales integra la arquitectura del Simulador Táctico Submarino?
```

La respuesta incorpora referencias `[F1]`, `[F2]`, etc.

### Abstención

Cuando no existe evidencia suficiente, el sistema debe indicar explícitamente que no puede responder.

Ejemplo:

```text
¿Cuál es el número de serie del generador principal de la fragata inexistente?
```

La abstención no es un error; es un control de seguridad.

## 6. Inventario

La pestaña **Inventario** permite:
- visualizar indicadores;
- filtrar registros;
- buscar por descripción, marca, modelo o ítem;
- revisar criticidad;
- analizar reposición;
- exportar resultados cuando corresponde.

La criticidad institucional no debe inferirse automáticamente: debe ser definida por personal autorizado.

## 7. Historial y auditoría

Según el rol, el usuario puede consultar:
- historial;
- eventos de auditoría;
- evaluaciones;
- trazabilidad de operaciones.

## 8. Documentos

Los usuarios autorizados pueden gestionar documentos conforme a los permisos configurados.

## 9. Evaluación de respuestas

Después de una consulta, el usuario puede registrar:
- correcta / útil;
- incorrecta / incompleta;
- comentario opcional.

Esto permite recopilar evidencia para mejora posterior.

## 10. Ejemplos recomendados

```text
¿Cuál es el stock del taladro DEWALT modelo DWD024-B3?

¿Cuántas impresoras 3D Creality K1 están disponibles?

¿Qué componentes principales integra la arquitectura del Simulador Táctico Submarino?

¿Cuál es el número de serie del generador principal de la fragata inexistente?
```

## 11. Verificación humana

Antes de utilizar una respuesta en una decisión relevante:
1. revise la fuente;
2. confirme vigencia y versión;
3. confirme que el contexto corresponde al caso;
4. consulte al especialista responsable cuando aplique.

## 12. Troubleshooting

| Problema | Acción |
|---|---|
| `ModuleNotFoundError` | `pip install -r requirements.txt` |
| Streamlit no inicia | verificar `.venv` y ejecutar `python -m streamlit run app/app.py` |
| No abre navegador automáticamente | abrir manualmente `http://localhost:8501` |
| No hay evidencia | reformular o verificar que la fuente exista |
| Abstención | comportamiento esperado si no hay evidencia suficiente |
| Error cloud | revisar logs de Streamlit y dependencias públicas |
| Login falla | revisar configuración de secretos/usuarios |

## 13. Seguridad

No ingrese ni publique:
- contraseñas;
- tokens;
- claves;
- información clasificada no autorizada;
- datos personales innecesarios.

## 14. Limitaciones

- El corpus público es sintético y pequeño.
- La versión cloud está optimizada para demostración.
- El sistema puede recuperar evidencia parcial.
- Una respuesta no sustituye revisión humana.
- Las métricas académicas no equivalen a desempeño operacional.

## 15. Soporte académico

Para reproducción técnica consulte:
- `README.md`
- `docs/arquitectura.md`
- `docs/analisis_datos.md`
- `docs/optimizacion.md`
- `docs/consideraciones_eticas.md`
