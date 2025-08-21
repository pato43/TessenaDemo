import streamlit as st
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
import textwrap

st.set_page_config(
    page_title="Agente de Preconsulta",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estado
DEFAULTS = dict(
    step="select",
    sel_patient=None,
    sel_condition=None,
    chat_idx=-1,
    pause=False,
    theme_name="Indigo Pro",
    density="Normal",                 # Compacto / Normal / Amplio
    radius="Large",                  # Small / Medium / Large
    contrast=0.08,                   # 0 - 0.18
    anim_on=True,
    agent_typing_speed=0.018,
    patient_thinking_delay=1.0,
    patient_typing_speed=0.022,
    show_timestamps=True,
    notes="",
    convo_enabled=False,             # lo activa la Parte 2
)
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# Datos
@dataclass
class Patient:
    pid: str
    nombre: str
    edad: int
    sexo: str
    condicion_base: str

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
    Condition("flu", "Gripe", "Fiebre, mialgia, congestión y fatiga."),
    Condition("mal", "Malaria", "Fiebre intermitente; antecedente de viaje a zona endémica."),
    Condition("mig", "Migraña", "Cefalea pulsátil lateralizada con foto/fonofobia, náusea."),
    Condition("ss",  "Síndrome serotoninérgico", "Exceso de serotonina (p. ej., ISRS + dextrometorfano)."),
]

# Paletas profesionales
THEMES = {
    "Indigo Pro": {
        "primary": "#4F46E5", "accent": "#06B6D4",
        "bg_top": "#0B1220", "bg_mid": "#0D1324", "bg_card": "#0F172A",
        "muted": "#A3B3D2", "text": "#EAF2FF", "border": "#1E2B46",
        "grad_a": "linear-gradient(90deg, #4F46E5, #06B6D4)",
    },
    "Teal Mint": {
        "primary": "#0EA5A4", "accent": "#22D3EE",
        "bg_top": "#061A1A", "bg_mid": "#082021", "bg_card": "#0D2A2B",
        "muted": "#9ED9DD", "text": "#E6FAFB", "border": "#1C3C3D",
        "grad_a": "linear-gradient(90deg, #0EA5A4, #22D3EE)",
    },
    "Plum Gold": {
        "primary": "#7C3AED", "accent": "#F59E0B",
        "bg_top": "#120C1D", "bg_mid": "#141027", "bg_card": "#181233",
        "muted": "#CBB8F7", "text": "#F4EEFF", "border": "#2A1D55",
        "grad_a": "linear-gradient(90deg, #7C3AED, #F59E0B)",
    },
    "Slate Blue": {
        "primary": "#2563EB", "accent": "#60A5FA",
        "bg_top": "#0B1120", "bg_mid": "#0C1426", "bg_card": "#0F1B35",
        "muted": "#9CB6E6", "text": "#E8F1FF", "border": "#1A2A4B",
        "grad_a": "linear-gradient(90deg, #2563EB, #60A5FA)",
    },
}

def _radius_token(size: str) -> str:
    return {"Small":"10px","Medium":"14px","Large":"18px"}.get(size, "18px")

def _density_tokens(mode: str):
    if mode == "Compacto":
        return ("0.35rem","0.6rem", "10px", "10px")
    if mode == "Amplio":
        return ("1.0rem","1.6rem", "18px", "16px")
    return ("0.6rem","1.0rem", "14px", "12px")  # Normal

def inject_css():
    t = THEMES[st.session_state.theme_name]
    pad_top, pad_bottom, pad_card, pad_btn = _density_tokens(st.session_state.density)
    radius = _radius_token(st.session_state.radius)
    contrast = st.session_state.contrast
    st.markdown(
        f"""
<style>
:root {{
  --bg-top: {t['bg_top']};
  --bg-mid: {t['bg_mid']};
  --bg-card: {t['bg_card']};
  --text: {t['text']};
  --muted: {t['muted']};
  --border: {t['border']};
  --primary: {t['primary']};
  --accent: {t['accent']};
  --grad-a: {t['grad_a']};
  --radius: {radius};
  --pad-card: {pad_card};
  --pad-btn: {pad_btn};
  --elev-1: 0 8px 26px rgba(0,0,0,{0.16+contrast});
  --elev-2: 0 12px 36px rgba(0,0,0,{0.22+contrast});
  --line: 1px solid {t['border']};
}}
html, body, [class*="css"] {{
  background: radial-gradient(80% 100% at 50% 0%, var(--bg-top) 0%, var(--bg-mid) 60%, var(--bg-mid) 100%) !important;
  color: var(--text) !important;
  font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif;
  font-size: 16px; line-height: 1.38;
}}
header {{ visibility: hidden; }}
.block-container {{ padding-top: {pad_top}; padding-bottom: {pad_bottom}; max-width: 1200px; }}
section.main > div {{ padding-top: 0 !important; }}

.topbar {{
  position: sticky; top: 0; z-index: 30;
  display: flex; align-items: center; justify-content: space-between; gap: 12px;
  background: color-mix(in oklab, var(--bg-card) 86%, #000 14%);
  border: var(--line); border-radius: var(--radius);
  padding: 10px 14px; box-shadow: var(--elev-1);
}}
.brand {{ display:flex; align-items:center; gap:10px; font-weight:900; letter-spacing:.2px; }}
.brand-badge {{
  width: 36px; height: 36px; border-radius: 12px;
  background: var(--grad-a);
  box-shadow: inset 0 0 0 4px rgba(255,255,255,.06), 0 0 0 1px rgba(255,255,255,.06), var(--elev-1);
}}
.kpis {{ display:flex; gap:8px; flex-wrap:wrap; align-items:center; }}
.badge {{
  display:inline-flex; align-items:center; gap:6px; border-radius: 999px; padding: 6px 10px;
  background: color-mix(in oklab, var(--bg-card) 92%, #fff 8%);
  color: var(--text); border: var(--line); font-weight: 800; font-size: .82rem;
}}

.stepper {{ display:flex; gap:8px; align-items:center; flex-wrap:wrap; margin-top: 6px; }}
.step {{
  padding:8px 12px; border-radius: 12px; border: var(--line); background: var(--bg-card);
  font-weight:800; font-size:.86rem; position:relative; overflow:hidden; transition: transform .12s ease, box-shadow .12s ease;
}}
.step::before {{
  content:""; position:absolute; inset:auto auto 0 0; height:3px; width:100%;
  background: var(--grad-a); opacity:.35;
}}
.step.active {{ box-shadow: inset 0 0 0 3px rgba(255,255,255,.04), var(--elev-1); transform: translateY(-1px); border-color: #3b82f633; }}
.dot {{ width:7px; height:7px; border-radius:999px; background: var(--muted); opacity:.6; }}

.sep {{
  height: 1px; border: none; margin: 10px 0 12px;
  background: linear-gradient(90deg, transparent, color-mix(in oklab, var(--primary) 70%, var(--accent) 30%), transparent);
}}

.h-title {{ font-weight:900; font-size: clamp(1.2rem, 1.1rem + 0.6vw, 1.6rem); margin:0 0 4px; letter-spacing:.15px; }}
.h-sub {{ color: var(--muted); font-weight: 600; margin-bottom: 2px; }}

.card {{
  background: color-mix(in oklab, var(--bg-card) 96%, #000 4%);
  border: var(--line); border-radius: var(--radius); padding: var(--pad-card);
  box-shadow: var(--elev-1);
}}
.soft {{ background: color-mix(in oklab, var(--bg-card) 88%, #fff 12%); }}

.select-card {{
  position:relative; border-radius: calc(var(--radius) + 2px);
  border: 2px solid transparent; cursor: pointer;
  background: linear-gradient(var(--bg-card), var(--bg-card)) padding-box, var(--grad-a) border-box;
  transition: transform .12s ease, box-shadow .12s ease;
}}
.select-card:hover {{ transform: translateY(-1px); box-shadow: var(--elev-2); }}
.select-card.selected {{ box-shadow: inset 0 0 0 4px #ffffff14, var(--elev-2); }}

.card-title {{ font-weight:800; font-size: 1.02rem; margin: 6px 0 2px; }
.card-sub {{ color: var(--muted); font-size:.92rem; }

.ph-img {{
  height: 120px; border-radius: calc(var(--radius) - 2px); display:flex; align-items:center; justify-content:center;
  background: repeating-linear-gradient(135deg, rgba(255,255,255,.06) 0 10px, rgba(255,255,255,.02) 10px 20px);
  border: 1px dashed color-mix(in oklab, var(--border) 80%, #fff 20%); color: var(--muted);
}}

.kit-chips { display:flex; gap:6px; flex-wrap:wrap; }
.chip {
  display:inline-flex; align-items:center; gap:6px; padding:5px 9px; border-radius: 999px;
  background: color-mix(in oklab, var(--bg-card) 94%, #fff 6%);
  border: var(--line); font-weight: 800; font-size: .80rem;
}

.grid { display:grid; gap:12px; grid-template-columns: repeat(12, 1fr); }
.col-12{ grid-column: span 12; } .col-10{ grid-column: span 10; } .col-8{ grid-column: span 8; }
.col-6{ grid-column: span 6; }  .col-4{ grid-column: span 4; }  .col-3{ grid-column: span 3; }
@media (max-width:1200px){ .col-6{grid-column:span 12} .col-4{grid-column:span 6} .col-3{grid-column:span 6} }

.stButton > button{
  border: none; border-radius: var(--radius); padding: var(--pad-btn) calc(var(--pad-btn) + 6px);
  font-weight: 900; color: #fff; background: var(--primary); box-shadow: var(--elev-1);
}
.stButton > button:hover{ filter:brightness(.97); transform: translateY(-1px); }
.btn-muted > button{ background: transparent !important; color: var(--muted) !important; border: var(--line) !important; }

.small{ color: var(--muted); font-size: .92rem; }

.wave { height: 12px; margin: 8px 0 10px; background:
  linear-gradient(90deg, transparent, color-mix(in oklab, var(--primary) 70%, var(--accent) 30%), transparent);
  border-radius: 999px;
  opacity: .75;
}

.chatwrap{ background: var(--bg-card); border: var(--line); border-radius: var(--radius); padding: 10px; }
.msg{ border-radius: 12px; padding: 8px 10px; margin: 6px 0; max-width: 96%; border: var(--line); }
.msg.agent{ background: color-mix(in oklab, var(--bg-card) 90%, var(--primary) 10%); }
.msg.patient{ background: color-mix(in oklab, var(--bg-card) 94%, #fff 6%); }
.typing{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace; }

.footer-note{ opacity:.7; margin:10px 0 6px; text-align:center; color: var(--muted); }
</style>
        """,
        unsafe_allow_html=True,
    )

def title(txt: str, sub: str = ""):
    st.markdown(f"<div class='h-title'>{txt}</div>", unsafe_allow_html=True)
    if sub:
        st.markdown(f"<div class='h-sub'>{sub}</div>", unsafe_allow_html=True)

def topbar():
    now = datetime.now().strftime("%d %b %Y • %H:%M")
    st.markdown(
        f"""
        <div class="topbar">
          <div class="brand">
            <div class="brand-badge"></div>
            <div>Agente de Preconsulta</div>
          </div>
          <div class="kpis">
            <span class="badge">ES • MX</span>
            <span class="badge">Preconsulta</span>
            <span class="badge">{now}</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def stepper(current: str):
    steps = [("select","Paciente y condición"), ("intro","Introducción"), ("convo","Entrevista y reporte")]
    marks = []
    for key, label in steps:
        cls = "step active" if key == current else "step"
        marks.append(f"<span class='{cls}'>{label}</span>")
        if key != steps[-1][0]: marks.append("<span class='dot'></span>")
    st.markdown("<div class='stepper'>"+"".join(marks)+"</div>", unsafe_allow_html=True)

def info_block(t: str, body: str, chips: Optional[List[str]]=None, soft=False):
    cls = "card soft" if soft else "card"
    st.markdown(f'<div class="{cls}">', unsafe_allow_html=True)
    title(t)
    if chips:
        st.markdown("<div class='kit-chips'>"+"".join([f"<span class='chip'>{c}</span>" for c in chips])+"</div>", unsafe_allow_html=True)
    st.markdown(body)
    st.markdown("</div>", unsafe_allow_html=True)

def patient_card(p: Patient, selected=False):
    sel = "selected" if selected else ""
    st.markdown(
        f"""
        <div class="select-card {sel}">
          <div class="ph-img">Imagen del paciente</div>
          <div class="card-title">{p.nombre}</div>
          <div class="card-sub">{p.edad} años • {p.sexo}</div>
          <div class="card-sub">Condición de base: <b>{p.condicion_base}</b></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def condition_card(c: Condition, selected=False):
    sel = "selected" if selected else ""
    st.markdown(
        f"""
        <div class="select-card {sel}">
          <div class="card-title">{c.titulo}</div>
          <div class="card-sub">{c.descripcion}</div>
          <div class="kit-chips" style="margin-top:6px">
            <span class="chip">Guía</span>
            <span class="chip">Entrevista</span>
            <span class="chip">Hechos útiles</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Sidebar (profesional y breve)
st.sidebar.subheader("Apariencia")
theme_choice = st.sidebar.selectbox("Tema", list(THEMES.keys()), index=list(THEMES.keys()).index(st.session_state.theme_name))
if theme_choice != st.session_state.theme_name:
    st.session_state.theme_name = theme_choice
inject_css()

col1, col2 = st.sidebar.columns(2)
with col1:
    st.session_state.density = st.selectbox("Densidad", ["Compacto","Normal","Amplio"], index=["Compacto","Normal","Amplio"].index(st.session_state.density))
with col2:
    st.session_state.radius = st.selectbox("Esquinas", ["Small","Medium","Large"], index=["Small","Medium","Large"].index(st.session_state.radius))
st.session_state.contrast = st.sidebar.slider("Profundidad", 0.00, 0.18, st.session_state.contrast, 0.01)
inject_css()

st.sidebar.markdown("---")
st.sidebar.subheader("Ritmo (Parte 2)")
st.session_state.anim_on = st.sidebar.toggle("Animar tipeo", value=st.session_state.anim_on)
st.session_state.agent_typing_speed = st.sidebar.slider("Vel. agente", 0.005, 0.05, st.session_state.agent_typing_speed, 0.001)
st.session_state.patient_thinking_delay = st.sidebar.slider("Pausa paciente", 0.2, 3.0, st.session_state.patient_thinking_delay, 0.05)
st.session_state.patient_typing_speed = st.sidebar.slider("Vel. paciente", 0.005, 0.05, st.session_state.patient_typing_speed, 0.001)
st.session_state.show_timestamps = st.sidebar.toggle("Hora en mensajes", value=st.session_state.show_timestamps)

st.sidebar.markdown("---")
st.sidebar.subheader("Notas")
st.session_state.notes = st.sidebar.text_area("Rápidas", value=st.session_state.notes, height=100)
st.sidebar.caption("Flujo: Selección → Introducción → (Entrevista en Parte 2)")

# Header
topbar()
stepper(st.session_state.step)
st.markdown('<hr class="sep">', unsafe_allow_html=True)

# STEP: SELECT
if st.session_state.step == "select":
    st.markdown('<div class="card">', unsafe_allow_html=True)
    L, R = st.columns([1.3, 1.0], gap="large")
    with L:
        title("Preconsulta asistida", "Selecciona paciente y condición")
        st.markdown(
            "<div class='kit-chips'>"
            "<span class='chip'>Diseño profesional</span>"
            "<span class='chip'>Color moderado</span>"
            "<span class='chip'>Adaptativo</span>"
            "</div>", unsafe_allow_html=True
        )
        st.markdown("</div>", unsafe_allow_html=True)
    with R:
        st.markdown(
            "<div class='card soft'>"
            "<div class='small'>Personaliza el tema en la barra lateral. Esta vista evita huecos grandes y mantiene contraste legible.</div>"
            "</div>", unsafe_allow_html=True
        )
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div class="wave"></div>', unsafe_allow_html=True)

    title("Paciente")
    cols = st.columns(3, gap="large")
    for i, p in enumerate(PACIENTES):
        with cols[i % 3]:
            is_sel = (st.session_state.sel_patient == p.pid)
            patient_card(p, is_sel)
            label = "Seleccionado" if is_sel else "Elegir"
            if st.button(label, key=f"pick_{p.pid}", use_container_width=True):
                st.session_state.sel_patient = p.pid
                st.rerun()

    st.markdown('<div class="wave"></div>', unsafe_allow_html=True)

    title("Condición", "Elige la condición a evaluar")
    cols2 = st.columns(2, gap="large")
    for idx, c in enumerate(CONDICIONES):
        with cols2[idx % 2]:
            is_sel = (st.session_state.sel_condition == c.cid)
            condition_card(c, is_sel)
            label = "Seleccionada" if is_sel else "Elegir"
            if st.button(label, key=f"cond_{c.cid}", use_container_width=True):
                st.session_state.sel_condition = c.cid
                st.rerun()

    st.markdown('<div class="wave"></div>', unsafe_allow_html=True)
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

# STEP: INTRO
elif st.session_state.step == "intro":
    p = next(x for x in PACIENTES if x.pid == st.session_state.sel_patient)
    c = next(x for x in CONDICIONES if x.cid == st.session_state.sel_condition)

    headL, headR = st.columns([1.25, 1.0], gap="large")
    with headL:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        title("Agente de preconsulta", "Resumen previo para tu consulta")
        st.markdown(
            "<div class='kit-chips'>"
            "<span class='chip'>Guía clínica</span>"
            "<span class='chip'>EHR</span>"
            "<span class='chip'>Hechos útiles</span>"
            "</div>", unsafe_allow_html=True
        )
        st.markdown("</div>", unsafe_allow_html=True)

        info_block(
            "¿Cómo usarlo?",
            textwrap.dedent("""
            1) Confirma paciente y condición.  
            2) En la Parte 2, la entrevista avanza con pausas naturales y tipeo por rol.  
            3) El reporte se construye en paralelo (Motivo, HPI, antecedentes, medicaciones, hechos útiles).  
            4) Al final verás faltantes sugeridos para cerrar calidad clínica.
            """),
            chips=["Ritmo humano", "Exportación (Parte 2)", "Diseño profesional"],
            soft=True,
        )

    with headR:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        title(f"Paciente: {p.nombre}", f"{p.edad} años • {p.sexo}")
        st.markdown("<div class='ph-img' style='margin-top:6px'>Imagen del paciente</div>", unsafe_allow_html=True)
        st.markdown("<div class='small' style='margin-top:8px'>Condición base: <b>"+p.condicion_base+"</b></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="card">', unsafe_allow_html=True)
        title("Condición a explorar", c.titulo)
        st.markdown(f"<div class='small'>{c.descripcion}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="wave"></div>', unsafe_allow_html=True)

    st.markdown('<div class="grid">', unsafe_allow_html=True)
    st.markdown('<div class="col-8">', unsafe_allow_html=True)
    info_block(
        "Ritmo humano activo",
        textwrap.dedent(f"""
        - Animación de tipeo: {"sí" if st.session_state.anim_on else "no"}  
        - Velocidad (agente): {st.session_state.agent_typing_speed:.3f} s/char  
        - Pausa previa (paciente): {st.session_state.patient_thinking_delay:.2f} s  
        - Velocidad (paciente): {st.session_state.patient_typing_speed:.3f} s/char  
        - Timestamps: {"sí" if st.session_state.show_timestamps else "no"}
        """),
        chips=["Natural", "Controlado"],
        soft=False,
    )
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="col-4">', unsafe_allow_html=True)
    info_block(
        "Tema visual",
        textwrap.dedent(f"""
        - Tema: {st.session_state.theme_name}  
        - Densidad: {st.session_state.density}  
        - Esquinas: {st.session_state.radius}  
        - Profundidad: {st.session_state.contrast:.2f}
        """),
        chips=["Color moderado", "Legible"],
        soft=False,
    )
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="wave"></div>', unsafe_allow_html=True)

    B1, B2, B3 = st.columns([1.1, 1.1, 2.8], gap="large")
    with B1:
        if st.button("◀ Regresar", use_container_width=True):
            st.session_state.step = "select"; st.rerun()
    with B2:
        if st.session_state.convo_enabled:
            if st.button("Iniciar entrevista", use_container_width=True):
                st.session_state.step = "convo"
                st.session_state.chat_idx = -1
                st.session_state.pause = False
                st.rerun()
        else:
            st.button("Iniciar entrevista", key="start_disabled", use_container_width=True, disabled=True)
            st.caption("Pega la PARTE 2 para habilitar la entrevista.")
    with B3:
        st.markdown(
            f"<div class='kpis'>"
            f"<span class='badge'>Paciente: {p.nombre}</span>"
            f"<span class='badge'>Condición: {c.titulo}</span>"
            f"<span class='badge'>Conversación guiada</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

st.markdown("<div class='footer-note'>Interfaz profesional y moderna — color equilibrado y rendimiento fluido.</div>", unsafe_allow_html=True)
# ─────────────────────────────────────────────────────────────────────────────
# PARTE 2/2 — Conversación guiada + Reporte + Exportación
# Estética profesional, rendimiento fluido, sin filtros.
# ─────────────────────────────────────────────────────────────────────────────

import time
from typing import List, Tuple, Dict

# Habilita el botón "Iniciar entrevista" definido en la PARTE 1
st.session_state.convo_enabled = True

# ----------------------------------------------------------------------------- 
# Guiones de entrevista (una lista de turnos) y reglas para componer el reporte
# -----------------------------------------------------------------------------
Turn = Tuple[str, str]         # ("agent"|"patient", "texto")
Rule = Tuple[int, str, str]    # (idx_turno_alcanzado, "Sección", "Hecho")

def script_serotonin() -> Tuple[List[Turn], List[Rule], List[str]]:
    chat: List[Turn] = [
        ("agent","Gracias por tu tiempo. Para anticipar la consulta, te haré preguntas breves. ¿Cuál es tu principal molestia hoy?"),
        ("patient","Me siento muy inquieto, sudo mucho y noto mis pupilas grandes."),
        ("agent","¿Desde cuándo empezó y cómo fue el inicio?"),
        ("patient","Comenzó hace dos días de manera súbita."),
        ("agent","¿Has tenido fiebre, escalofríos, rigidez o temblores?"),
        ("patient","Fiebre no estoy seguro, pero sí escalofríos y rigidez."),
        ("agent","¿Notas movimientos oculares extraños o visión borrosa?"),
        ("patient","A veces siento los ojos como temblorosos y la luz me molesta."),
        ("agent","¿Tomaste o ajustaste medicamentos recientemente, incluyendo jarabes para la tos o suplementos?"),
        ("patient","Uso fluoxetina diario y ayer tomé un antitusivo con dextrometorfano."),
        ("agent","¿Has consumido alcohol, estimulantes o drogas recreativas en los últimos días?"),
        ("patient","No, no he consumido nada de eso."),
        ("agent","¿Tienes náusea, diarrea o vómito?"),
        ("patient","Náusea leve. Ni diarrea ni vómito."),
        ("agent","¿Cómo dormiste estas noches?"),
        ("patient","Dormí poco y me noté inquieto."),
        ("agent","¿Has tenido dolores de cabeza, rigidez marcada o espasmos musculares?"),
        ("patient","Sí, sobre todo rigidez en piernas."),
        ("agent","¿Cambiaste dosis de la fluoxetina o agregaste otro medicamento recetado?"),
        ("patient","No cambié dosis. Solo el jarabe."),
        ("agent","Voy a compilar un resumen para tu médico. Si algo es inexacto, avísame."),
    ]
    rules: List[Rule] = [
        (1, "Motivo principal", "Inquietud, diaforesis y midriasis."),
        (3, "HPI", "Inicio súbito hace ~2 días."),
        (5, "Signos autonómicos", "Escalofríos y rigidez."),
        (7, "Signos oculares", "Molestia a la luz; sensación de movimientos oculares."),
        (9, "Medicaciones (EHR)", "Fluoxetina (ISRS) — uso crónico."),
        (9, "Medicaciones (entrevista)", "Dextrometorfano — uso reciente."),
        (11, "Historia dirigida", "Niega alcohol y estimulantes recientes."),
        (13, "HPI", "Náusea leve, sin diarrea ni vómito."),
        (15, "HPI", "Insomnio e inquietud."),
        (17, "Historia dirigida", "Rigidez en piernas."),
        (19, "Historia dirigida", "Sin cambio de dosis del ISRS."),
    ]
    faltantes: List[str] = [
        "Signos vitales objetivos: temperatura, FC, TA y SatO₂.",
        "Exploración neuromuscular dirigida: hiperreflexia, clonus, tono.",
        "Cronología/dosis exacta de cada fármaco (ISRS/OTC) y tiempos.",
        "Descartar otras causas de agitación (intoxicación, abstinencia).",
    ]
    return chat, rules, faltantes

def script_migraine() -> Tuple[List[Turn], List[Rule], List[str]]:
    chat: List[Turn] = [
        ("agent","Vamos a caracterizar tu dolor de cabeza para orientar el manejo. ¿Cómo describirías el dolor y dónde se localiza?"),
        ("patient","Es pulsátil y se concentra del lado derecho."),
        ("agent","¿Empezó cuándo y cuánto dura cada episodio?"),
        ("patient","Ayer por la tarde y dura varias horas."),
        ("agent","¿La luz o el sonido empeoran? ¿Náusea o vómito?"),
        ("patient","La luz y el ruido empeoran. Náusea leve, sin vómito."),
        ("agent","¿Antes de que empiece notas aura visual u hormigueo?"),
        ("patient","A veces veo destellos antes del dolor."),
        ("agent","¿Dormiste menos, ayunaste o consumiste cafeína tarde?"),
        ("patient","Dormí poco y tomé café por la noche."),
        ("agent","¿Qué analgésicos has usado y qué tanto ayudan?"),
        ("patient","Ibuprofeno; alivia parcialmente."),
        ("agent","¿Hay antecedentes familiares de migraña?"),
        ("patient","Sí, mi madre."),
        ("agent","¿El dolor te limita actividades o trabajo?"),
        ("patient","Sí, me cuesta concentrarme."),
        ("agent","Con esto armaré un resumen para tu médico."),
    ]
    rules: List[Rule] = [
        (1, "Motivo principal", "Cefalea pulsátil lateralizada."),
        (3, "HPI", "Inicio ayer; crisis por horas."),
        (5, "HPI", "Fotofobia y fonofobia; náusea leve."),
        (7, "Historia dirigida", "Aura visual ocasional."),
        (9, "Historia dirigida", "Privación de sueño y cafeína tardía."),
        (11, "Medicaciones (entrevista)", "Ibuprofeno PRN con respuesta parcial."),
        (13, "Antecedentes familiares", "Madre con migraña."),
        (15, "Limitación funcional", "Impacto en concentración y actividades."),
    ]
    faltantes: List[str] = [
        "Frecuencia mensual de los episodios y escala de dolor.",
        "Pruebas de ‘red flags’: inicio en trueno, fiebre, déficit neurológico.",
        "Uso previo de triptanos y eficacia.",
        "Desencadenantes personales (estrés, ciclo, ayuno, olores).",
    ]
    return chat, rules, faltantes

def script_flu() -> Tuple[List[Turn], List[Rule], List[str]]:
    chat: List[Turn] = [
        ("agent","Voy a registrar síntomas respiratorios para orientar la visita. ¿Has tenido fiebre y dolor corporal?"),
        ("patient","Sí, fiebre y el cuerpo cortado."),
        ("agent","¿Tos o congestión? ¿Desde cuándo?"),
        ("patient","Tos seca hace tres días y nariz tapada."),
        ("agent","¿Dificultad para respirar o dolor en el pecho?"),
        ("patient","No, solo cansancio."),
        ("agent","¿Tomaste algún medicamento?"),
        ("patient","Paracetamol y un antigripal."),
        ("agent","¿Contacto con personas enfermas o vacunación reciente?"),
        ("patient","Mi pareja tuvo gripe; me vacuné hace 8 meses."),
        ("agent","¿Antecedentes o factores de riesgo (asma, embarazo, inmunosupresión)?"),
        ("patient","No."),
        ("agent","Gracias, prepararé un resumen."),
    ]
    rules: List[Rule] = [
        (1, "Motivo principal", "Fiebre, mialgia y malestar."),
        (3, "HPI", "Tos seca y congestión de 3 días."),
        (5, "HPI", "Sin disnea ni dolor torácico."),
        (7, "Medicaciones (entrevista)", "Paracetamol + antigripal."),
        (9, "Historia dirigida", "Contacto positivo; vacunación hace 8 meses."),
        (11, "Factores de riesgo", "Niega comorbilidades relevantes."),
    ]
    faltantes: List[str] = [
        "Temperatura y saturación de O₂.",
        "Criterios de prueba diagnóstica según guía local.",
        "Indicaciones de alarma y aislamiento domiciliario.",
    ]
    return chat, rules, faltantes

def script_malaria() -> Tuple[List[Turn], List[Rule], List[str]]:
    chat: List[Turn] = [
        ("agent","Quiero documentar el patrón febril para orientar estudios. ¿La fiebre es intermitente con escalofríos?"),
        ("patient","Sí, sube y baja con sudoración."),
        ("agent","¿Has viajado a zona endémica recientemente?"),
        ("patient","Sí, estuve en selva hace dos semanas."),
        ("agent","¿Tienes cefalea, náusea o dolor muscular?"),
        ("patient","Cefalea y cuerpo cortado."),
        ("agent","¿Tomaste profilaxis antipalúdica?"),
        ("patient","No."),
        ("agent","¿Notas coloración amarillenta en piel u ojos, orina oscura o dolor en costado?"),
        ("patient","No lo he notado."),
        ("agent","Perfecto, armaré un resumen para tu médico."),
    ]
    rules: List[Rule] = [
        (1, "Motivo principal", "Fiebre intermitente con escalofríos y sudoración."),
        (3, "HPI", "Viaje a zona endémica hace 2 semanas."),
        (5, "HPI", "Cefalea y mialgias."),
        (7, "Historia dirigida", "Sin profilaxis."),
        (9, "Historia dirigida", "Niega ictericia u orina oscura."),
    ]
    faltantes: List[str] = [
        "Prueba rápida/frotis y gota gruesa para confirmar.",
        "Patrón horario de la fiebre y respuesta a antipiréticos.",
        "Exploración de anemia y esplenomegalia.",
    ]
    return chat, rules, faltantes

SCRIPTS: Dict[str, callable] = {
    "ss": script_serotonin,
    "mig": script_migraine,
    "flu": script_flu,
    "mal": script_malaria,
}

# ----------------------------------------------------------------------------- 
# Construcción del reporte a partir de reglas
# -----------------------------------------------------------------------------
EHR_SEED = {
    "Antecedentes (EHR)": ["Antecedente crónico declarado en ficha del paciente"],
    "Medicaciones (EHR)": ["Medicación habitual según expediente (si aplica)"],
}

SECTION_ORDER = [
    "Motivo principal",
    "HPI",
    "Antecedentes (EHR)",
    "Medicaciones (EHR)",
    "Medicaciones (entrevista)",
    "Signos autonómicos",
    "Signos oculares",
    "Historia dirigida",
    "Antecedentes familiares",
    "Factores de riesgo",
    "Limitación funcional",
    "Hechos útiles",
]

def seed_facts() -> Dict[str, List[str]]:
    facts: Dict[str, List[str]] = {k: [] for k in SECTION_ORDER}
    for k, arr in EHR_SEED.items():
        if k in facts:
            facts[k] = arr.copy()
    return facts

def facts_up_to(idx_limit: int, rules: List[Rule]) -> Dict[str, List[str]]:
    facts = seed_facts()
    for i_lim, section, text in rules:
        if idx_limit >= i_lim:
            facts.setdefault(section, []).append(text)
    # Consolidar "Hechos útiles" desde secciones orientadas a datos puntuales
    utiles = []
    for sec in ("Signos autonómicos","Signos oculares","Historia dirigida","Factores de riesgo","Limitación funcional"):
        utiles += facts.get(sec, [])
    if utiles:
        facts["Hechos útiles"] = utiles
    return facts

def render_box(title_txt: str, items: List[str] | str):
    st.markdown('<div class="card" style="margin-bottom:10px">', unsafe_allow_html=True)
    st.markdown(f"**{title_txt}:**", unsafe_allow_html=True)
    if isinstance(items, list):
        if items:
            st.markdown("<ul>" + "".join([f"<li>{st.session_state.get('•','•')} {x}</li>" for x in items]) + "</ul>", unsafe_allow_html=True)
        else:
            st.markdown("—", unsafe_allow_html=True)
    else:
        st.markdown(items or "—", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

def compose_markdown(idx_limit: int, rules: List[Rule], p_name: str, c_title: str) -> str:
    facts = facts_up_to(idx_limit, rules)
    out: List[str] = []
    out.append("# Reporte de Preconsulta\n")
    out.append(f"**Paciente:** {p_name}  \n**Condición:** {c_title}\n")
    motivo = facts["Motivo principal"][0] if facts["Motivo principal"] else "—"
    out.append(f"**Motivo principal:** {motivo}\n")
    def section_md(name: str):
        arr = facts.get(name, [])
        if not arr: return [f"- —"]
        return [f"- {x}" for x in arr]
    out.append("## Historia de la enfermedad actual (HPI)")
    out += section_md("HPI")
    out.append("\n## Antecedentes (EHR)")
    out += section_md("Antecedentes (EHR)")
    out.append("\n## Medicaciones")
    meds = []
    for m in facts.get("Medicaciones (EHR)", []): meds.append(f"- {m}")
    for m in facts.get("Medicaciones (entrevista)", []): meds.append(f"- **{m}**")
    out += meds if meds else ["- —"]
    utiles = facts.get("Hechos útiles", [])
    if utiles:
        out.append("\n## Hechos útiles")
        out += [f"- {x}" for x in utiles]
    return "\n".join(out)

def render_report(idx_limit: int, rules: List[Rule], faltantes: List[str]):
    fx = facts_up_to(idx_limit, rules)
    render_box("Motivo principal", (fx["Motivo principal"][0] if fx["Motivo principal"] else "—"))
    render_box("Historia de la enfermedad actual (HPI)", fx["HPI"])
    render_box("Antecedentes (EHR)", fx["Antecedentes (EHR)"])
    st.markdown('<div class="card" style="margin-bottom:10px">', unsafe_allow_html=True)
    st.markdown("**Medicaciones (EHR y entrevista):**", unsafe_allow_html=True)
    meds = [f"<li>{m}</li>" for m in fx["Medicaciones (EHR)"]]
    meds += [f"<li><span class='badge'>{m}</span></li>" for m in fx["Medicaciones (entrevista)"]]
    st.markdown("<ul>"+ "".join(meds) +"</ul>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    utiles = fx.get("Hechos útiles", [])
    if utiles:
        render_box("Hechos útiles", utiles)
    if idx_limit >= len(rules):
        st.markdown('<div class="card" style="border:1px solid rgba(245, 158, 11, .35); background: color-mix(in oklab, var(--bg-card) 90%, #F59E0B 10%);">', unsafe_allow_html=True)
        st.markdown("**Checklist sugerida para completar en la consulta:**", unsafe_allow_html=True)
        for x in faltantes:
            st.markdown(f"- {x}", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ----------------------------------------------------------------------------- 
# Animación de tipeo y utilidades de ritmo
# -----------------------------------------------------------------------------
def typewriter(ph, text: str, speed: float):
    if not st.session_state.anim_on:
        ph.markdown(text, unsafe_allow_html=True)
        return
    buf = ""
    for ch in text:
        buf += ch
        ph.markdown(buf, unsafe_allow_html=True)
        time.sleep(max(0.001, speed))

def timestamp() -> str:
    return datetime.now().strftime('%H:%M') if st.session_state.show_timestamps else ""

def render_message(role: str, text: str):
    who = "Asistente" if role == "agent" else "Paciente"
    klass = "agent" if role == "agent" else "patient"
    st.markdown(f"<div class='msg {klass}'><b>{who}:</b> {text}" + (f"<br><small>{timestamp()}</small>" if timestamp() else "") + "</div>", unsafe_allow_html=True)

def render_typing(role: str) -> st.delta_generator.DeltaGenerator:
    who = "Asistente" if role == "agent" else "Paciente"
    klass = "agent" if role == "agent" else "patient"
    st.markdown(f"<div class='msg {klass}'><b>{who}:</b> ", unsafe_allow_html=True)
    ph = st.empty()
    if timestamp():
        st.markdown(f"<br><small>{timestamp()}</small></div>", unsafe_allow_html=True)
    else:
        st.markdown(f"</div>", unsafe_allow_html=True)
    return ph

# ----------------------------------------------------------------------------- 
# Vista de conversación
# -----------------------------------------------------------------------------
if st.session_state.step == "convo":
    p = next(x for x in PACIENTES if x.pid == st.session_state.sel_patient)
    c = next(x for x in CONDICIONES if x.cid == st.session_state.sel_condition)
    chat, rules, faltantes = SCRIPTS[st.session_state.sel_condition]()
    total_turns = len(chat)

    headL, headR = st.columns([2.8, 1.2], gap="large")
    with headL:
        title("Entrevista guiada", "Mensajes automáticos con pausas naturales")
    with headR:
        cols = st.columns(3)
        with cols[0]:
            if st.button("◀ Volver", use_container_width=True):
                st.session_state.step = "intro"; st.rerun()
        with cols[1]:
            if st.button("🔁 Reiniciar", use_container_width=True):
                st.session_state.chat_idx = -1; st.session_state.pause = False; st.rerun()
        with cols[2]:
            if not st.session_state.pause:
                if st.button("⏸ Pausa", use_container_width=True):
                    st.session_state.pause = True; st.rerun()
            else:
                if st.button("▶ Reanudar", use_container_width=True):
                    st.session_state.pause = False; st.rerun()

    done = max(0, st.session_state.chat_idx + 1)
    pct = int(100 * done / total_turns)
    pcol, ccol = st.columns([0.72, 0.28])
    with pcol:
        st.progress(pct, text=f"Progreso: {pct}%")
    with ccol:
        st.markdown(
            f"<div class='kpis' style='justify-content:flex-end'>"
            f"<span class='badge'>Paciente: {p.nombre}</span>"
            f"<span class='badge'>Condición: {c.titulo}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

    st.markdown('<hr class="sep">', unsafe_allow_html=True)

    chat_col, rep_col = st.columns([1.45, 0.95], gap="large")

    with chat_col:
        st.markdown('<div class="chatwrap">', unsafe_allow_html=True)

        # Mensajes ya emitidos
        for i in range(st.session_state.chat_idx + 1):
            role, txt = chat[i]
            render_message(role, txt)

        # Próximo mensaje con pausas y tipeo
        next_idx = st.session_state.chat_idx + 1
        if next_idx < total_turns:
            role, txt = chat[next_idx]
            if not st.session_state.pause:
                if role == "patient":
                    time.sleep(max(0.0, st.session_state.patient_thinking_delay))
                ph = render_typing(role)
                speed = st.session_state.agent_typing_speed if role == "agent" else st.session_state.patient_typing_speed
                typewriter(ph, txt, speed)
                st.session_state.chat_idx = next_idx
                time.sleep(0.06)
                st.rerun()
            else:
                who = "Asistente" if role == "agent" else "Paciente"
                klass = "agent" if role == "agent" else "patient"
                st.markdown(f"<div class='msg {klass}'><b>{who}:</b> <span class='small'>[Pausado]</span></div>", unsafe_allow_html=True)
        else:
            st.success("Entrevista completa. El reporte quedó consolidado.")
            st.markdown("<div class='kpis'><span class='badge'>Resumen listo</span><span class='badge'>Revisa faltantes</span></div>", unsafe_allow_html=True)
            st.balloons()

        st.markdown('</div>', unsafe_allow_html=True)

    with rep_col:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        title("Reporte generado", f"Paciente: {p.nombre} • Condición: {c.titulo}")
        render_report(st.session_state.chat_idx, rules, faltantes)
        md = compose_markdown(st.session_state.chat_idx, rules, p.nombre, c.titulo)
        st.download_button("⬇️ Exportar (.md)", data=md.encode("utf-8"), file_name=f"reporte_{p.pid}_{c.cid}.md", mime="text/markdown", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<hr class="sep">', unsafe_allow_html=True)

    with st.expander("Notas rápidas y recomendaciones"):
        st.markdown("""
- El reporte se forma con Motivo, HPI, antecedentes, medicaciones y hechos útiles.
- La checklist al final sugiere información clínica a completar durante la consulta.
- Ajusta pausas y velocidades desde la barra lateral para un ritmo más natural.
- Mantuvimos una estética sobria y moderna para uso profesional.
""")

# ----------------------------------------------------------------------------- 
# Fin de la Parte 2/2
# -----------------------------------------------------------------------------
