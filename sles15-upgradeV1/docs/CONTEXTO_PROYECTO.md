# CONTEXTO_PROYECTO — SLES 15 SP4 → SP5 → SP6 → SP7

## Idioma

Todo el trabajo, documentación, explicaciones y reportes de este proyecto deben generarse en **español**, conservando en inglés únicamente comandos y términos técnicos cuando corresponda.

> **Propósito de este documento**
>
> Este archivo aporta el contexto técnico y operativo del ambiente donde se ejecutará la automatización.
> No reemplaza las instrucciones generales del proyecto ni la documentación oficial de SUSE.
>
> Los valores marcados como `CHANGE_ME` o `PENDIENTE` deben completarse con información real del ambiente antes de utilizar la automatización en producción.

---

## 1. Descripción del ambiente

La automatización será utilizada sobre servidores **SUSE Linux Enterprise Server 15 (SLES 15)** productivos.

El objetivo es automatizar mediante **Ansible y AWX** las siguientes migraciones:

- SLES 15 SP4 → SLES 15 SP5 (etapa independiente, para hosts que todavía están en SP4; no se encadena con lo siguiente)
- SLES 15 SP5 → SLES 15 SP6
- SLES 15 SP6 → SLES 15 SP7
- SLES 15 SP5 → SP6 → SP7 de forma secuencial

La operación debe priorizar seguridad, facilidad de diagnóstico y capacidad de comprobar el resultado sin necesidad de conectarse manualmente a cada servidor.

---

## 2. Aplicación productiva: GeoPOS

Los servidores objetivo alojan una aplicación Java denominada **GeoPOS**.

GeoPOS puede estar compuesto por múltiples componentes. Dependiendo del servidor pueden existir:

- uno o varios servicios systemd;
- uno o varios procesos Java;
- uno o varios puertos TCP;
- cero, uno o varios endpoints de health check;
- diferentes componentes o configuraciones según el grupo o servidor.

No asumir que todos los servidores GeoPOS tienen exactamente la misma configuración.

Las validaciones deben poder heredarse mediante `group_vars` y sobrescribirse mediante `host_vars` cuando un servidor sea diferente.

### 2.1 Datos de GeoPOS pendientes de completar

#### Servicios systemd

```yaml
geopos_services:
  - CHANGE_ME_GEOPOS_SERVICE_1
  - CHANGE_ME_GEOPOS_SERVICE_2
```

Estado: **PENDIENTE**

Para cada servicio se debe determinar:

- nombre real de la unidad systemd;
- estado esperado;
- si es crítico para considerar exitosa la migración.

#### Procesos Java

```yaml
geopos_java_processes:
  - name: CHANGE_ME_COMPONENT_1
    match: CHANGE_ME_PROCESS_PATTERN_1
  - name: CHANGE_ME_COMPONENT_2
    match: CHANGE_ME_PROCESS_PATTERN_2
```

Estado: **PENDIENTE**

El patrón debe identificar específicamente el componente GeoPOS correspondiente. No utilizar únicamente `java` como patrón.

Datos útiles para determinarlo:

```bash
ps -ef | grep '[j]ava'
systemctl status <servicio>
systemctl cat <servicio>
```

#### Puertos

```yaml
geopos_tcp_ports:
  - name: CHANGE_ME_COMPONENT_1
    port: CHANGE_ME_PORT_1
  - name: CHANGE_ME_COMPONENT_2
    port: CHANGE_ME_PORT_2
```

Estado: **PENDIENTE**

Datos útiles:

```bash
ss -lntp
```

#### Health checks

Los health checks son opcionales.

Si GeoPOS dispone de endpoints adecuados, podrán configurarse varios. Si no existen o no se desea utilizarlos, esta validación debe permanecer deshabilitada.

```yaml
health_checks:
  enabled: false
  items: []
```

Ejemplo únicamente estructural si posteriormente existen endpoints:

```yaml
health_checks:
  enabled: true
  items:
    - name: CHANGE_ME_COMPONENT
      url: CHANGE_ME_URL
      expected_status: 200
```

Estado: **PENDIENTE / OPCIONAL**

No inventar endpoints.

---

## 3. Servicios base del sistema

Además de GeoPOS, se deben definir los servicios de infraestructura que deben permanecer operativos después de la migración.

En el proyecto implementado, `critical_services` permanece como lista vacía por defecto hasta que se complete con nombres reales:

```yaml
critical_services: []
```

No usar `sshd`/`chronyd` como ejemplo "activo": no son datos confirmados del ambiente y podrían confundirse con una configuración real ya decidida.

Estado: **PENDIENTE — proporcionar la lista real**

La lista definitiva debe basarse en los servicios realmente requeridos.

La automatización debe capturar el estado antes y después de la migración.

---

## 4. Foreman/Katello

Los repositorios utilizados para realizar la migración deben provenir del **Foreman/Katello interno de la organización**.

Este requisito es obligatorio.

Los servidores no deben depender de acceso directo a repositorios públicos de SUSE para ejecutar este procedimiento.

### 4.1 Información pendiente de Foreman/Katello

Completar:

```yaml
katello:
  base_url: CHANGE_ME

  sp6_repositories:
    - name: CHANGE_ME
      url: CHANGE_ME

  sp7_repositories:
    - name: CHANGE_ME
      url: CHANGE_ME

  ca_certificate: CHANGE_ME_IF_REQUIRED
```

Estado: **PENDIENTE**

Antes de implementar el upgrade definitivo se necesita conocer:

- FQDN/URL real de Foreman/Katello;
- repositorios requeridos para SLES 15 SP6;
- repositorios requeridos para SLES 15 SP7;
- módulos/extensiones de SLES que utiliza GeoPOS;
- Content View correspondiente, si aplica;
- Lifecycle Environment correspondiente, si aplica;
- mecanismo de publicación de los repositorios;
- CA interna requerida;
- configuración GPG;
- si las URLs contienen `$releasever` o versiones fijas;
- conectividad desde cada servidor SLES hacia dichas URLs.

### 4.2 Repositorios actuales

Existe un proceso corporativo de parchado independiente que gestiona repositorios en los servidores.

Por esta razón, los repositorios utilizados específicamente por esta automatización para la migración deben considerarse **temporales**.

La automatización:

1. debe inventariar el estado actual;
2. debe respaldar la configuración relevante;
3. no debe eliminar indiscriminadamente repositorios existentes;
4. debe deshabilitar temporalmente los repositorios que interfieran;
5. debe crear/habilitar únicamente los repositorios aprobados para la etapa;
6. debe identificar claramente los repositorios creados por ella;
7. debe retirar sus repositorios temporales después de una migración exitosa;
8. no debe eliminar repositorios pertenecientes a otros procesos.

Prefijo sugerido para repositorios temporales:

```text
ansible-sles-upgrade-
```

En caso de fallo, conservar por defecto la información/configuración necesaria para diagnóstico en vez de realizar una limpieza ciega.

---

## 5. SUSEConnect no participa en la migración

Para este proyecto se ha tomado una decisión operativa explícita:

**La migración utilizará exclusivamente los repositorios internos de Foreman/Katello configurados por el administrador, independientemente del estado de SUSEConnect del servidor.**

Esto aplica si el servidor está:

- registrado;
- parcialmente registrado;
- incorrectamente registrado;
- no registrado.

No utilizar SUSEConnect para descubrir o habilitar los repositorios del Service Pack objetivo.

No intentar reparar el registro.

No utilizar `zypper migration` cuando ello implique dependencia del servicio de registro de SUSE/RMT/SMT para resolver la migración.

La automatización debe trabajar con el conjunto explícito de repositorios Foreman/Katello suministrado para SP6 o SP7 y utilizar el procedimiento oficial de Zypper que sea aplicable a una migración basada en repositorios configurados manualmente.

Si se recopila el estado de SUSEConnect para el reporte, será únicamente información diagnóstica y nunca una condición de éxito o bloqueo.

## 6. Documentación oficial SUSE — fuente técnica prioritaria

Claude debe revisar la documentación oficial añadida al Contexto antes de implementar el procedimiento.

### 6.1 SLES 15 SP6 — Upgrade Guide

Documento principal para estudiar la migración hacia SP6:

**SUSE Linux Enterprise Server 15 SP6 — Upgrade Guide**

URL oficial:

https://documentation.suse.com/sles/15-SP6/single-html/SLES-upgrade/

Secciones especialmente relevantes:

- Upgrade paths and methods
- Upgrading online
- Service pack migration workflow
- Upgrading with Zypper
- Upgrading with plain Zypper

Página específica de actualización online:

https://documentation.suse.com/sles/15-SP6/html/SLES-all/cha-upgrade-online.html

Página de rutas/métodos:

https://documentation.suse.com/sles/15-SP6/html/SLES-all/cha-upgrade-paths.html

### 6.2 SLES 15 SP7 — Upgrade Guide

Documento principal para estudiar la migración hacia SP7:

**SUSE Linux Enterprise Server 15 SP7 — Upgrade Guide**

URL oficial:

https://documentation.suse.com/sles/15-SP7/single-html/SLES-upgrade/

Secciones especialmente relevantes:

- Upgrade paths and methods
- Upgrading online
- Service pack migration workflow
- Upgrading with Zypper
- Upgrading with plain Zypper

Página específica de actualización online:

https://documentation.suse.com/sles/15-SP7/html/SLES-all/cha-upgrade-online.html

Página de rutas/métodos:

https://documentation.suse.com/sles/15-SP7/html/SLES-all/cha-upgrade-paths.html

### 6.3 Qué debe extraerse de estos documentos

Antes de escribir el procedimiento definitivo, determinar explícitamente:

1. qué método de migración es soportado para el escenario real;
2. requisitos del método;
3. preparación del sistema;
4. tratamiento de repositorios;
5. tratamiento de paquetes de terceros;
6. dry-run/prueba previa disponible;
7. opciones recomendadas de Zypper;
8. paquetes que pueden eliminarse/cambiar;
9. reboot requerido;
10. validaciones posteriores;
11. tratamiento de paquetes huérfanos cuando aplique;
12. limitaciones relacionadas con registro y servidores de repositorios.

No copiar comandos de forma aislada sin interpretar las condiciones bajo las cuales SUSE los documenta.

---

## 7. Consideraciones extraídas de la documentación oficial

La documentación oficial indica que la migración online entre Service Packs puede realizarse mediante las herramientas de migración de SUSE y que `zypper migration` depende del flujo de registro/migración correspondiente.

También documenta un procedimiento de **plain Zypper** para sistemas no registrados que no tienen acceso a Internet o a un servidor de registro, siempre que tengan acceso a los orígenes de instalación y a repositorios de actualización adecuados.

Para este proyecto, la documentación relativa a `zypper migration` sirve como referencia general, pero **no define el mecanismo operativo** si requiere integración con un servicio de registro. El mecanismo implementado debe utilizar exclusivamente los repositorios Foreman/Katello declarados por el administrador.

La documentación también enfatiza revisar los cambios propuestos, especialmente paquetes que serían eliminados, y reiniciar después de una migración exitosa.

La implementación final debe contrastar el procedimiento de Zypper basado en repositorios configurados manualmente con la documentación oficial y validar previamente que Foreman/Katello proporciona el contenido completo requerido.

---

## 8. Ruta operacional deseada

Aunque SUSE pueda documentar distintas rutas soportadas según versión y condiciones, para este proyecto la ruta operacional deseada es deliberadamente conservadora:

```text
SP5
 |
 | precheck
 | repos SP6
 | dry-run
 | upgrade
 | reboot
 | validación SO + GeoPOS
 v
SP6
 |
 | solo continuar si SP6 está validado
 | repos SP7
 | dry-run
 | upgrade
 | reboot
 | validación SO + GeoPOS
 v
SP7
 |
 | limpieza controlada
 | reporte final
 v
FIN
```

No realizar SP5 → SP7 directamente dentro de esta automatización.

> **Nota (agregado posterior al análisis inicial)**: el proyecto ya
> construido también soporta `SP4 → SP5` como etapa independiente
> (modo `sp4_to_sp5`), con el mismo patrón precheck → dry-run (`validate`)
> → upgrade → reboot → validación que el diagrama anterior, para hosts que
> todavía están en SP4. **Deliberadamente no se encadena** con el diagrama
> de arriba: `full` sigue siendo exclusivamente SP5 → SP6 → SP7. Ver
> `docs/ARQUITECTURA_Y_DISENO_TECNICO.html` para el razonamiento.

---

## 9. Reportes

Cada ejecución debe producir información suficiente para determinar el estado del servidor sin entrar manualmente al host.

Debe existir un reporte por servidor y por etapa, con un resumen final cuando se realice la migración completa.

Información esperada:

- hostname;
- fecha/hora;
- acción;
- versión inicial;
- versión objetivo;
- versión final;
- kernel antes/después;
- filesystems;
- Zypper;
- repositorios;
- resultado del dry-run;
- resultado del upgrade;
- reboot;
- conectividad;
- servicios críticos antes/después;
- servicios GeoPOS antes/después;
- procesos Java antes/después;
- puertos antes/después;
- health checks si están habilitados;
- limpieza de repositorios temporales;
- estado final `SUCCESS`, `WARNING` o `FAILED`;
- etapa exacta de fallo cuando corresponda.

Las validaciones opcionales deshabilitadas deben poder aparecer como `NOT_CHECKED` y no deben convertir la ejecución en fallo.

### 9.1 Persistencia del reporte

Destino central definitivo:

```text
CHANGE_ME_REPORT_DESTINATION
```

Estado: **PENDIENTE**

No depender exclusivamente del filesystem temporal de un Execution Environment de AWX.

El diseño inicial debe mantener sencilla la generación del reporte, preferiblemente mediante Jinja2 a HTML y/o Markdown/texto.

---

## 10. AWX

La ejecución principal será mediante AWX.

Datos del ambiente AWX pendientes:

```yaml
awx:
  project_name: CHANGE_ME
  inventory_name: CHANGE_ME
  credential_name: CHANGE_ME
  job_template_name: CHANGE_ME
```

No guardar contraseñas ni claves privadas en este documento.

AWX debe permitir seleccionar el alcance de la ejecución. Decisión explícita
del usuario para este ambiente (no se usa `Limit`): el alcance se define con
el match exacto entre `upgrade_crq`/`upgrade_lote`/`upgrade_ambiente` del
Survey y las columnas `CRQ`/`Lote`/`Ambiente` del inventario — ver
`playbooks/upgrade.yml` y README §13.

La ejecución productiva debe utilizar por defecto:

```yaml
serial_batch_size: 1
```

---

## 11. Variables iniciales conceptuales (histórico) — ver el modelo real implementado en el proyecto

> **Nota**: esta sección era un boceto conceptual previo a la implementación.
> El proyecto ya construido **no tiene** `dry_run` ni `reboot_after_upgrade`
> como variables: se decidió deliberadamente no incluirlas (ver
> `docs/ARQUITECTURA_Y_DISENO_TECNICO.html`, sección 5). Para ensayar sin
> modificar nada existe `upgrade_mode: validate`; el reinicio tras una
> migración real es siempre obligatorio. El modelo de variables real y
> vigente vive en `playbooks/group_vars/all.yml` (no aquí, para no
> duplicar valores en dos archivos) — este documento ya no debe usarse
> como referencia de nombres de variables.

```yaml
# Control (ver playbooks/group_vars/all.yml para el modelo real)
serial_batch_size: 1
confirm_production_upgrade: false

# Repositorios
temporary_repo_prefix: ansible-sles-upgrade-
cleanup_repositories_on_failure: false

# Servicios base — vacío hasta tener datos reales del ambiente
critical_services: []

# GeoPOS
geopos_validation:
  enabled: true
  fail_precheck_if_unhealthy: true

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

# Reporte
report_enabled: true
report_destination: CHANGE_ME_REPORT_DESTINATION
```

---

## 12. Información que debe recopilarse antes de producción

### Foreman/Katello

- [ ] URL/FQDN
- [ ] repos SP6
- [ ] repos SP7
- [ ] módulos/extensiones requeridos
- [ ] Content View/Lifecycle Environment si aplica
- [ ] CA
- [ ] GPG
- [ ] prueba de acceso desde SLES

### GeoPOS

- [ ] servicios systemd
- [ ] procesos Java/patrones
- [ ] puertos
- [ ] health checks, si existen
- [ ] estado esperado de cada componente
- [ ] diferencias por grupo/servidor

### Sistema

- [ ] filesystems críticos y umbrales
- [ ] servicios base definitivos
- [ ] política ante servicio previamente caído
- [ ] política ante paquetes a eliminar
- [ ] ventana de mantenimiento
- [ ] mecanismo de backup/snapshot externo, si existe

### AWX

- [ ] Inventory
- [ ] Credential
- [ ] Project
- [ ] Job Template
- [ ] Survey
- [ ] ubicación persistente de reportes
- [ ] Schedule si aplica

---

## 13. Información que NO debe asumirse

Hasta que se suministre evidencia real, no asumir:

- nombres de servicios GeoPOS;
- cantidad de JVM;
- argumentos de JVM;
- puertos;
- URLs de health check;
- URL de Foreman/Katello;
- repositorios necesarios;
- Content Views;
- certificados;
- que todos los hosts están registrados en SUSEConnect;
- que todos los hosts tienen la misma configuración;
- que existe snapshot de VM;
- que una migración puede revertirse automáticamente;
- que alcanzar el SP objetivo significa que GeoPOS está saludable.

---

## 14. Resultado esperado del análisis de contexto

Después de revisar este archivo y los documentos oficiales cargados, antes de generar el proyecto definitivo Claude debe poder responder claramente:

1. qué método de migración recomienda implementar para **este ambiente** y por qué está respaldado por SUSE;
2. cómo se manejarán SP5→SP6 y SP6→SP7;
3. qué información de Foreman/Katello falta;
4. qué información de GeoPOS falta;
5. qué prechecks son bloqueantes;
6. cómo se realizará el dry-run;
7. cómo se comprobará GeoPOS antes/después;
8. cómo se generará el reporte;
9. cómo se conservará el reporte;
10. cuál es la estructura mínima necesaria del proyecto Ansible/AWX.

Si falta información crítica, debe indicarla explícitamente en vez de inventarla.


---

## 15. Uso desde Claude Code

Este archivo es contexto del ambiente, no una lista de permisos para operar infraestructura.

Claude Code debe leer primero `CLAUDE.md` y este archivo antes de diseñar o modificar el procedimiento de upgrade.

Los documentos oficiales SUSE pueden almacenarse bajo `docs/references/` o consultarse desde sus URLs oficiales. Si se descargan copias locales, conservar nombres claros que identifiquen versión y tipo de guía.

Los valores `CHANGE_ME` representan información pendiente del entorno. Claude Code debe mantenerlos visibles y reportarlos como prerequisitos pendientes; no debe sustituirlos con valores inventados.
