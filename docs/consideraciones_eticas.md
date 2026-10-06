# Consideraciones éticas

## 1. Propósito

Este documento analiza los principales aspectos éticos del proyecto **Asistente de IA para Innovación, Desarrollo y Gestión del Conocimiento Técnico — DINDES**.

El sistema se plantea como una herramienta de apoyo para búsqueda, recuperación y gestión del conocimiento. No debe sustituir el criterio profesional, técnico ni institucional.

## 2. Principios

- privacidad por diseño;
- minimización de datos;
- trazabilidad;
- transparencia;
- supervisión humana;
- seguridad;
- proporcionalidad;
- uso autorizado;
- reconocimiento explícito de limitaciones.

## 3. Análisis de sesgos

Fuentes potenciales:

- proyectos más documentados que otros;
- áreas técnicas con mayor volumen de información;
- terminología institucional específica;
- documentos históricos desactualizados;
- predominio de determinadas categorías;
- QA producido por un grupo reducido de personas.

Impactos posibles:

- mejor desempeño en áreas sobrerrepresentadas;
- menor calidad en temas con poca evidencia;
- preferencia por terminología frecuente;
- mayor error en categorías con pocos ejemplos.

El principal riesgo no es un sesgo demográfico clásico, sino un **sesgo de cobertura del conocimiento**.

## 4. Equidad y fairness

Se deberá comparar desempeño entre:

- categorías de consulta;
- tipos de documento;
- proyectos;
- áreas técnicas.

Métricas propuestas:

- Precision@K por categoría;
- Recall@K por categoría;
- tasa de respuestas sustentadas;
- tasa de abstención;
- latencia por tipo de consulta.

Mitigaciones:

- ampliar cobertura documental;
- balancear QA;
- evaluar por subgrupos;
- no reportar únicamente métricas globales.

## 5. Privacidad

El repositorio público actual utiliza datasets sintéticos.

Una implementación real podría contener nombres, cargos, documentos internos, información técnica y metadatos institucionales.

Medidas previstas:

- procesamiento local/on-premise;
- no subir documentos reales a GitHub;
- separar código de datos;
- mantener secretos en `.env`;
- aplicar control de acceso;
- mantener logs mínimos.

La aplicabilidad de regulaciones específicas deberá revisarse antes de un despliegue productivo. El proyecto no afirma cumplimiento automático con GDPR, CCPA u otra regulación.

## 6. Transparencia y explicabilidad

El sistema deberá mostrar:

- fuentes recuperadas;
- fragmentos relevantes;
- scores de recuperación cuando correspondan;
- advertencias;
- limitaciones;
- mensaje explícito cuando no exista evidencia suficiente.

## 7. Explicabilidad del modelo

Componentes interpretables:

- BM25;
- scores de similitud;
- features explícitas;
- fuentes visibles.

Si se utilizan modelos auxiliares más complejos, podrán evaluarse SHAP, LIME o permutation feature importance cuando sean apropiados.

## 8. Impacto social y organizacional

Impactos positivos:

- reducción del tiempo de búsqueda;
- mejor acceso al conocimiento;
- trazabilidad;
- apoyo al personal nuevo;
- menor dependencia de conocimiento tácito.

Impactos negativos posibles:

- exceso de confianza;
- uso de respuestas fuera de contexto;
- interpretación incorrecta;
- dependencia excesiva;
- exposición accidental de información;
- uso de información desactualizada.

## 9. Responsabilidad

El asistente es una herramienta de apoyo.

La responsabilidad final sobre decisiones técnicas, administrativas u operativas corresponde a las personas y autoridades competentes.

Cuando exista un error, debe ser posible analizar:

```text
Consulta
→ recuperación
→ fuentes
→ prompt
→ respuesta
→ versión del sistema
```

## 10. Supervisión humana

Se mantendrá un enfoque **human-in-the-loop**.

El usuario deberá revisar fuentes, validar información crítica y consultar documentación original cuando corresponda.

## 11. Uso dual y mal uso

Riesgos:

- consultas fuera del ámbito autorizado;
- inferencia de información sensible;
- automatización de decisiones no previstas;
- extracción masiva de información.

Salvaguardas:

- control de acceso;
- filtrado por permisos;
- ejecución local;
- logs de auditoría;
- límites de consulta;
- exclusión de documentos no autorizados.

## 12. Limitaciones reconocidas

El sistema no debe utilizarse como única fuente en:

- decisiones operativas críticas;
- decisiones de seguridad;
- decisiones administrativas vinculantes;
- evaluación formal de personas;
- situaciones con fuentes incompletas;
- consultas fuera del corpus autorizado.

## 13. Alucinaciones

Los modelos generativos pueden producir información incorrecta.

Mitigaciones:

- RAG;
- fuentes visibles;
- grounding;
- umbrales de relevancia;
- abstención;
- evaluación QA;
- validación humana.

Comportamiento esperado:

> No se encontró evidencia suficiente en las fuentes disponibles para responder esta consulta.

## 14. Información desactualizada

El índice deberá conservar fecha, versión, estado de fuente y unidad responsable.

Se priorizarán fuentes vigentes y se alertará cuando una fuente sea borrador o histórica.

## 15. Seguridad del repositorio público

Nunca se publicarán:

- credenciales;
- tokens;
- claves privadas;
- documentos institucionales reales no autorizados;
- bases vectoriales derivadas de información sensible;
- logs con información restringida.

## 16. Monitoreo

Se recomienda monitorear:

- calidad de retrieval;
- Grounded Response Rate;
- consultas sin respuesta;
- falsos positivos;
- latencia;
- errores;
- categorías con bajo desempeño;
- uso anómalo.

## 17. Actualización

El sistema requerirá revisión periódica del corpus, eliminación de versiones obsoletas, reindexación, actualización del QA set y reevaluación de métricas.

## 18. Advertencia para usuarios

> **Aviso:** Este asistente es una herramienta de apoyo. Las respuestas se generan a partir de las fuentes disponibles y pueden contener errores. Verifique la documentación original antes de utilizar la información en decisiones técnicas, administrativas u operativas.

## 19. Estado de mitigaciones

| Riesgo | Mitigación | Estado |
|---|---|---|
| Exposición de información real en GitHub | Solo samples sintéticos | Implementado |
| Data leakage experimental | Split por `qa_id` | Implementado |
| Respuestas no sustentadas | RAG + fuentes | En desarrollo |
| Exceso de confianza | Advertencias + fuentes | En desarrollo |
| Acceso no autorizado | Autenticación/permisos | Pendiente |
| Datos obsoletos | Metadatos/versionamiento | En diseño |
| Alucinación | Grounding + abstención | En desarrollo |
| Sesgo de cobertura | Evaluación por categoría | Planificado |

## 20. Conclusión

El objetivo ético principal es que la IA facilite el acceso al conocimiento sin ocultar incertidumbre, sin sustituir responsabilidad humana y sin comprometer información institucional.
