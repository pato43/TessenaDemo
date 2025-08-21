# app.py
# Entrevista clínica simulada (ES-MX) — Tema claro/oscuro, selección robusta, chat paso a paso y reporte dinámico.
# Sin conexión a LLM. Flujo: Selección → Introducción → Conversación → Reporte.

import streamlit as st
from dataclasses import dataclass
from typing import List, Dict, Tuple
from datetime import datetime
from pathlib import Path
import time

# =========================
# CONFIG / STATE
# =========================
st.set_page_config(page_title="Agente de Preconsulta", layout="wide", page_icon="🩺", initial_sidebar_state="expanded")

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

# =========================
# THEME
# =========================
THEME = st.sidebar.radio("Tema", ["Claro", "Oscuro"], index=0)

base_css = """
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800;900&display=swap" rel="stylesheet">
<style>
:root{
  --bg: %(bg)s;
  --card: %(card)s;
  --text: %(text)s;
  --muted: %(muted)s;
  --primary: #7c3aed;
  --accent: #22d3ee;
  --accent2:#6EE7F9;
  --border: %(border)s;
  --chipbg: %(chipbg)s;
  --chipfg: %(chipfg)s;
  --agent: %(agent)s;
  --patient: %(patient)s;
}
html, body, [class*="css"]{
  background: var(--bg) !important;
  color: var(--text) !important;
  font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, "Helvetica Neue", Arial, sans-serif;
  font-size: 16.5px;
}
.block-container{ padding-top: .6rem; }
header{ visibility: hidden; }

/* Cards y secciones */
.card{ background:var(--card); border:1px solid var(--border); border-radius:16px; padding:16px; }
.card.soft{ background:rgba(255,255,255,.5); }
.section{ border:none; height:1px; background:linear-gradient(90deg,var(--primary),var(--accent)); margin:10px 0 14px; }

/* Chips y badges */
.badge{ display:inline-block; padding:6px 10px; border-radius:999px; background:var(--chipbg); color:var(--chipfg);
  font-weight:800; font-size:.80rem; border:1px solid var(--border); }
.tag{ display:inline-block; padding:4px 8px; border-radius:8px; background:var(--chipbg); color:var(--chipfg);
  font-weight:800; font-size:.80rem; border:1px solid var(--border); }

/* Selección de tarjetas */
.select-card{ border-radius:16px; border:2px solid transparent; transition: all .2s ease; cursor:pointer; }
.select-card:hover{ transform: translateY(-1px); box-shadow: 0 6px 22px rgba(0,0,0,.07); }
.select-card.selected{ border-color:#c7d2fe; box-shadow: 0 0 0 3px #e0e7ff55 inset; }

/* Títulos */
.h-title{ font-weight:900; font-size:1.5rem; margin:0 0 6px; }
.h-sub{ color:var(--muted); font-weight:600; }

/* Chat */
.chatwrap{ background:var(--card); border:1px solid var(--border); border-radius:16px; padding:12px; }
.msg{ border-radius:12px; padding:10px 12px; margin:8px 0; max-width:96%; border:1px solid var(--border); }
.msg.agent{ background:var(--agent); }
.msg.patient{ background:var(--patient); }
.msg small{ color:var(--muted); display:block; margin-top:2px; }

/* Botones */
.stButton > button{ border-radius:10px; font-weight:800; border:none; background:var(--primary); color:#fff; }
.stButton > button:hover{ filter:brightness(.95); }

/* Reporte */
.report h4{ margin:0 0 6px 0; }
.report .box{ background:var(--card); border:1px solid var(--border); border-radius:16px; padding:14px; margin-bottom:10px; }
.report .pill{ display:inline-block; padding:3px 8px; border-radius:999px; background:#dcfce7; color:#065f46; font-weight:800; font-size:.8rem; }
.report .note{ background:#fffbeb; border:1px solid #fde68a; border-radius:12px; padding:10px; color:#92400e; }

.small{ color:var(--muted); font-size:.92rem; }
</style>
"""

if THEME == "Claro":
    st.markdown(base_css % dict(
        bg="#f7f8fb", card="#ffffff", text="#0f172a", muted="#6b7280",
        border="#e5e7eb", chipbg="#eef2ff", chipfg="#4f46e5",
        agent="#eef2ff", patient="#f3f4f6"
    ), unsafe_allow_html=True)
else:
    st.markdown(base_css % dict(
        bg="#0B1220", card="#11182A", text="#EAF2FF", muted="#9EB0CC",
        border="#203049", chipbg="#0f1a2c", chipfg="#8ab6ff",
        agent="#0f1a2c", patient="#0F172A"
    ), unsafe_allow_html=True)

# =========================
# DATA
# =========================
@dataclass
class Patient:
    pid: str
    nombre: str
    edad: int
    sexo: str
    condicion_base: str
    img: str = ""  # agrega URL/ruta si gustas

@dataclass
class Condition:
    cid: str
    titulo: str
    descripcion: str

PACIENTES: List[Patient] = [
    Patient("nvelarde", "Nicolás Velarde", 34, "Masculino", "Trastorno de ansiedad"),
    Patient("aduarte",   "Amalia Duarte",   62, "Femenino",  "Diabetes tipo 2"),
    Patient("szamora",   "Sofía Zamora",    23, "Femenino",  "Asma"),
]

CONDICIONES: List[Condition] = [
    Condition("flu", "Gripe", "Infección viral contagiosa con fiebre, mialgia y fatiga."),
    Condition("mal", "Malaria", "Fiebre intermitente y escalofríos por parásito transmitido por mosquito."),
    Condition("mig", "Migraña", "Cefalea intensa, fotofobia/fonofobia; a veces náusea."),
    Condition("ss",  "Síndrome serotoninérgico", "Exceso de serotonina (p.ej., ISRS + dextrometorfano)."),
]

# Guiones por condición (chat + reglas para construir el reporte)
def get_condition_script(cid: str) -> Tuple[List[Dict], List[Tuple[int,str,str]], List[str]]:
    if cid == "ss":
        chat = [
            {"role":"agent","text":"Gracias por agendar. Haré preguntas para preparar tu visita. ¿Cuál es tu principal molestia hoy?"},
            {"role":"patient","text":"Me siento muy agitado, inquieto y algo confundido."},
            {"role":"agent","text":"¿Cuándo iniciaron los síntomas? ¿inicio súbito o gradual?"},
            {"role":"patient","text":"Hace dos días, de repente."},
            {"role":"agent","text":"¿Has notado fiebre, sudoración, escalofríos o rigidez?"},
            {"role":"patient","text":"Sí, sudo mucho y a veces tirito; los músculos rígidos."},
            {"role":"agent","text":"¿Cambios visuales o en tus ojos?"},
            {"role":"patient","text":"Pupilas dilatadas, y mis ojos se mueven raro."},
            {"role":"agent","text":"¿Cambios en medicación o nuevos productos?"},
            {"role":"patient","text":"Sigo con fluoxetina; tomé jarabe para la tos con dextrometorfano."},
            {"role":"agent","text":"Gracias, tengo lo necesario para tu reporte."},
        ]
        rules = [
            (1, "Motivo principal", "Agitación, inquietud, confusión."),
            (3, "HPI", "Inicio súbito ~2 días."),
            (5, "Signos autonómicos", "Diaforesis y escalofríos, rigidez muscular."),
            (7, "Signos oculares", "Midriasis/nistagmo subjetivo."),
            (9, "Medicaciones (EHR)", "Fluoxetina (ISRS) — uso crónico."),
            (9, "Medicaciones (entrevista)", "Jarabe para la tos con dextrometorfano — uso reciente."),
        ]
        faltantes = [
            "Signos vitales: temperatura, FC, TA.",
            "Exploración neuromuscular: hiperreflexia, mioclonías, rigidez.",
            "Historia farmacológica completa (fechas/dosis).",
        ]
        return chat, rules, faltantes

    if cid == "mig":
        chat = [
            {"role":"agent","text":"Entiendo que presentas dolor de cabeza. ¿Dónde se localiza y cómo lo describirías?"},
            {"role":"patient","text":"Late del lado derecho; la luz me molesta mucho."},
            {"role":"agent","text":"¿Desde cuándo y cuánto dura cada episodio?"},
            {"role":"patient","text":"Empezó ayer, dura horas."},
            {"role":"agent","text":"¿Hay náusea o vómito? ¿ruidos/olores empeoran?"},
            {"role":"patient","text":"Náusea leve; el ruido también me molesta."},
            {"role":"agent","text":"¿Usas analgésicos o triptanos?"},
            {"role":"patient","text":"Solo ibuprofeno; ayuda algo."},
            {"role":"agent","text":"Gracias, prepararé el reporte."},
        ]
        rules = [
            (1, "Motivo principal", "Cefalea pulsátil lateralizada con fotofobia."),
            (3, "HPI", "Inicio ayer; crisis por horas."),
            (5, "HPI", "Náusea leve, fonofobia."),
            (7, "Medicaciones (entrevista)", "Ibuprofeno PRN — respuesta parcial."),
        ]
        faltantes = [
            "Desencadenantes (sueño, alimentos, estrés).",
            "Escala de dolor y frecuencia mensual.",
            "Respuesta a triptanos previos, si existiera."
        ]
        return chat, rules, faltantes

    if cid == "flu":
        chat = [
            {"role":"agent","text":"Vamos a documentar tus síntomas respiratorios. ¿Tienes fiebre o dolor corporal?"},
            {"role":"patient","text":"Sí, fiebre y cuerpo cortado."},
            {"role":"agent","text":"¿Tos y congestión? ¿cuánto tiempo?"},
            {"role":"patient","text":"Tos seca desde hace 3 días, nariz tapada."},
            {"role":"agent","text":"¿Dificultad respiratoria o dolor torácico?"},
            {"role":"patient","text":"No, solo cansancio."},
            {"role":"agent","text":"¿Tomaste algún antipirético o antigripal?"},
            {"role":"patient","text":"Paracetamol y un antigripal de farmacia."},
            {"role":"agent","text":"Perfecto, prepararé el reporte."},
        ]
        rules = [
            (1, "Motivo principal", "Fiebre, mialgia, malestar general."),
            (3, "HPI", "Tos seca y congestión 3 días."),
            (5, "HPI", "Sin disnea ni dolor torácico."),
            (7, "Medicaciones (entrevista)", "Paracetamol y antigripal — automedicación."),
        ]
        faltantes = [
            "Temperatura documentada y saturación O2.",
            "Contacto con enfermos y estado de vacunación.",
            "Comorbilidades respiratorias/embarazo."
        ]
        return chat, rules, faltantes

    # malaria
    chat = [
        {"role":"agent","text":"Vamos a registrar tu cuadro febril. ¿Fiebre con escalofríos intermitentes?"},
        {"role":"patient","text":"Sí, viene y va con sudoraciones."},
        {"role":"agent","text":"¿Has viajado recientemente a zona endémica?"},
        {"role":"patient","text":"Sí, estuve en Chiapas zona selvática hace 2 semanas."},
        {"role":"agent","text":"¿Dolor de cabeza, náusea o dolor muscular?"},
        {"role":"patient","text":"Dolor de cabeza y cuerpo cortado."},
        {"role":"agent","text":"¿Tomas profilaxis antipalúdica?"},
        {"role":"patient","text":"No, no tomé nada."},
        {"role":"agent","text":"Gracias, prepararé el reporte."},
    ]
    rules = [
        (1, "Motivo principal", "Fiebre intermitente con escalofríos y sudoración."),
        (3, "HPI", "Viaje reciente a zona endémica (2 semanas)."),
        (5, "HPI", "Cefalea y mialgias."),
        (7, "Historia dirigida", "Sin profilaxis antipalúdica."),
    ]
    faltantes = [
        "Frotis gota gruesa / prueba rápida.",
        "Registro de fiebre y patrón horario.",
        "Estado hepatoesplénico y anemia."
    ]
    return chat, rules, faltantes

EHR_BASE = {
    # Se añade al reporte siempre
    "Historia clínica relevante": ["Antecedente crónico declarado en ficha de paciente"],
    "Medicaciones (EHR)": ["Medicación habitual según expediente (si aplica)"],
}

# =========================
# HELPERS UI
# =========================
def step_title(title: str, sub: str = ""):
    st.markdown(f"<div class='h-title'>{title}</div>", unsafe_allow_html=True)
    if sub:
        st.markdown(f"<div class='h-sub'>{sub}</div>", unsafe_allow_html=True)

def patient_card(p: Patient, selected=False):
    border = "selected" if selected else ""
    st.markdown(f"""
    <div class="select-card {border} card">
        <div style="height:190px;background:rgba(0,0,0,.06);border-radius:12px;display:flex;align-items:center;justify-content:center;overflow:hidden">
          <!-- Sustituye por st.image(p.img) si añades imagen -->
          <span class="small">Imagen del paciente</span>
        </div>
        <div style="margin-top:8px"><span class="tag">Expediente Clínico Sintético (FHIR)</span></div>
        <div style="font-weight:900; margin-top:6px">{p.nombre}</div>
        <div class="small">{p.edad} años • {p.sexo}</div>
        <div class="small">Condición de base: {p.condicion_base}</div>
    </div>
    """, unsafe_allow_html=True)

def condition_card(c: Condition, selected=False):
    border = "selected" if selected else ""
    st.markdown(f"""
    <div class="select-card {border} card">
      <div style="font-weight:900;margin-bottom:6px">{c.titulo}</div>
      <div class="small">{c.descripcion}</div>
    </div>
    """, unsafe_allow_html=True)

def collect_facts(idx_limit:int, rules:List[Tuple[int,str,str]]):
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
    for i_lim, kind, text in rules:
        if idx_limit >= i_lim:
            facts[kind].append(text)
    return facts

def render_report(idx_limit:int, rules):
    facts = collect_facts(idx_limit, rules)
    st.markdown('<div class="report">', unsafe_allow_html=True)
    st.markdown('<div class="h-title" style="margin-bottom:4px">Reporte generado</div>', unsafe_allow_html=True)

    def box(title, items):
        st.markdown('<div class="box">', unsafe_allow_html=True)
        st.markdown(f"**{title}:**")
        if isinstance(items, list):
            if items:
                st.markdown("<ul>"+ "".join([f"<li>{x}</li>" for x in items]) +"</ul>", unsafe_allow_html=True)
            else:
                st.markdown("—")
        else:
            st.markdown(items or "—")
        st.markdown('</div>', unsafe_allow_html=True)

    mp = facts["Motivo principal"][0] if facts["Motivo principal"] else "—"
    box("Motivo principal", mp)
    box("Historia de la enfermedad actual (HPI)", facts["HPI"])
    box("Antecedentes relevantes (EHR)", facts["Historia clínica relevante"])

    # Medicaciones
    st.markdown('<div class="box">', unsafe_allow_html=True)
    st.markdown("**Medicaciones (EHR y entrevista):**")
    meds_items = []
    for m in facts["Medicaciones (EHR)"]:
        meds_items.append(f"<li>{m}</li>")
    for m in facts["Medicaciones (entrevista)"]:
        meds_items.append(f"<li><span class='pill'>{m}</span></li>")
    st.markdown("<ul>"+ "".join(meds_items) +"</ul>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Hechos útiles
    utiles = facts["Signos autonómicos"] + facts["Signos oculares"] + facts["Historia dirigida"]
    if utiles:
        box("Hechos útiles", utiles)

    # Faltantes (solo al final)
    if idx_limit >= len(rules):
        st.markdown('<div class="box note">', unsafe_allow_html=True)
        st.markdown("**Qué no se cubrió pero sería útil:**")
        for x in get_condition_script(st.session_state.sel_condition)[2]:
            st.markdown(f"- {x}")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# =========================
# SIDEBAR CONTROLS
# =========================
st.sidebar.markdown("### Flujo")
st.sidebar.caption("1) Paciente y condición → 2) Introducción → 3) Entrevista y reporte.")
if st.sidebar.button("Reiniciar flujo"):
    st.session_state.step = "select"
    st.session_state.sel_patient = None
    st.session_state.sel_condition = None
    st.session_state.chat_idx = -1
    st.session_state.autoplay = False
    st.rerun()

# =========================
# STEP: SELECCIÓN
# =========================
if st.session_state.step == "select":
    step_title("Selecciona un paciente")
    st.markdown('<hr class="section"/>', unsafe_allow_html=True)
    cols = st.columns(3, gap="large")
    for i, p in enumerate(PACIENTES):
        with cols[i]:
            selected = (st.session_state.sel_patient == p.pid)
            patient_card(p, selected)
            if st.button(("Elegir" if not selected else "Seleccionado"), key=f"pickp_{p.pid}", use_container_width=True):
                st.session_state.sel_patient = p.pid
                st.rerun()

    st.markdown('<hr class="section"/>', unsafe_allow_html=True)
    step_title("Explorar una condición", "Selecciona la condición a investigar")
    cols2 = st.columns(2, gap="large")
    for j, c in enumerate(CONDICIONES):
        with cols2[j % 2]:
            selected = (st.session_state.sel_condition == c.cid)
            condition_card(c, selected)
            if st.button(("Elegir" if not selected else "Seleccionada"), key=f"pickc_{c.cid}", use_container_width=True):
                st.session_state.sel_condition = c.cid
                st.rerun()

    st.markdown('<hr class="section"/>', unsafe_allow_html=True)
    go = st.button("Iniciar", disabled=not (st.session_state.sel_patient and st.session_state.sel_condition), use_container_width=True)
    if go:
        st.session_state.step = "intro"
        st.rerun()

# =========================
# STEP: INTRO
# =========================
elif st.session_state.step == "intro":
    p = next(x for x in PACIENTES if x.pid == st.session_state.sel_patient)
    c = next(x for x in CONDICIONES if x.cid == st.session_state.sel_condition)

    l, r = st.columns(2, gap="large")
    with l:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        step_title("Agente de preconsulta")
        st.markdown("Este asistente recopila información previa a la visita, con preguntas clínicas estructuradas.")
        st.markdown('</div>', unsafe_allow_html=True)
    with r:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        step_title(f"Persona del paciente: {p.nombre}", f"{p.edad} años • {p.sexo} • Condición de base: {p.condicion_base}")
        st.markdown("Se incluye información contextual del paciente para guiar la entrevista.")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<hr class="section"/>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1.2, 1.2, 2.6], gap="large")
    with c1:
        if st.button("◀ Volver", use_container_width=True):
            st.session_state.step = "select"; st.rerun()
    with c2:
        if st.button("Comenzar entrevista", use_container_width=True):
            st.session_state.step = "convo"; st.session_state.chat_idx = -1; st.session_state.autoplay = False; st.rerun()
    with c3:
        st.caption(f"Condición: **{c.titulo}** — {c.descripcion}")

# =========================
# STEP: CONVERSACIÓN + REPORTE
# =========================
elif st.session_state.step == "convo":
    chat, rules, faltantes = get_condition_script(st.session_state.sel_condition)

    top_l, top_r = st.columns([2.5, 1.5], gap="large")
    with top_l:
        step_title("Entrevista simulada", "Audio opcional (si lo agregas)")
    with top_r:
        a, b, c3 = st.columns(3)
        with a:
            if st.button("◀ Volver", use_container_width=True):
                st.session_state.step = "intro"; st.rerun()
        with b:
            if st.button("🔁 Reiniciar", use_container_width=True):
                st.session_state.chat_idx = -1; st.session_state.autoplay = False; st.rerun()
        with c3:
            if not st.session_state.autoplay:
                if st.button("▶ Auto", use_container_width=True):
                    st.session_state.autoplay = True; st.rerun()
            else:
                if st.button("⏸︎ Pausa", use_container_width=True):
                    st.session_state.autoplay = False; st.rerun()

    st.markdown('<hr class="section"/>', unsafe_allow_html=True)

    # Audio opcional
    up, url = st.columns([1.4, 2.6], gap="large")
    with up:
        f = st.file_uploader("Sube audio (.mp3/.wav) opcional", type=["mp3","wav"])
        if f: st.audio(f)
    with url:
        st.session_state.audio_url = st.text_input("…o pega URL de audio (opcional)", value=st.session_state.audio_url)
        if st.session_state.audio_url: st.audio(st.session_state.audio_url)

    st.markdown('<hr class="section"/>', unsafe_allow_html=True)

    # Layout principal
    chat_col, report_col = st.columns([1.3, 1.0], gap="large")

    # CHAT
    with chat_col:
        st.markdown('<div class="chatwrap">', unsafe_allow_html=True)

        # avanzar un mensaje manual/auto
        if st.session_state.chat_idx < len(chat) - 1:
            if not st.session_state.autoplay:
                if st.button("Siguiente mensaje ▶", use_container_width=True, key="next"):
                    st.session_state.chat_idx += 1
                    st.rerun()
            else:
                # Auto avance con delay sin loops atascados
                time.sleep(1.0)
                st.session_state.chat_idx += 1
                st.rerun()
        else:
            st.success("Entrevista completa. El reporte está consolidado.")

        # render mensajes hasta el índice actual
        for i in range(st.session_state.chat_idx + 1):
            role = chat[i]["role"]
            txt = chat[i]["text"]
            who = "Asistente" if role == "agent" else "Paciente"
            klass = "agent" if role == "agent" else "patient"
            st.markdown(f"<div class='msg {klass}'><b>{who}:</b> {txt}<br><small>{datetime.now().strftime('%H:%M')}</small></div>", unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    # REPORTE
    with report_col:
        render_report(st.session_state.chat_idx, rules)

    st.markdown('<hr class="section"/>', unsafe_allow_html=True)
    with st.expander("Acerca de la evaluación de calidad"):
        st.markdown("""
Este bloque ilustra cómo listar **hechos útiles** y **faltantes** que mejorarían la completitud.  
No reemplaza criterio médico; sirve para mostrar cómo un agente podría estructurar la preconsulta.
        """)
