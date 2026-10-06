# ansible-sles-upgrade — SLES 15 SP4 → SP5 → SP6 → SP7 (GeoPOS)

Proyecto Ansible/AWX para automatizar el upgrade de Service Pack de servidores
**SUSE Linux Enterprise Server 15**, en los que corre la aplicación Java
**GeoPOS**, utilizando **exclusivamente repositorios internos de
Foreman/Katello**.

> Todos los servidores administrados por este proyecto se consideran
> productivos. Ninguna acción de este proyecto se ejecuta contra
> infraestructura real salvo que un operador la lance explícitamente desde
> AWX (o `ansible-playbook` con inventario real) indicando el alcance con
> CRQ + Lote + Ambiente (sección 13) — el host o los hosts que coincidan
> exactamente con esos 3 valores en el inventario.

Este README cubre la **operación** del proyecto. El diseño técnico y las
decisiones de arquitectura en detalle están en
[`docs/ARQUITECTURA_Y_DISENO_TECNICO.html`](docs/ARQUITECTURA_Y_DISENO_TECNICO.html)
(abrir en cualquier navegador). La presentación ejecutiva está en
`docs/presentacion/`. Antes de la primera ejecución contra un SLES real,
seguir
[`docs/CHECKLIST_LABORATORIO.html`](docs/CHECKLIST_LABORATORIO.html).

---

## 1. Alcance

Este proyecto automatiza:

- **SP4 → SP5** (modo independiente `sp4_to_sp5`, para hosts que todavía están en SP4)
- **SP5 → SP6**
- **SP6 → SP7**
- **SP5 → SP6 → SP7** de forma secuencial (modo `full`)
- Precheck independiente (`precheck`)
- Preflight real independiente contra Foreman (`validate`)

La ruta operacional es siempre secuencial. **Este proyecto nunca realiza
saltos directos de etapa** (ni SP4 → SP6, ni SP5 → SP7). Si una etapa no
queda realmente validada (aplicada, reiniciada y verificada), no se
continúa a la siguiente.

**`sp4_to_sp5` es deliberadamente independiente, no se encadena dentro de
`full`**: el modo `full` sigue siendo exclusivamente `SP5 → SP6 → SP7`. Un
host en SP4 debe ejecutar primero `sp4_to_sp5` por separado y, en una
corrida posterior, `sp5_to_sp6`/`full`. Ver
[`docs/ARQUITECTURA_Y_DISENO_TECNICO.html`](docs/ARQUITECTURA_Y_DISENO_TECNICO.html)
para el razonamiento de esta decisión.

---

## 2. Decisiones de arquitectura (ya aprobadas para este ambiente)

### 2.1 Repositorios exclusivamente Foreman/Katello

El upgrade utiliza únicamente los repositorios que el administrador define
explícitamente en `katello.sp4_repositories` / `katello.sp5_repositories` /
`katello.sp6_repositories` / `katello.sp7_repositories` (ver
`playbooks/group_vars/all.yml`). Esto aplica
tanto al Service Pack de **origen** (usado para `updatestack-only`) como al
de **destino** (usado para `dup`): **ningún repositorio preexistente del
servidor participa nunca** en ninguno de los dos. No se usan repositorios
públicos de SUSE, y **SUSEConnect nunca participa** en la selección,
habilitación o reparación de repositorios. Si se consulta su estado, es
únicamente informativo.

### 2.2 Procedimiento técnico: "plain Zypper" adaptado a Foreman/Katello

La documentación oficial de SUSE (*SLES 15 Upgrade Guide*, sección
**"Upgrading with plain Zypper"**) describe y soporta explícitamente este
procedimiento para **sistemas no registrados** que no tienen acceso a SUSE
Customer Center ni a un servidor de registro, siempre que tengan acceso a
repositorios de instalación/actualización adecuados.

**Importante — salvedad de soporte:** SUSE documenta ese procedimiento para
hosts *no registrados*. Este proyecto lo utiliza contra repositorios
Foreman/Katello **independientemente del estado real de registro del host**
(registrado, mal registrado o no registrado). Esa extensión —usar el mismo
mecanismo técnico también en hosts registrados— es una **decisión de
arquitectura de este proyecto**, tomada para no depender operacionalmente de
SUSEConnect, y no debe presentarse ni interpretarse como una recomendación
oficial de SUSE para hosts registrados.

### 2.3 Uso de `--releasever` (asimetría intencional entre etapas)

Se verificó el texto completo de las tres guías oficiales:

- La guía **SLES 15 SP5 Upgrade Guide** (sección "Upgrading with plain
  Zypper", describe el salto SP4 → SP5) **no menciona `--releasever` en
  ningún lugar**.
- La guía **SLES 15 SP6 Upgrade Guide** (SP5 → SP6) **tampoco menciona
  `--releasever`**.
- La guía **SLES 15 SP7 Upgrade Guide** (SP6 → SP7) **sí usa
  `--releasever=15-SP7`** de forma consistente en `repos -u`, `refresh`,
  `dup -D` y `dup`.

Por lo tanto, este proyecto usa `--releasever` únicamente en la etapa
SP6 → SP7 (tanto en `validate` como en `dup`/`dup -D` de `UPGRADE`), nunca en
SP4 → SP5 ni en SP5 → SP6. Esta asimetría es intencional y está documentada
aquí, no es un error. Ver el diseño técnico completo en
`docs/ARQUITECTURA_Y_DISENO_TECNICO.html`.

### 2.4 Repositorios preexistentes y repos temporales Foreman

Modelo aplicado en **cada** etapa de `UPGRADE` real:

1. Se **inventaría** el estado actual (`zypper repos -u`), clasificando cada
   repo preexistente como habilitado o ya deshabilitado, y se **respalda**
   `/etc/zypp/repos.d/` completo.
2. Se **deshabilitan únicamente los repos preexistentes que estaban
   habilitados**. Los que ya estaban deshabilitados no se tocan (no se les
   hace ninguna llamada a Zypper). Ninguno se borra jamás.
3. Se agregan los repos Foreman de **origen** (alias `...-src-NN`), se
   actualiza la pila de paquetes (`updatestack-only`) **usando
   exclusivamente esos repos**, y se retiran.
4. Se agregan los repos Foreman de **destino** (alias `...-dst-NN`) y se
   ejecuta la migración (`dup -D` como gate, luego `dup` real) **usando
   exclusivamente esos repos**.
5. Al finalizar **exitosamente**, se retiran los repos Foreman de destino.
   Los repos preexistentes que se deshabilitaron **nunca se reactivan
   automáticamente**: esa decisión queda a cargo del **proceso corporativo
   de parchado**, que administra los repositorios "normales" de forma
   independiente a esta automatización.
6. Ante un **fallo**, por defecto no se limpia nada (ni repos temporales ni
   el respaldo), para preservar la información de diagnóstico
   (`cleanup_repositories_on_failure: false`).

El concepto `permanent_repos` **no participa en esta decisión**: es
puramente informativo para un chequeo de precheck ("¿hay repos configurados
que no reconozco?"). No existe ninguna lista de repos que se libren de ser
deshabilitados durante una migración real — todo lo que esté habilitado se
deshabilita, sin excepción, para garantizar que `updatestack`/`dup` vean
exclusivamente los repos Foreman controlados por esta automatización.

---

## 3. Arquitectura del proyecto

```
sles15-upgrade/
├── ansible.cfg                    # habilita inventory_plugins/excel_inventory (sección 13)
├── inventory_plugins/
│   └── excel_inventory.py         # plugin de inventario dinámico (Excel/SharePoint), local al proyecto
├── inventory/
│   ├── hosts.ini                  # inventario de EJEMPLO local
│   └── linux_excel_inventory.yml  # Inventory Source dinámico (Excel/SharePoint, sección 13)
├── playbooks/
│   ├── upgrade.yml                # entrypoint único (todos los modos)
│   ├── report_summary.yml         # consolidación final (resumen.html); también usable como Etapa 4 de un Workflow (sección 13)
│   ├── tasks/run_stage.yml        # lógica común de UNA etapa de migración (soporta upgrade_phase, sección 10.1)
│   ├── group_vars/all.yml         # variables comunes del proyecto (ver sección 6)
│   ├── host_vars/*.yml.example    # excepciones puntuales por host
│   └── roles/                     # DENTRO de playbooks/ a propósito: Ansible busca
│       │                          # "roles/" junto al playbook que se ejecuta, sin
│       │                          # ninguna configuración adicional ni depender del
│       │                          # cwd real con el que corra AWX (ver sección 13)
│       ├── precheck/                  # prechecks + captura de estado + gate GeoPOS
│       ├── repo_management/           # inventario / backup / staging (origen y destino) / cleanup / CA interna
│       │   └── files/coldecom-ca.crt  # CA real "CAColdecom"; instalada automáticamente (sección 5)
│       ├── sp_migration/               # updatestack + dup -D (gate) + dup + reboot + preflight (VALIDATE)
│       ├── geopos_validation/         # validación 0..N servicios/procesos/puertos/health
│       └── reporting/                 # generación de reportes HTML/JSON
├── docs/
│   ├── CONTEXTO_PROYECTO.md
│   ├── ARQUITECTURA_Y_DISENO_TECNICO.html # diseño técnico detallado (abrir en el navegador)
│   ├── CHECKLIST_LABORATORIO.html         # checklist operativo antes del laboratorio
│   ├── AWX_SETUP.html                     # manual paso a paso: crear todo en AWX desde cero
│   ├── references/                # PDFs oficiales SUSE SP5/SP6/SP7
│   │   └── plantilla_inventario_sles15_geopos.xlsx  # plantilla para subir a SharePoint (sección 13)
│   └── presentacion/              # PowerPoint ejecutivo
└── reports/                       # reportes generados (área de trabajo local, ver sección 11)
```

Principios de diseño (evitar sobreingeniería, por instrucción explícita del
proyecto):

- **Un solo playbook de entrada** (`playbooks/upgrade.yml`), controlado por
  la variable `upgrade_mode`.
- **Un solo rol de migración parametrizado** (`sp_migration`), reutilizado
  para SP4→SP5, SP5→SP6 y SP6→SP7 — no hay un rol por Service Pack.
- Roles separados solo donde hay una responsabilidad operacional distinta
  (prechecks, gestión de repos, migración, validación GeoPOS, reporting).

---

## 4. Requisitos

- Ansible **2.15+** (`ansible-core`) en el nodo de control / Execution
  Environment de AWX. No se requieren colecciones externas: todo el
  proyecto usa módulos `ansible.builtin.*`.
- Acceso SSH + privilegios `sudo`/root en los hosts SLES administrados.
- Conectividad desde cada host SLES hacia las URLs de Foreman/Katello que
  se configuren (validado por el rol `precheck`).
- SLES 15 SP5 o SP6 instalado (según la etapa) en los hosts objetivo.
- `python-pptx` solo es necesario si se va a **regenerar** la presentación
  ejecutiva (`docs/presentacion/`); no es una dependencia de ejecución del
  playbook.

---

## 5. Foreman/Katello

Completar en `playbooks/group_vars/all.yml` (bloque `katello`):

```yaml
katello:
  base_url: "https://ansibleforeman.coldecom.com"
  ca_certificate_path: /etc/pki/trust/anchors/coldecom-ca.crt
  sp4_repositories:      # origen de la etapa SP4 -> SP5 (updatestack, modo "sp4_to_sp5")
    - name: SLE-Product-SLES15-SP4-Pool
      url: "https://..."
  sp5_repositories:      # destino de SP4->SP5 (dup) Y origen de SP5->SP6 (updatestack)
    - name: SLE-Product-SLES15-SP5-Pool
      url: "https://..."
  sp6_repositories:      # destino de SP5->SP6 (dup) Y origen de SP6->SP7 (updatestack)
    - name: SLE-Product-SLES15-SP6-Pool
      url: "https://..."
  sp7_repositories:      # destino de la etapa SP6 -> SP7 (dup)
    - name: SLE-Product-SLES15-SP7-Pool
      url: "https://..."
```

(ejemplo abreviado — ver el archivo real para los 10 repos completos por
Service Pack: SUSE Linux Enterprise Server, Basesystem Module, Server
Applications Module, Desktop Applications Module y Python 3 Module,
cada uno con Pool + Updates).

**Estado real (verificado por API contra Foreman/Katello el 2026-10-01,
solo lectura)**: `base_url` y `sp4_repositories`/`sp5_repositories`/
`sp6_repositories`/`sp7_repositories` ya están completos con los 10 repos
reales de cada Service Pack (confirmados sincronizados sin errores). Pendiente
real antes de producción (ver también sección 14):

- `ca_certificate_path` ya apunta a la ruta real que tendrá la CA interna
  **en el host administrado** (`/etc/pki/trust/anchors/coldecom-ca.crt`).
  La CA real (`CAColdecom`) está versionada en
  [`playbooks/roles/repo_management/files/coldecom-ca.crt`](playbooks/roles/repo_management/files/coldecom-ca.crt)
  y **se instala automáticamente** en esa ruta —y se actualiza el almacén
  de confianza del sistema con `update-ca-certificates`— justo antes de
  que se agregue o use cualquier repo Foreman real, tanto en `validate`
  (`playbooks/roles/sp_migration/tasks/preflight.yml`) como en los modos reales de
  `UPGRADE` (`playbooks/roles/repo_management/tasks/add_temp_repos.yml`), vía
  `playbooks/roles/repo_management/tasks/ensure_ca_trusted.yml`. Es la única
  escritura al sistema operativo que ocurre durante `validate` —decisión
  explícita para este ambiente, ver `ARQUITECTURA_Y_DISENO_TECNICO.html`,
  sección 1—, idempotente y sin afectar servicios. Las llaves GPG **no**
  se automatizan preventivamente: verificado por API que Katello no
  re-firma este contenido (`gpg_key_id: null` en productos/repos) — son
  las llaves originales de SUSE, normalmente ya presentes en el keyring
  del SLES desde su instalación base, y las guías oficiales de SUSE para
  este procedimiento no mencionan un paso de importación. Si alguna
  llegara a faltar, `zypper --non-interactive` falla explícito (nunca en
  silencio); ver sección 15.
- Content View y Lifecycle Environment aplicables, si el ambiente llega a
  usar alguno distinto de `Library` (hoy todo el contenido verificado vive
  en `Library`/`Default Organization View`, sin promoción).
- Prueba real de conectividad desde un host SLES hacia esas URLs (el rol
  `precheck` la ejecuta automáticamente cuando hay repos configurados; la
  validación de que Zypper puede usarlas de verdad ocurre en `validate`).

### Ciclo de vida de repositorios en un UPGRADE real

El orden es importante y sigue exactamente el paso 2 de la guía oficial de
SUSE ("plain Zypper"): la pila de gestión de paquetes se actualiza usando
repos Foreman del SP de **origen**, y solo después se reemplazan por los del
SP **destino**. En ningún momento participa un repositorio preexistente del
servidor.

```
inventariar (enabled/disabled) + respaldar /etc/zypp/repos.d/
        │
        ▼
deshabilitar SOLO los preexistentes que estaban enabled (nunca se borran)
        │
        ▼
agregar repos Foreman de ORIGEN (alias ...-src-NN)
        │
        ▼
zypper --non-interactive refresh -f ansible-sles-upgrade-<sp>-src-01 [...]   (SOLO esos alias, nunca -s/--services)
        │
        ▼
zypper --non-interactive patch --updatestack-only   (usa EXCLUSIVAMENTE los repos -src-)
        │
        ▼
retirar los repos Foreman de ORIGEN (ya cumplieron su función)
        │
        ▼
agregar repos Foreman de DESTINO (alias ...-dst-NN)
        │
        ▼
zypper [--releasever=...] --non-interactive refresh -f ansible-sles-upgrade-<sp>-dst-01 [...]   (SOLO esos alias)
        │
        ▼
dup -D (gate obligatorio, usa EXCLUSIVAMENTE los repos -dst-)
        │
        ▼
dup real -> reboot obligatorio -> validar (SP + servicios + GeoPOS)
        │
        ├── éxito/warning ──► retirar repos Foreman de DESTINO
        │
        └── fallo ──► se conservan todos los repos temporales (diagnóstico),
                       salvo cleanup_repositories_on_failure: true
```

**`refresh` nunca usa `-s`/`--services`**: en Zypper, `-s` significa
`--services`, y refresca *todos* los servicios de repositorios configurados
en el sistema — este proyecto no usa servicios de Zypper para descubrir
repositorios (los repos Foreman se agregan explícitamente), así que usar
`-s` podría introducir repositorios ajenos al conjunto controlado. Por eso
`refresh` siempre recibe, como argumentos explícitos, únicamente los alias
temporales creados en esa fase.

Esto se verificó de extremo a extremo con un Zypper simulado (ver sección
16): `updatestack` solo vio el repo `-src-`, `dup`/`dup -D` solo vieron el
repo `-dst-`; ningún repo preexistente participó en ninguno de los dos;
ningún `refresh` se ejecutó con `-s`/`--services`.

---

## 6. Variables — `playbooks/group_vars` / `playbooks/host_vars`

### 6.1 Por qué las variables viven junto al playbook, no junto al inventario

Ansible carga automáticamente `group_vars/`/`host_vars/` desde **dos**
ubicaciones: el directorio del inventario en uso, y el directorio del
**playbook que se ejecuta**. Localmente usamos `inventory/hosts.ini`, pero
en AWX el Job Template usa el **Inventory de AWX** (una fuente distinta,
que no es un archivo de este repositorio) — si las variables del proyecto
vivieran en `inventory/group_vars/`, dejarían de cargarse en cuanto AWX
sustituyera el inventario local por el suyo.

Por eso las variables comunes viven en **`playbooks/group_vars/all.yml`**
y las excepciones por host en **`playbooks/host_vars/<hostname>.yml`**:
como `playbooks/upgrade.yml` es el playbook que se ejecuta tanto local como
en AWX, Ansible las carga igual en ambos casos, sin importar qué Inventory
se use. `inventory/hosts.ini` queda reducido a un ejemplo mínimo de
hosts/grupos para pruebas locales — nunca es la fuente de variables del
proyecto.

Resumen de los bloques principales de `playbooks/group_vars/all.yml` (ver
el archivo, extensamente comentado, para el detalle):

- **Control**: `upgrade_mode`, `serial_batch_size`, `confirm_production_upgrade`.
  No existen `dry_run` ni `reboot_after_upgrade`: ver sección 9.
- **Foreman/Katello**: `katello.*` (`sp5_repositories`, `sp6_repositories`,
  `sp7_repositories`), `temporary_repo_prefix`, `cleanup_repositories_on_failure`.
  `permanent_repos` es puramente informativo (sección 2.4).
- **Sistema**: `critical_services` (vacía por defecto — CHANGE_ME real),
  `precheck_disk_checks`, `precheck_btrfs_double_space_check`.
- **GeoPOS**: `geopos_validation.*` (ver sección 7).
- **Reportes**: `report_enabled`, `report_local_dir`, `report_destination`.

Excepciones puntuales por host: `playbooks/host_vars/<hostname>.yml` (ver
`playbooks/host_vars/CHANGE_ME_HOSTNAME_1.yml.example`) — el nombre de
archivo debe coincidir con el `inventory_hostname` real tal como lo expone
el Inventory que se esté usando (local o de AWX).

### 6.2 Precedencia (de menor a mayor prioridad efectiva)

1. Valores por defecto de cada rol (`roles/*/defaults/main.yml`) — detalles
   técnicos internos, no datos de negocio.
2. Variables de grupo/host definidas **dentro del Inventory de AWX**
   (o en `inventory/hosts.ini` localmente), si se definieran ahí.
3. **`playbooks/group_vars/all.yml`** — la configuración base del proyecto.
4. **`playbooks/host_vars/<hostname>.yml`** — excepciones puntuales por host.
5. **Survey / extra-vars de AWX** (o `-e` en `ansible-playbook`) — **siempre
   gana**, sin excepción.

**Consecuencia práctica a tener presente**: los niveles 3 y 4 (nuestros
archivos, versionados en este repositorio) tienen **más prioridad** que una
variable con el mismo nombre definida directamente en el Inventory de AWX
(nivel 2). Por diseño, este proyecto reserva el Inventory de AWX para lo
que le es propio — hosts, grupos, y variables de **conexión** (`ansible_host`,
`ansible_user`, credenciales, etc., que este repositorio nunca define y por
lo tanto nunca entran en conflicto) — y mantiene toda variable de **negocio**
del proyecto (Foreman/Katello, GeoPOS, servicios críticos, reportes) en
`playbooks/group_vars`/`host_vars`, versionada y revisable. Si en algún
momento se necesitara una excepción real solo para un host, se resuelve
editando `playbooks/host_vars/<hostname>.yml` en el repositorio — no
definiendo la misma variable en el Inventory de AWX, donde quedaría
silenciosamente ignorada por la precedencia anterior. Para cambios
puntuales de una sola ejecución (por ejemplo, `upgrade_mode` o
`confirm_production_upgrade`), use siempre el Survey de AWX: al ser
extra-vars, siempre tiene la última palabra.

No se duplica ningún valor entre `inventory/` y `playbooks/`: las
variables del proyecto existen en un único lugar.

---

## 7. Validación de GeoPOS

Modelo 0..N por categoría, cada una habilitable/deshabilitable de forma
independiente, con `critical: true` por defecto en cada ítem:

```yaml
geopos_validation:
  enabled: true
  fail_precheck_if_unhealthy: true   # bloquea el upgrade si un ítem crítico está insalubre

  services:
    enabled: true
    items:
      - name: CHANGE_ME_GEOPOS_SERVICE_1
        critical: true              # default; usar critical: false para informativo

  java_processes:
    enabled: true
    items:
      - name: CHANGE_ME_COMPONENT_1
        match: CHANGE_ME_PROCESS_PATTERN_1   # patrón específico, nunca "java" a secas
        critical: true

  tcp_ports:
    enabled: true
    items:
      - name: CHANGE_ME_COMPONENT_1
        port: CHANGE_ME_PORT_1
        critical: true

  health_checks:
    enabled: false                  # opcional; activar solo si existen endpoints reales
    items: []
```

Reglas:

- Una categoría deshabilitada, o GeoPOS deshabilitado globalmente, se
  reporta como `NOT_CHECKED` (nunca como `FAILED`).
- Una lista vacía en una categoría habilitada se reporta `OK` (nada que
  validar).
- **Antes** del upgrade: si algún ítem `critical: true` está insalubre y
  `fail_precheck_if_unhealthy: true` (global, o sobrescrito en
  `host_vars`/`group_vars` para una excepción operacional autorizada), el
  **precheck bloquea el upgrade** para ese host.
- **Después** de una migración real aplicada, se vuelve a validar GeoPOS
  incondicionalmente (independientemente de `fail_precheck_if_unhealthy`):
  si un componente crítico queda insalubre tras el upgrade, la etapa se
  marca `FAILED` — alcanzar el Service Pack objetivo **no** es, por sí
  solo, criterio de éxito (ver sección 8.3).
- El patrón de proceso Java (`match`) debe identificar específicamente el
  componente GeoPOS (se usa con `pgrep -f`); un patrón como `java` no es
  válido para este propósito.

---

## 8. PRECHECK, VALIDATE y UPGRADE — tres cosas distintas

Este proyecto distingue deliberadamente tres niveles, cada uno con un
propósito propio. No son sinónimos ni pasos intercambiables:

| | **PRECHECK** | **VALIDATE** | **UPGRADE** (`sp5_to_sp6` / `sp6_to_sp7` / `full`) |
|---|---|---|---|
| Propósito | Salud y preparación del **servidor** | Simulación **real** del upgrade **contra Foreman** | Ejecución real, **con modificación del servidor** |
| ¿Toca `/etc/zypp/repos.d`? | No | No (usa un directorio de repos aislado y temporal, ver 8.2) | Sí (backup, deshabilitar, agregar temporales, limpiar) |
| ¿Contacta los repos Foreman? | Solo conectividad HTTP/HTTPS básica | Sí, con Zypper real (metadata, GPG, solver) | Sí (igual que VALIDATE, pero de forma persistida) |
| ¿Puede dejar el sistema modificado? | Solo la CA interna, si faltaba (ver 8.1) | Igual que PRECHECK (misma CA, si faltaba) | Sí, además, únicamente si `confirm_production_upgrade: true` |
| ¿Puede terminar "OK" sin haber comprobado nada realmente? | N/A | **No** — si el preflight no se pudo ejecutar, el resultado es `FAILED` o `NOT_CHECKED`, nunca `OK` | N/A |

### 8.1 PRECHECK (rol `precheck`) — no destructivo, con una única excepción documentada

No modifica repositorios ni paquetes (verificado en la sección 16: cero
llamadas a `addrepo`/`removerepo`/`modifyrepo`, estado de repos
byte-idéntico antes/después).

**Única excepción, decisión explícita del usuario para este ambiente**:
`repos_reachability.yml` instala la CA interna real ("CAColdecom",
`playbooks/roles/repo_management/files/coldecom-ca.crt`) en el almacén de
confianza del sistema, **si todavía no está presente**, antes de probar
conectividad HTTPS contra Foreman. Sin esto, un host que nunca ejecutó
`validate`/un upgrade real antes reportaría `FAILED` en esos checks
únicamente por falta de confianza TLS, no por un problema real de
red/Foreman (confirmado en laboratorio: 20 checks `endpoint_alcanzable_*`
con `CERTIFICATE_VERIFY_FAILED`). Es una operación idempotente y no
destructiva — agrega una CA de confianza si falta; no reinicia nada, no
toca servicios, no elimina ninguna CA existente (ver
`playbooks/roles/repo_management/tasks/ensure_ca_trusted.yml`). Al ejecutarse
siempre antes que `UPGRADE` real (ver `playbooks/tasks/run_stage.yml`),
esta misma instalación cubre también a `UPGRADE`, que ya no necesita
instalarla por su cuenta.

Valida (ver `playbooks/roles/precheck/tasks/`):

- **Gate de sistema operativo (primera verificación, obligatoria)**:
  `ansible_facts['distribution'] == 'SLES'`. Si el Inventory incluye
  servidores con otros sistemas operativos (por ejemplo, un inventario
  dinámico corporativo compartido con otras automatizaciones), un host que
  no sea SLES queda `FAILED` de inmediato con el mensaje "Sistema operativo
  detectado: X — NO COMPATIBLE", y **ninguna otra verificación ni acción**
  se ejecuta sobre ese host (ni locks, ni espacio en disco, ni inventario
  de repos, ni GeoPOS). Verificado con RedHat/Ubuntu simulados.
- **Inventario de repositorios actuales**: alias, nombre y si están
  habilitados o no (de solo lectura; queda en el reporte).
- Repositorios de terceros/no esperados frente a `permanent_repos`
  (informativo/`WARNING`; nunca se actúa automáticamente sobre ellos aquí).
- **Repos Foreman de ORIGEN y de DESTINO de la etapa, ambos, antes de
  tocar cualquier repositorio preexistente**: que `katello.<sp>_repositories`
  esté configurado (no vacío) tanto para el Service Pack de origen como
  para el de destino, que no contenga valores `CHANGE_ME` sin completar, y
  que sus URLs sean alcanzables (conectividad + TLS/CA básico, sección
  8.2 para la validación real). Si falta cualquiera de los dos conjuntos,
  el precheck **bloquea** (`FAILED`) antes de que `repo_management`
  deshabilite ningún repositorio preexistente — evita descubrir a mitad de
  camino que falta el repo de origen o de destino.
- **Service Pack actual = el esperado** para la
  etapa solicitada (bloqueante si no coincide), verificado con **doble
  evidencia**: `/etc/os-release` (`VERSION_ID`) y `zypper --xmlout
  products -i` (segunda fuente, comparada por consistencia; una
  discrepancia se reporta `WARNING`, no `FAILED`, porque el formato exacto
  del atributo de versión de Zypper en un Service Pack no está confirmado
  en la documentación oficial — ver riesgos, sección 16).
- Arquitectura, hostname, kernel, uptime (informativo, para el reporte).
- Espacio en disco: filesystems configurados en `precheck_disk_checks`
  (0..N, sin umbrales inventados — permanece `NOT_CHECKED` hasta que se
  definan valores reales) + verificación dinámica de la recomendación de
  SUSE para raíz Btrfs con snapshots (disponible ≥ usado).
- Locks de Zypper/RPM/libzypp activos (bloqueante si Zypper reporta el
  sistema bloqueado).
- Privilegios de escalamiento (`become`) realmente funcionales.
- Disponibilidad de Zypper.
- Servicios críticos del sistema (`critical_services`) — bloqueante si
  alguno no está `active`.
- **Conectividad básica** hacia las URLs Foreman/Katello de la etapa
  objetivo: una petición HTTP/HTTPS simple (sin invocar Zypper, sin agregar
  el repo). Un HTTP 401/403/404 se reporta como `WARNING` ("endpoint
  alcanzable"), **no** como prueba de que el repositorio sea utilizable —
  esa validación real ocurre en VALIDATE, nunca aquí.
- Validación de GeoPOS "antes" con el gate de la sección 7.

Una condición insegura para continuar **falla explícitamente** (no se
oculta con `ignore_errors`).

### 8.2 VALIDATE — preflight REAL de la migración, sin dejar cambios

`validate` va más allá de una prueba de conectividad: ejecuta un
**preflight real de Zypper contra los repos Foreman de la etapa
siguiente**, para comprobar de verdad acceso a metadata, TLS/CA, GPG,
resolución de dependencias, y qué paquetes se actualizarían/instalarían/
degradarían/eliminarían — **sin modificar `/etc/zypp/repos.d` ni instalar
nada**.

**Mecanismo — `--reposd-dir` (no `--disable-repositories`/`--plus-repo`):**
se evaluó usar `--disable-repositories` + `--plus-repo`, pero
`--disable-repositories` está documentada únicamente como *"Do not read
meta-data from repositories"* — no hay evidencia documental de que
garantice que el solver use **exclusivamente** los repos indicados por
`--plus-repo`. Se optó por el mecanismo inequívoco: la opción global
`--reposd-dir <dir>` (*"Use alternative repository definition file
directory"*) hace que Zypper **solo pueda ver** los repos definidos en ese
directorio, porque es el único lugar donde busca definiciones de
repositorio. **Alcance exacto**: `--reposd-dir` aísla los archivos `.repo`
(dónde busca Zypper definiciones de repositorio); no se afirma ni se asume
que también aísle servicios de Zypper (`services.d`) u otros componentes.
`playbooks/roles/sp_migration/tasks/preflight.yml`:

1. Verifica con `zypper --help` que el Zypper del host soporta
   `--reposd-dir`. Si no lo soporta, **no se inventa una alternativa**: el
   resultado queda `NOT_CHECKED` con el motivo explícito.
2. Crea un directorio temporal vacío (p. ej.
   `/var/tmp/ansible-sles-upgrade-validate-sp7-<timestamp>/`), sin ninguna
   relación con `/etc/zypp/repos.d`.
3. Agrega allí, con `zypper --reposd-dir <dir> --non-interactive addrepo`,
   únicamente los repos Foreman de la etapa objetivo, y refresca
   **exclusivamente esos alias** (nunca `-s`/`--services`, por la misma
   razón que en UPGRADE: sección 5).
4. Ejecuta `dup -D --no-allow-vendor-change --no-recommends` contra ese
   mismo directorio aislado — el chequeo real de metadata + TLS/CA + GPG +
   solver contra el Service Pack de **destino**.
5. Opcionalmente, si se le indican repos de **origen**
   (`sp_migration_origin_repositories`), hace lo mismo en un **segundo
   directorio aislado independiente** pero solo con `refresh` (sin `dup`,
   ya que verificar que el origen es accesible no requiere calcular una
   migración): confirma que los repos Foreman del Service Pack de origen
   también son alcanzables y su metadata es válida, sin mezclarlos nunca
   con los de destino.
6. **Siempre** (éxito o fallo) elimina ambos directorios temporales al final.

Si el repositorio Foreman requiere una clave GPG que el host aún no tiene
importada/confiada, el comando fallará limpiamente (no se usa
`--gpg-auto-import-keys` ni `--no-gpg-checks`): eso es exactamente lo que
VALIDATE debe detectar, no algo que deba ocultarse. Importar esa clave GPG
como prerrequisito real del ambiente es responsabilidad del administrador
(ver sección 14).

**Regla explícita: VALIDATE nunca es "OK" si el preflight no se ejecutó
realmente — ni siquiera parcialmente.** El resultado global combina origen
y destino con esta prioridad estricta:

```
FAILED en origen o en destino          -> global FAILED
si no, NOT_CHECKED en origen           -> global NOT_CHECKED
si no (origen OK y destino OK)         -> global OK
```

Esto significa que **si solo se verificó el destino y falta el origen**
(por ejemplo, `katello.sp5_repositories` sin configurar todavía para una
etapa SP5→SP6), el resultado global es `NOT_CHECKED`, **nunca `OK`** —
aunque el `dup -D` contra el destino haya salido perfecto. Verificar solo
la mitad del procedimiento real (falta `updatestack` contra el origen) no
es una validación completa. De la misma forma, si no hay repos Foreman
configurados en absoluto, o el Zypper del host no soporta `--reposd-dir`,
o cualquiera de los dos chequeos falla, el resultado queda en `NOT_CHECKED`
o `FAILED` respectivamente — el Job de AWX se marca como no exitoso para
que quede visible que la validación no se completó, sin tener que abrir
el reporte.

`validate` también reutiliza los chequeos básicos de PRECHECK (SO/SP,
inventario de repos, servicios críticos, GeoPOS) para dar contexto
completo en un solo reporte, pero **el resultado de VALIDATE nunca
bloquea ni condiciona una ejecución posterior de UPGRADE**: son modos
independientes que un operador puede invocar por separado.

### 8.3 Verificación post-reboot en UPGRADE (no basta con `/etc/os-release`)

Después de una migración real aplicada (ver sección 9), se recaptura el
estado del sistema en un hecho **separado y explícito**
(`system_state_snapshot_after`, nunca se sobrescribe
`system_state_snapshot_before`), y se revalidan servicios críticos y
GeoPOS. El Service Pack alcanzado se confirma con **doble evidencia real
como gate**, no solo con `/etc/os-release`: son necesarias las tres
condiciones siguientes, todas obligatorias:

1. `/etc/os-release` (`VERSION_ID`) reporta el Service Pack objetivo.
2. Hay evidencia de `zypper products` **disponible** (el parser la
   reconoció). **Si no la hay, la etapa queda `FAILED`** — no se continúa
   basándose únicamente en `os-release`. Si en el laboratorio real el
   formato de `zypper products` no coincide con lo esperado, este
   comportamiento es intencional: el objetivo es que un Service Pack nunca
   se dé por bueno solo porque `/etc/os-release` lo diga, y el reporte
   deja evidencia completa (`zypper_products_xml_evidence`) para corregir
   el parser en vez de continuar automáticamente sobre un supuesto no
   confirmado.
3. Ambas evidencias son **consistentes** entre sí (sección 7 de
   `docs/ARQUITECTURA_Y_DISENO_TECNICO.html`).

La etapa se marca `FAILED` si cualquiera de las tres no se cumple, si un
servicio crítico falla, o si un componente GeoPOS crítico queda insalubre
— aunque el SP del sistema operativo sea el correcto. Solo si todo esto
pasa (`OK` o `WARNING`, nunca `FAILED`) se activa `stage_validated: true`,
el gate real que permite continuar a la
siguiente etapa en modo `full` (ver sección 10).

---

## 9. UPGRADE real (modos `sp4_to_sp5` / `sp5_to_sp6` / `sp6_to_sp7` / `full`)

Orden exacto por etapa (ver `playbooks/tasks/run_stage.yml` — es el mismo
código genérico para las cuatro combinaciones de origen/destino, parametrizado
por `stage_current_sp`/`stage_target_sp`/`stage_releasever`):

1. **Precheck LIGERO** de la etapa (solo Service Pack actual vs. esperado
   para este salto exacto — no repite locks/disco/inventario de repos/
   alcanzabilidad/GeoPOS, ya cubiertos por el precheck completo de la
   Etapa 1 del Workflow, sección 13). Si falla, no se continúa. En la
   alternativa simplificada de un solo Job Template (sin Etapa 1 previa),
   sigue siendo la única verificación de Service Pack antes de modificar
   nada.
2. **`confirm_production_upgrade: true` (assert obligatorio)**. Esta
   verificación ocurre **antes** de tocar cualquier repositorio, antes del
   backup, antes de `updatestack` y antes de cualquier paquete. Si es
   `false`, la etapa termina en `FAILED` sin haber modificado absolutamente
   nada (verificado en la sección 16: estado de repos idéntico antes/después,
   cero llamadas a Zypper de escritura).
3. **Inventario + backup** de `/etc/zypp/repos.d` (sección 2.4).
4. **Deshabilitar** únicamente los repos preexistentes que estaban
   habilitados.
5. **Repos Foreman de origen** (`...-src-NN`) → `zypper --non-interactive
   refresh -f <alias-src-01> [<alias-src-02> ...]` (solo esos alias, nunca
   `-s`/`--services`) → `zypper --non-interactive patch --updatestack-only`
   (con reintentos: el propio Zypper puede pedir una segunda pasada tras
   actualizarse a sí mismo) → **retirar** esos repos de origen.
6. **Repos Foreman de destino** (`...-dst-NN`) → `zypper [--releasever=...]
   --non-interactive refresh -f <alias-dst-01> [<alias-dst-02> ...]` (ídem:
   solo esos alias, nunca `-s`/`--services`).
7. **`dup -D` como gate obligatorio**, inmediatamente antes del `dup` real,
   usando exclusivamente los repos de destino. Si falla, la etapa se
   detiene en `FAILED` **sin** ejecutar el `dup` real ni reiniciar.
8. **`dup` real** (`--no-allow-vendor-change --no-recommends`). Inmediatamente
   después de que termine exitosamente, se marca `dup_applied: true` — esta
   evidencia queda fija y **no se pierde aunque el reinicio falle después**.
   Luego, revisión de paquetes huérfanos/no necesarios (informativo, no se
   eliminan automáticamente).
9. **Reinicio obligatorio** (`ansible.builtin.reboot`) — no existe una
   opción para omitirlo. Su resultado se registra por separado:
   `reboot_completed` y `reconnected`. Si el reinicio o la reconexión
   fallan, la etapa termina en `FAILED` con esa causa exacta (`reboot_fallido`),
   **conservando** `dup_applied: true` y sin intentar la validación
   post-reboot (no tendría sentido si no se pudo reconectar).
10. **Validación post-reboot** (sección 8.3, solo si el reinicio se
    completó) → determina `stage_validated`.
11. **Limpieza**: si la etapa fue exitosa (`OK`/`WARNING`), se retiran
    únicamente los repos Foreman de destino de esta etapa. Si falló (en
    cualquier punto, incluido un reinicio fallido), se conservan
    (diagnóstico) — incluyendo el inventario final de qué quedó
    habilitado —, salvo `cleanup_repositories_on_failure: true`.

No existe una variable `dry_run` para estos modos ni una opción para omitir
el reinicio: para **ensayar sin modificar nada**, use `upgrade_mode:
validate` (sección 8.2). Un modo real siempre ejecuta el gate `dup -D`
internamente, de forma obligatoria, inmediatamente antes del `dup` real.

---

## 10. Modos de ejecución (`upgrade_mode`)

| Modo | Qué hace | Modifica el sistema |
|---|---|---|
| `precheck` | Salud y preparación del servidor: prechecks de la sección 8.1 (etapa objetivo autodetectada) | No, salvo instalar la CA interna si falta (idempotente, ver sección 8.1) |
| `validate` | Preflight real del upgrade contra Foreman (sección 8.2): metadata, TLS/CA, GPG y solver de Zypper, más los chequeos básicos de precheck | No |
| `sp4_to_sp5` | Ejecuta la etapa SP4→SP5 completa (para hosts que todavía están en SP4). **Independiente**: nunca se encadena dentro de `full` | Sí, si `confirm_production_upgrade: true` |
| `sp5_to_sp6` | Ejecuta la etapa SP5→SP6 completa (ver secciones 8-9) | Sí, si `confirm_production_upgrade: true` |
| `sp6_to_sp7` | Ejecuta la etapa SP6→SP7 completa | Sí, si `confirm_production_upgrade: true` |
| `full` | Ejecuta SP5→SP6 y, **solo si `stage_validated` quedó en `true`** (dup aplicado + reiniciado + reconectado + SP confirmado + servicios críticos OK + GeoPOS crítico OK) — o si el host ya partía de SP6 —, continúa con SP6→SP7. **Nunca incluye SP4→SP5** | Sí, si `confirm_production_upgrade: true` |

El gate hacia SP7 en modo `full` usa la bandera explícita `stage_validated`
(no simplemente "¿se aplicó el dup?"): un `dup` aplicado pero con un
reinicio fallido, un Service Pack final que no coincide, un servicio
crítico caído, o un componente GeoPOS crítico insalubre tras el upgrade,
**todos** dejan `stage_validated: false` y SP7 no se ejecuta. Esto se
verificó explícitamente con 4 casos de prueba (sección 16).

**Por qué `full` no incluye SP4→SP5**: es una decisión explícita, no una
limitación técnica — `run_stage.yml` es genérico y soportaría encadenarlo
igual que SP6→SP7. Se mantuvo fuera para no ampliar el alcance de lo que
ya estaba validado/congelado; un host en SP4 ejecuta primero `sp4_to_sp5`
de forma independiente y, en una corrida posterior, `sp5_to_sp6` o `full`.
Si se ejecuta `full` directamente sobre un host en SP4, el precheck de la
etapa `sp5_to_sp6` falla explícitamente en `service_pack_actual` (espera
SP5, encuentra SP4) — no hay riesgo de que se salte la etapa SP4→SP5
silenciosamente.

Cada modo produce su propio reporte por host (sección 11).

### 10.1 `upgrade_phase`: partir una etapa real en 2 corridas separadas

Para `sp4_to_sp5`/`sp5_to_sp6`/`sp6_to_sp7` (no para `full`, ver más abajo),
`upgrade_phase` permite dividir lo que hace `run_stage.yml` en 2 pasos — es
lo que usan, por defecto, los nodos 2 y 3 del Workflow Job Template de AWX,
con un Approval Node opcional entre ambos (ver `docs/AWX_SETUP.html`,
sección 7):

| `upgrade_phase` | Qué hace | Modifica el sistema |
|---|---|---|
| `both` (default) | Todo en una sola corrida, como siempre: backup → deshabilitar preexistentes → repos ORIGEN + `updatestack` → repos DESTINO → `dup -D` → `dup` real → reinicio → validar → limpiar | Sí |
| `prepare` | Backup → deshabilitar preexistentes → repos ORIGEN + `updatestack` (real) → repos DESTINO agregados y verificados. Se detiene ahí | Sí (pero sin `dup`/reinicio) |
| `apply` | Gate: verifica que los repos DESTINO de una fase `prepare` previa sigan exactamente habilitados (si no, falla explícito) → `dup -D` → `dup` real → reinicio → validar → limpiar | Sí |

**`upgrade_mode: full` ignora `upgrade_phase`** (siempre se comporta como
`both` para cada uno de sus 2 saltos encadenados: no existe un único momento
de "preparar" válido para SP5→SP6 y SP6→SP7 a la vez) — **excepto**
`upgrade_phase: prepare`, que en ese caso específico no hace absolutamente
nada (ver `_effective_upgrade_phase` en `playbooks/tasks/run_stage.yml`),
para que un mismo diseño de Workflow sirva tanto para un salto individual
como para `full` sin arriesgar un `dup` real por error en el nodo que se
supone que solo prepara.

---

## 11. Reportes

- Por cada host y etapa se genera un reporte **HTML** (con el detalle de
  prechecks, preflight, ciclo de vida completo de repositorios, migración,
  reinicio, servicios críticos y GeoPOS antes/después, y el estado final) y
  su equivalente **JSON** (mismo contenido, para auditoría/integración).
- El reporte muestra `upgrade_crq`/`upgrade_lote`/`upgrade_ambiente` (Survey
  de AWX) como `crq`/`lote`/`ambiente` (control de cambios) — además de
  quedar en el reporte, estos 3 valores son el criterio con el que se
  seleccionó el host de esta ejecución (sección 13); se omiten de la vista
  si están vacíos (ejecuciones locales de prueba sin match).
- El bloque de repositorios del reporte muestra explícitamente:
  `repos_enabled_before`, `repos_disabled_before`, `repos_disabled_by_upgrade`,
  `repos_temporary_created`, `repos_temporary_removed`, `repos_enabled_after`.
- Estados usados: `OK`, `WARNING`, `FAILED`, `NOT_CHECKED`.
- Cada ejecución añade una línea a `reports/run_summary.jsonl`, y al final
  de la ejecución se genera `reports/resumen.html`: un resumen consolidado
  con el **último estado conocido de cada host y etapa**, para que el
  operador pueda ver el resultado sin conectarse por SSH ni leer todo el
  log del Job de AWX.

### Persistencia (`report_destination`) — advertencia importante

`report_local_dir` es únicamente el **área de trabajo** mientras corre el
playbook (por defecto `reports/`, relativo al proyecto). **Esto NO es
almacenamiento persistente**: el filesystem del Execution Environment de
AWX puede ser efímero incluso para "localhost" y desecharse al terminar el
Job. Escribir ahí primero no garantiza nada por sí solo.

**Estado real**: `report_destination` ya está configurado en
`playbooks/group_vars/all.yml` como `/data/work/Salida_Upgrade` — una ruta
de archivo, copiada con `delegate_to: localhost` + `remote_src: true`
(`playbooks/roles/reporting/tasks/main.yml`), es decir, **en el mismo nodo de
control/Execution Environment donde corre Ansible**, nunca en el servidor
SLES administrado.

**Dos cosas que solo se pueden confirmar en el AWX real** (no verificables
desde el desarrollo de este proyecto):

1. Que `/data/work/Salida_Upgrade` **exista y tenga permisos de escritura**
   para el usuario con el que corre el Job — el módulo `copy` no crea
   directorios padre inexistentes, así que si no existe, la copia fallará
   (de forma controlada: queda como `WARNING` en el log, el reporte local
   en `report_local_dir` sigue disponible, nunca se pierde evidencia).
2. Que sea **realmente persistente**: si el Execution Environment de ese
   AWX es un contenedor que se destruye al terminar el Job,
   `/data/work/Salida_Upgrade` debe estar montada desde fuera de ese
   contenedor (un volumen/mount persistente) — si es solo una ruta dentro
   del propio contenedor efímero, no cumple su propósito.

Confirmar ambos puntos en la primera ejecución real revisando el bloque
"Persistencia del reporte" del reporte HTML generado.

### 11.1 Estructura de carpetas de los reportes

Tanto `report_local_dir` como `report_destination` organizan los reportes
individuales (HTML + JSON) con el mismo árbol de 3 niveles:

```
<CRQ sanitizado>/<hostname>/<etapa>/<etapa>_<timestamp>.html
<CRQ sanitizado>/<hostname>/<etapa>/<etapa>_<timestamp>.json
```

- **CRQ sanitizado**: `upgrade_crq` (el CRQ/RFC declarado en el Survey, sección 13),
  con espacios y caracteres especiales convertidos a `_` (ej. `RFC 2026-PRUEBA` →
  `RFC_2026-PRUEBA`). Si quedó vacío (ejecución local sin Survey), la carpeta es
  `SIN_CRQ`.
- **etapa**: `{{ action }}` para `precheck`/`validate`/`full`, o
  `{{ action }}_{{ phase }}` cuando `upgrade_phase` (sección 10.1) es `prepare` o
  `apply` (ej. `sp5_to_sp6_prepare`, `sp5_to_sp6_apply`) — `both` no se agrega al
  nombre, para no generar una carpeta redundante.

`run_summary.jsonl` y `resumen.html` (el resumen consolidado) se quedan en la raíz
de `report_local_dir`/`report_destination`, fuera de este árbol — abarcan todos los
CRQ/hosts/etapas, no uno en particular.

### 11.2 Sincronización a SharePoint (Etapa 5 opcional del Workflow)

`playbooks/sync_sharepoint.yml` sube hacia una carpeta real de SharePoint (sitio
`AreaInfraestructura`, misma cuenta que usa el inventario dinámico — ver
`playbooks/group_vars/all.yml`, `sharepoint_sync`) el subárbol completo de
`report_destination/<CRQ sanitizado>/` correspondiente al `upgrade_crq` de esta
ejecución — **nunca** `report_local_dir`, que es efímero y no sobrevive entre
nodos separados del Workflow (cada nodo es un Job de AWX independiente). Usa la
API REST de Microsoft Graph directamente (sin dependencias de Python
adicionales): token por client credentials, resolución del sitio, y un `PUT` por
archivo. Requiere las mismas credenciales que el inventario dinámico
(`TENANT_ID`/`CLIENT_ID`/`CLIENT_SECRET`) adjuntas también a este Job Template, y
que el App Registration de Azure AD tenga permiso de **escritura** en SharePoint
(`Sites.ReadWrite.All`) — el inventario dinámico solo necesitaba lectura; esto no
se pudo confirmar desde el desarrollo de este proyecto. Ver
`docs/AWX_SETUP.html`, sección 7, para la configuración completa de esta etapa.

---

## 12. Comportamiento ante fallos

- Ningún fallo se oculta con `ignore_errors: true` de forma general. Los
  puntos donde una falla es "capturable" (para poder seguir generando el
  reporte de la etapa) usan `block/rescue` explícito, registrando la causa
  exacta en `failure_stage`.
- Un host que falla en una etapa **no detiene** el procesamiento de los
  demás hosts del batch (comportamiento estándar de Ansible sin
  `any_errors_fatal`).
- Si SP6 falla, no reinicia, o no queda validado, **no se continúa a SP7**
  para ese host (en modo `full`) — ver `stage_validated`, sección 10.
- Al final de la ejecución, si el resultado del host fue `FAILED` **o**
  `NOT_CHECKED` (validate incompleto), la tarea del host se marca
  explícitamente como fallida en Ansible/AWX, después de haber generado
  igualmente el reporte completo.
- Los repositorios temporales y el respaldo se **conservan** ante un fallo
  (no se limpia nada), salvo que se fuerce `cleanup_repositories_on_failure:
  true` explícitamente.

---

## 13. AWX

Manual paso a paso para crear todo esto desde cero en un AWX nuevo (Credential
Type, Credential, Project, Inventory Source, Survey, Workflow Job Template):
[`docs/AWX_SETUP.html`](docs/AWX_SETUP.html).

**Configuración por defecto: Workflow Job Template de 5 etapas.** En vez de
un único Job Template, la forma recomendada de operar este proyecto es
partir la ejecución en 5 Job Templates (Precheck → Preparar repos → Aplicar →
Reporting → Sincronizar SharePoint) encadenados por un Workflow — ver la
variable `upgrade_phase` (sección 10.1), `sharepoint_sync` (sección 11) y
`docs/AWX_SETUP.html`, sección 7, para el diseño completo campo por campo
(incluye dónde insertar un Approval Node y cómo conectar notificaciones de
AWX, por ejemplo a un canal de Teams). Existe una
alternativa más simple con un solo Job Template (mismo código, mismo Survey,
sin las 5 etapas separadas) documentada en `docs/AWX_SETUP.html`, sección 8,
para casos donde no se necesita el control granular por etapa.

### Objetos a configurar (con datos reales, no inventados)

- **Project**: apuntando a este repositorio.
- **Inventory**: hosts/grupos reales de GeoPOS. Solo hosts/grupos y, si se
  necesita, variables de **conexión** (`ansible_host`, `ansible_user`,
  etc.) — las variables de negocio del proyecto viven en
  `playbooks/group_vars`/`host_vars` de este repositorio (ver sección 6.2
  para la precedencia exacta entre ambos).
  - **Inventario dinámico propio (Excel/SharePoint, dedicado)**:
    [`inventory/linux_excel_inventory.yml`](inventory/linux_excel_inventory.yml)
    — adaptado del mecanismo corporativo de parchado (mismo plugin
    `excel_inventory`, mismo SharePoint), pero con su **propio archivo
    Excel y hoja dedicados** (`Inventario_SLES15_GeoPOS_Upgrade.xlsx`,
    hoja "SLES15 GeoPOS") — no comparte archivo ni hoja con el inventario
    general de parchado. Sin columnas de virtualización (VMware,
    ancho de banda): todos los servidores de esta hoja son físicos.
    Plantilla lista para subir a SharePoint:
    [`docs/references/plantilla_inventario_sles15_geopos.xlsx`](docs/references/plantilla_inventario_sles15_geopos.xlsx).
    En AWX se configura como Inventory Source **"Sourced from a
    Project"**, apuntando a este archivo dentro del Project — ver
    `docs/AWX_SETUP.html` para el paso a paso. Las credenciales
    (tenant/client id/secret) se inyectan como variables de entorno
    mediante un **Credential de AWX** — nunca como archivo `.env` dentro
    de este repositorio (si alguna vez aparece uno, está excluido por
    `.gitignore`, pero no debería colocarse aquí).
    - **El plugin viaja con este proyecto**: a diferencia de lo que se
      pensó inicialmente, el código del plugin `excel_inventory` **no
      depende de una Collection instalada en el Execution Environment de
      AWX** — vive versionado en
      [`inventory_plugins/excel_inventory.py`](inventory_plugins/excel_inventory.py)
      (raíz del proyecto, no dentro de `inventory/`: Ansible solo
      descubre automáticamente una carpeta `inventory_plugins/` si está
      junto a `ansible.cfg`) y queda habilitado explícitamente en
      `ansible.cfg` (`[inventory] enable_plugins = excel_inventory, ...`
      — los plugins de inventario, a diferencia de módulos/filtros,
      requieren habilitación explícita). Lo único que debe existir en el
      Execution Environment son sus dependencias de Python: `pandas`,
      `openpyxl` (siempre) y `msal`, `requests` (solo para SharePoint).
      Verificado localmente: sin esas dependencias, el plugin falla con
      un mensaje claro (`Se requiere 'pandas'...`), nunca con un error
      confuso.
    Aunque esta hoja está pensada para contener únicamente servidores
    físicos SLES 15 con GeoPOS, PRECHECK igual valida
    `ansible_facts['distribution'] == 'SLES'` como primer chequeo
    obligatorio (sección 8.1), como defensa adicional ante un error de
    captura en la hoja: si el host no es SLES, el precheck
    queda `FAILED` de inmediato con un mensaje explícito y **no ejecuta
    ninguna otra verificación ni acción** sobre ese host.
- **Credential**: SSH + `become` con los privilegios necesarios.
- **Job Template(s)**: por defecto son 4, encadenados por un Workflow Job
  Template — ver `docs/AWX_SETUP.html` sección 7 para el detalle campo por
  campo de cada uno (hay una alternativa con un solo Job Template, sección
  8). En ninguno se marca `Limit` como "Prompt on Launch": ya no se usa
  para seleccionar hosts (ver más abajo).
- **Survey** (pequeño; `upgrade_crq`/`upgrade_lote`/`upgrade_ambiente` ya
  no son solo trazabilidad — son el mecanismo de selección de hosts; se
  crea una sola vez en el Workflow Job Template):
  - `upgrade_mode` (choice: en el Workflow, solo sp4_to_sp5 / sp5_to_sp6 /
    sp6_to_sp7 / full — precheck ya es automático en el Nodo 1 y validate
    no participa en el Workflow; en la alternativa de un solo Job
    Template, las 6: precheck / validate / sp4_to_sp5 / sp5_to_sp6 /
    sp6_to_sp7 / full)
  - `confirm_production_upgrade` (choice, **no boolean** — AWX no tiene ese tipo de
    pregunta; ver nota abajo)
  - `upgrade_crq` (texto, **obligatorio**): "Ingrese el CRQ/RFC"
  - `upgrade_lote` (texto u opción múltiple, **obligatorio**): "Seleccione el Lote a parchar del CRQ/RFC"
  - `upgrade_ambiente` (opción múltiple, **obligatorio**): "Seleccione el Ambiente asociado al CRQ/RFC y Lote" (ej. Producción/Desarrollo/Laboratorio/Staging)

  **Por qué existe `confirm_production_upgrade` si `upgrade_mode` ya dice
  que se quiere migrar — el patrón de "dos llaves".** No es redundante:
  `upgrade_mode` decide **qué** operación correría; `confirm_production_upgrade`
  decide si esa operación realmente **se ejecuta**, o se queda preparada pero
  bloqueada. Hacen falta las dos para modificar un servidor real:

  1. **Protege contra un valor guardado por defecto.** Si un Job Template o
     un Schedule queda configurado con `upgrade_mode: full` (por ejemplo,
     para no tener que re-seleccionarlo en cada lanzamiento), esa ejecución
     sigue sin modificar nada mientras no se active explícitamente
     `confirm_production_upgrade: true` en ese lanzamiento puntual.
  2. **Es intencionalmente independiente de `upgrade_ambiente`.** No se puede
     usar el Ambiente como candado porque, por política de este proyecto
     (ver encabezado del README), **todos** los hosts se tratan como
     productivos sin importar el Ambiente — así que se necesita un campo
     que no dependa de ningún dato del inventario, algo que un humano deba
     afirmar activamente cada vez.
  3. **Es un único punto de control en el código**
     (`playbooks/tasks/run_stage.yml`), revisado antes de tocar cualquier
     repositorio o paquete, igual para las 4 formas de modificar el sistema
     (`sp4_to_sp5`/`sp5_to_sp6`/`sp6_to_sp7`/`full`) — para auditoría es una
     sola pregunta uniforme ("¿este log muestra
     `confirm_production_upgrade=true`?"), en vez de confiar en que elegir
     el modo correcto nunca fue un error de click.

  Por defecto siempre es `false` (`playbooks/group_vars/all.yml`), así que
  cualquier ejecución que no lo active a propósito queda inofensiva, aunque
  el resto del Survey esté mal configurado.

  **`confirm_production_upgrade` — AWX no tiene un tipo de pregunta
  "Boolean" en el Survey** (solo texto/área de texto/contraseña/selección
  múltiple/opciones de selección múltiple/entero/decimal). Usar
  **"Selección múltiple"** con exactamente dos opciones, escritas
  literalmente `true` y `false` (en inglés, minúsculas — no `"Sí"`/`"No"`).
  El código (`playbooks/tasks/run_stage.yml`) aplica el filtro `| bool` de
  Ansible sobre este valor, que reconoce `true/false`, `yes/no`, `on/off`,
  `1/0` sin distinguir mayúsculas; cualquier otro texto bloquea la etapa
  explícitamente en vez de interpretarse mal — es intencional: sin este
  filtro, el string `"false"` (no vacío) se evaluaría como verdadero en
  Jinja y **autorizaría** la migración real por error.

  **¿Qué pasa si se selecciona `precheck` (o `validate`) con
  `confirm_production_upgrade: true`?** Nada distinto de dejarlo en
  `false`: ese valor solo se lee dentro de `playbooks/tasks/run_stage.yml`
  (línea con el assert), y ese archivo únicamente se incluye cuando
  `upgrade_mode` es `sp4_to_sp5`/`sp5_to_sp6`/`sp6_to_sp7`/`full` (ver
  `playbooks/upgrade.yml`). `precheck` y `validate` nunca llegan a ese
  código, así que el valor de `confirm_production_upgrade` se ignora por
  completo bajo esos dos modos — no hay ninguna combinación de
  `upgrade_mode`/`confirm_production_upgrade` que haga que `precheck` o
  `validate` modifiquen el servidor.

  **Por qué el prefijo `upgrade_`** (y no `crq`/`lote`/`ambiente` a secas):
  el inventario dinámico de arriba ya expone esos mismos nombres como
  variables de host (columnas CRQ/Lote/Ambiente del último ciclo de
  **parchado** registrado en la hoja). Si el Survey usara los mismos
  nombres, un host heredaría silenciosamente ese dato de parchado en el
  reporte de este upgrade en vez del CRQ/Lote/Ambiente real de esta
  ejecución. Ver `playbooks/group_vars/all.yml`.

  **Selección de hosts: match CRQ + Lote + Ambiente, no `Limit`.**
  Decisión explícita del usuario para este ambiente: cada ejecución
  (incluso un `precheck`) corresponde a un CRQ/RFC de control de cambios
  real, así que `upgrade_crq`/`upgrade_lote`/`upgrade_ambiente` del Survey
  se comparan contra las columnas `CRQ`/`Lote`/`Ambiente` **del inventario**
  (mismo nombre, sin prefijo, compuestas en `inventory/linux_excel_inventory.yml`
  desde el Excel) — ver los 3 primeros plays de `playbooks/upgrade.yml`. El
  host o los hosts cuyas 3 columnas coincidan EXACTAMENTE (comparación con
  `trim`, sensible a mayúsculas) con lo declarado en el Survey entran al
  alcance de la ejecución; si ninguno coincide, el playbook falla
  explícito antes de tocar cualquier host — nunca se ejecuta sin
  seleccionar nada ni contra el host equivocado. Deje `Limit` vacío y sin
  "Prompt on Launch" en el Job Template: ya no participa en la selección.
- **Schedule**: opcional, para ejecuciones programadas (por ejemplo,
  `validate` periódico) — en ese caso, `upgrade_crq`/`upgrade_lote`/
  `upgrade_ambiente` deben fijarse como extra-vars del Schedule, igual que
  cualquier otro valor del Survey.

No hay `dry_run` ni `reboot_after_upgrade` que agregar al Survey: no
existen en este proyecto (sección 9).

### Procesamiento por defecto

`serial_batch_size: 1` — un host a la vez en producción. Puede
sobrescribirse vía extra-vars/Survey si el operador decide explícitamente
procesar más de uno en paralelo, bajo su propio criterio de riesgo.

---

## 14. Información pendiente (`CHANGE_ME`) antes de producción

**Foreman/Katello**: `katello.base_url`, `katello.sp4/sp5/sp6/sp7_repositories`
y `katello.ca_certificate_path` ya están completos (verificados por API el
2026-10-01, ver sección 5). La instalación de la CA en el host ya está
automatizada (`ensure_ca_trusted.yml`), así que no requiere ningún paso
manual. Queda pendiente confirmar si el ambiente llega a usar un Content
View/Lifecycle Environment distinto de `Library` (hoy no se usa ninguno).

**GeoPOS**: nombres reales de servicios systemd, patrones de proceso Java
por componente, puertos, health checks (si existen), y si difieren por
host/grupo (usar `host_vars`).

**Sistema**: lista definitiva de `critical_services` (vacía por defecto),
umbrales reales de `precheck_disk_checks` por filesystem.

**Reportes**: `report_destination` ya está completo (`/data/work/Salida_Upgrade`
— ver sección 11). Pendiente de confirmar en el AWX real: que esa ruta
exista, tenga permisos de escritura, y sea realmente persistente (no
efímera dentro del contenedor del Execution Environment).

**AWX**: nombres reales de Project, Inventory, Credential, Job Template,
Survey.

Mientras estos valores permanezcan como `CHANGE_ME` o listas vacías, el
proyecto es seguro de ejecutar en modos de solo lectura (`precheck` y
`validate`), pero **no debe usarse para una migración real** hasta
completarlos.

Ver [`docs/CHECKLIST_LABORATORIO.html`](docs/CHECKLIST_LABORATORIO.html) para
el checklist completo (variables a conseguir, prerrequisitos de
infraestructura y orden recomendado de la primera ejecución real).

---

## 15. Troubleshooting

- **"No hay repositorios definidos en katello.spN_repositories"**: falta
  completar `katello.sp5_repositories`/`sp6_repositories`/`sp7_repositories`.
  El proyecto se detiene explícitamente en vez de continuar sin repos.
- **Precheck falla en `locks_zypper_rpm_libzypp`**: otro proceso
  (PackageKit, otro Zypper/YaST) tiene el gestor de paquetes bloqueado.
  Revisar `ps aux | grep -i zypp` en el host.
- **"No se pudieron agregar/deshabilitar/eliminar los siguientes
  repositorios..." con detalle `System management is locked by the
  application with pid ... (/usr/lib/packagekitd)`**: confirmado con
  evidencia real en laboratorio (2026-10-06) — es `rc=7`
  (`ZYPPER_EXIT_ZYPP_LOCKED`, código de salida oficial de zypper: "libzypp
  is locked, e.g. packagekit is running"). Es un lock **transitorio**
  (PackageKit lo libera solo, normalmente en segundos). `roles/repo_management`
  ya reintenta automáticamente ante este código exacto
  (`repo_management_zypper_lock_retries`/`_delay`, por defecto 5
  intentos / 5s de espera) — cualquier otro código de error se reporta de
  inmediato, sin reintentos. Si sigue fallando tras los 5 intentos, hay
  algo más que mantiene el lock de forma persistente (revisar
  `ps aux | grep -i zypp`/`packagekitd` en el host).
- **Precheck en `WARNING` en `endpoint_alcanzable_*`**: el host respondió
  (HTTP 401/403/404, por ejemplo), pero eso no confirma que el repositorio
  sea utilizable — ejecute `validate` para la comprobación real.
- **`geopos_precheck_gate` en `FAILED`**: un componente GeoPOS marcado
  `critical: true` no está saludable y `fail_precheck_if_unhealthy: true`.
  Si existe una excepción operacional autorizada, sobrescribir
  `fail_precheck_if_unhealthy: false` en el `host_vars` correspondiente
  (queda registrado en el reporte).
- **`validate` (preflight) en `FAILED`**: revisar
  `stage_report.preflight.output_summary` en el reporte — contiene la
  salida completa de Zypper. Las causas más comunes son: clave GPG no
  importada/confiada en el host (poco probable: Katello no re-firma este
  contenido, son las llaves originales de SUSE — ver sección 5; si pasa,
  importarla con `rpm --import` es responsabilidad del administrador, no
  algo que este proyecto automatice preventivamente), certificado TLS no
  confiable, URL de repo incorrecta, o conflictos reales del solver.
- **`validate` (preflight) en `NOT_CHECKED` con `supported: false`**: el
  Zypper de ese host no expone `--reposd-dir` (muy poco probable en SLES
  15, pero se verifica en cada ejecución en vez de asumirlo). Revisar
  `zypper --help` manualmente en el host.
- **Precheck en `WARNING` en `service_pack_doble_evidencia`**: `/etc/os-release`
  y `zypper products -i` no coinciden. No bloquea (el formato exacto del
  atributo de versión de Zypper para un Service Pack no está confirmado en
  la documentación oficial), pero debe revisarse manualmente antes de una
  migración real.
- **Logs útiles en el host SLES**: `/var/log/zypper.log`,
  `/var/log/zypp/history`, salida de `zypper repos -u`, `journalctl -u
  <servicio>` para servicios críticos/GeoPOS.
- **Rollback real**: solo existe si la raíz es **Btrfs con snapshots**
  (`snapper list` / `snapper rollback`, según el procedimiento oficial de
  SUSE). Este proyecto **no implementa ni afirma** un mecanismo de
  rollback automático.
- **Proceso corporativo de parchado**: gestiona los repositorios
  "normales" de forma independiente a esta automatización. Este proyecto
  nunca borra repos preexistentes (solo los deshabilita temporalmente
  durante una etapa) y nunca los reactiva automáticamente.

---

## 16. Validación de este proyecto

Validaciones estáticas ejecutadas (sin conexión a ningún servidor):

```bash
ansible-playbook playbooks/upgrade.yml --syntax-check
ansible-lint --profile production playbooks/upgrade.yml playbooks/roles/
yamllint playbooks/ inventory/
```

Las tres, limpias.

Además, se construyó un Zypper simulado (con estado persistente y registro
de cada invocación) y se ejecutaron de extremo a extremo, con datos
simulados y **sin tocar ningún sistema real**, los archivos reales del
proyecto (solo se neutralizó el paso de reinicio real, reemplazado por un
no-op simulable como éxito o fallo, por seguridad), probando:

- **PRECHECK no modifica repositorios ni paquetes**: estado de repos byte-idéntico antes/después,
  cero llamadas de escritura a Zypper (la única excepción real, agregada después de esta
  prueba simulada, es la instalación idempotente de la CA interna si faltaba — sección 8.1).
- **`confirm_production_upgrade: false` no modifica absolutamente nada**:
  mismo resultado — cero cambios, cero llamadas a `updatestack`/`dup`.
- **Un repo de origen ausente bloquea en PRECHECK**, antes de deshabilitar
  cualquier repositorio preexistente (`repos_disabled_by_upgrade` y
  `repos_temporary_created` quedan vacíos).
- **Un repo de destino ausente bloquea en PRECHECK** con el mismo resultado.
- **`refresh` nunca se invoca con `-s`/`--services`**, y cada llamada
  recibe únicamente los alias temporales exactos de esa fase — confirmado
  registrando los argumentos reales de cada invocación (el Zypper simulado
  además rechaza activamente cualquier `-s`, como red de seguridad
  adicional).
- **`updatestack` usa únicamente el repo Foreman de origen** y **`dup`/`dup -D`
  usan únicamente el repo Foreman de destino** — confirmado registrando qué
  repos veía Zypper en cada invocación real.
- **Solo se deshabilitan los repos que estaban `enabled`**: un repo
  preexistente ya deshabilitado no recibe ninguna llamada, y no aparece en
  `repos_disabled_by_upgrade`.
- **En éxito se retiran únicamente los repos temporales creados** (origen y
  destino), y `repos_enabled_after` queda vacío.
- **Un `dup` exitoso con reinicio fallido conserva `dup_applied: true`**:
  el reporte muestra `dup_applied: true`, `reboot.completed: false`,
  `stage_validated: false`, `status: FAILED`, y — corregido durante esta
  ronda — `repos_enabled_after` sigue mostrando el repo temporal de destino
  que quedó habilitado, para diagnóstico.
- **`stage_validated` nunca es `true` si el reinicio o la reconexión
  fallan** (mismo caso anterior).
- **VALIDATE usa `--reposd-dir` real y aislado, en dos directorios
  independientes** (uno para origen con solo `refresh`, otro para destino
  con `refresh` + `dup -D`): se verificó que ambos se crean, que Zypper
  solo ve en cada uno los repos que le corresponden (nunca se mezclan entre
  sí ni con los repos preexistentes), y que ambos se eliminan del
  filesystem al finalizar.
- **El gate `stage_validated` hacia SP7** se probó con 4 escenarios
  (SP6 falló / SP6 validado / host ya en SP6 / SP6 nunca completó
  dup+reboot): SP7 solo se ejecuta en los casos correctos.
- **El reporte contiene datos "antes" y "después" reales y distintos**
  (`sp_inicial` ≠ `sp_final` tras una migración simulada exitosa).
- **Las variables de `playbooks/group_vars/all.yml` se cargan con un
  inventario completamente ajeno al proyecto** (simulando un Inventory de
  AWX): se ejecutó el precheck real con un inventario externo sin ningún
  override de negocio, y `katello`, `geopos_validation`, `critical_services`
  etc. resolvieron correctamente a sus valores por defecto (en vez de
  fallar con "variable indefinida"), y el precheck reportó correctamente
  `FAILED` por repos Foreman vacíos — la prueba concreta de que la
  reubicación de variables (sección 6) funciona.
- **`validate` con origen `NOT_CHECKED` y destino `OK` da como resultado
  global `NOT_CHECKED`, nunca `OK`.**
- **`validate` con origen `OK`, destino `OK` y `dup -D` `OK` da como
  resultado global `OK`.**
- **Un Service Pack correcto según `/etc/os-release` pero con evidencia de
  `zypper products` inconsistente produce `stage_validated: false` y
  `status: FAILED`** (`service_pack_evidencia_inconsistente`), conservando
  correctamente `dup_applied: true` y `reboot.completed: true` — la
  discrepancia bloquea el avance sin ocultar que la migración técnica sí
  se aplicó.
- **Un fallo en el repositorio intermedio de un loop (ni el primero ni el
  último) conserva la evidencia de los que sí se modificaron, antes y
  después del que falló**: probado tanto para deshabilitar repos
  preexistentes (`repos_disabled_by_upgrade`) como para agregar repos
  temporales (`repos_temporary_created`) — en ambos casos el loop no
  aborta a mitad de camino, y el fallo se reporta explícitamente después
  de consolidar toda la evidencia real (nunca se oculta).

Durante el desarrollo de este proyecto se encontraron y corrigieron, en
distintas rondas, los siguientes errores reales (todos confirmados con
pruebas antes/después de la corrección):

- Un `regex_search` sin coincidencia podía hacer fallar la captura de
  estado (`capture_state.yml`).
- Una recursión al calcular un backslash de escape dentro de una etiqueta
  Jinja `{% for %}` en vez de una expresión `{{ }}` (`final_inventory.yml`).
- Una plantilla de reporte asumía lenientemente una clave (`preflight`) que
  no existía en todos los modos — el módulo `template` de Ansible usa
  variables no definidas en modo estricto, a diferencia de `set_fact`.
- `ansible.builtin.uri`, ante un fallo real de conexión, no deja el campo
  `status` indefinido: lo fija en `-1`. La clasificación de alcanzabilidad
  solo comprobaba "¿está definido?", así que un fallo real de red se
  clasificaba como advertencia en vez de fallo (`repos_reachability.yml`).
- El `when` de un `block:` de Ansible se propaga a cada tarea interna y se
  reevalúa en el momento en que esa tarea corre, no solo al entrar al
  bloque. Como el bloque de migración cambia `stage_status` a `FAILED`
  *dentro de sí mismo* (por ejemplo, ante un reinicio fallido), las tareas
  de limpieza/inventario final que debían ejecutarse **precisamente** en
  ese caso quedaban silenciosamente saltadas por la condición heredada del
  bloque, aunque su propia condición pidiera lo contrario. Se corrigió
  moviendo esas tareas fuera del bloque (`playbooks/tasks/run_stage.yml`).

**Riesgos que no pueden validarse sin un SLES real de laboratorio:**

- Que `--reposd-dir` efectivamente aísla a Zypper de `/etc/zypp/repos.d` en
  la versión real de Zypper de SLES 15 (se confirmó el comportamiento
  documentado y se simuló exhaustivamente, pero no se ejecutó contra un
  Zypper real).
- **El formato exacto del atributo `version` de un `<product name="SLES">`
  reportado por `zypper products -i --xmlout` para un Service Pack** (solo
  se confirmó el formato para GA en la documentación oficial). Esto es
  ahora el riesgo más relevante a confirmar en laboratorio: desde esta
  revisión, la doble evidencia es un **gate real y obligatorio** de
  `stage_validated` (sección 8.3) — si el parser no reconoce el formato
  real de un SLES de laboratorio, **cada etapa quedará `FAILED`** con esa
  causa exacta (`service_pack_sin_evidencia_zypper`) hasta corregir el
  regex de `playbooks/roles/precheck/tasks/capture_state.yml` con la evidencia real
  capturada en el reporte (`zypper_products_xml_evidence`). Es un
  comportamiento intencional (fail-safe), no un defecto — pero es
  virtualmente seguro que requerirá un ajuste en la primera ejecución real.
- El comportamiento real de `zypper patch --updatestack-only` y sus
  códigos de retorno (103, reintentos) en un sistema real.
- Tiempos reales de reinicio/reconexión en la infraestructura real (los
  valores por defecto de `sp_migration_reboot_*` son estimaciones
  razonables, no medidos).
- Cualquier interacción real con Foreman/Katello (autenticación,
  Content Views, GPG) — todos los `CHANGE_ME` de la sección 14.

Antes de producción: ejecutar `precheck` y luego `validate` contra un host
de laboratorio real con datos de Foreman/Katello reales, revisar el
reporte, y solo entonces evaluar una ejecución real de `sp5_to_sp6`.
