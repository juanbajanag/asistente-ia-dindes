# Asistente IA DINDES — Cloud Demo

Versión académica para evaluación remota.

## Alcance

Esta versión demuestra:

- consultas estructuradas;
- inventario;
- reposición;
- criticidad;
- recuperación documental;
- fuentes;
- abstención;
- trazabilidad disponible en la interfaz.

## Diferencia respecto al entorno local

El despliegue público evita cargar el LLM local pesado. Cuando el runtime cloud está habilitado, puede utilizar una generación ligera y conservadora basada en evidencia.

## Seguridad

Este repositorio público no debe contener información institucional sensible. Use solamente datasets sintéticos, anonimizados, públicos o autorizados.

## Ejecución local del punto de entrada cloud

Windows PowerShell:

```powershell
$env:DINDES_RUNTIME="cloud"
streamlit run streamlit_app.py
```

## Prueba de preparación

```powershell
python scripts/prepare_cloud_deploy.py
```
