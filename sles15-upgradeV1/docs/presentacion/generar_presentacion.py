#!/usr/bin/env python3
"""Genera las dos presentaciones ejecutivas del proyecto:

    ansible-sles-upgrade-presentacion-gerencial.pptx  (6 diapositivas)
    ansible-sles-upgrade-presentacion-tecnica.pptx    (12 diapositivas)

Refleja la arquitectura y el contenido REALES de ambos decks actuales del
repositorio (no supuestos). El diseño visual aquí es un sistema propio en
python-pptx -- limpio, con la misma paleta e idea de "tarjetas" de los
archivos .pptx entregados -- pero NO es un clon pixel a pixel de sus formas:
reconstruir en código cada una de las ~150 formas con posición exacta no
aporta valor real y sería frágil (ver CLAUDE.md, "Simplicidad"). Lo que este
script garantiza es que el CONTENIDO (títulos, mensajes clave y notas del
orador) sea coherente con lo que hoy existe en ambos .pptx.

Requiere python-pptx (pip install python-pptx). Regenerar con:

    python3 docs/presentacion/generar_presentacion.py

ADVERTENCIA: ejecutar este script SOBRESCRIBE los dos .pptx en este
directorio. Si alguno de los dos fue editado a mano después de la última
regeneración (por ejemplo, marcando a mano el checklist de pruebas QA de las
diapositivas finales del deck técnico -- ver `agregar_checklist()` abajo),
esa edición manual se pierde. Haga una copia antes de regenerar si necesita
conservarla.
"""

import os

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# ---------------------------------------------------------------------------
# Paleta (coherente con los .pptx entregados: verde/teal de marca + navy)
# ---------------------------------------------------------------------------
TEAL = RGBColor(0x15, 0xB5, 0x89)
TEAL_LIGHT = RGBColor(0x8B, 0xE7, 0xD0)
NAVY_DARK = RGBColor(0x0D, 0x24, 0x34)
NAVY = RGBColor(0x10, 0x2C, 0x3C)
NAVY_MED = RGBColor(0x1B, 0x3B, 0x4C)
NAVY_CARD = RGBColor(0x17, 0x3A, 0x49)
GRAY_TEXT = RGBColor(0x5A, 0x72, 0x81)
GRAY_LIGHT = RGBColor(0x9A, 0xB8, 0xC3)
GRAY_PALE = RGBColor(0xB7, 0xCF, 0xD8)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
BG_LIGHT = RGBColor(0xE8, 0xEF, 0xF2)
CARD_BG = RGBColor(0xFF, 0xFF, 0xFF)
OK_GREEN = RGBColor(0x15, 0xB5, 0x89)
OK_GREEN_BG = RGBColor(0xDA, 0xF3, 0xE7)
WARN_AMBER = RGBColor(0xB8, 0x86, 0x0B)
WARN_AMBER_BG = RGBColor(0xFB, 0xF0, 0xDA)
FAIL_RED = RGBColor(0xC6, 0x28, 0x28)
FAIL_RED_BG = RGBColor(0xFB, 0xE2, 0xE2)
NOT_CHECKED_GRAY = RGBColor(0x6B, 0x7A, 0x82)
NOT_CHECKED_BG = RGBColor(0xE4, 0xE8, 0xEA)

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)

FONT_NAME = "Calibri"  # "Inter" (usada en los .pptx entregados) no es una fuente estándar de PowerPoint/LibreOffice; Calibri es el equivalente ampliamente disponible más cercano.


# ---------------------------------------------------------------------------
# Helpers genéricos
# ---------------------------------------------------------------------------

def nueva_presentacion():
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H
    return prs


def add_slide(prs):
    blank = prs.slide_layouts[6]
    return prs.slides.add_slide(blank)


def set_notes(slide, text):
    """Notas del presentador: texto de apoyo que NO se proyecta."""
    notes_tf = slide.notes_slide.notes_text_frame
    notes_tf.text = text


def set_background(slide, color=WHITE):
    bg = slide.background
    bg.fill.solid()
    bg.fill.fore_color.rgb = color


def _apply_font(run_or_para, size=14, bold=False, color=NAVY, name=FONT_NAME, align=None):
    run_or_para.font.size = Pt(size)
    run_or_para.font.bold = bold
    run_or_para.font.color.rgb = color
    run_or_para.font.name = name
    if align is not None and hasattr(run_or_para, "alignment"):
        run_or_para.alignment = align


def add_text(slide, text, left, top, width, height, size=14, bold=False, color=NAVY,
             align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, wrap=True, line_spacing=None):
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame
    tf.word_wrap = wrap
    tf.vertical_anchor = anchor
    lines = text.split("\n")
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = line
        p.alignment = align
        if line_spacing:
            p.line_spacing = line_spacing
        _apply_font(p, size=size, bold=bold, color=color)
    return tb


def add_rect(slide, left, top, width, height, fill=TEAL, line=False):
    shp = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    shp.fill.solid()
    shp.fill.fore_color.rgb = fill
    if not line:
        shp.line.fill.background()
    shp.shadow.inherit = False
    return shp


def add_rounded(slide, left, top, width, height, fill=CARD_BG):
    shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    shp.fill.solid()
    shp.fill.fore_color.rgb = fill
    shp.line.fill.background()
    shp.shadow.inherit = False
    return shp


def add_top_accent(slide):
    """Barra delgada superior, igual idea que el Shape 0 de ambos .pptx entregados."""
    add_rect(slide, 0, 0, SLIDE_W, Inches(0.06), fill=TEAL)


def add_footer(slide, page, total):
    add_rect(slide, Inches(0.82), SLIDE_H - Inches(0.46), SLIDE_W - Inches(1.64), Emu(1), fill=GRAY_LIGHT)
    add_text(slide, "G E O P O S   /   I N F R A E S T R U C T U R A   L I N U X",
              Inches(0.82), SLIDE_H - Inches(0.43), Inches(7), Inches(0.2),
              size=8, bold=True, color=GRAY_TEXT)
    add_text(slide, f"{page:02d}  /  {total:02d}",
              SLIDE_W - Inches(1.5), SLIDE_H - Inches(0.44), Inches(0.9), Inches(0.2),
              size=9, bold=True, color=GRAY_TEXT, align=PP_ALIGN.RIGHT)


def add_header(slide, section_label, title, subtitle, dark=False):
    """Encabezado estándar de diapositiva de contenido: etiqueta de sección
    (teal), título grande y subtítulo gris. dark=True para fondo navy."""
    label_color = TEAL_LIGHT if dark else TEAL
    title_color = WHITE if dark else NAVY
    subtitle_color = GRAY_PALE if dark else GRAY_TEXT
    add_text(slide, section_label, Inches(0.82), Inches(0.44), Inches(10), Inches(0.3),
              size=14, bold=True, color=label_color)
    add_text(slide, title, Inches(0.82), Inches(0.90), Inches(11.9), Inches(0.66),
              size=30, bold=True, color=title_color)
    add_text(slide, subtitle, Inches(0.82), Inches(1.62), Inches(11.6), Inches(0.45),
              size=15, bold=False, color=subtitle_color)


def add_card(slide, left, top, width, height, numero, titulo, descripcion,
             numero_bg=BG_LIGHT, numero_color=TEAL, titulo_color=NAVY, desc_color=GRAY_TEXT,
             card_bg=CARD_BG, titulo_size=16, desc_size=12):
    """Tarjeta blanca con número/ícono + título + descripción (el patrón más
    repetido en ambos .pptx entregados: motivación, modelo operativo,
    gobierno, continuidad funcional, etc.)."""
    add_rounded(slide, left, top, width, height, fill=card_bg)
    pad = Inches(0.22)
    if numero:
        badge = Inches(0.42)
        add_rounded(slide, left + pad, top + pad, badge, badge, fill=numero_bg)
        add_text(slide, numero, left + pad, top + pad, badge, badge,
                  size=13, bold=True, color=numero_color, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        text_left = left + pad + badge + Inches(0.18)
    else:
        text_left = left + pad
    text_width = width - (text_left - left) - pad
    add_text(slide, titulo, text_left, top + pad - Inches(0.02), text_width, Inches(0.38),
              size=titulo_size, bold=True, color=titulo_color)
    add_text(slide, descripcion, text_left, top + pad + Inches(0.36), text_width,
              height - pad - Inches(0.36) - pad, size=desc_size, color=desc_color, wrap=True)


def add_card_row(slide, items, top, left=Inches(0.82), total_width=None, height=Inches(1.40), gap=Inches(0.27), **kwargs):
    """Distribuye tarjetas iguales en una fila horizontal."""
    total_width = total_width or (SLIDE_W - Inches(1.64))
    n = len(items)
    card_w = (total_width - gap * (n - 1)) / n
    x = left
    for numero, titulo, descripcion in items:
        add_card(slide, x, top, card_w, height, numero, titulo, descripcion, **kwargs)
        x += card_w + gap


def add_step_chip(slide, left, top, width, height, numero, texto, fill=BG_LIGHT, badge_fill=NAVY_MED):
    add_rounded(slide, left, top, width, height, fill=fill)
    badge = Inches(0.34)
    bpad = Inches(0.11)
    add_rounded(slide, left + bpad, top + bpad, badge, badge, fill=badge_fill)
    add_text(slide, numero, left + bpad, top + bpad, badge, badge,
              size=12, bold=True, color=WHITE, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    add_text(slide, texto, left + bpad + badge + Inches(0.12), top, width - bpad - badge - Inches(0.12), height,
              size=12, bold=True, color=NAVY, anchor=MSO_ANCHOR.MIDDLE)


def add_arrow_right(slide, left, y_center, length=Inches(0.4), color=TEAL, size=22):
    add_text(slide, "→", left, y_center - Inches(0.2), length, Inches(0.4),
              size=size, bold=True, color=color, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)


def add_legend_estado(slide, left, top, total_width=None, size=12):
    """Leyenda de los 4 estados de reporte: OK / ADVERTENCIA / FALLIDO / NO VERIFICADO.

    El ancho de cada píldora se calcula a partir de total_width (por defecto
    10.65", pensado para usarse a ancho casi completo de diapositiva) para
    poder encajar la misma leyenda también en columnas angostas sin que se
    salga de los límites de la diapositiva."""
    estados = [
        ("OK", OK_GREEN, OK_GREEN_BG),
        ("ADVERTENCIA", WARN_AMBER, WARN_AMBER_BG),
        ("FALLIDO", FAIL_RED, FAIL_RED_BG),
        ("NO VERIFICADO", NOT_CHECKED_GRAY, NOT_CHECKED_BG),
    ]
    n = len(estados)
    gap = Inches(0.15)
    total_width = total_width or Inches(10.65)
    w = (total_width - gap * (n - 1)) / n
    x = left
    for texto, color, bg in estados:
        add_rounded(slide, x, top, w, Inches(0.42), fill=bg)
        add_text(slide, texto, x, top, w, Inches(0.42), size=size, bold=True, color=color,
                  align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        x += w + gap


def add_checklist_item(slide, left, top, width, titulo, descripcion, completado=False):
    """Fila de checklist de pruebas (deck técnico, diapositivas 11-12).

    Por defecto siempre se genera en estado PENDIENTE: este script no tiene
    forma de saber qué pruebas se marcaron a mano en el .pptx actual, y
    fingir que ya pasaron violaría la regla de "no inventar" de CLAUDE.md.
    Después de regenerar, vuelva a marcar a mano (seleccionar la fila y
    confirmar) las pruebas que ya se hayan completado realmente.
    """
    completado = False  # ver docstring: nunca se asume completado al regenerar
    glyph = "☑" if completado else "☐"
    bg = OK_GREEN_BG if completado else BG_LIGHT
    color = OK_GREEN if completado else NAVY_MED
    estado = "COMPLETADA" if completado else "PENDIENTE"
    add_rounded(slide, left, top, width, Inches(0.56), fill=bg)
    add_text(slide, glyph, left + Inches(0.14), top, Inches(0.4), Inches(0.56),
              size=18, bold=True, color=color, anchor=MSO_ANCHOR.MIDDLE)
    add_text(slide, f"{titulo}   ·   {estado}", left + Inches(0.6), top + Inches(0.06),
              width - Inches(0.75), Inches(0.26), size=13, bold=True, color=NAVY)
    add_text(slide, descripcion, left + Inches(0.6), top + Inches(0.30),
              width - Inches(0.75), Inches(0.24), size=10.5, color=GRAY_TEXT)


# ===========================================================================
# DECK GERENCIAL (6 diapositivas)
# ===========================================================================

def construir_gerencial():
    prs = nueva_presentacion()
    TOTAL = 6

    # --- Diapositiva 1: portada ---------------------------------------
    s = add_slide(prs)
    set_background(s, NAVY_DARK)
    add_top_accent(s)
    add_text(s, "PRESENTACIÓN EJECUTIVA", Inches(0.82), Inches(0.82), Inches(4), Inches(0.3),
              size=14, bold=True, color=TEAL_LIGHT)
    add_text(s, "Upgrade automatizado de\nSUSE Linux Enterprise 15", Inches(0.82), Inches(1.57),
              Inches(7.5), Inches(1.7), size=36, bold=True, color=WHITE, line_spacing=1.05)
    add_text(s, "Actualización secuencial, controlada y trazable\npara la plataforma GeoPOS",
              Inches(0.82), Inches(3.50), Inches(7.0), Inches(0.85), size=17, color=GRAY_PALE, line_spacing=1.15)
    add_text(s, "AWX  +  ANSIBLE", Inches(0.82), Inches(5.17), Inches(3.3), Inches(0.35),
              size=12, bold=True, color=TEAL_LIGHT)
    add_text(s, "Repositorios internos Foreman / Katello", Inches(0.82), Inches(5.58), Inches(5.9), Inches(0.4),
              size=12, color=GRAY_PALE)
    # Evolución SP4..SP7 (columna derecha, diagonal ascendente simplificada)
    etapas = [("SP4", 4.73, NAVY_MED, WHITE), ("SP5", 3.72, NAVY_MED, WHITE),
              ("SP6", 2.70, NAVY_MED, WHITE), ("SP7", 1.68, TEAL, NAVY_DARK)]
    xs = [7.38, 8.72, 10.03, 11.33]
    for (txt, top, bg, fg), x in zip(etapas, xs):
        add_rounded(s, Inches(x), Inches(top), Inches(0.94), Inches(0.94), fill=bg)
        add_text(s, txt, Inches(x), Inches(top), Inches(0.94), Inches(0.94), size=19, bold=True,
                  color=fg, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    add_text(s, "EVOLUCIÓN POR ETAPAS", Inches(8.30), Inches(6.10), Inches(4.10), Inches(0.26),
              size=10.5, bold=True, color=TEAL_LIGHT)
    add_text(s, "Octubre de 2026", Inches(0.82), Inches(6.67), Inches(3.0), Inches(0.26),
              size=10, color=GRAY_LIGHT)
    add_text(s, "G E O P O S   /   I N F R A E S T R U C T U R A   L I N U X", Inches(0.82), Inches(7.07),
              Inches(7), Inches(0.18), size=8, bold=True, color=GRAY_LIGHT)
    add_text(s, "01  /  06", SLIDE_W - Inches(1.5), Inches(7.06), Inches(0.9), Inches(0.2),
              size=9, bold=True, color=GRAY_PALE, align=PP_ALIGN.RIGHT)
    set_notes(s, (
        "Abrir con el propósito: estandarizar y gobernar la actualización de los servidores SUSE "
        "Linux Enterprise 15 que soportan GeoPOS. La automatización utiliza AWX para orquestar, "
        "Ansible para ejecutar y Foreman/Katello como origen de contenido corporativo.\n\n"
        "Aclarar que los cambios de Service Pack se realizan de manera secuencial y no se salta "
        "directamente de SP5 a SP7. La presentación resume la solución y sus avances; no representa "
        "una puesta en producción ya completada. El objetivo final es avanzar hacia SP7, sujeto a "
        "los controles y pruebas establecidos."
    ))

    # --- Diapositiva 2: motivación -------------------------------------
    s = add_slide(prs)
    set_background(s, WHITE)
    add_top_accent(s)
    add_header(s, "02   /   MOTIVACIÓN", "Automatizar desde el diseño aporta mayor control",
               "La solución se concibió automatizada desde el inicio; no sustituye un proceso manual vigente.")
    add_card_row(s, [
        ("01", "Preparación verificable", "Revisar prerrequisitos antes de iniciar un cambio."),
        ("02", "Ejecución consistente", "Aplicar una secuencia estándar a cada servidor."),
    ], top=Inches(2.24))
    add_card_row(s, [
        ("03", "Gobierno del cambio", "Definir alcance, autorización y avance controlado."),
        ("04", "Trazabilidad completa", "Registrar resultados para seguimiento y auditoría."),
    ], top=Inches(3.89), numero_bg=OK_GREEN_BG)
    add_rect(s, Inches(0.82), Inches(5.80), Inches(11.66), Inches(0.70), fill=NAVY_DARK)
    add_text(s, "✓  Mayor estandarización y control del proceso", Inches(1.09), Inches(5.80),
              Inches(10.8), Inches(0.70), size=18, bold=True, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
    add_footer(s, 2, TOTAL)
    set_notes(s, (
        "La justificación no debe presentarse como reemplazo de una operación manual vigente: el "
        "proyecto se diseñó automatizado desde su origen. Frente a una intervención manual repetida, "
        "la automatización permite establecer una forma común de ejecución, validar condiciones antes "
        "de actuar y dejar evidencia de lo ocurrido.\n\n"
        "Los cuatro beneficios son preparación verificable (versión del sistema, espacio, conectividad "
        "y repositorios), consistencia (misma secuencia controlada), gobierno (CRQ/RFC, lote, ambiente "
        "y confirmación explícita) y trazabilidad (reportes por servidor, fase y lote).\n\n"
        "No afirmar un ahorro de tiempo medido ni eliminación de interrupciones: las migraciones "
        "reales requieren reinicio y ventana autorizada."
    ))

    # --- Diapositiva 3: solución ----------------------------------------
    s = add_slide(prs)
    set_background(s, WHITE)
    add_top_accent(s)
    add_header(s, "03   /   SOLUCIÓN", "Una automatización integrada a las plataformas actuales",
               "AWX coordina · Ansible ejecuta · Foreman / Katello suministra paquetes internos.")
    componentes = [
        ("01", "AWX", "Orquesta el cambio", "Selecciona el lote y coordina el flujo."),
        ("02", "Ansible", "Ejecuta las tareas", "Aplica el upgrade y las verificaciones."),
        ("03", "SLES 15 + GeoPOS", "Infraestructura objetivo", "Actualiza el SO y comprueba su estado."),
    ]
    x = Inches(0.82)
    w = Inches(3.65)
    gap = Inches(0.35)
    for i, (num, titulo, sub, desc) in enumerate(componentes):
        add_rounded(s, x, Inches(2.35), w, Inches(2.37), fill=CARD_BG)
        add_rounded(s, x + Inches(0.26), Inches(2.61), Inches(0.42), Inches(0.42), fill=OK_GREEN_BG)
        add_text(s, num, x + Inches(0.26), Inches(2.61), Inches(0.42), Inches(0.42), size=12, bold=True,
                  color=TEAL, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        add_text(s, titulo, x + Inches(0.26), Inches(3.23), w - Inches(0.5), Inches(0.42), size=22, bold=True, color=NAVY)
        add_text(s, sub, x + Inches(0.26), Inches(3.74), w - Inches(0.5), Inches(0.34), size=14, bold=True, color=TEAL)
        add_text(s, desc, x + Inches(0.26), Inches(4.15), w - Inches(0.5), Inches(0.5), size=11.5, color=GRAY_TEXT)
        if i < 2:
            add_arrow_right(s, x + w + Inches(0.02), Inches(3.49), length=gap)
        x += w + gap
    add_text(s, "FLUJO DE EJECUCIÓN EN AWX", Inches(0.82), Inches(5.12), Inches(7), Inches(0.27),
              size=11, bold=True, color=GRAY_TEXT)
    pasos = [("1", "Verificar", BG_LIGHT), ("2", "Preparar", BG_LIGHT), ("3", "Aplicar", OK_GREEN_BG),
             ("4", "Reportar", BG_LIGHT), ("5", "Sincronizar*", BG_LIGHT)]
    x = Inches(0.82)
    cw = Inches(2.17)
    for num, texto, fill in pasos:
        add_step_chip(s, x, Inches(5.53), cw, Inches(0.67), num, texto, fill=fill)
        x += cw + Inches(0.21)
    add_text(s, "* Sincronización de reportes a SharePoint opcional.", Inches(0.82), Inches(6.37),
              Inches(10.86), Inches(0.27), size=10, color=GRAY_TEXT)
    add_footer(s, 3, TOTAL)
    set_notes(s, (
        "La arquitectura es deliberadamente simple: AWX es la interfaz de orquestación y ejecución de "
        "cambios; Ansible realiza la lógica sobre los servidores SLES 15 y obtiene paquetes "
        "exclusivamente desde Foreman/Katello. El inventario dinámico procede de un Excel compartido "
        "en SharePoint y el Survey relaciona la ejecución con CRQ/RFC, lote y ambiente.\n\n"
        "El Workflow consta de cinco etapas. Verificar: evaluar prerrequisitos. Preparar: administrar "
        "repositorios temporales de la fase. Aplicar: simulación preventiva obligatoria justo antes del "
        "cambio real, actualización, reinicio y validación posterior. Reportar: generar resultados "
        "individuales y consolidados. Sincronizar: publicar una copia de los reportes en SharePoint, "
        "cuando esté configurado. Puede existir aprobación humana entre Preparar y Aplicar.\n\n"
        "La validación real de servicios GeoPOS requiere completar la parametrización por servidor "
        "antes de la salida a producción. No mencionar VALIDATE como modo independiente: ya no forma "
        "parte de la solución vigente."
    ))

    # --- Diapositiva 4: alcance (4 modos) --------------------------------
    s = add_slide(prs)
    set_background(s, NAVY_DARK)
    add_top_accent(s)
    add_header(s, "04   /   ALCANCE", "Cuatro modos; una regla: no saltar etapas",
               "Tres transiciones individuales y un modo FULL con dos cambios secuenciales.", dark=True)
    add_text(s, "MODOS INDIVIDUALES", Inches(0.82), Inches(2.25), Inches(5.5), Inches(0.29),
              size=12, bold=True, color=TEAL_LIGHT)
    transiciones = [("SP4", "SP5"), ("SP5", "SP6"), ("SP6", "SP7")]
    x = Inches(0.82)
    w = Inches(3.70)
    gap = Inches(0.32)
    for origen, destino in transiciones:
        add_rounded(s, x, Inches(2.65), w, Inches(1.23), fill=NAVY_MED)
        add_text(s, origen, x + Inches(0.24), Inches(2.98), Inches(1.08), Inches(0.45), size=22, bold=True, color=WHITE)
        add_text(s, "→", x + Inches(1.54), Inches(2.98), Inches(0.49), Inches(0.44), size=22, bold=True, color=TEAL, align=PP_ALIGN.CENTER)
        add_text(s, destino, x + Inches(2.30), Inches(2.98), Inches(1.08), Inches(0.45), size=22, bold=True, color=WHITE)
        x += w + gap
    add_rect(s, Inches(0.82), Inches(4.35), Inches(11.73), Inches(1.28), fill=RGBColor(0x18, 0x48, 0x40))
    add_rounded(s, Inches(1.07), Inches(4.66), Inches(1.42), Inches(0.32), fill=NAVY_MED)
    add_text(s, "MODO FULL", Inches(1.07), Inches(4.66), Inches(1.42), Inches(0.32), size=9, bold=True,
              color=TEAL_LIGHT, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    add_text(s, "SP5", Inches(3.27), Inches(4.71), Inches(1.22), Inches(0.43), size=24, bold=True, color=WHITE)
    add_text(s, "→", Inches(4.78), Inches(4.68), Inches(0.38), Inches(0.48), size=24, bold=True, color=TEAL_LIGHT, align=PP_ALIGN.CENTER)
    add_text(s, "SP6", Inches(5.39), Inches(4.71), Inches(1.22), Inches(0.43), size=24, bold=True, color=WHITE)
    add_text(s, "→", Inches(6.88), Inches(4.68), Inches(0.38), Inches(0.48), size=24, bold=True, color=TEAL_LIGHT, align=PP_ALIGN.CENTER)
    add_text(s, "SP7", Inches(7.50), Inches(4.71), Inches(1.19), Inches(0.43), size=24, bold=True, color=WHITE)
    add_text(s, "Verifica SP6 antes\nde continuar a SP7", Inches(9.41), Inches(4.72), Inches(2.87), Inches(0.62),
              size=12, bold=True, color=RGBColor(0xD2, 0xF7, 0xE8), line_spacing=1.05)
    add_text(s, "ℹ  SP4→SP5 se mantiene independiente para simplificar el flujo.",
              Inches(1.40), Inches(6.00), Inches(9.5), Inches(0.35), size=13, color=WHITE)
    add_text(s, "≈90 % del parque en SP5 · estimación operativa", Inches(1.40), Inches(6.42),
              Inches(10.4), Inches(0.26), size=11, color=GRAY_PALE)
    add_footer(s, 4, TOTAL)
    set_notes(s, (
        "Los cuatro modos de ejecución son SP4→SP5, SP5→SP6, SP6→SP7 y FULL. FULL ejecuta SP5→SP6 y, "
        "después de completar, reiniciar y verificar ese Service Pack intermedio, SP6→SP7. No existe "
        "salto directo de SP5 a SP7.\n\n"
        "Se decidió mantener SP4→SP5 como ejecución independiente para evitar añadir una tercera "
        "transición a FULL. La razón de cobertura también influye: aproximadamente el 90 % de los "
        "servidores se encuentra en SP5, según estimación operativa del proyecto (no una medición "
        "certificada); hay pocos equipos en SP4, algunos en Cuba. Un servidor en SP4 puede migrar "
        "primero a SP5 y luego usar el modo que corresponda.\n\n"
        "Cada transición tiene validaciones propias y un reinicio obligatorio; un error crítico bloquea "
        "el avance al siguiente Service Pack del mismo servidor."
    ))

    # --- Diapositiva 5: gobierno y evidencias ----------------------------
    s = add_slide(prs)
    set_background(s, WHITE)
    add_top_accent(s)
    add_header(s, "05   /   GOBIERNO Y EVIDENCIAS", "El cambio se controla de principio a fin",
               "Condiciones previas, ejecución supervisada y resultados consultables.")
    fases = [("01", "Antes", "Prerrequisitos y simulación preventiva"),
             ("02", "Durante", "Confirmación del cambio y avance controlado"),
             ("03", "Después", "Verificación del sistema y servicios definidos")]
    top = Inches(2.28)
    for num, titulo, desc in fases:
        add_card(s, Inches(0.82), top, Inches(6.31), Inches(0.97), num, titulo, desc,
                  numero_bg=OK_GREEN_BG if num == "03" else BG_LIGHT, titulo_size=18, desc_size=13)
        top += Inches(1.16)
    add_rounded(s, Inches(7.46), Inches(2.28), Inches(5.05), Inches(4.02), fill=CARD_BG)
    add_rect(s, Inches(7.46), Inches(2.28), Inches(5.05), Inches(0.59), fill=NAVY_DARK)
    add_text(s, "REPORTE DE EJECUCIÓN", Inches(7.75), Inches(2.43), Inches(4.46), Inches(0.26),
              size=12.5, bold=True, color=WHITE)
    add_text(s, "Evidencia generada automáticamente", Inches(7.74), Inches(3.15), Inches(4.41), Inches(0.29),
              size=13, bold=True, color=NAVY)
    niveles = ["POR SERVIDOR", "POR ETAPA", "POR LOTE"]
    x = Inches(7.74)
    for niv in niveles:
        add_text(s, niv, x, Inches(3.74), Inches(1.6), Inches(0.22), size=9, bold=True, color=GRAY_TEXT)
        add_rounded(s, x, Inches(4.12), Inches(1.6), Inches(0.57), fill=BG_LIGHT)
        add_text(s, "✓", x, Inches(4.12), Inches(1.6), Inches(0.57), size=16, bold=True, color=NAVY_MED,
                  align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        x += Inches(1.75)
    add_text(s, "Resultados diferenciados", Inches(7.74), Inches(4.98), Inches(4.4), Inches(0.26),
              size=11, bold=True, color=GRAY_TEXT)
    add_legend_estado(s, Inches(7.74), Inches(5.30), total_width=Inches(4.4), size=9)
    add_text(s, "Reportes HTML individuales y consolidados por lote", Inches(7.74), Inches(5.85),
              Inches(4.4), Inches(0.26), size=10.5, color=GRAY_TEXT)
    add_text(s, "* GeoPOS: validación funcional pendiente de parametrizar y probar.", Inches(0.82), Inches(6.60),
              Inches(11.6), Inches(0.26), size=10, color=GRAY_TEXT)
    add_footer(s, 5, TOTAL)
    set_notes(s, (
        "El control operativo se distribuye a lo largo de la ejecución. Antes del cambio se verifican "
        "condiciones técnicas y se corre una simulación preventiva obligatoria de Zypper en la propia "
        "fase Aplicar. Durante el cambio se exige confirmación y se ejecuta por defecto un servidor a "
        "la vez, con posibilidad de aprobación humana entre preparación y aplicación. Después se "
        "confirma el Service Pack alcanzado y el estado de los servicios configurados.\n\n"
        "Las evidencias HTML permiten revisar resultados por servidor y etapa y un consolidado por "
        "lote. Los estados distinguen OK, advertencia, fallido y no verificado; una revisión no "
        "ejecutada jamás debe presentarse como aprobada. La sincronización hacia SharePoint puede "
        "habilitarse.\n\n"
        "Importante: la tarjeta de reportes de esta diapositiva es una ilustración esquemática de la "
        "salida del sistema, no evidencia de una ejecución productiva. La parametrización y "
        "verificación de servicios reales GeoPOS se encuentra pendiente para QA y el despliegue."
    ))

    # --- Diapositiva 6: avances y siguientes pasos -----------------------
    s = add_slide(prs)
    set_background(s, WHITE)
    add_top_accent(s)
    add_header(s, "06   /   AVANCES Y SIGUIENTES PASOS", "Un resultado confirmado; próximos hitos definidos",
               "La salida a producción estará condicionada a las pruebas y verificaciones pendientes.")
    add_rect(s, Inches(0.82), Inches(2.15), Inches(11.68), Inches(0.62), fill=OK_GREEN_BG)
    add_text(s, "✓  PRUEBA COMPLETADA  ·  SP5 → SP6 sobre plantilla SUSE Linux Enterprise 15 SP5",
              Inches(1.05), Inches(2.15), Inches(11.2), Inches(0.62), size=14, bold=True, color=OK_GREEN,
              anchor=MSO_ANCHOR.MIDDLE)
    add_card_row(s, [
        ("01", "PLANTILLA", "SP6→SP7 y modo FULL · 2 escenarios pendientes"),
        ("02", "AMBIENTE QA", "Tres rutas individuales + FULL · 4 escenarios pendientes"),
        ("03", "CIERRE GEOPOS", "Servicios, procesos y puertos · verificación pendiente"),
    ], top=Inches(3.05), height=Inches(1.55), numero_bg=WARN_AMBER_BG, numero_color=WARN_AMBER, desc_size=11.5)
    add_rect(s, Inches(0.82), Inches(5.80), Inches(11.66), Inches(0.70), fill=NAVY_DARK)
    add_text(s, "Habilitación productiva: después de las pruebas, aprobación y ventana de mantenimiento.",
              Inches(1.09), Inches(5.80), Inches(10.8), Inches(0.70), size=15, bold=True, color=WHITE,
              anchor=MSO_ANCHOR.MIDDLE)
    add_footer(s, 6, TOTAL)
    set_notes(s, (
        "Cerrar distinguiendo resultados confirmados y pendientes. El único ensayo señalado como "
        "completado es la migración SP5→SP6 en una plantilla SUSE Linux Enterprise 15 SP5. Esto no "
        "equivale a una validación de QA ni a una implementación productiva.\n\n"
        "Sobre la plantilla quedan pendientes el salto SP6→SP7 y el modo FULL SP5→SP6→SP7, idealmente "
        "partiendo en FULL de un estado SP5 inicial. En el ambiente real de QA deben probarse las "
        "cuatro rutas: SP4→SP5, SP5→SP6, SP6→SP7 y FULL.\n\n"
        "Finalmente corresponde integrar y validar los servicios reales de GeoPOS por servidor "
        "(unidades systemd, procesos Java, puertos TCP y comprobaciones HTTP/HTTPS opcionales) para "
        "establecer el criterio de éxito funcional.\n\n"
        "Solo cuando estas pruebas estén completadas y las dependencias del cambio resueltas podrá "
        "coordinarse la ventana de mantenimiento y la aprobación para producción. No prometer una "
        "fecha ni una tasa de éxito aún no acreditadas. Esta presentación ejecutiva se complementa con "
        "una versión funcional/técnica de doce diapositivas y con el informe de pruebas."
    ))

    return prs


# ===========================================================================
# DECK TÉCNICO (12 diapositivas)
# ===========================================================================

def construir_tecnica():
    prs = nueva_presentacion()
    TOTAL = 12

    # --- Diapositiva 1: portada ------------------------------------------
    s = add_slide(prs)
    set_background(s, NAVY_DARK)
    add_top_accent(s)
    add_text(s, "PRESENTACIÓN EJECUTIVA", Inches(0.82), Inches(0.82), Inches(4), Inches(0.3),
              size=14, bold=True, color=TEAL_LIGHT)
    add_text(s, "Upgrade de Service Pack\nSUSE Linux Enterprise 15", Inches(0.82), Inches(1.57),
              Inches(8.0), Inches(1.7), size=34, bold=True, color=WHITE, line_spacing=1.05)
    add_text(s, "Modernización controlada de la plataforma GeoPOS", Inches(0.82), Inches(3.50),
              Inches(7.5), Inches(0.45), size=16, color=GRAY_PALE)
    add_text(s, "Automatización con AWX + Ansible", Inches(0.82), Inches(5.10), Inches(5.5), Inches(0.35),
              size=12, bold=True, color=TEAL_LIGHT)
    add_text(s, "Suministro de paquetes desde Foreman / Katello", Inches(0.82), Inches(5.50), Inches(6.5),
              Inches(0.4), size=12, color=GRAY_PALE)
    etapas = [("SP4", 4.73, NAVY_MED, WHITE), ("SP5", 3.72, NAVY_MED, WHITE),
              ("SP6", 2.70, NAVY_MED, WHITE), ("SP7", 1.68, TEAL, NAVY_DARK)]
    xs = [7.38, 8.72, 10.03, 11.33]
    for (txt, top, bg, fg), x in zip(etapas, xs):
        add_rounded(s, Inches(x), Inches(top), Inches(0.94), Inches(0.94), fill=bg)
        add_text(s, txt, Inches(x), Inches(top), Inches(0.94), Inches(0.94), size=19, bold=True,
                  color=fg, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    add_text(s, "EVOLUCIÓN POR ETAPAS", Inches(8.30), Inches(6.10), Inches(4.10), Inches(0.26),
              size=10.5, bold=True, color=TEAL_LIGHT)
    add_text(s, "Octubre de 2026", Inches(0.82), Inches(6.67), Inches(3.0), Inches(0.26),
              size=10, color=GRAY_LIGHT)
    add_text(s, "G E O P O S   /   I N F R A E S T R U C T U R A   L I N U X", Inches(0.82), Inches(7.07),
              Inches(7), Inches(0.18), size=8, bold=True, color=GRAY_LIGHT)
    add_text(s, "01  /  12", SLIDE_W - Inches(1.5), Inches(7.06), Inches(0.9), Inches(0.2),
              size=9, bold=True, color=GRAY_PALE, align=PP_ALIGN.RIGHT)
    set_notes(s, (
        "Abrir con el propósito: convertir las migraciones de Service Pack de SLES 15 en un proceso "
        "estandarizado, gobernado desde AWX y ejecutado con Ansible para los servidores de GeoPOS. El "
        "objetivo es avanzar hacia SP7 conservando controles de disponibilidad, preparación y "
        "evidencia.\n\n"
        "Precisar desde el principio que no se realizan saltos entre Service Packs: las migraciones se "
        "ejecutan secuencialmente. En el proyecto actual, SP4→SP5 es un modo independiente; la ruta "
        "completa automatizada agrupa SP5→SP6→SP7 y comprueba la etapa intermedia antes de continuar. "
        "La presentación resume capacidades y resultados de laboratorio; no debe interpretarse como "
        "despliegue completado en producción."
    ))

    # --- Diapositiva 2: visión ejecutiva ----------------------------------
    s = add_slide(prs)
    set_background(s, WHITE)
    add_top_accent(s)
    add_header(s, "01 / VISIÓN EJECUTIVA", "Automatizar desde el diseño: control y trazabilidad",
               "La solución se concibió automatizada desde el inicio; no reemplaza un procedimiento manual vigente.")
    add_text(s, "DECISIÓN DE DISEÑO: ESTANDARIZAR LA MIGRACIÓN ANTES DE ESCALARLA", Inches(0.82), Inches(2.15),
              Inches(11), Inches(0.26), size=11, bold=True, color=GRAY_TEXT)
    add_card_row(s, [
        ("01", "Prerrequisitos verificados", "Versión, espacio, conectividad y acceso a repositorios"),
        ("02", "Validaciones preventivas", "Comprobaciones iniciales y simulación previa al cambio"),
    ], top=Inches(2.55))
    add_card_row(s, [
        ("03", "Ejecución gobernada", "CRQ, lote, ambiente, confirmación y avance secuencial"),
        ("04", "Evidencia y seguimiento", "Resultados por servidor, etapa y lote para auditoría"),
    ], top=Inches(4.20), numero_bg=OK_GREEN_BG)
    add_rect(s, Inches(0.82), Inches(6.00), Inches(11.66), Inches(0.62), fill=NAVY_DARK)
    add_text(s, "Mayor estandarización y control del proceso  ·  Validaciones previas  ·  Evidencia disponible",
              Inches(1.05), Inches(6.00), Inches(11.2), Inches(0.62), size=13.5, bold=True, color=WHITE,
              anchor=MSO_ANCHOR.MIDDLE)
    add_footer(s, 2, TOTAL)
    set_notes(s, (
        "No existía un procedimiento manual de upgrade de Service Pack actualmente en ejecución que "
        "este proyecto busque reemplazar. Se decidió diseñar desde el principio una solución "
        "automatizada para estandarizar la forma de actualizar los servidores SLES 15 que soportan "
        "GeoPOS. La comparación con la ejecución manual es conceptual: automatizar ofrece ventajas "
        "potenciales frente a intervenciones repetidas manualmente; no afirmar resultados de "
        "productividad ya medidos.\n\n"
        "Explicar cuatro beneficios: (1) prerequisitos técnicos medidos antes de iniciar, entre ellos "
        "SP de origen, espacio, bloqueo del gestor de paquetes, conectividad y repositorios disponibles "
        "en Foreman/Katello; (2) validaciones preventivas, incluida una simulación automática de la "
        "operación de paquetes inmediatamente antes de aplicar cada migración real; (3) gobierno del "
        "cambio, ya que AWX exige datos CRQ/RFC, lote, ambiente y confirmación explícita, con "
        "procesamiento secuencial; (4) evidencias HTML por servidor y consolidado de lote, con estados "
        "inequívocos que facilitan auditoría y diagnóstico.\n\n"
        "La automatización no significa una migración sin interrupción: cada transición real requiere "
        "reinicio, revisión de salud y una ventana de mantenimiento autorizada.\n\n"
        "“Mayor estandarización y control del proceso” destaca que cada transición se ejecuta "
        "con un procedimiento uniforme, validaciones técnicas y evidencia por servidor y por lote."
    ))

    # --- Diapositiva 3: estrategia de upgrade -----------------------------
    s = add_slide(prs)
    set_background(s, WHITE)
    add_top_accent(s)
    add_header(s, "02 / ESTRATEGIA DE UPGRADE", "Cuatro modos de upgrade, sin omitir Service Packs",
               "Tres rutas individuales y una ejecución FULL que une dos transiciones consecutivas.")
    add_text(s, "MODOS INDIVIDUALES", Inches(0.82), Inches(2.15), Inches(5), Inches(0.26),
              size=11, bold=True, color=GRAY_TEXT)
    rutas = [("1", "SP4  →  SP5", "Primer salto"), ("2", "SP5  →  SP6", "Segundo salto"),
             ("3", "SP6  →  SP7", "Tercer salto")]
    add_card_row(s, rutas, top=Inches(2.50), height=Inches(1.1), titulo_size=18, desc_size=12)
    add_rect(s, Inches(0.82), Inches(4.00), Inches(11.68), Inches(1.15), fill=RGBColor(0x18, 0x48, 0x40))
    add_rounded(s, Inches(1.05), Inches(4.26), Inches(1.0), Inches(0.32), fill=NAVY_MED)
    add_text(s, "FULL", Inches(1.05), Inches(4.26), Inches(1.0), Inches(0.32), size=11, bold=True,
              color=TEAL_LIGHT, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    add_text(s, "SP5", Inches(2.45), Inches(4.28), Inches(1.0), Inches(0.4), size=22, bold=True, color=WHITE)
    add_text(s, "→", Inches(3.55), Inches(4.26), Inches(0.4), Inches(0.44), size=22, bold=True, color=TEAL_LIGHT, align=PP_ALIGN.CENTER)
    add_text(s, "SP6", Inches(4.05), Inches(4.28), Inches(1.0), Inches(0.4), size=22, bold=True, color=WHITE)
    add_text(s, "→", Inches(5.15), Inches(4.26), Inches(0.4), Inches(0.44), size=22, bold=True, color=TEAL_LIGHT, align=PP_ALIGN.CENTER)
    add_text(s, "SP7", Inches(5.65), Inches(4.28), Inches(1.0), Inches(0.4), size=22, bold=True, color=WHITE)
    add_text(s, "Validación obligatoria de SP6 antes de continuar", Inches(7.10), Inches(4.35), Inches(5.2), Inches(0.5),
              size=13, bold=True, color=RGBColor(0xD2, 0xF7, 0xE8))
    add_text(s, "≈90 %  del parque se encuentra en SP5 (estimación). SP4 se mantiene separado para "
                 "simplificar el flujo.", Inches(0.82), Inches(5.55), Inches(11.4), Inches(0.5), size=13, color=GRAY_TEXT)
    add_footer(s, 3, TOTAL)
    set_notes(s, (
        "Son cuatro modos implementados: individual SP4 a SP5, individual SP5 a SP6, individual SP6 a "
        "SP7 y FULL, que encadena SP5 a SP6 y luego SP6 a SP7. FULL no realiza un salto directo de SP5 "
        "a SP7: completa la transición intermedia y exige haber aplicado el cambio, reiniciado y "
        "validado SP6 antes de continuar a SP7.\n\n"
        "¿Por qué SP4 no se incluyó dentro del FULL? Fue una decisión de simplificación: incorporar una "
        "tercera etapa haría el flujo y sus controles más complejos, mientras que aproximadamente el "
        "90 % de los servidores se encontraría en SP5, de acuerdo con la estimación operativa "
        "comunicada para este proyecto. Los SP4 restantes son casos minoritarios, incluyendo algunos "
        "servidores de Cuba. Este porcentaje debe comunicarse como estimación, no como una medición "
        "certificada en la presentación.\n\n"
        "Si se necesita actualizar un servidor desde SP4, se ejecuta el modo individual SP4 a SP5, se "
        "verifica que terminó correctamente y posteriormente se selecciona el flujo desde SP5 que "
        "corresponda. Las migraciones se planifican de forma secuencial, sin omitir Service Packs."
    ))

    # --- Diapositiva 4: modelo operativo ----------------------------------
    s = add_slide(prs)
    set_background(s, WHITE)
    add_top_accent(s)
    add_header(s, "03 / MODELO OPERATIVO", "Una arquitectura simple, integrada a las plataformas actuales",
               "AWX coordina, Ansible ejecuta y Foreman / Katello suministra contenido interno.")
    add_card_row(s, [
        ("01", "AWX", "Control y selección de lote"),
        ("02", "Ansible", "Secuencia automatizada"),
        ("03", "SLES 15 + GeoPOS", "Servidores objetivo"),
    ], top=Inches(2.30), height=Inches(1.5), titulo_size=18, desc_size=13)
    add_card(s, Inches(0.82), Inches(4.10), Inches(11.68), Inches(1.9), None,
              "Foreman / Katello", "Repositorios corporativos de cada SP", titulo_size=20, desc_size=13)
    add_text(s, "•  Inventario: Excel compartido en SharePoint", Inches(1.10), Inches(4.95),
              Inches(6), Inches(0.3), size=13, color=GRAY_TEXT)
    add_text(s, "•  Sin repositorios públicos durante la migración", Inches(1.10), Inches(5.30),
              Inches(8), Inches(0.3), size=13, color=GRAY_TEXT)
    add_footer(s, 4, TOTAL)
    set_notes(s, (
        "AWX es la plataforma de orquestación: presenta la encuesta (Survey), dispara los cinco "
        "componentes del workflow y brinda visibilidad del estado de ejecución. Ansible ejecuta la "
        "lógica del procedimiento sobre cada servidor SLES 15 que contiene GeoPOS. Los paquetes se "
        "obtienen de Foreman/Katello, no de repositorios públicos de SUSE. El registro SUSEConnect no "
        "gobierna el éxito de este proceso.\n\n"
        "La selección del alcance se hace a partir del inventario corporativo dinámico que se lee desde "
        "un Excel compartido en SharePoint. La selección no se realiza mediante un campo manual de host "
        "independiente: AWX recibe CRQ, Lote y Ambiente, que se contrastan con ese inventario. En la "
        "ejecución por defecto se procesa un servidor a la vez.\n\n"
        "En la fase de preparación se inventarían los repositorios existentes, se deshabilitan los "
        "activos y se agregan temporalmente los repositorios adecuados de Foreman. Al finalizar una "
        "etapa satisfactoria los repositorios temporales se retiran. Los preexistentes deshabilitados "
        "no se reactivan de manera automática."
    ))

    # --- Diapositiva 5: lanzamiento del cambio (Survey) -------------------
    s = add_slide(prs)
    set_background(s, WHITE)
    add_top_accent(s)
    add_header(s, "04 / LANZAMIENTO DEL CAMBIO", "Un formulario define qué se ejecuta y sobre qué lote",
               "La operación se inicia con datos de cambio obligatorios y una confirmación expresa.")
    add_card_row(s, [
        ("01", "Ruta de migración", "Selecciona el tramo autorizado"),
        ("02", "Confirmación de cambio", "Evita ejecuciones reales accidentales"),
        ("03", "CRQ · Lote · Ambiente", "Identifica servidores desde inventario"),
    ], top=Inches(2.35), height=Inches(1.6), titulo_size=17, desc_size=13)
    add_text(s, "Captura real del Survey de AWX", Inches(0.82), Inches(4.25), Inches(6), Inches(0.3),
              size=12, bold=True, color=GRAY_TEXT)
    add_rounded(s, Inches(0.82), Inches(4.65), Inches(11.68), Inches(2.0), fill=BG_LIGHT)
    add_text(s, "upgrade_mode · confirmar_cambio_real · upgrade_crq · upgrade_lote · upgrade_ambiente",
              Inches(1.1), Inches(4.65), Inches(11.1), Inches(2.0), size=16, bold=True, color=NAVY_MED,
              anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER)
    add_footer(s, 5, TOTAL)
    set_notes(s, (
        "Mostrar la pantalla real del Survey del workflow. Son cinco entradas obligatorias: modo de "
        "ejecución, confirmación para ejecutar un cambio real en producción, CRQ/RFC, Lote y Ambiente. "
        "El modo de ejecución puede elegir SP4→SP5, SP5→SP6, SP6→SP7 o full, donde full cubre "
        "SP5→SP6→SP7.\n\n"
        "Los tres campos CRQ/Lote/Ambiente se comparan con los datos del inventario dinámico. Una "
        "coincidencia puede seleccionar uno o varios servidores, pero si no hay ninguna coincidencia la "
        "automatización falla antes de intervenir un host. Si el Service Pack detectado no corresponde "
        "a la ruta indicada, el precheck detiene ese servidor.\n\n"
        "La confirmación obligatoria evita aplicar un cambio real por error. El workflow procesa por "
        "defecto un servidor a la vez. Si uno de los hosts falla, los restantes del lote se continúan "
        "procesando de manera independiente y cada uno genera su evidencia."
    ))

    # --- Diapositiva 6: orquestación AWX (workflow 5 etapas) --------------
    s = add_slide(prs)
    set_background(s, WHITE)
    add_top_accent(s)
    add_header(s, "05 / ORQUESTACIÓN AWX", "Un workflow de cinco etapas hace visible el proceso",
               "Separar preparación y aplicación permite ubicar un control de aprobación antes del cambio.")
    pasos = [("1", "PRECHECK", "Condiciones iniciales", BG_LIGHT),
             ("2", "PREPARAR", "Repositorios internos", BG_LIGHT),
             ("3", "APLICAR", "Migración + reinicio", OK_GREEN_BG),
             ("4", "REPORTAR", "Resultado del lote", BG_LIGHT),
             ("5", "SINCRONIZAR", "Copia a SharePoint", BG_LIGHT)]
    x = Inches(0.82)
    w = Inches(2.17)
    for num, titulo, desc, fill in pasos:
        add_rounded(s, x, Inches(2.40), w, Inches(1.5), fill=fill)
        badge = Inches(0.4)
        add_rounded(s, x + Inches(0.18), Inches(2.58), badge, badge, fill=NAVY_MED)
        add_text(s, num, x + Inches(0.18), Inches(2.58), badge, badge, size=14, bold=True, color=WHITE,
                  align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        add_text(s, titulo, x + Inches(0.18), Inches(3.10), w - Inches(0.36), Inches(0.3), size=13, bold=True, color=NAVY)
        add_text(s, desc, x + Inches(0.18), Inches(3.42), w - Inches(0.36), Inches(0.44), size=10.5, color=GRAY_TEXT)
        x += w + Inches(0.17)
    add_text(s, "Aprobación humana opcional entre “Preparar” y “Aplicar”", Inches(0.82), Inches(4.25),
              Inches(11.5), Inches(0.3), size=13, bold=True, color=TEAL)
    add_text(s, "Captura real del workflow configurado en AWX", Inches(0.82), Inches(4.65), Inches(8), Inches(0.3),
              size=11, color=GRAY_TEXT)
    add_rounded(s, Inches(0.82), Inches(5.00), Inches(11.68), Inches(1.6), fill=BG_LIGHT)
    add_footer(s, 6, TOTAL)
    set_notes(s, (
        "La segunda captura procede de AWX y muestra la configuración real de los cinco nodos del "
        "proyecto.\n\n"
        "1. Precheck: verifica la versión actual, los bloqueos del sistema, espacio disponible, "
        "conectividad, servicios relevantes y condiciones previas. 2. Preparar: respalda el inventario "
        "de repositorios, deshabilita los repositorios anteriores que estén activos y habilita los "
        "repositorios internos necesarios, sin migrar todavía el Service Pack. 3. Aplicar: ejecuta una "
        "simulación obligatoria inmediatamente antes del cambio real, aplica la actualización, reinicia "
        "el servidor y valida tanto el sistema operativo como GeoPOS, según la configuración del host. "
        "4. Reporting: consolida la evidencia del lote. 5. Sincronizar SharePoint: copia opcional de "
        "reportes."
    ))

    # --- Diapositiva 7: ejecución controlada (ciclo por servidor) ---------
    s = add_slide(prs)
    set_background(s, WHITE)
    add_top_accent(s)
    add_header(s, "06 / EJECUCIÓN CONTROLADA", "Cada servidor recorre el mismo ciclo de validación",
               "El proceso avanza sólo cuando se cumplen las condiciones de la etapa actual.")
    add_card_row(s, [
        ("1", "Revisar", "Versión, espacio, servicios y conectividad"),
        ("2", "Preparar", "Repositorios internos de origen y destino"),
        ("3", "Actualizar", "Ensayo, cambio real y reinicio obligatorio"),
        ("4", "Comprobar", "SLES, GeoPOS y reporte de resultado"),
    ], top=Inches(2.30), height=Inches(1.8), titulo_size=17, desc_size=12)
    add_rect(s, Inches(0.82), Inches(4.45), Inches(11.68), Inches(0.62), fill=WARN_AMBER_BG)
    add_text(s, "⚠  Si una verificación crítica falla, no se avanza al siguiente Service Pack en ese servidor.",
              Inches(1.05), Inches(4.45), Inches(11.2), Inches(0.62), size=13.5, bold=True, color=WARN_AMBER,
              anchor=MSO_ANCHOR.MIDDLE)
    add_text(s, "Repetible por cada transición", Inches(0.82), Inches(5.30), Inches(6), Inches(0.3),
              size=12, bold=True, color=GRAY_TEXT)
    add_footer(s, 7, TOTAL)
    set_notes(s, (
        "El ciclo se repite para cada transición de Service Pack. Primero se revisa que el estado "
        "inicial es compatible con la migración. En esta etapa de precheck se contemplan dos "
        "excepciones técnicas idempotentes: instalar la autoridad certificadora interna si hace falta y "
        "pausar temporalmente agentes de seguridad conocidos que puedan bloquear el gestor de "
        "paquetes. No prometer que precheck jamás modifica absolutamente nada.\n\n"
        "Preparar manipula exclusivamente la configuración de repositorios, sin efectuar todavía el "
        "upgrade del Service Pack.\n\n"
        "Aplicar realiza obligatoriamente la simulación zypper dup -D con los repositorios destino, para "
        "detectar conflictos justo antes de la actualización. Solo si la validación tiene éxito ejecuta "
        "el cambio real, realiza un reinicio obligatorio y comprueba el Service Pack y los servicios.\n\n"
        "El último ciclo, comprobar, realiza validación de servicios y generación de reportes; aquí se "
        "pueden incluir validaciones de servicios de GeoPOS.\n\n"
        "NUEVO -- trazabilidad del reinicio (sección 8.6 del README): en esta etapa también se registra "
        "boot_id antes/después (evidencia de que el reinicio fue real a nivel de kernel), hora de "
        "inicio/fin, duración reportada por Ansible y tiempo de reconexión, además de una espera "
        "acotada a que systemd salga de 'starting'. Es información para diagnóstico, nunca decide el "
        "resultado de la etapa."
    ))

    # --- Diapositiva 8: gobierno y seguridad -------------------------------
    s = add_slide(prs)
    set_background(s, WHITE)
    add_top_accent(s)
    add_header(s, "07 / GOBIERNO Y SEGURIDAD", "Salvaguardas diseñadas para el cambio en producción",
               "Los controles forman parte del flujo; no dependen sólo de la memoria del operador.")
    add_card_row(s, [
        ("01", "Alcance delimitado", "CRQ, lote y ambiente validados contra inventario"),
        ("02", "Autorización expresa", "Confirmación obligatoria y aprobación opcional"),
    ], top=Inches(2.30))
    add_card_row(s, [
        ("03", "Ejecución secuencial", "Un servidor a la vez, con seguimiento independiente"),
        ("04", "Verificación de salud", "Estado del SO y GeoPOS antes y después"),
    ], top=Inches(3.95), numero_bg=OK_GREEN_BG)
    add_rect(s, Inches(0.82), Inches(5.65), Inches(11.68), Inches(0.62), fill=NAVY_DARK)
    add_text(s, "Actualizaciones únicamente desde los repositorios internos de Foreman / Katello",
              Inches(1.05), Inches(5.65), Inches(11.2), Inches(0.62), size=14, bold=True, color=WHITE,
              anchor=MSO_ANCHOR.MIDDLE)
    add_footer(s, 8, TOTAL)
    set_notes(s, (
        "Los principales mecanismos de control son: alcance determinado por tres datos del cambio "
        "(CRQ/RFC, Lote y Ambiente) contrastados contra el inventario; selección explícita del modo de "
        "ejecución; confirmación obligatoria para la ejecución real; posibilidad de integrar un nodo de "
        "aprobación humana previo a aplicar; procesamiento por defecto secuencial con una sola máquina "
        "a la vez; bloqueo del avance ante errores críticos y comprobaciones de salud antes y "
        "después.\n\n"
        "Se usan exclusivamente repositorios corporativos de Foreman/Katello. La automatización revisa "
        "la conectividad y evita mezclar repositorios preexistentes con los de la migración. Los "
        "repositorios temporales se retiran al concluir una etapa exitosa.\n\n"
        "Para preguntas de riesgo: no existe promesa de reversión automática universal. El rollback "
        "depende de la estrategia de snapshots y capacidades del almacenamiento del servidor, por "
        "ejemplo Btrfs, y debe analizarse por plataforma. La intervención implica reinicios, por lo que "
        "requiere una ventana de mantenimiento y coordinación con las áreas de GeoPOS y seguridad."
    ))

    # --- Diapositiva 9: continuidad funcional ------------------------------
    s = add_slide(prs)
    set_background(s, WHITE)
    add_top_accent(s)
    add_header(s, "08 / CONTINUIDAD FUNCIONAL", "El éxito no es sólo llegar al Service Pack objetivo",
               "También debe comprobarse que los componentes críticos de GeoPOS permanezcan operativos.")
    add_card(s, Inches(0.82), Inches(2.30), Inches(5.65), Inches(2.9), None, "ANTES DEL CAMBIO · Línea base de salud",
              "•  Servicios definidos\n•  Procesos Java\n•  Puertos · URLs opcionales\n•  SP actual",
              titulo_size=15, desc_size=13)
    add_card(s, Inches(6.85), Inches(2.30), Inches(5.65), Inches(2.9), None, "DESPUÉS DEL CAMBIO · Verificación final",
              "•  Service Pack alcanzado\n•  Servicios recuperados\n•  GeoPOS saludable",
              titulo_size=15, desc_size=13, numero_bg=OK_GREEN_BG)
    add_text(s, "Validaciones configurables por servidor  ·  Parametrización real pendiente antes de producción",
              Inches(0.82), Inches(5.55), Inches(11.6), Inches(0.4), size=13, bold=True, color=WARN_AMBER)
    add_footer(s, 9, TOTAL)
    set_notes(s, (
        "La automatización puede verificar el funcionamiento de GeoPOS en diferentes dimensiones según "
        "el servidor: unidades de servicio, procesos Java, puertos y pruebas HTTP/HTTPS opcionales. "
        "Puede haber múltiples instancias de cada componente en un host; no es una lista uniforme para "
        "todo el parque. La revisión previa establece una línea base y la revisión posterior comprueba "
        "recuperación.\n\n"
        "La comprobación funcional es parametrizable e incluso deshabilitable globalmente o por "
        "dimensión. Si no se ejecuta, se informa como NO VERIFICADO, no como OK. Un host no debe "
        "considerarse exitoso únicamente por haber alcanzado el SP si un componente definido como "
        "crítico de GeoPOS queda insalubre.\n\n"
        "Advertir con precisión el estado actual: aún no están cargados para producción los nombres "
        "reales de servicios, procesos y puertos por servidor. Este es uno de los elementos pendientes "
        "de validación y parametrización con los responsables de GeoPOS antes de la salida a "
        "producción."
    ))

    # --- Diapositiva 10: seguimiento y auditoría ---------------------------
    s = add_slide(prs)
    set_background(s, WHITE)
    add_top_accent(s)
    add_header(s, "09 / SEGUIMIENTO Y AUDITORÍA", "Cada ejecución deja evidencia clara y consolidada",
               "Los resultados pueden consultarse por servidor, etapa y lote, sin reconstruir los logs manualmente.")
    add_card_row(s, [
        ("01", "SERVIDOR", "Estado individual"),
        ("02", "ETAPA", "Controles y hallazgos"),
        ("03", "LOTE", "Vista consolidada"),
    ], top=Inches(2.30), height=Inches(1.1))
    add_text(s, "HTML  ·  Reporte legible por host y por lote      SharePoint  ·  sincronización opcional y configurable",
              Inches(0.82), Inches(3.70), Inches(11.5), Inches(0.4), size=13, bold=True, color=NAVY)
    add_text(s, "Estados diferenciados", Inches(0.82), Inches(4.35), Inches(4), Inches(0.26),
              size=11, bold=True, color=GRAY_TEXT)
    add_legend_estado(s, Inches(0.82), Inches(4.68))
    add_footer(s, 10, TOTAL)
    set_notes(s, (
        "En cada fase se registra evidencia del resultado por host. Los reportes HTML muestran el "
        "estado real de las verificaciones y la automatización produce un consolidado por Lote que "
        "permite comparar los servidores y las fases. Un error no debe aparecer transformado en un "
        "resultado global OK.\n\n"
        "Los estados son OK, ADVERTENCIA, FALLIDO y NO VERIFICADO; esa separación es importante para no "
        "confundir una prueba omitida con una prueba superada. La última etapa del workflow puede "
        "sincronizar los archivos al repositorio compartido de SharePoint.\n\n"
        "Esta diapositiva es un esquema del flujo de información, no una captura de resultados de "
        "producción. No se incluyen métricas de mejora de productividad porque el proyecto no las ha "
        "medido todavía. La utilidad gerencial de los reportes es el seguimiento de los cambios y el "
        "cierre soportado por evidencia.\n\n"
        "NUEVO -- trazabilidad del reinicio: el reporte HTML por servidor ahora incluye también "
        "boot_id antes/después, hora de inicio/fin del reinicio, duración reportada por Ansible, "
        "tiempo de reconexión y el estado final de systemd (running/degraded/timeout), además de si "
        "journald persistente quedó habilitado antes de la migración -- ver README sección 8.6."
    ))

    # --- Diapositiva 11: validación del proyecto (checklist plantilla) ----
    s = add_slide(prs)
    set_background(s, WHITE)
    add_top_accent(s)
    add_header(s, "10 / VALIDACIÓN DEL PROYECTO", "Pruebas sobre plantilla SLES 15: estado de avance",
               "La misma plantilla progresa por etapas; el modo FULL se ensaya desde SP5.")
    add_text(s, "FASE DE LABORATORIO   ·   VALIDACIONES SOBRE PLANTILLA SLES 15", Inches(0.82), Inches(2.15),
              Inches(11), Inches(0.26), size=11, bold=True, color=GRAY_TEXT)
    items = [
        ("SP5 → SP6", "Plantilla SUSE Linux Enterprise 15 SP5 · transición inicial completada."),
        ("SP6 → SP7", "Continuación sobre la misma plantilla, una vez actualizada de SP5 a SP6."),
        ("FULL · SP5 → SP6 → SP7", "Prueba integral desde SP5; valida SP6 antes de avanzar a SP7."),
    ]
    top = Inches(2.50)
    for titulo, desc in items:
        add_checklist_item(s, Inches(0.82), top, Inches(11.68), titulo, desc)
        top += Inches(0.70)
    add_text(s, "Marcar manualmente en PowerPoint cuando la prueba real se complete (no es un checkbox "
                 "dinámico de presentación).", Inches(0.82), top + Inches(0.1), Inches(11.5), Inches(0.4),
              size=11, color=GRAY_TEXT)
    add_footer(s, 11, TOTAL)
    set_notes(s, (
        "OBJETIVO DE LA DIAPOSITIVA: Diferenciar las pruebas sobre la plantilla SLES 15 de las próximas "
        "validaciones en servidores reales de QA.\n\n"
        "Estado real al momento de regenerar este deck: revisar manualmente cuál de las tres pruebas "
        "(SP5→SP6, SP6→SP7, FULL) ya se completó sobre la plantilla, y marcarla. Este script siempre "
        "genera las tres filas en PENDIENTE por defecto -- regenerar NO conserva marcas manuales "
        "previas, así que vuelva a aplicarlas después de correr el script.\n\n"
        "SP5→SP6 fue la primera transición completada sobre una plantilla de SUSE Linux Enterprise 15 "
        "Service Pack 5. Esta prueba de laboratorio NO equivale a una prueba en QA ni a un despliegue "
        "en producción.\n\n"
        "SP6→SP7: ejecutar individual aprovechando la misma plantilla ya migrada a Service Pack 6, "
        "conservando la continuidad lógica del primer ensayo.\n\n"
        "FULL: encadena SP5→SP6 y SP6→SP7 en el mismo flujo, con validación de SP6 antes de continuar. "
        "Para probar FULL se necesita comenzar nuevamente en SP5 (copia/restauración de la plantilla "
        "base); no sería correcto ejecutar FULL desde el estado SP7 de la prueba anterior."
    ))

    # --- Diapositiva 12: siguientes pasos (checklist QA) -------------------
    s = add_slide(prs)
    set_background(s, WHITE)
    add_top_accent(s)
    add_header(s, "11 / SIGUIENTES PASOS", "Pruebas en QA y cierre funcional",
               "Seguimiento de los cuatro modos en servidores reales de QA y de la validación GeoPOS.")
    add_text(s, "AMBIENTE REAL QA   ·   CUATRO ESCENARIOS DE PRUEBA", Inches(0.82), Inches(2.10),
              Inches(11), Inches(0.24), size=10.5, bold=True, color=GRAY_TEXT)
    qa_items = [
        ("SP4 → SP5", "Upgrade individual en servidor QA con Service Pack 4."),
        ("SP5 → SP6", "Upgrade individual en servidor QA con Service Pack 5."),
        ("SP6 → SP7", "Upgrade individual en servidor QA con Service Pack 6."),
        ("FULL · SP5 → SP6 → SP7", "Secuencia integrada desde SP5 y validación intermedia de SP6."),
    ]
    top = Inches(2.40)
    for titulo, desc in qa_items:
        add_checklist_item(s, Inches(0.82), top, Inches(11.68), titulo, desc)
        top += Inches(0.62)
    add_text(s, "CIERRE FUNCIONAL   ·   ÚLTIMA ACTIVIDAD DE VALIDACIÓN", Inches(0.82), top + Inches(0.08),
              Inches(11), Inches(0.24), size=10.5, bold=True, color=GRAY_TEXT)
    top += Inches(0.38)
    add_checklist_item(s, Inches(0.82), top, Inches(11.68), "Verificación de servicios GeoPOS",
                         "Incorporar y probar servicios, procesos Java, puertos y URL de salud opcionales.")
    add_footer(s, 12, TOTAL)
    set_notes(s, (
        "OBJETIVO DE LA DIAPOSITIVA: Completar las pruebas posteriores a las de laboratorio en un "
        "ambiente QA real y, por último, incorporar la verificación funcional GeoPOS. Todas las "
        "pruebas de esta diapositiva están pendientes.\n\n"
        "QA — Cuatro escenarios independientes a validar: (1) SP4→SP5 desde un servidor QA en SP4; (2) "
        "SP5→SP6 desde SP5; (3) SP6→SP7 desde SP6; y (4) FULL SP5→SP6→SP7, encadenando las dos fases y "
        "validando SP6 antes de SP7. Los servidores o estados base elegidos deben coincidir con la "
        "versión de origen de cada modo. No se afirma que estos ensayos se hayan realizado.\n\n"
        "ÚLTIMO CHECK DE PRUEBAS: incorporar el inventario real de servicios GeoPOS y su parametrización "
        "por host, con procesos Java, puertos y opcionalmente comprobaciones de salud HTTP/HTTPS; "
        "ejecutar las comprobaciones antes y después de las migraciones según corresponda. Evitar "
        "marcar los servicios como OK si la verificación fue deshabilitada o no se ejecutó.\n\n"
        "DESPUÉS DE LAS PRUEBAS: Definir cambio autorizado, ventana de mantenimiento, coordinación con "
        "equipos de seguridad, plataforma y responsables de GeoPOS, y criterios de aceptación. Es una "
        "fase posterior y no aparece como prueba completada.\n\n"
        "Este script siempre genera las filas de checklist en PENDIENTE; marque a mano en PowerPoint "
        "las que realmente ya se completaron después de regenerar."
    ))

    return prs


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    base = os.path.dirname(os.path.abspath(__file__))

    prs_gerencial = construir_gerencial()
    out_gerencial = os.path.join(base, "ansible-sles-upgrade-presentacion-gerencial.pptx")
    prs_gerencial.save(out_gerencial)
    print(f"Generado: {out_gerencial}")

    prs_tecnica = construir_tecnica()
    out_tecnica = os.path.join(base, "ansible-sles-upgrade-presentacion-tecnica.pptx")
    prs_tecnica.save(out_tecnica)
    print(f"Generado: {out_tecnica}")


if __name__ == "__main__":
    main()
