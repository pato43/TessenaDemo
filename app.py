# ===================== Agente de Preconsulta — ES·MX (PARTE 1/2) =====================
# UI moderna, tema adaptable (claro/oscuro), selección de paciente/condición e introducción.
# Esta parte NO tiene filtros de búsqueda; selección directa con tarjetas.
# La PARTE 2 añade: conversación automática + reporte clínico dinámico.

import streamlit as st
from streamlit.components.v1 import html as st_html
from dataclasses import dataclass
from typing import List
from datetime import datetime

st.set_page_config(
    page_title="Agente de Preconsulta",
    layout="wide",
    page_icon="🩺",
    initial_sidebar_state="expanded",
)

# ------------------------- Estado -------------------------
if "step" not in st.session_state: st.session_state.step = "select"   # select → intro → convo
if "sel_patient" not in st.session_state: st.session_state.sel_patient = None
if "sel_condition" not in st.session_state: st.session_state.sel_condition = None
if "chat_idx" not in st.session_state: st.session_state.chat_idx = -1
if "pause" not in st.session_state: st.session_state.pause = False

# ------------------------- Datos base ----------------------
@dataclass
class Patient:
    pid: str; nombre: str; edad: int; sexo: str; condicion_base: str; img: str = ""

@dataclass
class Condition:
    cid: str; titulo: str; descripcion: str

PACIENTES: List[Patient] = [
    Patient("nvelarde", "Nicolás Velarde", 34, "Masculino", "Trastorno de ansiedad"),
    Patient("aduarte",   "Amalia Duarte",   62, "Femenino",  "Diabetes tipo 2"),
    Patient("szamora",   "Sofía Zamora",    23, "Femenino",  "Asma"),
]
CONDICIONES: List[Condition] = [
    Condition("flu", "Gripe", "Infección viral con fiebre, mialgia y fatiga."),
    Condition("mal", "Malaria", "Fiebre intermitente con escalofríos (vector: mosquito)."),
    Condition("mig", "Migraña", "Cefalea pulsátil lateralizada, foto/fonofobia; posible náusea."),
    Condition("ss",  "Síndrome serotoninérgico", "Exceso de serotonina (p. ej., ISRS + dextrometorfano)."),
]

# ------------------------- Estilos (no se “cuelan”) ----------------------
# Inyectamos CSS con components y altura 0 para evitar que se vea texto en pantalla.
CSS = """
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800;900&display=swap" rel="stylesheet">
<style>
:root{
  --bg:#f7f8fb; --card:#ffffff; --text:#0f172a; --muted:#6b7280; --border:#e5e7eb;
  --primary:#7c3aed; --accent:#22d3ee; --ok:#10b981; --warn:#f59e0b;
  --chipbg:#eef2ff; --chipfg:#4f46e5; --agent:#eef2ff; --patient:#f3f4f6;
  --glass:linear-gradient(180deg,rgba(255,255,255,.8),rgba(255,255,255,.7));
}
@media (prefers-color-scheme: dark){
  :root{
    --bg:#0B1220; --card:#11182A; --text:#EAF2FF; --muted:#9EB0CC; --border:#203049;
    --primary:#7c3aed; --accent:#22d3ee; --ok:#34d399; --warn:#fbbf24;
    --chipbg:#0f1a2c; --chipfg:#8ab6ff; --agent:#0f1a2c; --patient:#0F172A;
    --glass:linear-gradient(180deg,rgba(17,24,42,.68),rgba(17,24,42,.58));
  }
}
html, body, [class*="css"]{
  background:var(--bg) !important; color:var(--text) !important;
  font-family:Inter,system-ui,-apple-system,Segoe UI,Roboto,Helvetica Neue,Arial,sans-serif;
  font-size:16.5px; line-height:1.35;
}
header{ visibility:hidden; }
.block-container{ padding-top:.6rem; }

/* Topbar compacto (sin rectángulo gigantesco) */
.topbar{
  position:sticky; top:0; z-index:20;
  padding:10px 14px; margin:0 0 14px 0;
  background:var(--glass);
  backdrop-filter: blur(8px);
  border:1px solid var(--border); border-radius:14px;
  display:flex; align-items:center; justify-content:space-between; gap:14px;
  box-shadow: 0 10px 28px rgba(0,0,0,.08);
}
.brand{ font-weight:900; letter-spacing:.3px; display:flex; align-items:center; gap:8px; }
.spark{
  width:12px;height:12px;border-radius:999px;background:conic-gradient(var(--primary),var(--accent));
  box-shadow:0 0 0 2px #00000010;
}
.kpis{ display:flex; gap:8px; flex-wrap:wrap; align-items:center; }
.badge{
  display:inline-flex; align-items:center; gap:8px;
  border-radius:999px; padding:6px 10px; background:var(--chipbg); color:var(--chipfg);
  border:1px solid var(--border); font-weight:800; font-size:.8rem;
}

/* Stepper */
.stepper{ display:flex; gap:10px; align-items:center; }
.step{ padding:6px 10px; border-radius:999px; border:1px solid var(--border); background:var(--card); font-weight:700; font-size:.85rem; }
.step.active{ border-color:#c7d2fe; box-shadow:0 0 0 3px #e0e7ff66 inset; }
.dot{ width:6px; height:6px; border-radius:999px; background:var(--muted); opacity:.6; }

/* Secciones y separadores */
.card{ background:var(--card); border:1px solid var(--border); border-radius:16px; padding:16px; }
.card.soft{ background:linear-gradient(180deg,var(--card),rgba(0,0,0,0)); }
.sep{ height:1px; border:none; margin:12px 0 16px; background:linear-gradient(90deg,var(--primary),var(--accent)); border-radius:2px; }

.h-title{ font-weight:900; font-size:1.55rem; margin:0 0 6px; }
.h-sub{ color:var(--muted); font-weight:600; }
.small{ color:var(--muted); font-size:.92rem; }

/* Tarjetas seleccionables */
.select-card{ border-radius:16px; border:2px solid transparent; transition:.18s ease; cursor:pointer; }
.select-card:hover{ transform:translateY(-1px); box-shadow:0 16px 34px rgba(0,0,0,.12); }
.select-card.selected{ border-color:#c7d2fe; box-shadow:0 0 0 3px #e0e7ff66 inset; }

/* Placeholder imagen paciente */
.ph-img{
  height:190px; border-radius:12px; display:flex; align-items:center; justify-content:center;
  background:radial-gradient(ellipse at top,var(--patient),transparent 60%), var(--patient);
  color:var(--muted);
}

/* Botones */
.stButton > button{ border:none; border-radius:12px; padding:10px 14px; font-weight:800; color:#fff; background:var(--primary); }
.stButton > button:hover{ filter:brightness(.95); }
.btn-ghost{ border:1px solid var(--border) !important; background:transparent !important; color:var(--muted) !important; }

/* Grid utilitario */
.grid{ display:grid; gap:16px; grid-template-columns: repeat(12, 1fr); }
.col-12{ grid-column: span 12; } .col-6{ grid-column: span 6; } .col-4{ grid-column: span 4; }
@media (max-width:1100px){ .col-6{ grid-column: span 12; } .col-4{ grid-column: span 6; } }
</style>
"""
st_html(CSS, height=0, scrolling=False)  # <- no imprime nada

# ------------------------- Helpers UI ----------------------
def title(txt: str, sub: str = ""):
    st.markdown(f"<div class='h-title'>{txt}</div>", unsafe_allow_html=True)
    if sub:
        st.markdown(f"<div class='h-sub'>{sub}</div>", unsafe_allow_html=True)

def topbar():
    now = datetime.now().strftime("%d %b %Y • %H:%M")
    st.markdown(
        f"""
        <div class="topbar">
          <div class="brand"><span class="spark"></span>Agente de Preconsulta</div>
          <div class="kpis">
            <span class="badge">ES • MX</span>
            <span class="badge">Previo a consulta</span>
            <span class="badge">{now}</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def stepper(current: str):
    steps = [("select", "Paciente y condición"), ("intro", "Introducción"), ("convo", "Entrevista y reporte")]
    marks = []
    for key, label in steps:
        cls = "step active" if key == current else "step"
        marks.append(f"<span class='{cls}'>{label}</span>")
        if key != steps[-1][0]: marks.append("<span class='dot'></span>")
    st.markdown("<div class='stepper'>"+"".join(marks)+"</div>", unsafe_allow_html=True)

def patient_card(p: Patient, selected=False):
    sel = "selected" if selected else ""
    st.markdown(
        f"""
        <div class="select-card {sel} card">
          <div class="ph-img">Imagen del paciente</div>
          <div style="margin-top:10px"><span class="badge">Expediente Clínico Sintético (FHIR)</span></div>
          <div style="font-weight:900;margin-top:8px">{p.nombre}</div>
          <div class="small">{p.edad} años • {p.sexo}</div>
          <div class="small">Condición de base: {p.condicion_base}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def condition_card(c: Condition, selected=False):
    sel = "selected" if selected else ""
    st.markdown(
        f"""
        <div class="select-card {sel} card">
          <div style="font-weight:900;margin-bottom:6px">{c.titulo}</div>
          <div class="small">{c.descripcion}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ------------------------- Topbar + Stepper -----------------
topbar()
stepper(st.session_state.step)
st.markdown('<hr class="sep">', unsafe_allow_html=True)

# ------------------------- Sidebar -------------------------
st.sidebar.markdown("### Controles")
c1, c2 = st.sidebar.columns(2)
with c1:
    if st.button("Reiniciar"):
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
st.sidebar.markdown("---")
st.sidebar.caption("Flujo: 1) Selecciona paciente y condición • 2) Revisa la introducción • 3) Entrevista automática con reporte.")

# ------------------------- STEP: SELECT ---------------------
if st.session_state.step == "select":
    # Encabezado bonito sin filtros
    title("Selecciona un paciente")
    st.markdown('<hr class="sep">', unsafe_allow_html=True)

    cols = st.columns(3, gap="large")
    for i, p in enumerate(PACIENTES):
        with cols[i]:
            selected = (st.session_state.sel_patient == p.pid)
            patient_card(p, selected)
            # Botón principal
            label = "Seleccionado" if selected else "Elegir"
            key = f"pick_{p.pid}"
            if st.button(label, key=key, use_container_width=True):
                st.session_state.sel_patient = p.pid
                st.rerun()

    st.markdown('<hr class="sep">', unsafe_allow_html=True)
    title("Explora una condición", "Escoge la condición a indagar en la entrevista")
    cols2 = st.columns(2, gap="large")
    for i, c in enumerate(CONDICIONES):
        with cols2[i % 2]:
            selected = (st.session_state.sel_condition == c.cid)
            condition_card(c, selected)
            label = "Seleccionada" if selected else "Elegir"
            key = f"cond_{c.cid}"
            if st.button(label, key=key, use_container_width=True):
                st.session_state.sel_condition = c.cid
                st.rerun()

    st.markdown('<hr class="sep">', unsafe_allow_html=True)
    CTA1, CTA2, CTA3 = st.columns([1.1, 1.1, 2.8], gap="large")
    with CTA1:
        can_go = st.session_state.sel_patient and st.session_state.sel_condition
        if st.button("Continuar", disabled=not can_go, use_container_width=True):
            st.session_state.step = "intro"; st.rerun()
    with CTA2:
        if st.button("Volver a inicio", use_container_width=True):
            st.session_state.sel_patient = None
            st.session_state.sel_condition = None
            st.rerun()
    with CTA3:
        if st.session_state.sel_patient and st.session_state.sel_condition:
            p = next(x for x in PACIENTES if x.pid == st.session_state.sel_patient)
            c = next(x for x in CONDICIONES if x.cid == st.session_state.sel_condition)
            st.markdown(
                f"<span class='badge'>Paciente: {p.nombre}</span> &nbsp; "
                f"<span class='badge'>Condición: {c.titulo}</span>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown("<span class='small'>Selecciona paciente y condición para continuar.</span>", unsafe_allow_html=True)

# ------------------------- STEP: INTRO ----------------------
elif st.session_state.step == "intro":
    # Datos seleccionados
    p = next(x for x in PACIENTES if x.pid == st.session_state.sel_patient)
    c = next(x for x in CONDICIONES if x.cid == st.session_state.sel_condition)

    L, R = st.columns(2, gap="large")
    with L:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        title("Agente de preconsulta")
        st.markdown("Asiste en la **recolección clínica previa** a la visita y estructura un **resumen útil** para el profesional de salud.")
        st.markdown(
            "<div class='kpis' style='margin-top:8px'>"
            "<span class='badge'>Guía clínica</span>"
            "<span class='badge'>Registro EHR (FHIR)</span>"
            "<span class='badge'>Resumen estructurado</span>"
            "</div>", unsafe_allow_html=True
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with R:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        title(f"Paciente: {p.nombre}", f"{p.edad} años • {p.sexo} • Condición de base: {p.condicion_base}")
        st.markdown("<div class='ph-img' style='height:160px;margin-top:6px'>Imagen del paciente</div>", unsafe_allow_html=True)
        st.markdown("<div class='small' style='margin-top:8px'>El asistente considera el contexto para orientar la entrevista.</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<hr class="sep">', unsafe_allow_html=True)
    st.markdown('<div class="card soft">', unsafe_allow_html=True)
    title("¿Cómo usarlo?")
    st.markdown("""
1. Confirma **paciente** y **condición**.  
2. Pulsa **Iniciar entrevista**: los mensajes aparecerán **automáticamente**; puedes **pausar/reanudar** desde la barra lateral.  
3. El **reporte** se actualizará en paralelo (Motivo, HPI, antecedentes, medicaciones y hechos útiles).  
4. Se sugerirán **datos faltantes** deseables para mejorar la calidad clínica.
""")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<hr class="sep">', unsafe_allow_html=True)
    B1, B2, B3 = st.columns([1.1, 1.1, 2.8], gap="large")
    with B1:
        if st.button("◀ Regresar", use_container_width=True):
            st.session_state.step = "select"; st.rerun()
    with B2:
        if st.button("Iniciar entrevista", use_container_width=True):
            st.session_state.step = "convo"
            st.session_state.chat_idx = -1
            st.session_state.pause = False
            st.rerun()
    with B3:
        st.markdown(
            f"<span class='badge'>Paciente: {p.nombre}</span> &nbsp; "
            f"<span class='badge'>Condición: {c.titulo}</span> &nbsp; "
            f"<span class='badge'>Conversación guiada</span>",
            unsafe_allow_html=True,
        )

# ------------------------- (Fin PARTE 1/2) ------------------
# La PARTE 2/2 agregará la entrevista con animación typewriter y el reporte.
# ===================== PARTE 2/2 — Conversación automática + Reporte =====================

def script_ss():
    chat = [
        ("agent","Gracias por agendar. Te haré preguntas breves para preparar tu visita. ¿Cuál es tu principal molestia hoy?"),
        ("patient","Me siento muy agitado e inquieto; también algo confundido."),
        ("agent","¿Desde cuándo? ¿inicio súbito o progresivo?"),
        ("patient","Empezó hace dos días, de golpe."),
        ("agent","¿Has notado fiebre, sudoración, escalofríos o rigidez muscular?"),
        ("patient","Sí, sudo mucho, tiritas a veces y siento los músculos rígidos."),
        ("agent","¿Percibes cambios visuales o movimientos oculares extraños?"),
        ("patient","Mis pupilas se ven grandes y se mueven raro."),
        ("agent","¿Tomaste o cambiaste medicamentos, jarabes o suplementos en los últimos días?"),
        ("patient","Uso fluoxetina diario y anoche tomé jarabe con dextrometorfano."),
        ("agent","¿Consumiste alcohol, estimulantes o drogas recreativas recientemente?"),
        ("patient","No, nada."),
        ("agent","¿Náusea, diarrea o vómito?"),
        ("patient","Náusea leve, sin diarrea ni vómito."),
        ("agent","¿Problemas para dormir o inquietud extrema?"),
        ("patient","Sí, casi no pude dormir."),
        ("agent","Gracias, con esto elaboro reporte para tu médico."),
    ]
    rules = [
        (1,"Motivo principal","Agitación, inquietud y confusión."),
        (3,"HPI","Inicio súbito hace ~2 días; insomnio."),
        (5,"Signos autonómicos","Diaforesis, escalofríos, rigidez."),
        (7,"Signos oculares","Midriasis y movimientos oculares anómalos."),
        (9,"Medicaciones (EHR)","Fluoxetina (ISRS) — uso crónico."),
        (9,"Medicaciones (entrevista)","Dextrometorfano — uso reciente."),
        (11,"Historia dirigida","Niega alcohol/estimulantes."),
        (13,"HPI","Náusea leve; sin diarrea ni vómito."),
    ]
    faltantes = [
        "Signos vitales: temperatura, FC, TA.",
        "Exploración neuromuscular: hiperreflexia, mioclonías, rigidez.",
        "Historial preciso de medicaciones (fechas/dosis).",
    ]
    return chat, rules, faltantes

def script_mig():
    chat = [
        ("agent","Vamos a caracterizar tu cefalea. ¿Dónde se localiza y cómo la describirías?"),
        ("patient","Late del lado derecho; la luz me molesta."),
        ("agent","¿Desde cuándo y cuánto dura cada episodio?"),
        ("patient","Desde ayer; duran varias horas."),
        ("agent","¿Náusea, vómito o sensibilidad a ruidos/olores?"),
        ("patient","Náusea leve; el ruido empeora el dolor."),
        ("agent","¿Dormiste menos o consumiste cafeína tarde?"),
        ("patient","Dormí poco y tomé café muy tarde."),
        ("agent","¿Has tomado analgésicos o triptanos antes?"),
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
    faltantes = [
        "Frecuencia mensual y escala de dolor.",
        "Pruebas/uso previo de triptanos.",
        "Desencadenantes (estrés, ayuno, ciclo, etc.).",
    ]
    return chat, rules, faltantes

def script_flu():
    chat = [
        ("agent","Vamos a documentar tus síntomas respiratorios. ¿Tienes fiebre o dolor corporal?"),
        ("patient","Sí, fiebre y cuerpo cortado."),
        ("agent","¿Tos/congestión? ¿desde cuándo?"),
        ("patient","Tos seca hace 3 días y nariz tapada."),
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
    faltantes = [
        "Temperatura y saturación O₂ documentadas.",
        "Factores de riesgo (edad, comorbilidades).",
        "Prueba diagnóstica según criterio clínico.",
    ]
    return chat, rules, faltantes

def script_mal():
    chat = [
        ("agent","Vamos a registrar tu cuadro febril. ¿La fiebre aparece con escalofríos intermitentes?"),
        ("patient","Sí, viene y va con sudoración."),
        ("agent","¿Viajaste a zona endémica recientemente?"),
        ("patient","Sí, estuve en selva hace dos semanas."),
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
    faltantes = [
        "Prueba rápida/frotis para confirmar.",
        "Patrón horario de la fiebre.",
        "Valoración de anemia y esplenomegalia.",
    ]
    return chat, rules, faltantes

SCRIPTS = {"ss": script_ss, "mig": script_mig, "flu": script_flu, "mal": script_mal}

EHR_BASE = {
    "Historia clínica relevante": ["Antecedente crónico declarado en ficha del paciente"],
    "Medicaciones (EHR)": ["Medicación habitual según expediente (si aplica)"],
}

def _collect_facts(idx_limit, rules):
    facts = {
        "Motivo principal": [], "HPI": [],
        "Historia clínica relevante": EHR_BASE["Historia clínica relevante"].copy(),
        "Medicaciones (EHR)": EHR_BASE["Medicaciones (EHR)"].copy(),
        "Medicaciones (entrevista)": [], "Signos autonómicos": [],
        "Signos oculares": [], "Historia dirigida": [],
    }
    for i_lim, kind, txt in rules:
        if idx_limit >= i_lim: facts[kind].append(txt)
    return facts

def render_report(idx_limit, rules):
    facts = _collect_facts(idx_limit, rules)

    def box(t, items):
        st.markdown('<div class="card" style="margin-bottom:10px">', unsafe_allow_html=True)
        st.markdown(f"**{t}:**", unsafe_allow_html=True)
        if isinstance(items, list):
            st.markdown("<ul>"+ "".join([f"<li>{x}</li>" for x in items]) +"</ul>" if items else "—", unsafe_allow_html=True)
        else:
            st.markdown(items or "—", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    box("Motivo principal", (facts["Motivo principal"][0] if facts["Motivo principal"] else "—"))
    box("Historia de la enfermedad actual (HPI)", facts["HPI"])
    box("Antecedentes relevantes (EHR)", facts["Historia clínica relevante"])

    st.markdown('<div class="card" style="margin-bottom:10px">', unsafe_allow_html=True)
    st.markdown("**Medicaciones (EHR y entrevista):**", unsafe_allow_html=True)
    meds = [f"<li>{m}</li>" for m in facts["Medicaciones (EHR)"]]
    meds += [f"<li><span class='badge'>{m}</span></li>" for m in facts["Medicaciones (entrevista)"]]
    st.markdown("<ul>"+ "".join(meds) +"</ul>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    utiles = facts["Signos autonómicos"] + facts["Signos oculares"] + facts["Historia dirigida"]
    if utiles: box("Hechos útiles", utiles)

    if idx_limit >= len(rules):
        falt = SCRIPTS[st.session_state.sel_condition]()[2]
        st.markdown('<div class="card" style="border:1px solid #fde68a;background:#fffbeb;">', unsafe_allow_html=True)
        st.markdown("**Qué no se cubrió pero sería útil:**", unsafe_allow_html=True)
        for x in falt: st.markdown(f"- {x}", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

def typewriter(placeholder, text, speed=0.012):
    out = ""
    for ch in text:
        out += ch
        placeholder.markdown(f"<div class='typing'>{out}</div>", unsafe_allow_html=True)
        time.sleep(speed)

if st.session_state.step == "convo":
    chat, rules, _ = SCRIPTS[st.session_state.sel_condition]()
    p = next(x for x in PACIENTES if x.pid == st.session_state.sel_patient)
    c = next(x for x in CONDICIONES if x.cid == st.session_state.sel_condition)

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
    chat_col, rep_col = st.columns([1.4, 1.0], gap="large")

    with chat_col:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        for i in range(st.session_state.chat_idx + 1):
            role, txt = chat[i]
            who = "Asistente" if role == "agent" else "Paciente"
            klass = "agent" if role == "agent" else "patient"
            st.markdown(
                f"<div class='msg {klass}'><b>{who}:</b> {txt}<br><small>{datetime.now().strftime('%H:%M')}</small></div>",
                unsafe_allow_html=True,
            )

        next_idx = st.session_state.chat_idx + 1
        if next_idx < len(chat):
            role, txt = chat[next_idx]
            who = "Asistente" if role == "agent" else "Paciente"
            klass = "agent" if role == "agent" else "patient"

            if not st.session_state.pause:
                st.markdown(f"<div class='msg {klass}'><b>{who}:</b> ", unsafe_allow_html=True)
                ph = st.empty()
                st.markdown("<small>"+datetime.now().strftime("%H:%M")+"</small></div>", unsafe_allow_html=True)
                typewriter(ph, txt, speed=0.012)
                st.session_state.chat_idx = next_idx
                time.sleep(0.15)
                st.rerun()
            else:
                st.markdown(f"<div class='msg {klass}'><b>{who}:</b> <span class='small'>[Pausado]</span></div>", unsafe_allow_html=True)
        else:
            st.success("Entrevista completa. El reporte quedó consolidado.")
        st.markdown('</div>', unsafe_allow_html=True)

    with rep_col:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        title("Reporte generado", f"Paciente: {p.nombre} • Condición: {c.titulo}")
        render_report(st.session_state.chat_idx, rules)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<hr class="sep">', unsafe_allow_html=True)
    with st.expander("Notas y recomendaciones"):
        st.markdown("""
- El reporte prioriza **Motivo**, **HPI**, **antecedentes EHR** y **medicaciones**.
- **Hechos útiles** resalta señales clave emergentes.
- **Faltantes** sugiere información para mejorar calidad clínica.
""")
