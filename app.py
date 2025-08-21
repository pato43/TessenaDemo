# app.py — Agente de preconsulta (ES-MX)
# - Auto claro/oscuro (prefers-color-scheme)
# - Selección paciente/condición
# - Conversación automática con tipeo y reporte dinámico
# - Sin audio, sin LLM

import streamlit as st
from dataclasses import dataclass
from typing import List, Dict, Tuple
from datetime import datetime
import time

st.set_page_config(page_title="Agente de Preconsulta", layout="wide", page_icon="🩺")

# --------- State ---------
if "step" not in st.session_state: st.session_state.step = "select"   # select → intro → convo
if "sel_patient" not in st.session_state: st.session_state.sel_patient = None
if "sel_condition" not in st.session_state: st.session_state.sel_condition = None
if "chat_idx" not in st.session_state: st.session_state.chat_idx = -1  # último índice COMPLETADO
if "pause" not in st.session_state: st.session_state.pause = False

# --------- Styles (no se imprimen) ---------
CSS = """
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800;900&display=swap" rel="stylesheet">
<style>
:root{
  --bg:#f7f8fb; --card:#ffffff; --text:#0f172a; --muted:#6b7280;
  --primary:#7c3aed; --accent:#22d3ee; --border:#e5e7eb;
  --chipbg:#eef2ff; --chipfg:#4f46e5; --agent:#eef2ff; --patient:#f3f4f6;
}
@media (prefers-color-scheme: dark){
  :root{
    --bg:#0B1220; --card:#11182A; --text:#EAF2FF; --muted:#9EB0CC;
    --primary:#7c3aed; --accent:#22d3ee; --border:#203049;
    --chipbg:#0f1a2c; --chipfg:#8ab6ff; --agent:#0f1a2c; --patient:#0F172A;
  }
}
html, body, [class*="css"]{
  background:var(--bg) !important; color:var(--text) !important;
  font-family:Inter,system-ui,-apple-system,Segoe UI,Roboto,Helvetica Neue,Arial,sans-serif;
  font-size:16.5px; line-height:1.35;
}
.block-container{ padding-top:.8rem; }
header { visibility:hidden; }

/* Topbar */
.topbar{ position:sticky; top:0; z-index:10; padding:10px 14px; margin-bottom:12px;
  background:linear-gradient(90deg,var(--card),var(--card));
  border:1px solid var(--border); border-radius:12px; box-shadow:0 6px 22px rgba(0,0,0,.05); }
.topbar .brand{ font-weight:900; letter-spacing:.3px; }
.topbar .badge{ margin-left:8px; }

/* Cards / separators */
.card{ background:var(--card); border:1px solid var(--border); border-radius:16px; padding:16px; }
.sep{ height:1px; border:none; margin:12px 0 16px; background:linear-gradient(90deg,var(--primary),var(--accent)); border-radius:2px; }

/* Chips */
.badge,.tag{ display:inline-block; border-radius:999px; padding:6px 10px; background:var(--chipbg); color:var(--chipfg);
  border:1px solid var(--border); font-weight:800; font-size:.8rem; }

/* Select cards */
.select-card{ border-radius:16px; border:2px solid transparent; transition:.2s; cursor:pointer; }
.select-card:hover{ transform:translateY(-1px); box-shadow:0 10px 28px rgba(0,0,0,.08); }
.select-card.selected{ border-color:#c7d2fe; box-shadow:0 0 0 3px #e0e7ff55 inset; }

/* Titles */
.h-title{ font-weight:900; font-size:1.45rem; margin:0 0 6px; }
.h-sub{ color:var(--muted); font-weight:600; }

/* Chat */
.chatwrap{ background:var(--card); border:1px solid var(--border); border-radius:16px; padding:14px; }
.msg{ border-radius:12px; padding:10px 12px; margin:8px 0; max-width:96%; border:1px solid var(--border); }
.msg.agent{ background:var(--agent); }
.msg.patient{ background:var(--patient); }
.msg small{ color:var(--muted); display:block; margin-top:2px; }
.typing{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono"; }

/* Buttons */
.stButton > button{ border-radius:10px; font-weight:800; border:none; background:var(--primary); color:#fff; }
.stButton > button:hover{ filter:brightness(.95); }

/* Report */
.report .box{ background:var(--card); border:1px solid var(--border); border-radius:16px; padding:14px; margin-bottom:10px; }
.report .pill{ display:inline-block; padding:3px 8px; border-radius:999px; background:#dcfce7; color:#065f46; font-weight:800; font-size:.8rem; }
.report .note{ background:#fffbeb; border:1px solid #fde68a; border-radius:12px; padding:10px; color:#92400e; }
.small{ color:var(--muted); font-size:.92rem; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# --------- Data ---------
@dataclass
class Patient:
    pid: str
    nombre: str
    edad: int
    sexo: str
    condicion_base: str
    img: str = ""

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
    Condition("flu", "Gripe", "Infección viral con fiebre, mialgia y fatiga."),
    Condition("mal", "Malaria", "Fiebre intermitente y escalofríos (vector: mosquito)."),
    Condition("mig", "Migraña", "Cefalea pulsátil con foto/fonofobia; posible náusea."),
    Condition("ss",  "Síndrome serotoninérgico", "Exceso de serotonina (p. ej., ISRS + dextrometorfano)."),
]

def script_ss():
    chat = [
        # Motivo, cronología, autonomicos, oculares, meds, riesgos
        ("agent","Gracias por agendar. Te haré preguntas breves para preparar tu visita. ¿Cuál es tu principal molestia hoy?"),
        ("patient","Me siento muy agitado e inquieto; también algo confundido."),
        ("agent","¿Desde cuándo? ¿inicio súbito o progresivo?"),
        ("patient","Empezó hace dos días, de golpe."),
        ("agent","¿Has notado fiebre, sudoración, escalofríos o rigidez muscular?"),
        ("patient","Sí, sudo mucho, tiritas de vez en cuando y los músculos rígidos."),
        ("agent","¿Percibes cambios visuales o movimientos oculares extraños?"),
        ("patient","Mis pupilas se ven grandes y se mueven raro."),
        ("agent","¿Tomaste o cambiaste medicamentos, jarabes o suplementos en los últimos días?"),
        ("patient","Uso fluoxetina diario; tomé un jarabe para la tos con dextrometorfano anoche."),
        ("agent","¿Consumiste alcohol o estimulantes recientemente?"),
        ("patient","No, nada de eso."),
        ("agent","¿Dolor intenso, diarrea o vómito?"),
        ("patient","No vómito; algo de náusea leve."),
        ("agent","¿Problemas para dormir o inquietud extrema?"),
        ("patient","Sí, casi no pude dormir."),
        ("agent","Gracias, con esto elaboro un reporte para tu médico."),
    ]
    # (turn_index, sección, texto)
    rules = [
        (1,"Motivo principal","Agitación, inquietud y confusión."),
        (3,"HPI","Inicio súbito ~2 días, insomnio."),
        (5,"Signos autonómicos","Diaforesis, escalofríos, rigidez muscular."),
        (7,"Signos oculares","Midriasis y movimientos anómalos."),
        (9,"Medicaciones (EHR)","Fluoxetina (ISRS) — uso crónico."),
        (9,"Medicaciones (entrevista)","Dextrometorfano — uso reciente."),
        (11,"Historia dirigida","Niega alcohol/estimulantes."),
        (13,"HPI","Náusea leve, sin vómito."),
    ]
    faltantes = [
        "Signos vitales: temperatura, FC y TA.",
        "Exploración neuromuscular: hiperreflexia, mioclonías, rigidez.",
        "Historia farmacológica completa (fechas/dosis).",
    ]
    return chat, rules, faltantes

def script_mig():
    chat = [
        ("agent","Entiendo que presentas cefalea. ¿Dónde se localiza y cómo la describirías?"),
        ("patient","Late del lado derecho; la luz me molesta."),
        ("agent","¿Desde cuándo y cuánto dura cada episodio?"),
        ("patient","Desde ayer; duran varias horas."),
        ("agent","¿Náusea, vómito o sensibilidad a ruidos/olores?"),
        ("patient","Náusea leve; el ruido empeora el dolor."),
        ("agent","¿Dormiste menos o comiste algo inusual?"),
        ("patient","Dormí poco; tomé café tarde."),
        ("agent","¿Has tomado analgésicos o triptanos?"),
        ("patient","Ibuprofeno; ayuda un poco."),
        ("agent","De acuerdo, prepararé tu reporte."),
    ]
    rules = [
        (1,"Motivo principal","Cefalea pulsátil lateralizada con fotofobia."),
        (3,"HPI","Inicio ayer; crisis por horas."),
        (5,"HPI","Náusea leve y fonofobia."),
        (7,"Historia dirigida","Privación de sueño y cafeína tardía."),
        (9,"Medicaciones (entrevista)","Ibuprofeno PRN — respuesta parcial."),
    ]
    faltantes = ["Frecuencia mensual y escala de dolor.","Respuesta a triptanos previos.","Desencadenantes específicos."]
    return chat, rules, faltantes

def script_flu():
    chat = [
        ("agent","Vamos a documentar tus síntomas respiratorios. ¿Tienes fiebre o dolor corporal?"),
        ("patient","Sí, fiebre y cuerpo cortado."),
        ("agent","¿Tos/congestión? ¿desde cuándo?"),
        ("patient","Tos seca hace 3 días; nariz tapada."),
        ("agent","¿Dificultad para respirar o dolor torácico?"),
        ("patient","No, solo cansancio."),
        ("agent","¿Tomaste antipiréticos o antigripales?"),
        ("patient","Paracetamol y un antigripal."),
        ("agent","¿Contacto con personas enfermas o vacunación reciente?"),
        ("patient","Mi pareja tuvo gripe; vacunado hace 8 meses."),
        ("agent","Gracias, prepararé tu reporte."),
    ]
    rules = [
        (1,"Motivo principal","Fiebre, mialgia, malestar."),
        (3,"HPI","Tos seca y congestión 3 días."),
        (5,"HPI","Sin disnea ni dolor torácico."),
        (7,"Medicaciones (entrevista)","Paracetamol y antigripal."),
        (9,"Historia dirigida","Contacto positivo; vacunación hace 8 meses."),
    ]
    faltantes=["Temperatura y saturación O₂ documentadas.","Factores de riesgo y comorbilidades.","Prueba diagnóstica si aplica."]
    return chat, rules, faltantes

def script_mal():
    chat = [
        ("agent","Vamos a registrar tu cuadro febril. ¿La fiebre aparece con escalofríos intermitentes?"),
        ("patient","Sí, viene y va con sudoración."),
        ("agent","¿Viajaste a zona endémica recientemente?"),
        ("patient","Sí, selva hace dos semanas."),
        ("agent","¿Cefalea, náusea o dolor muscular?"),
        ("patient","Cefalea y cuerpo cortado."),
        ("agent","¿Tomaste profilaxis antipalúdica?"),
        ("patient","No."),
        ("agent","Bien, prepararé tu reporte."),
    ]
    rules = [
        (1,"Motivo principal","Fiebre intermitente con escalofríos y sudoración."),
        (3,"HPI","Viaje a zona endémica (2 semanas)."),
        (5,"HPI","Cefalea y mialgias."),
        (7,"Historia dirigida","Sin profilaxis."),
    ]
    faltantes = ["Prueba rápida/frotis.","Patrón horario de fiebre.","Valoración de anemia y esplenomegalia."]
    return chat, rules, faltantes

SCRIPTS = {"ss":script_ss, "mig":script_mig, "flu":script_flu, "mal":script_mal}

EHR_BASE = {
    "Historia clínica relevante": ["Antecedente crónico declarado en ficha del paciente"],
    "Medicaciones (EHR)": ["Medicación habitual según expediente (si aplica)"],
}

# --------- Helpers ---------
def title(txt, sub=""):
    st.markdown(f"<div class='h-title'>{txt}</div>", unsafe_allow_html=True)
    if sub: st.markdown(f"<div class='h-sub'>{sub}</div>", unsafe_allow_html=True)

def patient_card(p: Patient, selected=False):
    sel = "selected" if selected else ""
    st.markdown(f"""
    <div class="select-card {sel} card">
      <div style="height:190px;background:rgba(0,0,0,.06);border-radius:12px;display:flex;align-items:center;justify-content:center;">
        <span class="small">Imagen del paciente</span>
      </div>
      <div style="margin-top:8px"><span class="tag">Expediente Clínico Sintético (FHIR)</span></div>
      <div style="font-weight:900;margin-top:6px">{p.nombre}</div>
      <div class="small">{p.edad} años • {p.sexo}</div>
      <div class="small">Condición de base: {p.condicion_base}</div>
    </div>
    """, unsafe_allow_html=True)

def condition_card(c: Condition, selected=False):
    sel = "selected" if selected else ""
    st.markdown(f"""
    <div class="select-card {sel} card">
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
    for i_lim, kind, txt in rules:
        if idx_limit >= i_lim:
            facts[kind].append(txt)
    return facts

def render_report(idx_limit, rules):
    facts = collect_facts(idx_limit, rules)

    def box(title_txt, items):
        st.markdown('<div class="box">', unsafe_allow_html=True)
        st.markdown(f"**{title_txt}:**")
        if isinstance(items, list):
            if items: st.markdown("<ul>"+ "".join([f"<li>{x}</li>" for x in items]) +"</ul>", unsafe_allow_html=True)
            else: st.markdown("—")
        else:
            st.markdown(items or "—")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="report">', unsafe_allow_html=True)
    mp = facts["Motivo principal"][0] if facts["Motivo principal"] else "—"
    box("Motivo principal", mp)
    box("Historia de la enfermedad actual (HPI)", facts["HPI"])
    box("Antecedentes relevantes (EHR)", facts["Historia clínica relevante"])

    st.markdown('<div class="box">', unsafe_allow_html=True)
    st.markdown("**Medicaciones (EHR y entrevista):**")
    meds = [f"<li>{m}</li>" for m in facts["Medicaciones (EHR)"]]
    meds += [f"<li><span class='pill'>{m}</span></li>" for m in facts["Medicaciones (entrevista)"]]
    st.markdown("<ul>"+ "".join(meds) +"</ul>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    utiles = facts["Signos autonómicos"] + facts["Signos oculares"] + facts["Historia dirigida"]
    if utiles: box("Hechos útiles", utiles)

    if idx_limit >= len(rules):
        st.markdown('<div class="box note">', unsafe_allow_html=True)
        st.markdown("**Qué no se cubrió pero sería útil:**")
        for x in SCRIPTS[st.session_state.sel_condition]()[2]:
            st.markdown(f"- {x}")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

def typewriter(container, full_text: str, speed: float = 0.012):
    out = ""
    for ch in full_text:
        out += ch
        container.markdown(f"<div class='typing'>{out}</div>", unsafe_allow_html=True)
        time.sleep(speed)

# --------- Topbar ---------
st.markdown("""
<div class="topbar">
  <span class="brand">Agente de Preconsulta</span>
  <span class="badge">ES • MX</span>
</div>
""", unsafe_allow_html=True)

# --------- Sidebar flow ---------
st.sidebar.markdown("### Flujo")
st.sidebar.caption("1) Paciente y condición → 2) Introducción → 3) Entrevista y reporte.")
c1, c2 = st.sidebar.columns(2)
with c1:
    if st.button("Reiniciar flujo"):
        st.session_state.step = "select"
        st.session_state.sel_patient = None
        st.session_state.sel_condition = None
        st.session_state.chat_idx = -1
        st.session_state.pause = False
        st.rerun()
with c2:
    if not st.session_state.pause:
        if st.button("⏸ Pausa"):
            st.session_state.pause = True; st.rerun()
    else:
        if st.button("▶ Reanudar"):
            st.session_state.pause = False; st.rerun()

# --------- SELECT ---------
if st.session_state.step == "select":
    title("Selecciona un paciente"); st.markdown('<hr class="sep">', unsafe_allow_html=True)
    cols = st.columns(3, gap="large")
    for i, p in enumerate(PACIENTES):
        with cols[i]:
            selected = (st.session_state.sel_patient == p.pid)
            patient_card(p, selected)
            if st.button(("Elegir" if not selected else "Seleccionado"), key=f"p_{p.pid}", use_container_width=True):
                st.session_state.sel_patient = p.pid; st.rerun()

    st.markdown('<hr class="sep">', unsafe_allow_html=True)
    title("Explorar una condición", "Selecciona la condición a investigar")
    cols2 = st.columns(2, gap="large")
    for j, c in enumerate(CONDICIONES):
        with cols2[j % 2]:
            selected = (st.session_state.sel_condition == c.cid)
            condition_card(c, selected)
            if st.button(("Elegir" if not selected else "Seleccionada"), key=f"c_{c.cid}", use_container_width=True):
                st.session_state.sel_condition = c.cid; st.rerun()

    st.markdown('<hr class="sep">', unsafe_allow_html=True)
    if st.button("Iniciar", disabled=not (st.session_state.sel_patient and st.session_state.sel_condition), use_container_width=True):
        st.session_state.step = "intro"; st.rerun()

# --------- INTRO ---------
elif st.session_state.step == "intro":
    p = next(x for x in PACIENTES if x.pid == st.session_state.sel_patient)
    c = next(x for x in CONDICIONES if x.cid == st.session_state.sel_condition)

    L, R = st.columns(2, gap="large")
    with L:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        title("Agente de preconsulta")
        st.markdown("Guía preguntas clínicas previas a la visita y estructura la información para el médico.")
        st.markdown('</div>', unsafe_allow_html=True)
    with R:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        title(f"Persona del paciente: {p.nombre}", f"{p.edad} años • {p.sexo} • Condición de base: {p.condicion_base}")
        st.markdown("Incluye contexto del paciente para orientar la entrevista.")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<hr class="sep">', unsafe_allow_html=True)
    a, b, c3 = st.columns([1.1, 1.1, 2.8], gap="large")
    with a:
        if st.button("◀ Volver", use_container_width=True):
            st.session_state.step = "select"; st.rerun()
    with b:
        if st.button("Comenzar entrevista", use_container_width=True):
            st.session_state.step = "convo"; st.session_state.chat_idx = -1; st.session_state.pause = False; st.rerun()
    with c3:
        st.caption(f"Condición: **{c.titulo}** — {c.descripcion}")

    st.markdown('<hr class="sep">', unsafe_allow_html=True)
    with st.expander("¿Cómo usarlo?"):
        st.markdown("""
1) Elige **paciente** y **condición**.  
2) Inicia la **entrevista**: los mensajes aparecen **automáticamente** (puedes **pausar**/**reanudar** desde la barra lateral).  
3) El **reporte** a la derecha se **actualiza en tiempo real** (Motivo, HPI, antecedentes, medicaciones y hechos útiles).  
4) Al cierre se listan **datos faltantes** recomendados para completar calidad clínica.

**Integración (visión TESSENA):** validación con **COFEPRIS**, **FDA** y **OpenDrugs**; FHIR/HealthLake para datos clínicos; razonamiento clínico con modelos especializados y resumen estructurado, con trazabilidad y auditoría.
""")

# --------- CONVO ---------
elif st.session_state.step == "convo":
    chat, rules, _falt = SCRIPTS[st.session_state.sel_condition]()

    topL, topR = st.columns([2.5, 1.5], gap="large")
    with topL: title("Entrevista simulada", "Mensajes automáticos con animación de tipeo")
    with topR:
        a, b, c3 = st.columns(3)
        with a:
            if st.button("◀ Volver", use_container_width=True):
                st.session_state.step = "intro"; st.rerun()
        with b:
            if st.button("🔁 Reiniciar", use_container_width=True):
                st.session_state.chat_idx = -1; st.session_state.pause = False; st.rerun()
        with c3:
            if not st.session_state.pause:
                if st.button("⏸ Pausa", use_container_width=True):
                    st.session_state.pause = True; st.rerun()
            else:
                if st.button("▶ Reanudar", use_container_width=True):
                    st.session_state.pause = False; st.rerun()

    st.markdown('<hr class="sep">', unsafe_allow_html=True)
    chat_col, rep_col = st.columns([1.35, 1.0], gap="large")

    # Chat
    with chat_col:
        st.markdown('<div class="chatwrap">', unsafe_allow_html=True)

        # Mostrar anteriores completos
        for i in range(st.session_state.chat_idx + 1):
            role, txt = chat[i]
            who = "Asistente" if role == "agent" else "Paciente"
            klass = "agent" if role == "agent" else "patient"
            st.markdown(f"<div class='msg {klass}'><b>{who}:</b> {txt}<br><small>{datetime.now().strftime('%H:%M')}</small></div>", unsafe_allow_html=True)

        next_idx = st.session_state.chat_idx + 1
        if next_idx < len(chat):
            role, txt = chat[next_idx]
            who = "Asistente" if role == "agent" else "Paciente"
            klass = "agent" if role == "agent" else "patient"

            if not st.session_state.pause:
                st.markdown(f"<div class='msg {klass}'><b>{who}:</b> ", unsafe_allow_html=True)
                ph = st.empty()
                st.markdown("<small>"+datetime.now().strftime("%H:%M")+"</small></div>", unsafe_allow_html=True)
                # animación
                for ch in txt:
                    ph.markdown(f"<span class='typing'>{ch if False else ''}</span>", unsafe_allow_html=True)  # warm-up render
                    break
                out = ""
                for ch in txt:
                    out += ch
                    ph.markdown(f"<div class='typing'>{out}</div>", unsafe_allow_html=True)
                    time.sleep(0.012)
                st.session_state.chat_idx = next_idx
                time.sleep(0.2)
                st.rerun()
            else:
                st.markdown(f"<div class='msg {klass}'><b>{who}:</b> <span class='small'>[Pausado]</span></div>", unsafe_allow_html=True)
        else:
            st.success("Entrevista completa. El reporte quedó consolidado.")
        st.markdown('</div>', unsafe_allow_html=True)

    # Reporte
    with rep_col:
        render_report(st.session_state.chat_idx, rules)

    st.markdown('<hr class="sep">', unsafe_allow_html=True)
    with st.expander("Notas sobre calidad y completitud"):
        st.markdown("El reporte resalta **hechos útiles** y lista **datos faltantes** recomendados para mejorar la calidad clínica.")

# --------- end ---------
