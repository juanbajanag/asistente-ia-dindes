# Gobernanza, responsabilidad y accountability

## 1. Propósito

Este documento define la cadena de responsabilidad, mecanismos de accountability y respuesta a incidentes del **Asistente IA DINDES**.

---

## 2. Principio de responsabilidad

El sistema es una herramienta de apoyo. La responsabilidad final sobre el uso de la información permanece en las personas y autoridades competentes.

---

## 3. Cadena de responsabilidad

| Rol | Responsabilidades | Rendición de cuentas |
|---|---|---|
| Desarrolladores / equipo IA | Arquitectura, implementación, pruebas, control de errores, logging técnico | Code review, pruebas y documentación de cambios |
| Responsable de datos/conocimiento | Selección de fuentes, calidad, vigencia, permisos y metadatos | Revisión del corpus, altas/bajas y auditoría de datos |
| Product Owner / Jefatura del proyecto | Objetivo, casos permitidos, trade-offs y prioridades | Aprobación de releases y riesgos aceptados |
| TI / Seguridad | Infraestructura, autenticación, hardening, respaldos y monitoreo | Auditorías técnicas, gestión de incidentes y accesos |
| Organización / autoridad competente | Gobernanza, políticas, recursos y límites de uso | Aprobación de despliegue y revisión periódica |
| Usuarios | Uso conforme a propósito, validación de fuentes y reporte de errores | Cumplimiento de reglas y trazabilidad de reportes |

---

## 4. Documentación de accountability

Se deberán mantener:

- model card del componente generativo;
- datasheet del corpus/datasets;
- ethics statement;
- historial de versiones;
- parámetros relevantes;
- decisiones y trade-offs;
- registro de incidentes.

---

## 5. Supervisión humana

Las decisiones críticas deben conservar revisión humana.

El sistema no debe utilizarse como autoridad final en decisiones técnicas, administrativas u operativas.

---

## 6. Auditoría

Como punto de partida:

- revisión trimestral del sistema;
- revisión inmediata ante incidentes graves;
- revisión extraordinaria ante cambios relevantes del corpus, modelo o permisos.

---

## 7. Monitoreo continuo

Métricas recomendadas:

- Precision@K y Recall@K por categoría;
- Grounded Response Rate;
- tasa de abstención;
- latencia;
- errores;
- consultas sin respuesta;
- intentos de acceso no autorizado;
- cambios relevantes del corpus;
- incidentes reportados.

---

## 8. Proceso de apelación y escalamiento

Los usuarios podrán:

1. cuestionar una respuesta;
2. solicitar revisión de la fuente;
3. reportar fuente inapropiada o posible acceso indebido;
4. escalar al responsable funcional o custodio;
5. solicitar revisión por autoridad competente cuando corresponda.

Cada caso debe registrar:

- consulta original;
- respuesta;
- fuentes utilizadas;
- versión del sistema;
- motivo del reporte;
- responsable asignado;
- resolución;
- acciones correctivas.

---

## 9. Plan de respuesta a incidentes

### 9.1 Detección

- alertas;
- reportes de usuario;
- revisión de logs;
- monitoreo de métricas.

### 9.2 Respuesta inmediata

- suspender componente o acceso afectado;
- preservar evidencia;
- notificar al responsable.

### 9.3 Investigación

Revisar:

- consulta;
- retrieval;
- fuente;
- permisos;
- prompt;
- versión;
- configuración.

### 9.4 Corrección

Según el incidente:

- retirar o reclasificar una fuente;
- corregir configuración;
- parchear software;
- ajustar reglas;
- revocar permisos;
- comunicar a afectados cuando corresponda.

### 9.5 Prevención

- actualizar pruebas;
- actualizar checklist;
- mejorar documentación;
- capacitar;
- ajustar monitoreo;
- revisar políticas.

---

## 10. Condiciones mínimas antes de un piloto

Se consideran condiciones de entrada:

- corpus autorizado;
- control de acceso;
- grounding y abstención;
- fuentes visibles;
- monitoreo;
- plan de incidentes;
- responsables designados;
- mecanismo de reporte y apelación.

---

## 11. Estado de implementación

| Componente | Estado |
|---|---|
| Cadena de responsabilidad | Definida |
| Proceso de apelación | Definido conceptualmente |
| Auditoría periódica | Propuesta |
| Monitoreo | En diseño |
| Botón/mecanismo de reporte | Pendiente |
| Logging de incidentes | Pendiente |
| Roles y permisos técnicos | Pendiente |
| Plan de incidentes | Definido conceptualmente |

---

## 12. Documentos relacionados

- `docs/consideraciones_eticas.md`
- `docs/compliance.md`
- `docs/arquitectura.md`
