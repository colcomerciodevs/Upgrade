# 02 — Claude Code: construir el proyecto aprobado

## Cuándo utilizar este prompt

Utilízalo solamente después de revisar y aprobar la arquitectura propuesta en la fase 01.

## Prompt para copiar y pegar en Claude Code

```text
Apruebo la arquitectura, el procedimiento y la estructura general propuesta.

Ahora implementa el proyecto completo directamente en este repositorio siguiendo CLAUDE.md, docs/CONTEXTO_PROYECTO.md y las decisiones aprobadas durante nuestro análisis.

Requisitos:

- genera todos los playbooks, roles/tasks, defaults/vars, templates y documentación realmente necesarios;
- mantén la estructura mínima aprobada;
- deja como CHANGE_ME únicamente datos reales del ambiente que todavía no te he proporcionado;
- no inventes URLs, repositorios, servicios, procesos, puertos ni health checks;
- implementa los modos precheck, SP5->SP6, SP6->SP7, full SP5->SP6->SP7 y validate;
- usa exclusivamente repositorios Foreman/Katello configurados;
- no hagas depender el upgrade de SUSEConnect;
- implementa validaciones configurables de GeoPOS con 0..N servicios, procesos Java, puertos y health checks;
- implementa reportes por servidor y por etapa, más resumen final cuando corresponda;
- prepara el proyecto para AWX usando Limit como selector principal y serial_batch_size=1 por defecto;
- genera un README completo, operativo y en español.

También genera la presentación ejecutiva PowerPoint (.pptx) aprobada en la fase anterior.

La presentación debe:
- estar en español;
- estar orientada a gerencia y otras áreas;
- ser breve, clara y visual;
- evitar comandos, YAML y detalles técnicos innecesarios;
- reflejar la arquitectura REAL finalmente implementada;
- explicar objetivo, alcance, arquitectura, flujo, controles productivos, validación GeoPOS, reporting, beneficios, riesgos/control y próximos pasos;
- tener aproximadamente 7 a 10 diapositivas;
- quedar almacenada dentro del proyecto en una ubicación clara, por ejemplo docs/presentacion/;
- poder presentarse sin necesidad de explicar internamente cada tarea Ansible.

Trabaja directamente sobre los archivos.

Cuando termines, ejecuta únicamente validaciones locales/estáticas seguras disponibles, como syntax-check y ansible-lint si están instalados.

No conectes ni ejecutes el upgrade contra servidores reales.

Finalmente revisa el árbol completo, comprueba que las variables sean coherentes entre todos los archivos y entrégame:

1. resumen de lo implementado;
2. árbol final;
3. validaciones ejecutadas y resultado;
4. lista exacta de CHANGE_ME pendientes;
5. checklist de información que debo completar antes de probar en laboratorio;
6. ruta del PowerPoint generado;
7. resumen de las diapositivas incluidas.
```
