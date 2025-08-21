# app.py
# Entrevista clínica simulada — Agente de preconsulta (ES-MX)
# UI inspirada en la experiencia de selección de paciente → condición → entrevista → reporte.
# Sin conexión a LLM; todo es determinístico y controlado por estado/controles.

import streamlit as st
from dataclasses import dataclass
from typing import List, Dict
from datetime import datetime
import time
from pathlib import Path

# --------------------------
# CONFIGURACIÓN GLOBAL
# --------------------------
st.set_page_config(page_title="Agente de Preconsulta — ES-MX", layout="wide", page_icon="🩺")

# Estilos (ligero, tarjetas, chips, resaltado)
st.markdown("""
<style>
/* Reset y tipografía */
html, body, [class*="css"] {
  font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, "Helvetica Neue", Arial, sans-serif;
  color: #1f2937;
}
.block-container { padding-top: 0.6rem; }

/* Chips y badges */
.badge { display:inline-block; padding:6px 10px; border-radius:999px; background:#eef2ff; 
         color:#4f46e5; font-weight:800; font-size:.80rem; border:1px solid #e0e7ff; }

/* Tarjetas */
.card { background:#ffffff; border:1px solid #e5e7eb; border-radius:16px; padding:16px; }
.card.soft { background: #f9fafb; }
.section { border:none; height:1px; background:linear-gradient(90deg,#7c3aed,#22d3ee); margin:12px 0 18px; }

/* Cabeceras */
.h-title { font-weight:900; font-size:1.6rem; margin:0 0 8px; }
.h-sub   { color:#6b7280; font-weight:600; }

/* Selección de tarjetas (pacientes/condiciones) */
.select-card { border-radius:16px; border:2px solid transparent; transition: all .2s ease; cursor:pointer; }
.select-card:hover { transform: translateY(-1px); box-shadow: 0 6px 20px rgba(0,0,0,0.07); }
.select-card.selected { border-color:#c7d2fe; box-shadow: 0 0 0 3px #e0e7ff inset; }
.tag { display:inline-block; padding:4px 8px; border-radius:8px; background:#eef2ff; color:#4f46e5; 
       font-weight:800; font-size:.8rem; border:1px solid #e0e7ff; }

/* Chat estilo burbuja */
.chatwrap { background:#fff; border:1px solid #e5e7eb; border-radius:16px; padding:12px; }
.msg { border-radius:12px; padding:10px 12px; margin:8px 0; max-width:95%; }
.msg.agent { background:#eef2ff; color:#111827; border:1px solid #e0e7ff; }
.msg.patient { background:#f3f4f6; color:#111827; border:1px solid #e5e7eb; }
.msg small { color:#6b7280; display:block; margin-top:2px; }

/* Botones */
.stButton > button { border-radius:10px; font-weight:800; border:none; background:#7c3aed; color:#fff; }
.stButton > button:hover { background:#6d28d9; }

/* Títulos en reporte */
.report h4 { margin:0 0 6px 0; }
.report .box { background:#ffffff; border:1px solid #e5e7eb; border-radius:16px; padding:14px; margin-bottom:10px; }
.report .pill { display:inline-block; padding:3px 8px; border-radius:999px; background:#dcfce7; color:#065f46; font-weight:800; font-size:.8rem; }
.report .note { background:#fffbeb; border:1px solid #fde68a; border-radius:12px; padding:10px; }

/* Encabezados secciones grandes */
.bigtitle { font-weight:900; font-size:1.35rem; margin-bottom:4px; }
.helper { color:#6b7280; font-size:.95rem; }

/* Botón plano claro */
.btn-light > button { background:#eef2ff !important; color:#1f2937 !important; border:1px solid #e0e7ff !important; }
</style>
""", unsafe_allow_html=True)

# --------------------------
# DATASETS BÁSICOS
# --------------------------
@dataclass
class Patient:
    pid: str
    nombre: str
    edad: int
    sexo: str
    condicion_base: str
    img: str = ""  # agrega tu ruta/URL

@dataclass
class Condition:
    cid: str
    titulo: str
    descripcion: str

PACIENTES: List[Patient] = [
    Patient("jdubois", "Jordon Dubois", 35, "Masculino", "Depresión"),
    Patient("asharma", "Alex Sharma", 63, "Femenino", "Diabetes"),
    Patient("ssilva",  "Sacha Silva",  24, "Femenino", "Asma"),
]

CONDICIONES: List[Condition] = [
    Condition("flu", "Gripe", "Infección viral contagiosa con fiebre, mialgia y fatiga."),
    Condition("mal", "Malaria", "Enfermedad transmitida por mosquitos con fiebre intermitente y escalofríos."),
    Condition("mig", "Migraña", "Cefalea intensa con fotofobia/fonofobia y ocasional náusea."),
    Condition("ss",  "Síndrome serotoninérgico", "Reacción por exceso de serotonina (p. ej. antidepresivos + dextrometorfano)."),
]

# Conversación y hechos: caso guiado de Síndrome serotoninérgico
# Cada turno descubierto actualiza el reporte
CHAT_SS: List[Dict] = [
    {"role":"agent",   "text":"Gracias por agendar. Soy asistente clínico; te haré algunas preguntas para preparar tu visita. ¿Cuál es tu principal molestia hoy?"},
    {"role":"patient", "text":"Me siento muy agitado e inquieto, también confundido y desorientado. Me preocupa bastante."},
    {"role":"agent",   "text":"¿Cuándo iniciaron estos síntomas? ¿Fue algo gradual o de inicio súbito?"},
    {"role":"patient", "text":"Hace como dos días y fue de repente."},
    {"role":"agent",   "text":"Describe la agitación e inquietud que presentas."},
    {"role":"patient", "text":"No puedo estar quieto, me muevo todo el tiempo y me siento \"en alerta\". Es incómodo."},
    {"role":"agent",   "text":"¿Has tenido fiebre, escalofríos o dolor muscular?"},
    {"role":"patient", "text":"He sudado mucho y a veces me da como escalofríos. Los músculos se sienten rígidos."},
    {"role":"agent",   "text":"¿Cambios visuales o en los ojos?"},
    {"role":"patient", "text":"Sí, siento las pupilas muy dilatadas y mis ojos se mueven raro."},
    {"role":"agent",   "text":"¿Cambios recientes en tus medicamentos o dosis?"},
    {"role":"patient", "text":"No cambios en mi receta; sigo con fluoxetina de siempre."},
    {"role":"agent",   "text":"¿Has consumido alcohol, drogas recreativas o suplementos nuevos?"},
    {"role":"patient", "text":"No, pero estaba tosiendo y tomé un jarabe para la tos de venta libre."},
    {"role":"agent",   "text":"¿Recuerdas el nombre y desde cuándo lo tomas?"},
    {"role":"patient", "text":"No recuerdo la marca, lo tomé ayer y hoy. Creo que tenía dextrometorfano."},
    {"role":"agent",   "text":"Gracias por responder. Con esto puedo preparar el reporte para tu médico."},
]

EHR_BASE = {
    "Historia clínica relevante": ["Trastorno depresivo (diagnosticado 2024-01-15)"],
    "Medicaciones (EHR)": ["Fluoxetina 20 mg VO cada 24 h"],
}

# Mapeo de hechos extraídos a partir de índices de chat
FACT_RULES = [
    # (index límite, tipo, contenido)
    (1,  "Motivo principal", "Agitación, inquietud, confusión y desorientación."),
    (3,  "HPI", "Inicio súbito ~2 días."),
    (5,  "HPI", "Inquietud marcada/incapacidad para estar quieto."),
    (7,  "Signos autonómicos", "Diaforesis, escalofríos, rigidez muscular."),
    (9,  "Signos oculares", "Midriasis y nistagmo subjetivo."),
    (11, "Medicaciones (EHR)", "Fluoxetina (ISRS) — crónica."),
    (13, "Historia dirigida", "Niega alcohol/drogas/suplementos recientes."),
    (15, "Medicaciones (entrevista)", "Jarabe para la tos con dextrometorfano (uso reciente)."),
]

FALTANTES_SUGERIDOS = [
    "Signos vitales objetivos: temperatura, FC, TA.",
    "Exploración neuromuscular: temblor, hiperreflexia, mioclonías, rigidez.",
    "Historia detallada de medicación: inicio/duración de fluoxetina y otros agentes serotoninérgicos.",
]

# --------------------------
# STATE
# --------------------------
if "step" not in st.session_state:
    st.session_state.step = "select"  # select → intro → convo
if "sel_patient" not in st.session_state:
    st.session_state.sel_patient = None
if "sel_condition" not in st.session_state:
    st.session_state.sel_condition = None
if "chat_idx" not in st.session_state:
    st.session_state.chat_idx = -1
if "autoplay" not in st.session_state:
    st.session_state.autoplay = False
if "audio_url" not in st.session_state:
    st.session_state.audio_url = ""

# --------------------------
# UTILIDADES
# --------------------------
def patient_card(p: Patient, selected=False):
    border_class = "selected" if selected else ""
    st.markdown(f"""
    <div class="select-card {border_class} card">
      <div style="display:flex;flex-direction:column;gap:10px">
        <div style="height:190px;background:#f3f4f6;border-radius:12px;display:flex;align-items:center;justify-content:center;overflow:hidden">
          <!-- Inserta imagen real del paciente en p.img -->
          <span style="color:#9ca3af">Imagen del paciente</span>
        </div>
        <span class="tag">Expediente Clínico Sintético (FHIR)</span>
        <div style="font-weight:900">{p.nombre}</div>
        <div class="helper">{p.edad} años, {p.sexo}</div>
        <div class="helper">Condición de base: {p.condicion_base}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

def condition_card(c: Condition, selected=False):
    border_class = "selected" if selected else ""
    st.markdown(f"""
    <div class="select-card {border_class} card">
      <div style="font-weight:900;margin-bottom:6px;">{c.titulo}</div>
      <div class="helper">{c.descripcion}</div>
    </div>
    """, unsafe_allow_html=True)

def collect_facts(idx_limit:int):
    facts = {
        "Motivo principal": [],
        "HPI": [],
        "Historia clínica relevante": EHR_BASE["Historia clínica relevante"].copy(),
        "Medicaciones (EHR)": EHR_BASE["Medicaciones (EHR)"].copy(),
        "Medicaciones (entrevista)": [],
        "Signos autonómicos": [],
        "Signos oculares": [],
        "Historia dirigida": [],
    }
    for i_lim, kind, text in FACT_RULES:
        if idx_limit >= i_lim:
            facts[kind].append(text)
    return facts

def render_report(idx_limit:int):
    facts = collect_facts(idx_limit)
    st.markdown('<div class="report">', unsafe_allow_html=True)
    st.markdown('<div class="bigtitle">Reporte generado</div>', unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="box">', unsafe_allow_html=True)
        st.markdown("**Motivo principal:**")
        mp = facts["Motivo principal"][0] if facts["Motivo principal"] else "—"
        st.markdown(mp)
        st.markdown('</div>', unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="box">', unsafe_allow_html=True)
        st.markdown("**Historia de la enfermedad actual (HPI):**")
        if facts["HPI"]:
            st.markdown("<ul>" + "".join([f"<li>{x}</li>" for x in facts["HPI"]]) + "</ul>", unsafe_allow_html=True)
        else:
            st.markdown("—")
        st.markdown('</div>', unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="box">', unsafe_allow_html=True)
        st.markdown("**Antecedentes relevantes (desde EHR):**")
        st.markdown("<ul>" + "".join([f"<li>{x}</li>" for x in facts["Historia clínica relevante"]]) + "</ul>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="box">', unsafe_allow_html=True)
        st.markdown("**Medicaciones (EHR y entrevista):**")
        meds = facts["Medicaciones (EHR)"] + facts["Medicaciones (entrevista)"]
        if meds:
            # Resalta nuevas medicaciones de la entrevista en verde
            items = []
            for m in facts["Medicaciones (EHR)"]:
                items.append(f"<li>{m}</li>")
            for m in facts["Medicaciones (entrevista)"]:
                items.append(f"<li><span class='pill'>{m}</span></li>")
            st.markdown("<ul>" + "".join(items) + "</ul>", unsafe_allow_html=True)
        else:
            st.markdown("—")
        st.markdown('</div>', unsafe_allow_html=True)

    if facts["Signos autonómicos"] or facts["Signos oculares"] or facts["Historia dirigida"]:
        with st.container():
            st.markdown('<div class="box">', unsafe_allow_html=True)
            st.markdown("**Hechos útiles:**")
            lst = facts["Signos autonómicos"] + facts["Signos oculares"] + facts["Historia dirigida"]
            st.markdown("<ul>" + "".join([f"<li>{x}</li>" for x in lst]) + "</ul>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    if idx_limit >= len(CHAT_SS)-1:
        with st.container():
            st.markdown('<div class="box note">', unsafe_allow_html=True)
            st.markdown("**Qué no se cubrió pero sería útil:**", unsafe_allow_html=True)
            st.markdown("<ul>" + "".join([f"<li>{x}</li>" for x in FALTANTES_SUGERIDOS]) + "</ul>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

def step_header(title:str, subtitle:str=""):
    st.markdown(f"<div class='h-title'>{title}</div>", unsafe_allow_html=True)
    if subtitle:
        st.markdown(f"<div class='h-sub'>{subtitle}</div>", unsafe_allow_html=True)

# --------------------------
# STEP: SELECCIÓN
# --------------------------
if st.session_state.step == "select":
    step_header("Selecciona un paciente")
    st.markdown('<hr class="section"/>', unsafe_allow_html=True)

    cols = st.columns(3, gap="large")
    for i, p in enumerate(PACIENTES):
        with cols[i]:
            selected = (st.session_state.sel_patient == p.pid)
            with st.container():
                c = st.container()
                with c:
                    patient_card(p, selected)
                if st.button(("Elegir" if not selected else "Seleccionado"), key=f"pickp_{p.pid}", use_container_width=True):
                    st.session_state.sel_patient = p.pid

    st.markdown('<hr class="section"/>', unsafe_allow_html=True)
    step_header("Explorar una condición", "Selecciona la condición actual a investigar")
    st.markdown("""
En esta experiencia, el agente realiza preguntas estructuradas y actualiza un reporte médico en tiempo real con base en las respuestas del paciente y algunos elementos del expediente electrónico (FHIR).
""")

    cols2 = st.columns(2, gap="large")
    for i, c in enumerate(CONDICIONES):
        with cols2[i % 2]:
            selected = (st.session_state.sel_condition == c.cid)
            condition_card(c, selected)
            if st.button(("Elegir" if not selected else "Seleccionada"), key=f"pickc_{c.cid}", use_container_width=True):
                st.session_state.sel_condition = c.cid

    st.markdown('<hr class="section"/>', unsafe_allow_html=True)
    col_a, col_b = st.columns([1,3])
    with col_a:
        launch = st.button("Iniciar", type="primary", use_container_width=True,
                           disabled=not (st.session_state.sel_patient and st.session_state.sel_condition))
    with col_b:
        st.caption("Primero elige **paciente** y **condición**. Después podrás avanzar a la entrevista.")

    if launch:
        st.session_state.step = "intro"
        st.experimental_rerun()

# --------------------------
# STEP: INTRO
# --------------------------
elif st.session_state.step == "intro":
    p = next(x for x in PACIENTES if x.pid == st.session_state.sel_patient)
    c = next(x for x in CONDICIONES if x.cid == st.session_state.sel_condition)

    cols = st.columns(2, gap="large")
    with cols[0]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        step_header("Agente de preconsulta")
        st.markdown("""
Este asistente recopila información previa a la visita para ayudar al médico a preparar la consulta.  
Tiene acceso controlado a partes del expediente electrónico (**FHIR**) y guía la conversación con preguntas clínicas.
        """)
        st.markdown('</div>', unsafe_allow_html=True)

    with cols[1]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        step_header(f"Persona del paciente: {p.nombre}",
                    f"{p.edad} años, {p.sexo} • Condición de base: {p.condicion_base}")
        st.markdown("""
Se ha configurado una persona del paciente con síntomas compatibles con la condición seleccionada; algunas señales confusas también se incluyen para simular un caso realista.
        """)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<hr class="section"/>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1.2, 1.2, 2.6], gap="large")
    with col1:
        if st.button("◀ Volver", use_container_width=True, key="back_sel", type="secondary"):
            st.session_state.step = "select"
            st.experimental_rerun()
    with col2:
        if st.button("Comenzar entrevista", use_container_width=True, key="start_chat"):
            st.session_state.step = "convo"
            st.session_state.chat_idx = -1
            st.session_state.autoplay = False
            st.experimental_rerun()
    with col3:
        st.caption(f"Condición: **{c.titulo}** — {c.descripcion}")

# --------------------------
# STEP: CONVERSACIÓN + REPORTE
# --------------------------
elif st.session_state.step == "convo":
    # Encabezado con controles
    top_l, top_r = st.columns([2.5, 1.5], gap="large")
    with top_l:
        step_header("Entrevista simulada", "audio opcional")
    with top_r:
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            if st.button("◀ Volver", use_container_width=True, key="back_intro", type="secondary"):
                st.session_state.step = "intro"; st.experimental_rerun()
        with col_b:
            if st.button("🔁 Reiniciar", use_container_width=True, key="reset_chat"):
                st.session_state.chat_idx = -1
                st.session_state.autoplay = False
                st.experimental_rerun()
        with col_c:
            if not st.session_state.autoplay:
                if st.button("▶ Auto", use_container_width=True):
                    st.session_state.autoplay = True
                    st.experimental_rerun()
            else:
                if st.button("⏸︎ Pausa", use_container_width=True):
                    st.session_state.autoplay = False
                    st.experimental_rerun()

    st.markdown('<hr class="section"/>', unsafe_allow_html=True)

    # Audio (opcional)
    upcol, urlcol = st.columns([1.4, 2.6], gap="large")
    with upcol:
        audio = st.file_uploader("Sube audio (.mp3/.wav) opcional", type=["mp3","wav"])
        if audio: st.audio(audio)
    with urlcol:
        url = st.text_input("…o pega una URL de audio (opcional)", value=st.session_state.audio_url)
        st.session_state.audio_url = url
        if url: st.audio(url)

    st.markdown('<hr class="section"/>', unsafe_allow_html=True)

    # Layout principal: chat a la izquierda, reporte a la derecha
    chat_col, report_col = st.columns([1.3, 1.0], gap="large")

    # --- CHAT ---
    with chat_col:
        st.markdown('<div class="chatwrap">', unsafe_allow_html=True)
        # Avance de mensajes
        if st.session_state.chat_idx < len(CHAT_SS)-1:
            if not st.session_state.autoplay:
                if st.button("Siguiente mensaje ▶", key="next_msg", use_container_width=True):
                    st.session_state.chat_idx += 1
                    st.experimental_rerun()
            else:
                # Auto-play
                time.sleep(1.1)
                st.session_state.chat_idx += 1
                st.experimental_rerun()
        else:
            st.success("Entrevista completa. El reporte incluye un resumen de hechos útiles y sugerencias.")

        # Render de los mensajes hasta el índice actual
        for i in range(st.session_state.chat_idx + 1):
            role = CHAT_SS[i]["role"]
            txt  = CHAT_SS[i]["text"]
            klass = "agent" if role == "agent" else "patient"
            who = "Asistente" if role == "agent" else "Paciente"
            st.markdown(f"<div class='msg {klass}'><b>{who}:</b> {txt}<br><small>{datetime.now().strftime('%H:%M')}</small></div>", unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    # --- REPORTE DINÁMICO ---
    with report_col:
        render_report(st.session_state.chat_idx)

    st.markdown('<hr class="section"/>', unsafe_allow_html=True)

    # Botón final para evaluación (texto, sin modal)
    if st.session_state.chat_idx >= len(CHAT_SS)-1:
        with st.expander("Acerca de la evaluación de calidad"):
            st.markdown("""
Este apartado ilustra cómo identificar **fortalezas** del reporte (hechos útiles) y **oportunidades de mejora** (elementos faltantes que conviene medir o preguntar).
- Los **hechos útiles** resaltan datos que orientan el juicio clínico.
- Los **faltantes** listados sugieren qué medir/indagar para aumentar la completitud del reporte.
            """)

# --------------------------
# FOOTER LIGERO
# --------------------------
st.markdown("<hr class='section'/>", unsafe_allow_html=True)
st.caption("Agente de preconsulta • ES-MX • flujo interactivo de paciente → condición → entrevista → reporte.")
