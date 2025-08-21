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
