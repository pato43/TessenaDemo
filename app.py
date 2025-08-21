# app.py
# Agente de preconsulta (ES-MX)
# - Tema adaptable (claro/oscuro por sistema)
# - Selección de paciente + condición
# - Conversación automática con animación de tipeo y reporte dinámico
# - Instrucciones de uso y notas de integración futura (TESSENA)

import streamlit as st
from dataclasses import dataclass
from typing import List, Dict, Tuple
from datetime import datetime
import time

# ---------------------------
# CONFIG Y ESTADO
# ---------------------------
st.set_page_config(page_title="Agente de Preconsulta", layout="wide", page_icon="🩺")

if "step" not in st.session_state:
    st.session_state.step = "select"   # select → intro → convo
if "sel_patient" not in st.session_state:
    st.session_state.sel_patient = None
if "sel_condition" not in st.session_state:
    st.session_state.sel_condition = None
if "chat_idx" not in st.session_state:
    st.session_state.chat_idx = -1     # índice del último mensaje COMPLETADO
if "typing" not in st.session_state:
    st.session_state.typing = False    # si estamos tipeando el mensaje actual
if "pause" not in st.session_state:
    st.session_state.pause = False     # control pausa

# ---------------------------
# ESTILOS (auto claro/oscuro)
# ---------------------------
st.markdown("""
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
  font-family:Inter, system-ui, -apple-system, Segoe UI, Roboto, "Helvetica Neue", Arial, sans-serif;
  font-size:16.5px;
}
.block-container{ padding-top:.75rem; }
header{ visibility:hidden; }

/* Cards / secciones */
.card{ background:var(--card); border:1px solid var(--border); border-radius:16px; padding:16px; }
.section{ height:1px; border:none; margin:10px 0 16px; background:linear-gradient(90deg,var(--primary),var(--accent)); }

/* Chips y badges */
.badge,.tag{ display:inline-block; border-radius:999px; padding:6px 10px; background:var(--chipbg); color:var(--chipfg);
  border:1px solid var(--border); font-weight:800; font-size:.8rem; }

/* Tarjetas seleccionables */
.select-card{ border-radius:16px; border:2px solid transparent; transition:.2s; cursor:pointer; }
.select-card:hover{ transform:translateY(-1px); box-shadow:0 10px 28px rgba(0,0,0,.08); }
.select-card.selected{ border-color:#c7d2fe; box-shadow:0 0 0 3px #e0e7ff55 inset; }

/* Títulos */
.h-title{ font-weight:900; font-size:1.5rem; margin:0 0 6px; }
.h-sub{ color:var(--muted); font-weight:600; }

/* Chat */
.chatwrap{ background:var(--card); border:1px solid var(--border); border-radius:16px; padding:14px; }
.msg{ border-radius:12px; padding:10px 12px; margin:8px 0; max-width:96%; border:1px solid var(--border); }
.msg.agent{ background:var(--agent); }
.msg.patient{ background:var(--patient); }
.msg small{ color:var(--muted); display:block; margin-top:2px; }
.typing{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace; }

/* Botones */
.stButton > button{ border-radius:10px; font-weight:800; border:none; background:var(--primary); color:#fff; }
.stButton > button:hover{ filter:brightness(.95); }

/* Reporte */
.report .box{ background:var(--card); border:1px solid var(--border); border-radius:16px; padding:14px; margin-bottom:10px; }
.report .pill{ display:inline-block; padding:3px 8px; border-radius:999px; background:#dcfce7; color:#065f46; font-weight:800; font-size:.8rem; }
.report .note{ background:#fffbeb; border:1px solid #fde68a; border-radius:12px; padding:10px; color:#92400e; }
.small{ color:var(--muted); font-size:.92rem; }
</style>
""", unsafe_allow_html=True)

# ---------------------------
# DATOS
# ---------------------------
@dataclass
class Patient:
    pid: str
    nombre: str
    edad: int
    sexo: str
    condicion_base: str
    img: str = ""  # URL/ruta si quieres mostrar foto

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

# Guiones por condición (chat + reglas para reporte)
def get_condition_script(cid: str) -> Tuple[List[Dict], List[Tuple[int,str,str]], List[str]]:
    if cid == "ss":
        chat = [
            {"role":"agent","text":"Gracias por agendar. Haré algunas preguntas para preparar tu visita. ¿Cuál es tu principal molestia hoy?"},
            {"role":"patient","text":"Me siento muy agitado e inquieto, también algo confundido."},
            {"role":"agent","text":"¿Cuándo iniciaron los síntomas? ¿inicio súbito o gradual?"},
            {"role":"patient","text":"Hace dos días, de repente."},
            {"role":"agent","text":"¿Has notado fiebre, sudoración, escalofríos o rigidez?"},
            {"role":"patient","text":"Sí, sudo mucho y a veces tirito; siento rigidez."},
            {"role":"agent","text":"¿Algún cambio visual?"},
            {"role":"patient","text":"Pupilas dilatadas y ojos con movimientos raros."},
            {"role":"agent","text":"¿Cambios en medicación o productos nuevos?"},
            {"role":"patient","text":"Sigo con fluoxetina; tomé jarabe para la tos con dextrometorfano."},
            {"role":"agent","text":"Gracias, tengo lo necesario para elaborar tu reporte."},
        ]
        rules = [
            (1, "Motivo principal", "Agitación, inquietud, confusión."),
            (3, "HPI", "Inicio súbito ~2 días."),
            (5, "Signos autonómicos", "Diaforesis y escalofríos, rigidez muscular."),
            (7, "Signos oculares", "Midriasis y nistagmo subjetivo."),
            (9, "Medicaciones (EHR)", "Fluoxetina (ISRS) — uso crónico."),
            (9, "Medicaciones (entrevista)", "Dextrometorfano (jarabe para la tos) — uso reciente."),
        ]
        faltantes = [
            "Signos vitales: temperatura, FC y TA.",
            "Exploración neuromuscular: hiperreflexia, mioclonías, rigidez.",
            "Historia farmacológica completa (fechas/dosis).",
        ]
        return chat, rules, faltantes

    if cid == "mig":
        chat = [
            {"role":"agent","text":"Entiendo que presentas cefalea. ¿Dónde se localiza y cómo la describirías?"},
            {"role":"patient","text":"Del lado derecho y late; la luz me molesta."},
            {"role":"agent","text":"¿Desde cuándo y cuánto dura cada episodio?"},
            {"role":"patient","text":"Desde ayer, dura horas."},
            {"role":"agent","text":"¿Hay náusea? ¿ruidos/olores la empeoran?"},
            {"role":"patient","text":"Náusea leve; el ruido también molesta."},
            {"role":"agent","text":"¿Has usado analgésicos o triptanos?"},
            {"role":"patient","text":"Solo ibuprofeno; ayuda un poco."},
            {"role":"agent","text":"Perfecto, con eso preparo el reporte."},
        ]
        rules = [
            (1, "Motivo principal", "Cefalea pulsátil lateralizada con fotofobia."),
            (3, "HPI", "Inicio ayer; crisis por horas."),
            (5, "HPI", "Náusea leve y fonofobia."),
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
            {"role":"agent","text":"¿Tos y congestión? ¿desde cuándo?"},
            {"role":"patient","text":"Tos seca desde hace 3 días, nariz tapada."},
            {"role":"agent","text":"¿Dificultad respiratoria o dolor torácico?"},
            {"role":"patient","text":"No, solo cansancio."},
            {"role":"agent","text":"¿Has tomado antipiréticos o antigripales?"},
            {"role":"patient","text":"Paracetamol y un antigripal."},
            {"role":"agent","text":"Listo, prepararé el reporte."},
        ]
        rules = [
            (1, "Motivo principal", "Fiebre, mialgia y malestar."),
            (3, "HPI", "Tos seca y congestión 3 días."),
            (5, "HPI", "Sin disnea ni dolor torácico."),
            (7, "Medicaciones (entrevista)", "Paracetamol y antigripal — automedicación."),
        ]
        faltantes = [
            "Temperatura y saturación O2 documentadas.",
            "Contacto con enfermos y estado de vacunación.",
            "Comorbilidades respiratorias/embarazo."
        ]
        return chat, rules, faltantes

    # malaria
    chat = [
        {"role":"agent","text":"Vamos a registrar tu cuadro febril. ¿Fiebre con escalofríos intermitentes?"},
        {"role":"patient","text":"Sí, viene y va con sudoración."},
        {"role":"agent","text":"¿Viajaste a zona endémica recientemente?"},
        {"role":"patient","text":"Sí, estuve en zona selvática hace 2 semanas."},
        {"role":"agent","text":"¿Cefalea, náusea o dolor muscular?"},
        {"role":"patient","text":"Cefalea y cuerpo cortado."},
        {"role":"agent","text":"¿Tomaste profilaxis antipalúdica?"},
        {"role":"patient","text":"No, no tomé."},
        {"role":"agent","text":"Gracias, prepararé el reporte."},
    ]
    rules = [
        (1, "Motivo principal", "Fiebre intermitente con escalofríos y sudoración."),
        (3, "HPI", "Viaje a zona endémica (2 semanas)."),
        (5, "HPI", "Cefalea y mialgias."),
        (7, "Historia dirigida", "Sin profilaxis antipalúdica."),
    ]
    faltantes = [
        "Frotis gota gruesa / prueba rápida.",
        "Registro horario de fiebre.",
        "Valoración de anemia y esplenomegalia."
    ]
    return chat, rules, faltantes

EHR_BASE = {
    "Historia clínica relevante": ["Antecedente crónico declarado en ficha del paciente"],
    "Medicaciones (EHR)": ["Medicación habitual según expediente (si aplica)"],
}

# ---------------------------
# HELPERS
# ---------------------------
def title(title: str, sub: str = ""):
    st.markdown(f"<div class='h-title'>{title}</div>", unsafe_allow_html=True)
    if sub: st.markdown(f"<div class='h-sub'>{sub}</div>", unsafe_allow_html=True)

def patient_card(p: Patient, selected=False):
    border = "selected" if selected else ""
    st.markdown(f"""
    <div class="select-card {border} card">
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

    def box(title_txt, items):
        st.markdown('<div class="box">', unsafe_allow_html=True)
        st.markdown(f"**{title_txt}:**")
        if isinstance(items, list):
            st.markdown("<ul>"+ "".join([f"<li>{x}</li>" for x in items]) +"</ul>", unsafe_allow_html=True) if items else st.markdown("—")
        else:
            st.markdown(items or "—")
        st.markdown("</div>", unsafe_allow_html=True)

    mp = facts["Motivo principal"][0] if facts["Motivo principal"] else "—"
    box("Motivo principal", mp)
    box("Historia de la enfermedad actual (HPI)", facts["HPI"])
    box("Antecedentes relevantes (EHR)", facts["Historia clínica relevante"])

    st.markdown('<div class="box">', unsafe_allow_html=True)
    st.markdown("**Medicaciones (EHR y entrevista):**")
    meds = []
    meds += [f"<li>{m}</li>" for m in facts["Medicaciones (EHR)"]]
    meds += [f"<li><span class='pill'>{m}</span></li>" for m in facts["Medicaciones (entrevista)"]]
    st.markdown("<ul>"+ "".join(meds) +"</ul>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    utiles = facts["Signos autonómicos"] + facts["Signos oculares"] + facts["Historia dirigida"]
    if utiles: box("Hechos útiles", utiles)

    if idx_limit >= len(rules):
        st.markdown('<div class="box note">', unsafe_allow_html=True)
        st.markdown("**Qué no se cubrió pero sería útil:**")
        for x in get_condition_script(st.session_state.sel_condition)[2]:
            st.markdown(f"- {x}")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# Animación de tipeo (devuelve cuando termina)
def typewriter(placeholder, full_text: str, speed: float = 0.012):
    shown = ""
    for ch in full_text:
        shown += ch
        placeholder.markdown(f"<div class='typing'>{shown}</div>", unsafe_allow_html=True)
        time.sleep(speed)

# ---------------------------
# SIDEBAR
# ---------------------------
st.sidebar.markdown("### Flujo")
st.sidebar.caption("1) Paciente y condición → 2) Introducción → 3) Entrevista y reporte.")
col_sb1, col_sb2 = st.sidebar.columns(2)
with col_sb1:
    if st.button("Reiniciar flujo"):
        st.session_state.step = "select"
        st.session_state.sel_patient = None
        st.session_state.sel_condition = None
        st.session_state.chat_idx = -1
        st.session_state.typing = False
        st.session_state.pause = False
        st.rerun()
with col_sb2:
    if not st.session_state.pause:
        if st.button("⏸ Pausa"):
            st.session_state.pause = True
            st.rerun()
    else:
        if st.button("▶ Reanudar"):
            st.session_state.pause = False
            st.rerun()

# ---------------------------
# STEP: SELECCIÓN
# ---------------------------
if st.session_state.step == "select":
    title("Selecciona un paciente")
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
    title("Explorar una condición", "Selecciona la condición a investigar")
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

# ---------------------------
# STEP: INTRO
# ---------------------------
elif st.session_state.step == "intro":
    p = next(x for x in PACIENTES if x.pid == st.session_state.sel_patient)
    c = next(x for x in CONDICIONES if x.cid == st.session_state.sel_condition)

    l, r = st.columns(2, gap="large")
    with l:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        title("Agente de preconsulta")
        st.markdown("Este asistente guía preguntas clínicas previas a la visita y estructura la información para el médico.")
        st.markdown('</div>', unsafe_allow_html=True)
    with r:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        title(f"Persona del paciente: {p.nombre}", f"{p.edad} años • {p.sexo} • Condición de base: {p.condicion_base}")
        st.markdown("Se incluye información de contexto del paciente para orientar la entrevista.")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<hr class="section"/>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1.2, 1.2, 2.6], gap="large")
    with c1:
        if st.button("◀ Volver", use_container_width=True):
            st.session_state.step = "select"; st.rerun()
    with c2:
        if st.button("Comenzar entrevista", use_container_width=True):
            st.session_state.step = "convo"
            st.session_state.chat_idx = -1
            st.session_state.typing = False
            st.session_state.pause = False
            st.rerun()
    with c3:
        st.caption(f"Condición: **{c.titulo}** — {c.descripcion}")

    # Instrucciones de uso
    st.markdown('<hr class="section"/>', unsafe_allow_html=True)
    with st.expander("¿Cómo usarlo?"):
        st.markdown("""
1. Elige **paciente** y **condición**.  
2. Inicia la **entrevista**: los mensajes aparecen **automáticamente** (puedes **pausar**/**reanudar** desde la barra lateral).  
3. El **reporte** a la derecha se **actualiza en tiempo real** con el motivo principal, HPI, antecedentes, medicaciones y hechos útiles.  
4. Al final verás elementos **aún no cubiertos** que conviene medir o preguntar.

**Integración operativa (visión TESSENA):**  
- Validación y referencia cruzada con **COFEPRIS**, **FDA** y **OpenDrugs** para guías y alertas de medicamentos.  
- Acceso federado a datos clínicos (FHIR) y señales de **Amazon HealthLake**.  
- Razonamiento clínico con modelos de lenguaje y **MedGemma** para estructurar resúmenes y planes.  
- Todo bajo trazabilidad, controles de acceso y registro de auditoría.
        """)

# ---------------------------
# STEP: CONVERSACIÓN + REPORTE
# ---------------------------
elif st.session_state.step == "convo":
    chat, rules, _faltantes = get_condition_script(st.session_state.sel_condition)

    top_l, top_r = st.columns([2.5, 1.5], gap="large")
    with top_l:
        title("Entrevista simulada", "Mensajes automáticos con animación de tipeo")
    with top_r:
        a, b, c3 = st.columns(3)
        with a:
            if st.button("◀ Volver", use_container_width=True):
                st.session_state.step = "intro"; st.rerun()
        with b:
            if st.button("🔁 Reiniciar", use_container_width=True):
                st.session_state.chat_idx = -1
                st.session_state.typing = False
                st.session_state.pause = False
                st.rerun()
        with c3:
            if not st.session_state.pause:
                if st.button("⏸ Pausa", use_container_width=True):
                    st.session_state.pause = True; st.rerun()
            else:
                if st.button("▶ Reanudar", use_container_width=True):
                    st.session_state.pause = False; st.rerun()

    st.markdown('<hr class="section"/>', unsafe_allow_html=True)

    chat_col, report_col = st.columns([1.3, 1.0], gap="large")

    # --- CHAT (auto con typewriter) ---
    with chat_col:
        st.markdown('<div class="chatwrap">', unsafe_allow_html=True)

        # Renderizar completos los anteriores al actual
        for i in range(st.session_state.chat_idx + 1):
            role = chat[i]["role"]
            klass = "agent" if role == "agent" else "patient"
            who = "Asistente" if role == "agent" else "Paciente"
            txt = chat[i]["text"]
            st.markdown(f"<div class='msg {klass}'><b>{who}:</b> {txt}<br><small>{datetime.now().strftime('%H:%M')}</small></div>", unsafe_allow_html=True)

        # Si hay uno nuevo por tipear…
        next_idx = st.session_state.chat_idx + 1
        if next_idx < len(chat):
            if not st.session_state.pause:
                role = chat[next_idx]["role"]
                klass = "agent" if role == "agent" else "patient"
                who = "Asistente" if role == "agent" else "Paciente"

                st.markdown(f"<div class='msg {klass}'><b>{who}:</b> ", unsafe_allow_html=True)
                ph = st.empty()
                st.markdown("<small>"+datetime.now().strftime("%H:%M")+"</small></div>", unsafe_allow_html=True)

                # animación de tipeo
                st.session_state.typing = True
                typewriter(ph, chat[next_idx]["text"], speed=0.012)
                st.session_state.typing = False

                # Al terminar, avanzamos el índice y rerun para continuar con el siguiente
                st.session_state.chat_idx = next_idx
                time.sleep(0.25)
                st.rerun()
            else:
                # Pausado: mostrar placeholder del próximo turno
                role = chat[next_idx]["role"]
                klass = "agent" if role == "agent" else "patient"
                who = "Asistente" if role == "agent" else "Paciente"
                st.markdown(f"<div class='msg {klass}'><b>{who}:</b> <span class='small'>[Pausado]</span></div>", unsafe_allow_html=True)
        else:
            st.success("Entrevista completa. El reporte quedó consolidado.")

        st.markdown('</div>', unsafe_allow_html=True)

    # --- REPORTE DINÁMICO ---
    with report_col:
        render_report(st.session_state.chat_idx, rules)

    st.markdown('<hr class="section"/>', unsafe_allow_html=True)
    with st.expander("Notas sobre calidad y completitud"):
        st.markdown("""
El reporte resalta **hechos útiles** y señala **datos faltantes** que conviene capturar para mejorar la calidad clínica.
""")
