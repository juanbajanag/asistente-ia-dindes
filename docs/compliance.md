# Compliance y marco regulatorio

## 1. Propósito

Este documento registra el análisis de cumplimiento aplicable al **Asistente IA DINDES**.

> Este documento es una guía académica y técnica. Antes de un despliegue real con información institucional o datos personales se requiere revisión por las áreas jurídica, de protección de datos, seguridad y TI competentes.

---

## 2. Ley Orgánica de Protección de Datos Personales del Ecuador (LOPDP)

La LOPDP constituye la referencia principal cuando el sistema trate datos personales contenidos en:

- documentos;
- perfiles de usuario;
- autenticación;
- logs;
- reportes;
- metadatos.

### Estado actual

El repositorio público utiliza datasets sintéticos.

### Acciones antes de usar datos reales

- inventario de datos personales;
- definición de base jurídica;
- minimización;
- política de retención;
- control de acceso;
- información a titulares cuando corresponda;
- medidas de seguridad;
- evaluación de riesgos.

---

## 3. Reglamento General a la LOPDP

El Reglamento desarrolla obligaciones y medidas de aplicación.

### Estado

Pendiente de análisis operativo detallado para un piloto con información real.

### Acción

Validación con responsable jurídico/protección de datos antes de incorporar datos personales reales.

---

## 4. Normativa institucional y seguridad de la información

Por tratarse de un sistema destinado a DINDES, el despliegue real deberá ajustarse a normas internas aplicables a:

- clasificación de información;
- necesidad de conocer;
- acceso;
- ciberseguridad;
- gestión documental;
- hosting;
- autorización de fuentes;
- continuidad;
- incidentes.

### Estado

Las normas institucionales específicas aún deben ser identificadas formalmente con las áreas competentes.

---

## 5. Normas internacionales

### GDPR

No se considera aplicable por defecto al alcance actual. Podría ser relevante si el sistema tratara datos sujetos a su ámbito territorial o material.

### CCPA

No se considera aplicable por defecto. Podría ser relevante si existiera tratamiento comprendido dentro de su ámbito.

### HIPAA

No se considera aplicable al proyecto actual, al no tratarse de un sistema de salud en Estados Unidos.

### EU AI Act

No se asume aplicable al piloto local en Ecuador. Puede utilizarse como referencia de buenas prácticas o ser relevante si el sistema entra en su ámbito territorial/material.

---

## 6. Matriz de cumplimiento

| Marco | Requisito/alcance | Estado | Acción |
|---|---|---|---|
| LOPDP Ecuador | Tratamiento de datos personales | Parcial | Inventariar datos, base jurídica, retención, acceso y riesgos |
| Reglamento LOPDP | Aplicación operativa de obligaciones | Pendiente | Revisión jurídica antes del piloto con datos reales |
| Políticas internas | Clasificación y acceso documental | Pendiente | Identificar normas, corpus y permisos |
| GDPR | Solo si entra en su ámbito | No aplicable por defecto | Reevaluar si cambia el alcance |
| CCPA | Solo si entra en su ámbito | No aplicable por defecto | Reevaluar si cambia el alcance |
| HIPAA | Datos de salud sujetos a EE. UU. | No aplicable | Ninguna en alcance actual |
| EU AI Act | Según ámbito territorial/material | Referencial | Reevaluar si cambia despliegue |

---

## 7. Requisitos técnicos derivados de compliance

- control de acceso por rol;
- trazabilidad;
- minimización de logs;
- retención definida;
- cifrado cuando corresponda;
- separación de datos y código;
- `.env` fuera de Git;
- no publicar corpus real sin autorización;
- registro de incidentes;
- capacidad de revocación de acceso.

---

## 8. Revisión previa a producción

Antes de un despliegue real se deberá confirmar:

- qué datos serán tratados;
- quién es responsable del tratamiento;
- finalidad;
- base jurídica;
- permisos;
- retención;
- hosting;
- acceso;
- auditoría;
- respuesta a incidentes;
- políticas institucionales aplicables.

---

## 9. Documentos relacionados

- `docs/consideraciones_eticas.md`
- `docs/gobernanza_responsabilidad.md`
- `docs/arquitectura.md`
