# Fase 13 — Despliegue Cloud del Asistente IA DINDES

## Objetivo

Publicar una versión académica y demostrativa del MVP mediante una URL accesible por la profesora.

La versión cloud NO sustituye el MVP local institucional.

## Arquitectura

```text
MVP LOCAL
├── Streamlit
├── RAG
├── consultas estructuradas
└── Qwen local / hardware institucional

MVP CLOUD DEMO
├── Streamlit Community Cloud
├── RAG / consultas estructuradas
├── datos sintéticos o autorizados
└── generación ligera basada en evidencia
```

## Principio de seguridad

NO publicar:

- documentos institucionales reales;
- información clasificada o reservada;
- credenciales;
- claves API;
- archivos `.env`;
- pesos del modelo local;
- información personal;
- datos operacionales no autorizados.

La versión pública debe contener exclusivamente datos sintéticos, anonimizados, públicos o expresamente autorizados.

---

## Paso 1 — Copiar los archivos

Descomprima el paquete en la raíz:

```text
C:\Proyectos\Asistente_IA
```

Debe aparecer, entre otros:

```text
streamlit_app.py
requirements-cloud.txt
.streamlit/config.toml
config/cloud_config.json
src/cloud_runtime.py
scripts/test_cloud_readiness.py
```

---

## Paso 2 — Validar preparación

Con `.venv` activado:

```powershell
python scripts/prepare_cloud_deploy.py
```

Si todo es correcto debe terminar con:

```text
FASE 13 — PREPARACIÓN CLOUD: OK
```

Si `check_public_data.py` detecta columnas potencialmente sensibles, deténgase y revise manualmente el archivo.

---

## Paso 3 — Dependencias cloud

El script genera:

```text
requirements.txt.cloud
```

Revíselo.

Para una rama de despliegue cloud, la opción más simple es:

```powershell
Copy-Item requirements.txt requirements-local.txt
Copy-Item requirements.txt.cloud requirements.txt
```

No borre el respaldo local.

La lista cloud excluye paquetes pesados conocidos del entorno local, por ejemplo:

- torch
- vllm
- llama-cpp-python
- bitsandbytes
- flash-attn

Si su aplicación importa alguno de ellos incondicionalmente, deberá convertir ese import en opcional para cloud.

---

## Paso 4 — GitHub

Cree un repositorio privado o público según las reglas de la universidad.

Antes del primer commit:

```powershell
git status
```

Verifique que NO aparezcan:

```text
.env
.streamlit/secrets.toml
models/
*.gguf
*.safetensors
```

Luego:

```powershell
git add .
git commit -m "Fase 13 - Cloud demo para evaluacion academica"
git branch -M main
git remote add origin <URL_DEL_REPOSITORIO>
git push -u origin main
```

Si el repositorio ya existe, solo haga commit y push.

---

## Paso 5 — Streamlit Community Cloud

1. Ingrese a Streamlit Community Cloud.
2. Inicie sesión y conecte GitHub.
3. Seleccione **Create app / Deploy an app**.
4. Seleccione el repositorio.
5. Rama: `main` o la rama cloud que haya creado.
6. Main file path:

```text
streamlit_app.py
```

7. Despliegue.

La aplicación obtendrá una URL similar a:

```text
https://<nombre-app>.streamlit.app
```

---

## Paso 6 — Validación remota

Desde una ventana de incógnito pruebe:

### Consulta estructurada

```text
¿Cuál es el stock del taladro DEWALT modelo DWD024-B3?
```

### Reposición

```text
¿Qué herramientas requieren reposición?
```

### RAG

```text
¿Qué documento contiene información sobre el inventario de bodega?
```

### Abstención

Use una pregunta claramente fuera de las fuentes disponibles y confirme que no inventa una respuesta.

---

## Paso 7 — Evidencia para la profesora

Registre:

- URL pública.
- Fecha de despliegue.
- Commit de GitHub.
- Captura de pantalla.
- Resultado de las cuatro pruebas anteriores.
- Limitaciones de la versión cloud.

---

## Importante sobre el LLM

`streamlit_app.py` activa:

```text
DINDES_RUNTIME=cloud
DINDES_DISABLE_LOCAL_LLM=1
```

Esto evita intentar cargar el Qwen local pesado.

El archivo:

```text
src/cloud_runtime.py
```

incluye un `EvidenceExtractGenerator` ligero para responder únicamente desde evidencia recuperada.

### Integración

Si el pipeline actual intenta cargar siempre Qwen, agregue en el punto donde se construye el generador:

```python
from src.cloud_runtime import is_cloud_runtime, get_cloud_generator

if is_cloud_runtime():
    generator = get_cloud_generator()
else:
    generator = generador_qwen_actual
```

No modifique el retrieval ni las consultas estructuradas.

---

## Banner de la demo

Opcionalmente en `app/app.py`:

```python
from cloud_demo.banner import render_cloud_banner

render_cloud_banner()
```

Esto mostrará que la URL corresponde a una versión académica Cloud Demo y evitará confundirla con el despliegue institucional.

---

## Criterio de cumplimiento

La instrucción de evaluación remota se considera cumplida cuando:

1. La aplicación está alojada en un servidor cloud.
2. Existe una URL pública activa.
3. La profesora puede abrirla sin acceder a la PC local.
4. Puede interactuar con la aplicación.
5. El sistema usa únicamente datos aptos para publicación.
