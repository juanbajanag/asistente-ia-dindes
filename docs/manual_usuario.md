# Manual de usuario

## 1. Propósito

Este manual describe el uso previsto de la aplicación web del **Asistente IA DINDES**.

> **Estado actual:** la interfaz final todavía está en desarrollo. Este documento será actualizado con capturas reales cuando `app/app.py` esté implementado.

---

## 2. Principio de uso

El asistente **informa y apoya; no decide**.

Las respuestas deben considerarse un punto de partida para consultar antecedentes y no un sustituto de la documentación oficial ni del criterio técnico.

---

## 3. Iniciar la aplicación

Desde la raíz del proyecto:

```powershell
.\.venv\Scripts\Activate.ps1
streamlit run app/app.py
```

URL prevista:

```text
http://localhost:8501
```

---

## 4. Realizar una consulta

1. Ingresar una pregunta específica.
2. Presionar **Consultar**.
3. Esperar el proceso de retrieval, reranking y generación.
4. Revisar la respuesta.
5. Revisar las fuentes y evidencias antes de utilizar la información.

---

## 5. Evidencias que debe mostrar la interfaz

Cuando estén disponibles:

- título de la fuente;
- sección;
- fragmento relevante;
- fecha;
- versión;
- estado;
- score de relevancia.

---

## 6. Cuando no existe evidencia suficiente

El sistema debe abstenerse.

Mensaje esperado:

> **No se encontró evidencia suficiente en las fuentes disponibles para responder esta consulta.**

El usuario no debe interpretar una abstención como error: es un mecanismo de seguridad.

---

## 7. Verificación humana

Antes de utilizar una respuesta en una decisión importante:

- revisar la fuente original;
- confirmar vigencia y versión;
- verificar que el documento corresponde al contexto;
- consultar a un especialista cuando sea necesario.

---

## 8. Reportar una respuesta o fuente

La interfaz final deberá incorporar un mecanismo de reporte.

Casos:

- respuesta incorrecta;
- respuesta incompleta;
- fuente no apropiada;
- fuente desactualizada;
- posible acceso indebido;
- comportamiento inesperado.

---

## 9. Proceso de apelación y escalamiento

Si el usuario no está de acuerdo con una respuesta:

1. reportar la consulta;
2. solicitar revisión de la fuente;
3. el caso se registra;
4. se escala al responsable funcional o custodio de información;
5. si corresponde, se remite a la autoridad competente;
6. la resolución se documenta para trazabilidad.

---

## 10. Buenas prácticas

- formular preguntas específicas;
- revisar siempre las fuentes;
- no ingresar información no autorizada;
- no utilizar respuestas como única base de decisiones críticas;
- reportar errores;
- respetar permisos y necesidad de conocer.

---

## 11. Seguridad y privacidad

No ingresar:

- contraseñas;
- tokens;
- claves;
- información clasificada no autorizada;
- datos personales innecesarios.

El acceso a información depende del rol del usuario.

---

## 12. Limitaciones

El MVP:

- trabaja con un corpus limitado;
- puede no responder fuera del corpus;
- puede recuperar fuentes incorrectas;
- puede usar información desactualizada si el corpus no se mantiene;
- puede producir errores de generación;
- no sustituye especialistas.

---

## 13. Troubleshooting

| Problema | Acción |
|---|---|
| `ModuleNotFoundError` | Ejecutar `pip install -r requirements.txt` |
| Streamlit no reconocido | Instalar Streamlit dentro de `.venv` |
| Modelo no carga | Revisar configuración y memoria |
| Índice vacío | Ejecutar pipeline de ingesta |
| Respuesta sin fuentes | No utilizarla; revisar retrieval |
| Fuente desactualizada | Reportar y solicitar revisión |
| Acceso denegado | Verificar permisos con el administrador |

---

## 14. FAQ

### ¿El asistente toma decisiones?
No. Proporciona información y evidencia para apoyar al usuario.

### ¿Puede equivocarse?
Sí. Por eso las fuentes deben revisarse.

### ¿Qué ocurre si no existe suficiente información?
Debe abstenerse.

### ¿Todos los usuarios ven los mismos documentos?
No necesariamente. El acceso debe depender del rol y de la necesidad de conocer.

### ¿Puedo cuestionar una respuesta?
Sí. El diseño contempla reporte, apelación y escalamiento.

### ¿Puede usarse información real en GitHub?
No, salvo que exista autorización expresa y sea apropiado publicarla.

---

## 15. Advertencia visible recomendada

> **Aviso:** Este asistente es una herramienta de apoyo. Las respuestas dependen del corpus disponible y pueden contener errores o información desactualizada. Verifique las fuentes originales antes de utilizar la información en decisiones técnicas, administrativas u operativas.

---

## 16. Pendientes antes de la entrega final

- implementar `app/app.py`;
- validar comandos reales;
- agregar capturas anotadas;
- documentar autenticación y permisos;
- implementar botón de reporte;
- incorporar ejemplos reales de abstención;
- actualizar métricas finales.
