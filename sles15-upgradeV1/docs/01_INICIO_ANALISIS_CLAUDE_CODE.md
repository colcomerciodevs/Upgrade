# 01 — Inicio de Claude Code: análisis y arquitectura

## Objetivo de esta fase

Este es el **primer prompt** que debes pasar a Claude Code.

En esta fase Claude Code debe analizar el proyecto, la documentación y proponer la arquitectura. **Todavía no debe construir el proyecto Ansible completo.**

Además debe proponer la estructura de una presentación ejecutiva en PowerPoint para gerencia y otras áreas. La presentación definitiva se generará después de aprobar la arquitectura, para que refleje el diseño real.

## Prompt para copiar y pegar en Claude Code

```text
Lee primero CLAUDE.md y docs/CONTEXTO_PROYECTO.md completos.

Revisa también toda la documentación oficial de SUSE disponible en docs/references/.

Este proyecto se utilizará para realizar upgrades productivos de SLES 15:

SP5 -> SP6
SP6 -> SP7
SP5 -> SP6 -> SP7

mediante Ansible y AWX.

Hay una decisión de arquitectura que ya está tomada:

El upgrade debe utilizar EXCLUSIVAMENTE los repositorios internos de Foreman/Katello que yo configure.

Esto debe cumplirse independientemente de si el servidor está registrado, mal registrado o no registrado en SUSEConnect.

SUSEConnect no debe participar en la selección ni habilitación de repositorios y su estado no debe bloquear la migración.

Antes de crear archivos Ansible quiero que analices el proyecto.

Necesito que determines:

1. El procedimiento técnico soportado por SUSE que debemos utilizar para SP5 -> SP6 utilizando repositorios Foreman/Katello configurados manualmente.

2. El procedimiento técnico para SP6 -> SP7 bajo las mismas condiciones.

3. Los comandos Zypper que propones utilizar y por qué son apropiados según la documentación oficial.

4. Cómo manejarás los repositorios temporales de Foreman/Katello.

5. Qué prechecks serán obligatorios antes de permitir un upgrade.

6. Cómo realizarás el dry-run/preflight antes de modificar paquetes.

7. Cómo comprobarás después del reboot que realmente se alcanzó el Service Pack esperado.

8. Cómo validarás GeoPOS antes y después del upgrade considerando que pueden existir:
   - múltiples servicios systemd;
   - múltiples procesos Java;
   - múltiples puertos;
   - múltiples health checks;
   - categorías deshabilitadas o listas vacías.

9. Cómo generarás un reporte por servidor y por etapa para poder saber desde AWX si el upgrade fue satisfactorio sin conectarme manualmente al servidor.

10. Cómo implementarás el flujo completo:

    SP5
      -> precheck
      -> upgrade SP6
      -> reboot
      -> validación SP6
      -> reporte SP6
      -> solamente si SP6 es correcto
      -> upgrade SP7
      -> reboot
      -> validación SP7
      -> reporte final

11. Qué variables o información real todavía debo proporcionarte de Foreman/Katello, GeoPOS y AWX.

12. La estructura MÍNIMA de archivos, playbooks y roles que propones para el proyecto.

13. Adicionalmente, necesito que este proyecto tenga una presentación ejecutiva en PowerPoint (.pptx), en español, orientada a gerencia y otras áreas no necesariamente técnicas.

    En esta primera fase NO generes todavía el PowerPoint definitivo. Propón únicamente su estructura/contenido resumido para mi aprobación.

    La presentación debe ser muy fácil de explicar y visual, evitando detalles técnicos innecesarios. Debe resumir aproximadamente:
    - objetivo y necesidad del proyecto;
    - alcance SP5 -> SP6 -> SP7;
    - qué automatizará Ansible/AWX;
    - arquitectura de alto nivel;
    - uso exclusivo de repositorios internos Foreman/Katello;
    - flujo general del upgrade;
    - controles y consideraciones para producción;
    - validación de GeoPOS antes y después;
    - reportes y trazabilidad;
    - beneficios operativos;
    - riesgos principales y cómo se controlan;
    - próximos pasos.

    Preferiblemente debe quedar en unas 7 a 10 diapositivas, con poco texto y diagramas simples.

    Una vez aprobada la arquitectura y construido el proyecto, deberás generar el PowerPoint definitivo basándote en la implementación real y no en supuestos.

Prioriza simplicidad y facilidad de mantenimiento.

No quiero sobreingeniería ni una gran cantidad de roles, playbooks o abstracciones si no son necesarios.

IMPORTANTE:

En esta primera fase NO generes todavía el proyecto Ansible completo.

NO ejecutes comandos contra servidores.

NO modifiques infraestructura.

NO generes todavía la presentación PowerPoint definitiva.

Primero quiero revisar y aprobar contigo:
- la arquitectura;
- el procedimiento de upgrade;
- la estructura propuesta del proyecto;
- la estructura propuesta de la presentación ejecutiva.
```

## Qué debe ocurrir después

Revisa la respuesta de Claude Code antes de continuar.

En particular valida:

- que no dependa de SUSEConnect;
- que utilice únicamente Foreman/Katello;
- que el procedimiento Zypper esté sustentado en documentación SUSE;
- que SP6 deba quedar validado antes de continuar a SP7;
- que GeoPOS se compruebe antes y después;
- que exista reporting por host/etapa;
- que la estructura Ansible sea simple;
- que la presentación propuesta sea ejecutiva y no una copia técnica del README.

Cuando apruebes esta fase, utiliza el documento `02_CONSTRUIR_PROYECTO_CLAUDE_CODE.md`.
```
