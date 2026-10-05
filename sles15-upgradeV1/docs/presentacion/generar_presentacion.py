#!/usr/bin/env python3
"""Genera la presentación ejecutiva ansible-sles-upgrade-presentacion.pptx.

Refleja la arquitectura REAL implementada en el repositorio (no supuestos).
Requiere python-pptx (pip install python-pptx). Regenerar con:

    python3 docs/presentacion/generar_presentacion.py
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
import os

# Paleta neutra (sin branding corporativo, ya que no se suministró uno real)
NAVY = RGBColor(0x1B, 0x2A, 0x4A)
TEAL = RGBColor(0x1F, 0x7A, 0x6C)
GRAY_DARK = RGBColor(0x33, 0x33, 0x33)
GRAY_MID = RGBColor(0x66, 0x66, 0x66)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT_BG = RGBColor(0xF4, 0xF6, 0xF8)
OK_GREEN = RGBColor(0x2E, 0x7D, 0x32)
WARN_AMBER = RGBColor(0xB8, 0x86, 0x0B)
FAIL_RED = RGBColor(0xC6, 0x28, 0x28)

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)

prs = Presentation()
prs.slide_width = SLIDE_W
prs.slide_height = SLIDE_H
BLANK = prs.slide_layouts[6]


def add_slide():
    return prs.slides.add_slide(BLANK)


def set_background(slide, color=WHITE):
    bg = slide.background
    bg.fill.solid()
    bg.fill.fore_color.rgb = color


def add_footer(slide, text):
    tb = slide.shapes.add_textbox(Inches(0.5), SLIDE_H - Inches(0.45), SLIDE_W - Inches(1), Inches(0.35))
    p = tb.text_frame.paragraphs[0]
    p.text = text
    p.font.size = Pt(11)
    p.font.color.rgb = GRAY_MID


def add_title_bar(slide, title, subtitle=None):
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, SLIDE_W, Inches(1.15))
    bar.fill.solid()
    bar.fill.fore_color.rgb = NAVY
    bar.line.fill.background()
    tb = slide.shapes.add_textbox(Inches(0.6), Inches(0.15), SLIDE_W - Inches(1.2), Inches(0.7))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(28)
    p.font.bold = True
    p.font.color.rgb = WHITE
    if subtitle:
        p2 = tf.add_paragraph()
        p2.text = subtitle
        p2.font.size = Pt(14)
        p2.font.color.rgb = RGBColor(0xC9, 0xD6, 0xE8)


def add_bullets(slide, items, left=Inches(0.7), top=Inches(1.5), width=None, height=None, size=18):
    width = width or (SLIDE_W - Inches(1.4))
    height = height or (SLIDE_H - Inches(2.2))
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame
    tf.word_wrap = True
    first = True
    for item in items:
        if isinstance(item, tuple):
            text, level = item
        else:
            text, level = item, 0
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.text = ("•  " if level == 0 else "‒  ") + text
        p.level = level
        p.font.size = Pt(size if level == 0 else size - 2)
        p.font.color.rgb = GRAY_DARK if level == 0 else GRAY_MID
        p.space_after = Pt(10 if level == 0 else 6)
    return tb


def add_box(slide, text, left, top, width, height, fill=TEAL, font_color=WHITE, size=14, bold=True):
    shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    shp.fill.solid()
    shp.fill.fore_color.rgb = fill
    shp.line.color.rgb = fill
    shp.shadow.inherit = False
    tf = shp.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(size)
    p.font.bold = bold
    p.font.color.rgb = font_color
    p.alignment = PP_ALIGN.CENTER
    return shp


def add_arrow_down(slide, x_center, top, length=Inches(0.35)):
    arrow = slide.shapes.add_shape(MSO_SHAPE.DOWN_ARROW, x_center - Inches(0.12), top, Inches(0.24), length)
    arrow.fill.solid()
    arrow.fill.fore_color.rgb = GRAY_MID
    arrow.line.fill.background()


def add_arrow_right(slide, left, y_center, length=Inches(0.35)):
    arrow = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, left, y_center - Inches(0.12), length, Inches(0.24))
    arrow.fill.solid()
    arrow.fill.fore_color.rgb = GRAY_MID
    arrow.line.fill.background()


# =============================================================================
# 1. Portada
# =============================================================================
s = add_slide()
set_background(s, NAVY)
tb = s.shapes.add_textbox(Inches(1), Inches(2.5), SLIDE_W - Inches(2), Inches(2))
tf = tb.text_frame
tf.word_wrap = True
p = tf.paragraphs[0]
p.text = "Upgrade automatizado de SLES 15"
p.font.size = Pt(40)
p.font.bold = True
p.font.color.rgb = WHITE
p2 = tf.add_paragraph()
p2.text = "SP4 → SP5 → SP6 → SP7 para los servidores GeoPOS"
p2.font.size = Pt(22)
p2.font.color.rgb = RGBColor(0xC9, 0xD6, 0xE8)
p2.space_before = Pt(12)
p3 = tf.add_paragraph()
p3.text = "Automatización con Ansible y AWX · Repositorios internos Foreman/Katello"
p3.font.size = Pt(16)
p3.font.color.rgb = TEAL
p3.space_before = Pt(20)

# =============================================================================
# 2. Objetivo y necesidad
# =============================================================================
s = add_slide()
set_background(s)
add_title_bar(s, "Objetivo y necesidad del proyecto")
add_bullets(s, [
    "Mantener los servidores SLES 15 que ejecutan GeoPOS en un Service Pack soportado por SUSE, de forma segura y repetible.",
    "Hoy el upgrade de Service Pack es una tarea manual: lenta, dependiente de una persona y difícil de auditar entre muchos servidores.",
    "Se necesita un mecanismo controlado, con evidencia clara de resultado, que no dependa del registro SUSEConnect de cada servidor.",
    "El resultado debe poder verificarse sin conectarse por SSH a cada servidor ni leer manualmente el log completo de cada ejecución.",
])
add_footer(s, "ansible-sles-upgrade · Presentación ejecutiva")

# =============================================================================
# 3. Alcance
# =============================================================================
s = add_slide()
set_background(s)
add_title_bar(s, "Alcance del proyecto")
add_bullets(s, [
    "Rutas contempladas por el proyecto: SP4 → SP5, SP5 → SP6, SP6 → SP7, y la secuencia completa SP5 → SP6 → SP7.",
    "SP4 → SP5 es independiente (para servidores que todavía están en SP4): se ejecuta aparte, no se encadena automáticamente con lo siguiente.",
    "Nunca se realiza un salto directo de etapa (ni SP4 → SP6, ni SP5 → SP7): cada etapa debe quedar realmente validada (aplicada, reiniciada y verificada) antes de continuar.",
    "Aplica a todos los servidores SLES 15 que ejecutan la aplicación GeoPOS (uno o varios servicios, procesos Java y puertos por servidor).",
    "Incluye: verificación previa, ensayo real sin cambios contra los repositorios, migración real, reinicio obligatorio, validación posterior y reporte.",
])
add_footer(s, "ansible-sles-upgrade · Presentación ejecutiva")

# =============================================================================
# 4. Arquitectura de alto nivel
# =============================================================================
s = add_slide()
set_background(s)
add_title_bar(s, "Arquitectura de alto nivel")

col_w = Inches(3.4)
gap = Inches(0.5)
top = Inches(2.0)
h = Inches(1.1)
x0 = Inches(0.7)

add_box(s, "AWX\n(orquestación, Survey)", x0, top, col_w, h, fill=NAVY)
add_arrow_right(s, x0 + col_w, top + h / 2, gap)
add_box(s, "Ansible\n(este proyecto)", x0 + col_w + gap, top, col_w, h, fill=TEAL)
add_arrow_right(s, x0 + 2 * col_w + 2 * gap, top + h / 2, gap)
add_box(s, "Servidores SLES 15\n(GeoPOS)", x0 + 2 * (col_w + gap), top, col_w, h, fill=TEAL)

top2 = top + h + Inches(0.9)
add_box(s, "Foreman / Katello\n(repositorios internos únicamente)", x0 + col_w + gap, top2, col_w, h, fill=GRAY_MID)
arrow = s.shapes.add_shape(MSO_SHAPE.UP_ARROW, x0 + col_w + gap + col_w / 2 - Inches(0.12), top + h + Inches(0.05), Inches(0.24), Inches(0.35))
arrow.fill.solid()
arrow.fill.fore_color.rgb = GRAY_MID
arrow.line.fill.background()

add_bullets(s, [
    "AWX dispara la ejecución (Job Template + Survey); el alcance de servidores se define con el CRQ/Lote/Ambiente declarados en el Survey, verificados contra el inventario — nunca con un campo de selección manual aparte.",
    "Ansible ejecuta el procedimiento en cada servidor, uno a la vez por defecto.",
    "Los servidores obtienen los paquetes de actualización exclusivamente desde Foreman/Katello, nunca desde Internet ni desde SUSEConnect.",
], top=Inches(4.6), size=15)
add_footer(s, "ansible-sles-upgrade · Presentación ejecutiva")

# =============================================================================
# 5. Flujo general del upgrade
# =============================================================================
s = add_slide()
set_background(s)
add_title_bar(s, "Flujo general del upgrade")

steps = [
    "Verificación previa (precheck)",
    "Confirmación explícita para producción",
    "Preparar repositorios Foreman/Katello de la etapa",
    "Migración real, con verificación interna obligatoria justo antes de aplicar",
    "Reinicio obligatorio",
    "Validar sistema operativo, servicios y GeoPOS",
    "Reporte de la etapa",
]
box_h = Inches(0.55)
top = Inches(1.4)
box_w = Inches(6.4)
left = Inches(0.9)
for i, step in enumerate(steps):
    add_box(s, f"{i + 1}. {step}", left, top, box_w, box_h, fill=NAVY if i % 2 == 0 else TEAL, size=13)
    if i < len(steps) - 1:
        add_arrow_down(s, left + box_w / 2, top + box_h, Inches(0.16))
    top += box_h + Inches(0.16)

note = s.shapes.add_textbox(Inches(7.7), Inches(1.6), Inches(4.9), Inches(4.8))
tf = note.text_frame
tf.word_wrap = True
p = tf.paragraphs[0]
p.text = "Este mismo ciclo aplica igual a SP4→SP5 (independiente) y se repite para SP5→SP6 y, solo si esa etapa quedó realmente validada, para SP6→SP7."
p.font.size = Pt(15)
p.font.color.rgb = GRAY_DARK
p2 = tf.add_paragraph()
p2.text = "\nPara ensayar sin modificar nada, existe un modo de validación real independiente (siguiente diapositiva)."
p2.font.size = Pt(14)
p2.font.color.rgb = GRAY_MID
p3 = tf.add_paragraph()
p3.text = "\nUna migración real requiere una confirmación explícita adicional (no ocurre por defecto), verificada antes de tocar cualquier repositorio."
p3.font.size = Pt(14)
p3.font.color.rgb = GRAY_MID
p4 = tf.add_paragraph()
p4.text = "\nLos pasos 3 (preparar repos) y 4-6 (aplicar el cambio) pueden ejecutarse juntos (por defecto) o como 2 etapas separadas con aprobación entre ambas — ver diapositiva siguiente."
p4.font.size = Pt(14)
p4.font.color.rgb = GRAY_MID
add_footer(s, "ansible-sles-upgrade · Presentación ejecutiva")

# =============================================================================
# 5b. Workflow opcional: Preparar y Aplicar por separado
# =============================================================================
s = add_slide()
set_background(s)
add_title_bar(s, "Opcional: separar “Preparar” de “Aplicar”",
              subtitle="Mismo procedimiento, con un punto de control humano en el medio")

col_w = Inches(2.75)
gap = Inches(0.35)
top = Inches(1.65)
h = Inches(1.1)
x0 = Inches(0.6)
add_box(s, "1. Precheck\n\n¿Está listo\nel servidor?", x0, top, col_w, h, fill=GRAY_MID, size=14)
add_arrow_right(s, x0 + col_w, top + h / 2, gap)
add_box(s, "2. Preparar\nrepositorios\n\n(cambio real)", x0 + (col_w + gap), top, col_w, h, fill=TEAL, size=14)
add_arrow_right(s, x0 + 2 * (col_w + gap), top + h / 2, gap)
add_box(s, "3. Aplicar\nel upgrade\n\n(cambio real,\nreinicio)", x0 + 2 * (col_w + gap), top, col_w, h, fill=NAVY, size=14)
add_arrow_right(s, x0 + 3 * (col_w + gap), top + h / 2, gap)
add_box(s, "4. Reporte\nconsolidado", x0 + 3 * (col_w + gap), top, col_w, h, fill=GRAY_MID, size=14)

gate = s.shapes.add_textbox(x0 + (col_w + gap) + col_w + Inches(0.02), top + h + Inches(0.05), col_w + gap, Inches(0.4))
gp = gate.text_frame.paragraphs[0]
gp.text = "⬆ punto de aprobación opcional"
gp.font.size = Pt(11)
gp.font.italic = True
gp.font.color.rgb = WARN_AMBER
gp.alignment = PP_ALIGN.CENTER

add_bullets(s, [
    "Por qué separar “preparar” de “aplicar”: permite que una persona (ej. un supervisor de cambios) autorice el paso irreversible (el reinicio) después de ver que la preparación salió bien, sin tener que repetir todo desde cero.",
    "Qué hace “preparar”: deja el servidor listo para migrar — respalda, deshabilita lo anterior, actualiza la herramienta de paquetes con los repositorios de origen, y agrega los repositorios de destino. Todavía NO aplica el cambio de Service Pack ni reinicia.",
    "Qué hace “aplicar”: primero repite, con el sistema real ya preparado, la misma simulación que recomienda SUSE antes de migrar (ver nota abajo); si todo está bien, aplica el cambio real y reinicia.",
    "Es opcional: por defecto las 2 etapas se ejecutan juntas, en una sola corrida, exactamente igual que antes de incluir esta opción.",
], top=Inches(3.1), size=14)

note_box = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.6), Inches(6.15), SLIDE_W - Inches(1.2), Inches(0.95))
note_box.fill.solid()
note_box.fill.fore_color.rgb = LIGHT_BG
note_box.line.color.rgb = GRAY_MID
tf = note_box.text_frame
tf.word_wrap = True
p = tf.paragraphs[0]
p.text = "Por qué se hizo así: la guía oficial de SUSE (“SLES Upgrade Guide”, sección “Upgrading with plain Zypper”) ya indica ejecutar una simulación (zypper dup -D) y corregir cualquier problema ANTES de aplicar el cambio real (zypper dup). Separar “preparar” de “aplicar” simplemente hace visible, como un paso propio del flujo de aprobación, algo que el procedimiento oficial ya recomienda hacer antes de comprometerse al cambio real."
p.font.size = Pt(12.5)
p.font.color.rgb = GRAY_DARK
add_footer(s, "ansible-sles-upgrade · Presentación ejecutiva")

# =============================================================================
# 6. PRECHECK, VALIDATE, UPGRADE
# =============================================================================
s = add_slide()
set_background(s)
add_title_bar(s, "Tres niveles, nunca confundidos")

col_w = Inches(3.85)
gap = Inches(0.35)
top = Inches(1.6)
h = Inches(1.35)
x0 = Inches(0.7)
add_box(s, "PRECHECK\n\n¿Está el servidor listo?", x0, top, col_w, h, fill=GRAY_MID, size=16)
add_box(s, "VALIDATE\n\n¿Funcionaría la migración\nahora mismo?", x0 + col_w + gap, top, col_w, h, fill=TEAL, size=16)
add_box(s, "UPGRADE\n\nEjecución real,\ncon cambios", x0 + 2 * (col_w + gap), top, col_w, h, fill=NAVY, size=16)

add_bullets(s, [
    "PRECHECK nunca modifica nada: revisa salud del servidor y su preparación.",
    "VALIDATE hace un ensayo real contra los repositorios Foreman, sin dejar ningún cambio permanente en el servidor.",
    "Solo UPGRADE modifica el servidor, y únicamente tras una confirmación explícita adicional.",
    "Estos tres niveles no son intercambiables: nunca se presenta un ensayo como si fuera la ejecución real, ni al revés.",
], top=Inches(3.4), size=16)
add_footer(s, "ansible-sles-upgrade · Presentación ejecutiva")

# =============================================================================
# 7. Repositorios internos / independencia de SUSEConnect
# =============================================================================
s = add_slide()
set_background(s)
add_title_bar(s, "Repositorios internos Foreman/Katello")
add_bullets(s, [
    "El upgrade usa exclusivamente los repositorios internos que el administrador configura en Foreman/Katello.",
    "No se usan repositorios públicos de SUSE en ningún momento de la migración.",
    "El estado de registro de SUSEConnect (registrado, mal registrado o no registrado) no determina ni bloquea el procedimiento; si se consulta, es solo informativo.",
    "Antes de migrar, se inventarían los repositorios ya existentes en el servidor y se deshabilitan los que estén activos — nunca se borran, y no se reactivan automáticamente al terminar.",
    "Los repositorios que la automatización agrega son temporales y quedan claramente identificados; al finalizar una etapa con éxito, se retiran automáticamente.",
    "El proceso corporativo de parchado, que administra los repositorios habituales de forma independiente, decide después qué hacer con lo que quedó deshabilitado.",
], size=15)
add_footer(s, "ansible-sles-upgrade · Presentación ejecutiva")

# =============================================================================
# 6b. Repositorios requeridos por Service Pack (tabla real)
# =============================================================================
s = add_slide()
set_background(s)
add_title_bar(s, "Repositorios requeridos por Service Pack",
              subtitle="Verificado por API contra Foreman/Katello (solo lectura) — todos sincronizados sin errores")

modulos = [
    "SUSE Linux Enterprise Server",
    "Basesystem Module",
    "Server Applications Module",
    "Desktop Applications Module",
    "Python 3 Module",
]
sps = ["SP4", "SP5", "SP6", "SP7"]

tbl_left, tbl_top = Inches(0.8), Inches(1.6)
tbl_w, tbl_h = Inches(11.7), Inches(3.4)
n_rows, n_cols = len(modulos) + 1, len(sps) + 1
graphic_frame = s.shapes.add_table(n_rows, n_cols, tbl_left, tbl_top, tbl_w, tbl_h)
table = graphic_frame.table
table.columns[0].width = Inches(4.5)
for c in range(1, n_cols):
    table.columns[c].width = Inches((11.7 - 4.5) / 4)

# Encabezado
hdr_cells = ["Módulo"] + sps
for c, text in enumerate(hdr_cells):
    cell = table.cell(0, c)
    cell.text = text
    cell.fill.solid()
    cell.fill.fore_color.rgb = NAVY
    p = cell.text_frame.paragraphs[0]
    p.font.bold = True
    p.font.size = Pt(15)
    p.font.color.rgb = WHITE
    p.alignment = PP_ALIGN.CENTER if c > 0 else PP_ALIGN.LEFT

for r, modulo in enumerate(modulos, start=1):
    cell = table.cell(r, 0)
    cell.text = modulo
    cell.fill.solid()
    cell.fill.fore_color.rgb = LIGHT_BG
    p = cell.text_frame.paragraphs[0]
    p.font.size = Pt(13)
    p.font.color.rgb = GRAY_DARK
    p.font.bold = True
    for c in range(1, n_cols):
        cell = table.cell(r, c)
        cell.text = "✓ Pool + Updates"
        cell.fill.solid()
        cell.fill.fore_color.rgb = WHITE
        p = cell.text_frame.paragraphs[0]
        p.font.size = Pt(12)
        p.font.color.rgb = OK_GREEN
        p.alignment = PP_ALIGN.CENTER

add_bullets(s, [
    "5 módulos × 4 Service Pack × (Pool + Updates) = 40 repositorios reales, todos confirmados sincronizados sin errores en Foreman/Katello.",
    "Deliberadamente no se incluyen repos de Source ni Debuginfo (no son necesarios para el upgrade).",
], top=Inches(5.3), size=14)
add_footer(s, "ansible-sles-upgrade · Presentación ejecutiva")

# =============================================================================
# 7. Controles para producción
# =============================================================================
s = add_slide()
set_background(s)
add_title_bar(s, "Controles y consideraciones para producción")
add_bullets(s, [
    "Un servidor a la vez por defecto (procesamiento serial), para minimizar el impacto de cualquier imprevisto.",
    "Ensayo real disponible (VALIDATE) antes de cualquier cambio, y una verificación interna obligatoria se repite automáticamente justo antes de aplicar cualquier cambio real.",
    "Una migración real requiere una confirmación explícita adicional, verificada antes de tocar cualquier repositorio; no puede ocurrir por accidente.",
    "El reinicio tras una migración real es siempre obligatorio: no existe una opción para omitirlo.",
    "SP6 debe quedar realmente validado (aplicado, reiniciado, sistema operativo, servicios y GeoPOS) antes de que el mismo servidor continúe hacia SP7.",
    "Ante cualquier fallo, la información de diagnóstico se conserva por defecto en el propio servidor (no se limpia a ciegas).",
    "El alcance de servidores se controla con el CRQ/Lote/Ambiente del Survey, verificados contra el inventario: si no coinciden con ningún servidor, la ejecución falla antes de tocar nada — evitando ejecuciones accidentales sobre servidores no previstos.",
], size=15)
add_footer(s, "ansible-sles-upgrade · Presentación ejecutiva")

# =============================================================================
# 8. Validación de GeoPOS
# =============================================================================
s = add_slide()
set_background(s)
add_title_bar(s, "Validación de GeoPOS antes y después")
add_bullets(s, [
    "GeoPOS se valida en cuatro dimensiones configurables por servidor: servicios, procesos Java, puertos y (opcionalmente) health checks.",
    "Cada servidor puede tener cero, uno o varios elementos en cada categoría; no se asume una configuración única para todos.",
    "Si un componente marcado como crítico no está saludable antes de iniciar, el upgrade de ese servidor se bloquea por política (configurable para excepciones autorizadas).",
    "Después de una migración real, GeoPOS se vuelve a validar: alcanzar el Service Pack objetivo no se considera éxito si GeoPOS quedó insalubre.",
])
add_footer(s, "ansible-sles-upgrade · Presentación ejecutiva")

# =============================================================================
# 9. Reportes y trazabilidad
# =============================================================================
s = add_slide()
set_background(s)
add_title_bar(s, "Reportes y trazabilidad")
add_bullets(s, [
    "Cada servidor y cada etapa generan un reporte legible (HTML) con el resultado y el detalle de cada verificación.",
    "Estados claros: OK, ADVERTENCIA, FALLIDO, NO VERIFICADO — sin ambigüedad sobre lo que realmente se comprobó.",
    "Un resumen consolidado permite ver, de un vistazo, el estado de todos los servidores procesados.",
    "El operador puede determinar si la migración fue satisfactoria sin conectarse por SSH ni revisar todo el log del Job en AWX.",
    "Importante: para que los reportes se conserven más allá de cada ejecución, se necesita definir un destino de almacenamiento persistente real; mientras no exista, solo están garantizados durante esa ejecución puntual.",
], size=15)
add_footer(s, "ansible-sles-upgrade · Presentación ejecutiva")

# =============================================================================
# 10. Riesgos y próximos pasos
# =============================================================================
s = add_slide()
set_background(s)
add_title_bar(s, "Riesgos principales y próximos pasos")

left_w = Inches(6.0)
tb = s.shapes.add_textbox(Inches(0.6), Inches(1.5), left_w, Inches(5.3))
tf = tb.text_frame
tf.word_wrap = True
p = tf.paragraphs[0]
p.text = "Riesgos y cómo se controlan"
p.font.size = Pt(18)
p.font.bold = True
p.font.color.rgb = NAVY
rows = [
    "Interrupción del servicio durante el upgrade → ensayo real previo (VALIDATE), un servidor a la vez, validación GeoPOS antes/después.",
    "Repositorios incorrectos o inaccesibles → verificación de conectividad antes de modificar el sistema; nunca se inventan datos de Foreman.",
    "Falta de evidencia de rollback real → el proyecto no afirma capacidad de rollback automático salvo que el servidor use Btrfs con snapshots.",
    "Ejecución accidental contra servidores no previstos → el alcance siempre se define explícitamente desde AWX.",
]
for r in rows:
    pp = tf.add_paragraph()
    pp.text = "•  " + r
    pp.font.size = Pt(14)
    pp.font.color.rgb = GRAY_DARK
    pp.space_before = Pt(8)

tb2 = s.shapes.add_textbox(Inches(7.0), Inches(1.5), Inches(5.7), Inches(5.3))
tf2 = tb2.text_frame
tf2.word_wrap = True
p = tf2.paragraphs[0]
p.text = "Próximos pasos"
p.font.size = Pt(18)
p.font.bold = True
p.font.color.rgb = NAVY
steps2 = [
    "Repositorios Foreman/Katello y CA interna: ya completados, verificados e instalación automatizada (SP4 a SP7). Pendiente real: servicios/puertos de GeoPOS, destino definitivo de los reportes.",
    "Configurar los objetos de AWX (Inventory, Credential, Job Template, Survey) con datos del ambiente.",
    "Ejecutar precheck y luego validate en un servidor de laboratorio antes de la primera ejecución real.",
    "Definir la ventana de mantenimiento y acordar el criterio de éxito con el equipo de GeoPOS.",
]
for r in steps2:
    pp = tf2.add_paragraph()
    pp.text = "•  " + r
    pp.font.size = Pt(14)
    pp.font.color.rgb = GRAY_DARK
    pp.space_before = Pt(8)

add_footer(s, "ansible-sles-upgrade · Presentación ejecutiva")

# =============================================================================
# ANEXO 1. Arquitectura técnica (opcional)
# =============================================================================
s = add_slide()
set_background(s)
add_title_bar(s, "Anexo: arquitectura técnica", subtitle="Diapositiva opcional para audiencia técnica")
add_bullets(s, [
    "Un solo playbook de entrada, controlado por el modo de ejecución (precheck / validate / sp4_to_sp5 / sp5_to_sp6 / sp6_to_sp7 / full).",
    "Un solo rol de migración parametrizado, reutilizado para las tres etapas — la diferencia entre ellas es de datos (repositorios, opción --releasever), no de procedimiento.",
    "El ensayo real (VALIDATE) usa un directorio de repositorios temporal y aislado que Zypper consulta en lugar del real, y que se elimina siempre al finalizar.",
    "El diseño técnico completo, con sus justificaciones, está documentado en docs/ARQUITECTURA_Y_DISENO_TECNICO.html del propio repositorio.",
], size=16)
add_footer(s, "ansible-sles-upgrade · Anexo técnico")

# =============================================================================
# ANEXO 2. Ciclo de vida de repositorios (opcional)
# =============================================================================
s = add_slide()
set_background(s)
add_title_bar(s, "Anexo: ciclo de vida de repositorios", subtitle="Diapositiva opcional para audiencia técnica")

steps3 = [
    "Inventariar repositorios actuales (habilitados / deshabilitados)",
    "Deshabilitar solo los que estaban habilitados (nunca se borran)",
    "Agregar repos Foreman de origen -> actualizar la pila de paquetes",
    "Retirar los repos Foreman de origen",
    "Agregar repos Foreman de destino (listos para migrar)",
    "Migrar (dup); si la etapa fue exitosa, retirar los repos Foreman de destino",
]
box_h = Inches(0.6)
top = Inches(1.5)
box_w = Inches(7.6)
left = Inches(0.7)
for i, step in enumerate(steps3):
    add_box(s, f"{i + 1}. {step}", left, top, box_w, box_h, fill=NAVY if i % 2 == 0 else TEAL, size=13)
    if i < len(steps3) - 1:
        add_arrow_down(s, left + box_w / 2, top + box_h, Inches(0.14))
    top += box_h + Inches(0.14)

note2 = s.shapes.add_textbox(Inches(8.7), Inches(1.6), Inches(3.9), Inches(4.8))
tf = note2.text_frame
tf.word_wrap = True
p = tf.paragraphs[0]
p.text = "Los repositorios que estaban deshabilitados antes de empezar no se tocan."
p.font.size = Pt(13)
p.font.color.rgb = GRAY_DARK
p2 = tf.add_paragraph()
p2.text = "\nLos que se deshabilitan durante la migración no se reactivan automáticamente al terminar."
p2.font.size = Pt(13)
p2.font.color.rgb = GRAY_MID
p3 = tf.add_paragraph()
p3.text = "\nAnte un fallo, todo se conserva tal cual para diagnóstico."
p3.font.size = Pt(13)
p3.font.color.rgb = GRAY_MID
p4 = tf.add_paragraph()
p4.text = "\nLos pasos 1-5 son la etapa “Preparar”; el paso 6 (migrar + retirar destino) es la etapa “Aplicar” — ver diapositiva 6."
p4.font.size = Pt(13)
p4.font.color.rgb = GRAY_MID
add_footer(s, "ansible-sles-upgrade · Anexo técnico")

out_path = os.path.join(os.path.dirname(__file__), "ansible-sles-upgrade-presentacion-ejecutiva.pptx")
prs.save(out_path)
print(f"Presentación generada en: {out_path}")
print(f"Diapositivas: {len(prs.slides.__iter__.__self__._sldIdLst)}")
