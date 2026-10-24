# Checklist final — GitHub + Streamlit Community Cloud

## Antes de GitHub

- [ ] `python scripts/run_phase13_4.py` termina en OK.
- [ ] `python scripts/prepare_cloud_deploy.py` termina en OK.
- [ ] `requirements.txt.cloud` revisado.
- [ ] No hay `.env`.
- [ ] No hay `.streamlit/secrets.toml`.
- [ ] No hay modelos `.gguf`, `.safetensors`, `.bin`.
- [ ] No hay documentos institucionales sensibles.
- [ ] Solo datos sintéticos, públicos, anonimizados o autorizados.

## Configuración esperada

### Local

```text
temperature = 0.2
top_k = 5
dense_min_score = 0.45
```

### Cloud

```text
temperature = 0.0
top_k = 5
dense_min_score = 0.45
```

## Preparar requirements para rama cloud

```powershell
Copy-Item requirements.txt requirements-local.txt
Copy-Item requirements.txt.cloud requirements.txt
```

## Git

```powershell
git status
git add .
git commit -m "Fase 13.4 - Cloud demo final"
git push
```

## Streamlit Community Cloud

- Main file: `streamlit_app.py`
- Rama: la rama cloud o `main`.
- Confirmar que la URL pública carga.
- Probar en ventana incógnito.

## Pruebas mínimas

1. Consulta estructurada.
2. Consulta de reposición.
3. Consulta RAG.
4. Consulta no respondible / abstención.
5. Inventario.
6. Historial/Auditoría si se publican en la demo.

## Evidencia para profesora

- URL pública.
- Fecha de prueba.
- Captura de pantalla.
- Commit desplegado.
- Limitaciones cloud documentadas.
