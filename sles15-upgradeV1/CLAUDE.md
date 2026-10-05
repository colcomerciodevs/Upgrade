# CLAUDE.md — Upgrade SLES 15 SP4 → SP5 → SP6 → SP7

## Idioma obligatorio

Trabaja y responde **siempre en español**.

Todo el contenido generado para este proyecto debe estar en español, incluyendo:

- explicaciones;
- README;
- documentación;
- comentarios en YAML/Jinja2;
- mensajes de validación;
- reportes HTML/Markdown/texto;
- resúmenes;
- troubleshooting;
- nombres descriptivos de tareas Ansible cuando sea razonable.

Se pueden conservar en inglés únicamente términos técnicos, comandos, nombres oficiales de módulos, parámetros, estados del sistema y nombres propios cuya traducción pueda causar confusión, por ejemplo: `systemd`, `zypper`, `ansible.builtin.reboot`, `running`, `active`, `health check`, `dry-run`, `Foreman/Katello`, `AWX`.

## Objetivo

Construir y mantener un proyecto Ansible/AWX seguro para producción, entendible y documentado para:

- SLES 15 SP4 → SP5 (etapa independiente);
- SLES 15 SP5 → SP6;
- SLES 15 SP6 → SP7;
- SLES 15 SP5 → SP6 → SP7 de forma secuencial.

Los servidores administrados ejecutan la aplicación Java **GeoPOS**.

Antes de diseñar o modificar el procedimiento de upgrade, leer `docs/CONTEXTO_PROYECTO.md` y revisar la documentación oficial de SUSE allí referenciada.

## Regla obligatoria de repositorios

El upgrade debe utilizar **exclusivamente los repositorios internos de Foreman/Katello configurados explícitamente por el administrador**.

Esta regla aplica independientemente de que un host esté:

- registrado en SUSEConnect;
- parcialmente registrado;
- incorrectamente registrado;
- no registrado.

SUSEConnect no debe determinar el procedimiento de upgrade, habilitar repositorios del Service Pack objetivo, registrar el host, reparar el registro ni bloquear la migración.

Si se consulta SUSEConnect, su estado será únicamente informativo/diagnóstico.

No utilizar repositorios públicos de SUSE para ejecutar la migración.

No utilizar `zypper migration` si su funcionamiento requiere SUSE Customer Center, RMT/SMT u otro servicio de registro para descubrir o habilitar los repositorios del Service Pack objetivo.

Implementar el procedimiento oficial de Zypper aplicable a repositorios configurados manualmente/internamente, después de contrastarlo con la documentación oficial de SUSE y con el contenido real disponible en Foreman/Katello.

Nunca inventar:

- URLs de Foreman/Katello;
- nombres de repositorios;
- Content Views;
- Lifecycle Environments;
- rutas de CA;
- configuración GPG;
- servicios GeoPOS;
- patrones de procesos Java;
- puertos;
- URLs de health check.

Utilizar `CHANGE_ME` claramente identificados cuando falten datos reales del ambiente.

## Ruta de upgrade

La ruta operacional del proyecto es:

`SP5 → SP6 → SP7`

Adicionalmente, el proyecto soporta `SP4 → SP5` como etapa **independiente**
(modo `sp4_to_sp5`), para servidores que todavía están en SP4. Esta etapa
reutiliza el mismo procedimiento (precheck → dry-run/preflight → upgrade →
reiniciar → validar) y la misma regla de "no saltos directos" (nunca
SP4 → SP6 ni SP4 → SP7 directo). **`SP4 → SP5` no se encadena dentro de
"full"**: `full` sigue siendo exclusivamente `SP5 → SP6 → SP7`. Un host en
SP4 ejecuta `sp4_to_sp5` por separado y, en una corrida posterior,
`sp5_to_sp6`/`full`.

No implementar una migración directa SP5 → SP7 (ni SP4 → SP6/SP7).

Para un upgrade completo:

1. identificar el Service Pack actual;
2. ejecutar prechecks;
3. capturar el estado previo;
4. preparar y validar los repositorios Foreman aprobados para SP6;
5. ejecutar el dry-run/preflight soportado;
6. realizar SP5 → SP6;
7. reiniciar de forma controlada;
8. validar SP6, sistema operativo, repositorios, servicios críticos y GeoPOS;
9. generar el reporte de la etapa SP6;
10. continuar solamente si las validaciones críticas de SP6 fueron satisfactorias;
11. cambiar controladamente los repositorios temporales SP6 por los de SP7;
12. validar los repositorios Foreman SP7;
13. ejecutar dry-run/preflight;
14. realizar SP6 → SP7;
15. reiniciar;
16. validar SP7, sistema operativo, repositorios, servicios críticos y GeoPOS;
17. limpiar únicamente los repositorios/archivos temporales creados por esta automatización;
18. generar el reporte final por host y el resumen de la ejecución.

Si SP6 falla o no puede validarse, **no continuar a SP7**.

También deben soportarse ejecuciones independientes SP4→SP5, SP5→SP6 y SP6→SP7.

## Seguridad en producción

Considerar todos los hosts administrados como sistemas productivos.

Claude Code puede realizar de forma autónoma acciones locales y reversibles sobre este repositorio, como:

- leer y modificar archivos del proyecto;
- crear YAML/Jinja2/documentación;
- ejecutar syntax-check;
- ejecutar lint;
- renderizar/probar plantillas localmente;
- consultar el estado y diff de Git.

No conectarse, modificar, reiniciar, parchar ni actualizar infraestructura real a menos que el usuario autorice explícitamente esa acción concreta e identifique los targets/ambiente.

La existencia de inventarios o credenciales no constituye autorización para ejecutar contra producción.

No:

- ocultar fallos críticos con `ignore_errors: true`;
- deshabilitar TLS o GPG como solución permanente;
- habilitar vendor change por defecto;
- eliminar indiscriminadamente `/etc/zypp/repos.d/*`;
- reparar SUSEConnect automáticamente;
- reiniciar automáticamente GeoPOS únicamente para hacer pasar una validación;
- afirmar que existe rollback si no existe un mecanismo real;
- exponer secretos en YAML, logs o reportes.

Respaldar la configuración relevante de repositorios antes de modificarla.

Preservar repositorios permanentes.

Los artefactos de repositorio creados temporalmente por esta automatización deben utilizar un prefijo identificable, por ejemplo:

`ansible-sles-upgrade-`

En una ejecución exitosa, retirar únicamente los repositorios temporales creados por esta automatización.

Ante un fallo, conservar por defecto la información/configuración necesaria para diagnóstico en lugar de ejecutar una limpieza ciega.

## Prechecks

Antes de un upgrade modificador validar como mínimo:

- distribución SLES y Service Pack;
- arquitectura;
- hostname;
- kernel;
- uptime;
- conectividad Ansible/SSH;
- privilegios requeridos;
- disponibilidad de Zypper;
- locks de Zypper/RPM/libzypp;
- repositorios actuales y sus URLs;
- acceso desde el propio servidor SLES a los repositorios Foreman/Katello requeridos;
- metadata, TLS/CA y GPG;
- espacio libre en filesystems relevantes;
- servicios críticos configurados;
- validaciones GeoPOS configuradas;
- repositorios de terceros/no esperados que puedan interferir.

Una condición que haga inseguro continuar debe fallar explícitamente.

Capturar el estado previo para compararlo con el posterior en el reporte.

## Validación de GeoPOS

GeoPOS debe ser configurable y soportar **cero, uno o múltiples elementos** en cada categoría.

El modelo de variables debe permitir:

- habilitar/deshabilitar GeoPOS globalmente;
- múltiples servicios systemd;
- múltiples patrones de procesos Java;
- múltiples puertos TCP;
- múltiples health checks HTTP/HTTPS opcionales;
- valores comunes mediante `group_vars`;
- excepciones mediante `host_vars`.

Cada categoría debe poder habilitarse o deshabilitarse independientemente.

Las listas vacías son válidas.

Concepto:

```yaml
geopos_validation:
  enabled: true

  services:
    enabled: true
    items: []

  java_processes:
    enabled: true
    items: []

  tcp_ports:
    enabled: true
    items: []

  health_checks:
    enabled: false
    items: []
```

No exigir health checks cuando no existan.

Una validación deshabilitada debe representarse como `NOT_CHECKED`, no como `FAILED`.

La búsqueda de procesos Java debe ser suficientemente específica para identificar el componente GeoPOS. Encontrar cualquier proceso `java` no demuestra que GeoPOS esté funcionando.

Comparar el estado previo y posterior cuando sea práctico.

No considerar el upgrade completamente satisfactorio únicamente porque `/etc/os-release` muestre el Service Pack objetivo.

## Reportes

El reporting es obligatorio.

Generar un reporte legible por host después de cada etapa de upgrade y un reporte final para la migración completa.

Si se procesan varios hosts, generar también un resumen consolidado cuando pueda hacerse sin complejidad innecesaria.

El operador debe poder determinar si la migración fue satisfactoria sin conectarse por SSH al servidor ni leer toda la salida del Job de AWX.

Preferir un reporte HTML sencillo generado con Jinja2. Puede acompañarse de Markdown/texto si aporta valor.

Estados permitidos:

- `OK`;
- `WARNING`;
- `FAILED`;
- `NOT_CHECKED`.

Incluir como mínimo:

- hostname;
- fecha/hora de inicio y fin;
- acción solicitada;
- SP inicial, objetivo y final;
- kernel antes/después;
- filesystems;
- validación de repositorios;
- estado final de repositorios temporales;
- resultado del dry-run/preflight;
- resultado del upgrade;
- reboot y conectividad;
- servicios críticos antes/después;
- servicios GeoPOS antes/después;
- procesos Java configurados antes/después;
- puertos configurados antes/después;
- health checks configurados antes/después;
- etapa/check exacto que falló;
- resultado final.

No incluir secretos.

No depender del filesystem efímero del Execution Environment de AWX como almacenamiento permanente de reportes.

El destino persistente será configurable hasta que el administrador proporcione la ubicación real.

## AWX

El proyecto debe poder utilizarse directamente desde AWX.

Soportar:

- precheck;
- SP4 → SP5 (independiente);
- SP5 → SP6;
- SP6 → SP7;
- full SP5 → SP6 → SP7;
- validación independiente;
- un host;
- varios hosts;
- grupo de inventario;
- ejecución programada.

Mecanismo de selección de hosts (decisión explícita del usuario para este
ambiente, 2026-10-05): **no se usa `Limit`**. Cada ejecución (incluso un
`precheck`) corresponde a un CRQ/RFC de control de cambios real, así que el
alcance se define con el match exacto entre `upgrade_crq`/`upgrade_lote`/
`upgrade_ambiente` del Survey y las columnas `CRQ`/`Lote`/`Ambiente` del
inventario dinámico — ver `playbooks/upgrade.yml`. Si ningún host coincide
con los 3 valores declarados, el playbook falla explícito antes de tocar
cualquier host. `Limit` se deja vacío y sin "Prompt on Launch" en el Job
Template.

El procesamiento productivo por defecto debe ser de un host a la vez:

```yaml
serial_batch_size: 1
```

Mantener el Survey pequeño y útil operacionalmente.

Los 3 campos de selección (`upgrade_crq`/`upgrade_lote`/`upgrade_ambiente`)
deben marcarse como obligatorios ("Required") en el Survey.

## Simplicidad

Evitar sobreingeniería.

La complejidad correcta es la mínima necesaria para satisfacer los requisitos productivos.

No crear:

- roles separados para cada Service Pack si una parametrización clara es más simple;
- helpers utilizados una sola vez sin necesidad;
- funcionalidades hipotéticas futuras;
- capas de abstracción innecesarias;
- exceso de handlers/includes/playbooks;
- archivos auxiliares temporales que permanezcan en el repositorio.

Preferir un proyecto pequeño que un administrador Linux pueda leer, mantener y explicar.

Antes de añadir un archivo o abstracción, comprobar que resuelve una necesidad concreta de operación, seguridad o mantenibilidad.

## Calidad Ansible

Utilizar nombres de tareas descriptivos y variables claras.

Preferir módulos nativos de Ansible cuando expresen correctamente la operación.

Utilizar `command`/`shell` cuando la operación SUSE/Zypper lo requiera o sea más clara, manejando correctamente return codes y salida.

Conservar información útil para reporting/diagnóstico sin filtrar secretos.

Utilizar `block/rescue/always` únicamente cuando mejore realmente el manejo de errores.

Una migración de Service Pack no es completamente idempotente como una configuración normal. No fingir lo contrario.

Hacer idempotentes, cuando sea razonable, la preparación, validación y limpieza.

Ejecutar validaciones estáticas disponibles:

```bash
ansible-playbook --syntax-check ...
ansible-lint
```

No afirmar que se realizaron pruebas reales en SLES cuando solamente se ejecutaron pruebas estáticas.

## Documentación

Mantener un `README.md` práctico y en español que cubra:

- alcance;
- rutas soportadas;
- arquitectura;
- requisitos;
- Foreman/Katello;
- ciclo de vida de repositorios;
- variables GeoPOS;
- inventario/group_vars/host_vars;
- configuración de AWX;
- Project;
- Inventory;
- Credential;
- Job Template;
- Survey;
- selección de hosts (CRQ/Lote/Ambiente, ya no Limit);
- Schedule;
- precheck;
- dry-run/preflight;
- cada modo de upgrade;
- reporting;
- persistencia de reportes;
- comportamiento ante fallos;
- troubleshooting;
- logs útiles de SUSE/Zypper;
- recuperación frente a rollback real;
- interacción con el proceso corporativo independiente de parchado.

## Forma de trabajar en Claude Code

Investigar antes de modificar.

Leer los archivos relevantes y `docs/CONTEXTO_PROYECTO.md`. No especular sobre archivos que no se hayan inspeccionado.

Para decisiones importantes sobre arquitectura o comandos de upgrade, explicar primero la propuesta y los `CHANGE_ME` pendientes.

No inventar datos de infraestructura.

Después de que el usuario apruebe la implementación, modificar directamente el repositorio en vez de limitarse a mostrar archivos hipotéticos en el chat.

Trabajar incrementalmente.

Cuando Git esté disponible, utilizar `git status` y `git diff` para revisar cambios.

No ejecutar `push`, `force push`, `reset --hard`, eliminar trabajo desconocido ni modificar infraestructura compartida sin autorización explícita.

Eliminar archivos temporales creados durante el desarrollo cuando ya no sean necesarios.

Antes de declarar terminado el proyecto:

1. inspeccionar el árbol final;
2. comprobar coherencia de variables;
3. ejecutar syntax/lint disponibles;
4. distinguir validación estática de prueba real;
5. enumerar todos los `CHANGE_ME` pendientes;
6. enumerar prerrequisitos antes de producción.

## Orden de fuentes de verdad

Si existe conflicto, utilizar este orden:

1. decisiones explícitas del usuario para este ambiente;
2. documentación oficial de SUSE aplicable;
3. este `CLAUDE.md`;
4. `docs/CONTEXTO_PROYECTO.md`;
5. implementación existente;
6. conocimiento general del modelo.

Si una decisión del ambiente resulta técnicamente incompatible con el soporte oficial de SUSE, detenerse y explicar el conflicto en lugar de modificar silenciosamente la decisión o el procedimiento.
