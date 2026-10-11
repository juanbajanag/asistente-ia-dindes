# Consideraciones éticas

## 1. Propósito

Este documento consolida el análisis ético del proyecto **Asistente de IA para Innovación, Desarrollo y Gestión del Conocimiento Técnico — DINDES** y recoge los resultados del workshop de Semana 4 sobre impacto social y responsabilidad.

El sistema se concibe como una herramienta de apoyo para búsqueda, recuperación y gestión del conocimiento. No sustituye el criterio profesional, técnico ni institucional de las personas responsables.

---

## 2. Principios éticos aplicados

El proyecto adopta como principios:

- **Beneficencia:** mejorar el acceso al conocimiento y reducir el tiempo de búsqueda.
- **No maleficencia:** evitar exposición de información, respuestas incorrectas y usos fuera de propósito.
- **Autonomía:** mantener la decisión final en el usuario y en la cadena institucional competente.
- **Justicia/Fairness:** evitar que áreas o categorías con menor cobertura documental reciban sistemáticamente peor servicio.
- **Explicabilidad:** mostrar fuentes, fragmentos, fecha, versión y estado de la evidencia recuperada.
- **Privacidad y confidencialidad:** tratar únicamente información autorizada y aplicar controles de acceso acordes al rol y necesidad de conocer.
- **Accountability:** definir responsables, auditoría, monitoreo, reporte, apelación y respuesta a incidentes.

---

## 3. Stakeholders

Se identifican los siguientes grupos:

| Stakeholder | Beneficios | Riesgos principales | Poder/Voz |
|---|---|---|---|
| Usuarios directos de DINDES | Ahorro de tiempo, acceso centralizado, trazabilidad | Sobreconfianza, respuestas incompletas | Alto |
| Especialistas y responsables de proyectos | Reutilización de antecedentes y continuidad | Descontextualización, uso de versiones antiguas | Alto |
| Custodios/administradores de información y TI | Organización y monitoreo | Mayor carga de gobierno y seguridad | Alto |
| Dirección y tomadores de decisión | Mayor disponibilidad de antecedentes | Uso indebido como sustituto del análisis formal | Alto |
| Personal nuevo o con menor experiencia | Menor dependencia del conocimiento tácito | Mayor vulnerabilidad a sobreconfianza | Medio |
| Organización y beneficiarios indirectos | Continuidad institucional y eficiencia | Riesgo reputacional o de seguridad | Medio |

---

## 4. Impactos sociales positivos

### 4.1 Reducción del tiempo de búsqueda

El sistema puede recuperar evidencia desde múltiples fuentes y priorizar resultados. La meta inicial del proyecto es reducir el tiempo de búsqueda al menos en un 50 %, sujeto a validación experimental.

### 4.2 Preservación y transferencia de conocimiento

El RAG permite reutilizar antecedentes documentados sin entrenar nuevamente el LLM, reduciendo dependencia del conocimiento tácito.

### 4.3 Mayor trazabilidad

Las respuestas deberán vincularse con documentos, secciones, versiones y estado de la fuente, facilitando verificación humana y auditoría.

### 4.4 Uso más eficiente de recursos

Se reduce la repetición de búsquedas y la reconstrucción de antecedentes ya existentes.

---

## 5. Impactos negativos y riesgos sociales

| Riesgo | Severidad | Probabilidad | Grupos más expuestos |
|---|---:|---:|---|
| Exposición de información institucional | Alta | Media | Custodios, organización, usuarios autorizados |
| Respuesta incorrecta o no sustentada | Alta | Media | Usuarios, responsables de proyecto, dirección |
| Uso de información desactualizada | Alta | Media | Especialistas y tomadores de decisión |
| Sesgo de cobertura documental | Media | Alta | Áreas con menor documentación |
| Sobreconfianza y pérdida de autonomía crítica | Media | Media | Personal nuevo y usuarios frecuentes |

---

## 6. Análisis de equidad

La equidad en este proyecto no implica que todos deban acceder a toda la información. Implica:

- acceso proporcional al rol y a la necesidad de conocer;
- calidad de recuperación comparable entre categorías;
- detección de áreas con baja cobertura documental;
- capacitación para usuarios con menor experiencia;
- existencia de mecanismos alternativos de consulta.

El sistema puede reducir desigualdad de acceso al conocimiento tácito, pero también puede aumentar desigualdades entre áreas bien y mal documentadas. Por ello se deben medir métricas de recuperación por categoría y no solo de manera global.

---

## 7. Riesgos éticos prioritarios

### R1. Privacidad y confidencialidad

**Descripción:** indexación, logging o presentación de información a personas no autorizadas.  
**Severidad:** Alta.  
**Mitigación:** corpus autorizado, filtros por rol antes del retrieval, cifrado, logs mínimos y auditoría.

### R2. Respuestas no sustentadas / alucinación

**Descripción:** el modelo generativo puede producir texto plausible cuando la evidencia es débil o insuficiente.  
**Severidad:** Alta.  
**Mitigación:** grounding, umbral de relevancia, Top-K controlado, abstención y fuentes visibles.

### R3. Sesgo de cobertura y fairness

**Descripción:** áreas con menos documentación o lenguaje distinto pueden obtener peor recuperación.  
**Severidad:** Media.  
**Mitigación:** métricas por categoría, ampliación del corpus y QA, reevaluación periódica.

### R4. Falta de transparencia / explicabilidad

**Descripción:** el usuario puede confundir evidencia recuperada con texto generado o desconocer la vigencia de una fuente.  
**Severidad:** Alta.  
**Mitigación:** panel de evidencias con fuente, fragmento, fecha, versión y estado.

### R5. Pérdida de autonomía y sobreconfianza

**Descripción:** el asistente podría pasar de herramienta de apoyo a sustituto del juicio experto.  
**Severidad:** Media.  
**Mitigación:** human-in-the-loop, advertencias visibles, capacitación y reglas de uso.

### R6. Seguridad y uso indebido

**Descripción:** un usuario legítimo o una cuenta comprometida podría intentar extraer información masivamente o consultar fuera de su necesidad funcional.  
**Severidad:** Alta.  
**Mitigación:** autenticación, autorización, límites de consulta, monitoreo, pruebas de abuso y respuesta a incidentes.

---

## 8. Decisiones de diseño derivadas del análisis ético

Se incorporan como requisitos del MVP:

1. **Filtros de autorización antes del retrieval.**
2. **Abstención automática ante evidencia insuficiente.**
3. **Visualización de fuente, fragmento, fecha, versión y estado.**
4. **Métricas de recuperación por categoría.**
5. **Logging mínimo y orientado a auditoría.**
6. **Mecanismo para reportar respuestas incorrectas o fuentes inapropiadas.**
7. **Proceso de apelación y escalamiento.**
8. **Supervisión humana en decisiones críticas.**

---

## 9. Uso dual y mal uso

El sistema podría ser mal utilizado para:

- extraer información fuera del propósito autorizado;
- automatizar decisiones no previstas;
- compartir respuestas con usuarios no autorizados;
- realizar consultas masivas;
- inferir información sensible a partir de múltiples fuentes.

Salvaguardas:

- control por roles;
- límites de consulta;
- auditoría;
- separación de corpus;
- revocación de acceso;
- políticas de uso;
- respuesta a incidentes.

---

## 10. Limitaciones reconocidas

El sistema no debe utilizarse como única fuente en:

- decisiones operativas críticas;
- decisiones administrativas vinculantes;
- situaciones donde las fuentes estén incompletas o desactualizadas;
- consultas fuera del corpus autorizado;
- casos donde no exista evidencia suficiente.

---

## 11. Advertencia para usuarios

> **Aviso:** Este asistente es una herramienta de apoyo. Las respuestas dependen de las fuentes disponibles y pueden contener errores. Revise la documentación original antes de utilizar la información en decisiones técnicas, administrativas u operativas.

---

## 12. Compromiso ético del equipo

El equipo se compromete a:

- evaluar periódicamente la calidad de recuperación y la tasa de respuestas sustentadas;
- no publicar información institucional real sin autorización;
- implementar abstención, trazabilidad y supervisión humana;
- actuar ante daños, accesos indebidos o errores recurrentes;
- mejorar la cobertura de áreas menos representadas;
- mantener transparencia sobre capacidades, limitaciones y cambios del sistema.

---

## 13. Documentos relacionados

- `docs/gobernanza_responsabilidad.md`
- `docs/compliance.md`
- `docs/arquitectura.md`
- `docs/manual_usuario.md`
