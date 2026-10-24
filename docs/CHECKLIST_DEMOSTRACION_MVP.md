# Checklist de demostración — Asistente IA DINDES

## Inicio
- [ ] Activar `.venv`.
- [ ] Ejecutar `python scripts/validar_mvp.py`.
- [ ] Confirmar `FASE 10 — VALIDACIÓN INTEGRAL: OK`.
- [ ] Ejecutar `streamlit run app/app.py`.

## Consulta / RAG
- [ ] Hacer una consulta documental.
- [ ] Confirmar fuentes visibles.
- [ ] Confirmar abstención cuando no exista evidencia suficiente.

## Consultas estructuradas
- [ ] Consultar stock de un modelo exacto.
- [ ] Consultar artículos con stock cero.
- [ ] Descargar CSV.

## Inventario
- [ ] Revisar KPIs.
- [ ] Filtrar por marca/estado/calidad.
- [ ] Revisar gráficos y alertas.

## Calidad
- [ ] Revisar observaciones de calidad.
- [ ] Revisar duplicados potenciales.

## Criticidad operativa
- [ ] Mostrar catálogo de criticidad.
- [ ] Confirmar que la app no infiere criticidad automáticamente.

## Reposición y priorización
- [ ] Mostrar propuesta de reposición.
- [ ] Mostrar matriz de prioridad operativa.
- [ ] Mostrar ranking consolidado.

## Seguimiento
- [ ] Mostrar estados de gestión.
- [ ] Mostrar responsable y observación.

## Auditoría
- [ ] Filtrar por fecha.
- [ ] Filtrar por transición.
- [ ] Filtrar por responsable.
- [ ] Descargar CSV de auditoría.

## Cierre
- [ ] Explicar operación local/on-premise.
- [ ] Explicar separación entre RAG y lógica determinística.
- [ ] Explicar responsabilidad humana.
- [ ] Ejecutar `python scripts/backup_mvp.py` si hubo cambios.
