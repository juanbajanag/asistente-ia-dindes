# Fase 10 — Consolidación del MVP

El MVP consolida:

1. Ingesta documental local.
2. RAG con evidencia y fuentes.
3. Consultas estructuradas determinísticas.
4. Dashboard de inventario.
5. Calidad de datos.
6. Criticidad operativa definida por personal autorizado.
7. Gestión de reposición.
8. Priorización operativa.
9. Seguimiento de decisiones.
10. Auditoría y trazabilidad.

## Archivos persistentes protegidos

- `config/inventory_criticality.csv`
- `config/replenishment_decisions.csv`
- `config/replenishment_decision_audit.csv`

## Validación

```powershell
python scripts/validar_mvp.py
```

Resultado esperado:

```text
FASE 10 — VALIDACIÓN INTEGRAL: OK
```

## Respaldo

```powershell
python scripts/backup_mvp.py
```

Se genera una carpeta en `backups/` con `manifest.json` y hash SHA-256.

## Ejecución

```powershell
streamlit run app/app.py
```
