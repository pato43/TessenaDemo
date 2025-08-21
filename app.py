# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  AGENTE DE PRECONSULTA — ES·MX                                              ║
# ║  PARTE 1/2 — UI glam + flujo Select/Intro (sin entrevista)                  ║
# ║  - Colorido, dinámico, sin filtros de datos                                 ║
# ║  - Tarjetas con micro-animaciones, mosaicos de cuadrados, stickers, ribbons ║
# ║  - Sidebar con tema y ritmo humano (usado en la parte 2)                    ║
# ╚════════════════════════════════════════════════════════════════════════════╝

import streamlit as st
from streamlit.components.v1 import html as st_html
from dataclasses import dataclass
from typing import List, Tuple, Optional
from datetime import datetime
import textwrap

# ─────────────────────────────────────────────────────────────────────────────
# Configuración base
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Agente de Preconsulta",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# Estado (session_state) y defaults
# ─────────────────────────────────────────────────────────────────────────────
DEFAULTS = dict(
    step="select",               # select → intro → (convo en parte 2)
    sel_patient=None,
    sel_condition=None,
    chat_idx=-1,
    pause=False,

    # Apariencia y animación
    theme_name="Aurora",
    theme_primary="#7C3AED",     # morado
    theme_accent="#22D3EE",      # aqua
    theme_bg_variant="Aurora",   # tema de decoraciones
    glow_intensity=0.65,         # 0.0-1.0
    vignette_on=True,
    ornaments_on=True,
    glass_on=True,

    # Ritmo humano (usado en la entrevista en la Parte 2)
    anim_on=True,
    agent_typing_speed=0.018,    # seg/char agente
    patient_thinking_delay=1.25, # seg antes de escribir paciente
    patient_typing_speed=0.023,  # seg/char paciente
    show_timestamps=True,

    # Notas del operador
    notes="",

    # Puente con Parte 2
    convo_enabled=False,         # La activa Parte 2 al cargarse
)

for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────────────────────────────────────────
# Datos de ejemplo
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class Patient:
    pid: str
    nombre: str
    edad: int
    sexo: str
    condicion_base: str
    img: str = ""  # url

@dataclass
class Condition:
    cid: str
    titulo: str
    descripcion: str

PACIENTES: List[Patient] = [
    Patient("nvelarde", "Nicolás Velarde", 34, "Masculino", "Trastorno de ansiedad"),
    Patient("aduarte",   "Amalia Duarte",   62, "Femenino",  "Diabetes tipo 2"),
    Patient("szamora",   "Sofía Zamora",    23, "Femenino",  "Asma"),
    # Puedes agregar más pacientes aquí…
]

CONDICIONES: List[Condition] = [
    Condition("flu", "Gripe", "Viral respiratoria: fiebre, mialgia, congestión y fatiga."),
    Condition("mal", "Malaria", "Fiebre intermitente con escalofríos; antecedente de viaje a zona endémica."),
    Condition("mig", "Migraña", "Cefalea pulsátil lateralizada con foto/fonofobia, posible náusea."),
    Condition("ss",  "Síndrome serotoninérgico", "Exceso de serotonina (p. ej., ISRS + dextrometorfano)."),
    # Puedes agregar más condiciones aquí…
]

# ─────────────────────────────────────────────────────────────────────────────
# CSS — tema vistoso, mosaicos, stickers, ribbons, chips, glow y blobs
# ─────────────────────────────────────────────────────────────────────────────
BASE_CSS = """
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800;900&display=swap" rel="stylesheet">
<style>
:root{
  --text:#0f172a; --muted:#64748b; --border:#e5e7eb; --card:#ffffff; --bg:#F6F7FB;
  --primary:VAR_PRIMARY; --accent:VAR_ACCENT;
  --ok:#10b981; --warn:#f59e0b; --bad:#ef4444;
  --chipfg:#1f2937; --chipbg:#eef2ff;
  --agent:#eef2ff; --patient:#f3f4f6;
  --glass-bg:rgba(255,255,255,.82);
  --glass-brd:rgba(255,255,255,.45);
  --glow:VAR_GLOW;
}
/* Dark scheme override */
@media (prefers-color-scheme: dark){
  :root{
    --text:#EAF2FF; --muted:#9EB0CC; --border:#1f2b43; --card:#0E1628; --bg:#070D19;
    --chipfg:#D7E4FF; --chipbg:#0f1a33;
    --agent:#0f1a33; --patient:#111827;
    --glass-bg:rgba(9,14,26,.62);
    --glass-brd:rgba(255,255,255,.08);
  }
}
/* Reset/typography */
html, body, [class*="css"]{
  background:var(--bg) !important; color:var(--text) !important;
  font-family:Inter,system-ui,-apple-system,Segoe UI,Roboto,Helvetica Neue,Arial,sans-serif;
  font-size:16.2px; line-height:1.35;
}
header{ visibility:hidden; }
.block-container{ padding-top:.8rem; }

/* Gradiente maestro dinámico (Aurora / Ocean / Sunset) */
.body-gradient{
  position: fixed; inset: -10vmax; z-index: -2;
  background: radial-gradient(120vmax 120vmax at 20% 10%, VAR_BG1, transparent 60%),
              radial-gradient(110vmax 110vmax at 80% 20%, VAR_BG2, transparent 60%),
              radial-gradient(100vmax 100vmax at 50% 90%, VAR_BG3, transparent 50%),
              radial-gradient(80vmax  80vmax  at 90% 80%, VAR_BG4, transparent 55%);
  filter: saturate(1.08) brightness(1.01);
  opacity: .55;
  transition: opacity .3s ease;
}

/* Vignette sutil */
.vignette:before{
  content:"";
  position:fixed; inset:0; pointer-events:none; z-index:-1;
  background: radial-gradient(ellipse at center, rgba(0,0,0,0) 30%, rgba(0,0,0,.12) 100%);
  mix-blend-mode:multiply;
}

/* Mosaico de cuadrados animados (decorativo) */
.squares{
  position: fixed; inset: 0; z-index: -3; pointer-events:none;
  background-image:
    linear-gradient(90deg, rgba(255,255,255,.05) 1px, transparent 1px),
    linear-gradient(0deg,  rgba(255,255,255,.05) 1px, transparent 1px);
  background-size: 28px 28px, 28px 28px;
  animation: gridfloat 20s linear infinite;
  opacity:.5;
}
@keyframes gridfloat{
  0%{ transform: translateY(0px); }
  50%{ transform: translateY(10px); }
  100%{ transform: translateY(0px); }
}

/* “Blobs” suaves */
.blob{
  position: fixed; border-radius: 999px; filter: blur(48px);
  opacity: .35; mix-blend-mode: screen; z-index:-2;
  animation: sway 16s ease-in-out infinite;
}
.blob.one{ width:420px; height:420px; left:8%; top:14%; background:VAR_BLOB1; }
.blob.two{ width:360px; height:360px; right:10%; top:22%; background:VAR_BLOB2; animation-delay: -6s;}
.blob.tri{ width:520px; height:520px; left:40%; bottom: -6%; background:VAR_BLOB3; animation-delay: -10s;}
@keyframes sway{
  0%{ transform: translate(0,0) scale(1); }
  50%{ transform: translate(10px,-8px) scale(1.06); }
  100%{ transform: translate(0,0) scale(1); }
}

/* Topbar con glass + glow */
.topbar{
  position:sticky; top:0; z-index:20;
  padding:12px 16px; margin:0 0 14px 0;
  background: var(--glass-bg);
  backdrop-filter: blur(10px) saturate(1.15);
  border: 1px solid var(--glass-brd); border-radius:16px;
  display:flex; align-items:center; justify-content:space-between; gap:14px;
  box-shadow: 0 10px 28px rgba(0,0,0,.12), 0 0 0 2px rgba(255,255,255,.04) inset;
}
.brand{
  display:flex; align-items:center; gap:12px; font-weight:900; letter-spacing:.3px;
}
.brand .logo{
  width:38px; height:38px; border-radius:12px;
  background: conic-gradient(from 180deg, var(--primary), var(--accent));
  box-shadow: 0 0 0 4px rgba(255,255,255,.08) inset, 0 0 22px var(--glow);
}
.kpis{ display:flex; gap:8px; flex-wrap:wrap; align-items:center; }
.badge{
  display:inline-flex; align-items:center; gap:8px; border-radius:999px; padding:6px 10px;
  background:var(--chipbg); color:var(--chipfg); border:1px solid var(--border);
  font-weight:800; font-size:.8rem;
}

/* Stepper con chips y conectores */
.stepper{ display:flex; gap:8px; align-items:center; flex-wrap:wrap; margin-top:4px;}
.step{
  padding:8px 12px; border-radius:14px; border:1px solid var(--border); background:var(--card);
  font-weight:800; font-size:.86rem; position:relative; overflow:hidden;
  transition: transform .12s ease, box-shadow .12s ease;
}
.step:before{
  content:""; position:absolute; inset:auto auto 0 0; height:3px; width:100%;
  background: linear-gradient(90deg, var(--primary), var(--accent));
  opacity:.35;
}
.step.active{ border-color:#c7d2fe; box-shadow:0 0 0 3px #a78bfa33 inset, 0 6px 20px rgba(0,0,0,.08); transform: translateY(-1px);}
.dot{ width:8px; height:8px; border-radius:999px; background:var(--muted); opacity:.6; }

/* Títulos y separadores */
.h-title{ font-weight:900; font-size:1.62rem; margin:0 0 6px; letter-spacing:.1px; }
.h-sub{ color:var(--muted); font-weight:600; }
.sep{
  height:2px; border:none; margin:14px 0 18px;
  background:linear-gradient(90deg,var(--primary),var(--accent));
  border-radius:2px; opacity:.75;
}

/* Tarjetas y contenedores */
.card{
  background:var(--card); border:1px solid var(--border); border-radius:18px; padding:16px;
  box-shadow: 0 1px 0 rgba(255,255,255,.04) inset, 0 10px 24px rgba(0,0,0,.06);
}
.card.soft{
  background:linear-gradient(180deg,var(--card),rgba(0,0,0,0));
}
.ribbon{
  position:relative; overflow:hidden;
}
.ribbon:after{
  content:""; position:absolute; top:10px; right:-30px; width:160px; height:26px;
  background: linear-gradient(90deg,var(--primary),var(--accent));
  transform: rotate(12deg); border-radius:8px; opacity:.35;
}

/* Tarjeta seleccionable con “squircle” y sticker */
.select-card{
  position:relative; border-radius:20px; border:2px solid transparent; transition:.18s ease; cursor:pointer;
  background:
    radial-gradient(120px 120px at 10% 10%, rgba(255,255,255,.12), transparent 60%) ,
    linear-gradient(var(--card), var(--card)) padding-box,
    linear-gradient(90deg, var(--primary), var(--accent)) border-box;
}
.select-card:hover{ transform:translateY(-2px); box-shadow:0 22px 40px rgba(0,0,0,.16); }
.select-card.selected{
  box-shadow:0 0 0 4px #c7d2fe66 inset, 0 24px 50px rgba(0,0,0,.18);
}
.ph-img{
  height:190px; border-radius:16px; display:flex; align-items:center; justify-content:center;
  background:
    radial-gradient(ellipse at top, rgba(127, 127, 170,.25), transparent 60%),
    var(--patient);
  color:var(--muted); border:1px dashed rgba(127,127,170,.35);
}
.sticker{
  position:absolute; top:-8px; left:-8px; background:var(--accent); color:#001018;
  font-weight:900; padding:6px 10px; border-radius:10px; transform: rotate(-6deg) scale(.98);
  box-shadow:0 4px 14px rgba(0,0,0,.18);
}

/* Chips y listas “bonitas” */
.kit-chips{ display:flex; gap:8px; flex-wrap:wrap; }
.chip{
  display:inline-flex; align-items:center; gap:8px; padding:6px 10px; border-radius:999px;
  background: linear-gradient(180deg, rgba(255,255,255,.7), rgba(255,255,255,.45));
  border:1px solid var(--border); font-weight:800; font-size:.82rem;
}

/* Grids */
.grid{ display:grid; gap:16px; grid-template-columns: repeat(12, 1fr); }
.col-12{ grid-column: span 12; } .col-10{ grid-column: span 10; } .col-8{ grid-column: span 8; }
.col-6{ grid-column: span 6; } .col-4{ grid-column: span 4; } .col-3{ grid-column: span 3; }
@media (max-width:1200px){
  .col-6{ grid-column: span 12; } .col-4{ grid-column: span 6; } .col-3{ grid-column: span 6; }
}

/* Callouts con borde glow */
.callout{
  border:1px solid var(--border); border-radius:18px; padding:14px 16px;
  background:linear-gradient(180deg, rgba(255,255,255,.65), rgba(255,255,255,.45));
  box-shadow: 0 0 0 3px #ffffff11 inset, 0 0 28px var(--glow);
}

/* Botones */
.stButton > button{
  border:none; border-radius:14px; padding:12px 14px; font-weight:900; color:#fff; background:var(--primary);
  box-shadow: 0 8px 22px rgba(0,0,0,.18), 0 0 0 3px #ffffff22 inset;
}
.stButton > button:hover{ filter:brightness(.97); transform: translateY(-1px); }
.btn-ghost{ border:1px solid var(--border) !important; background:transparent !important; color:var(--muted) !important; }
.btn-disabled{ pointer-events:none; opacity:.6; }

/* Contenido “hero” curvadito */
.hero{
  position:relative; overflow:hidden; border-radius:20px;
  background:
     radial-gradient(160px 120px at 10% 10%, rgba(255,255,255,.8), rgba(255,255,255,.3) 60%),
     var(--card);
  border: 1px solid var(--border);
}
.hero:before{
  content:""; position:absolute; inset:auto auto 0 0; height:5px; width:100%;
  background:linear-gradient(90deg,var(--primary),var(--accent)); opacity:.55;
}

/* Etiquetas mini */
.small{ color:var(--muted); font-size:.92rem; }

/* Glow utilitario */
.glow{
  box-shadow: 0 0 18px var(--glow);
}
</style>
"""

# ─────────────────────────────────────────────────────────────────────────────
# Sistemas de color/tema (paletas vistosas)
# ─────────────────────────────────────────────────────────────────────────────
THEMES = {
    "Aurora": {
        "primary": "#7C3AED", "accent": "#22D3EE",
        "bg1": "rgba(125, 64, 255, .45)", "bg2": "rgba(34, 211, 238, .45)",
        "bg3": "rgba(236, 72, 153, .32)", "bg4": "rgba(99, 102, 241, .32)",
        "blob1": "rgba(124, 58, 237, .85)", "blob2": "rgba(34, 211, 238, .85)", "blob3": "rgba(236, 72, 153, .75)"
    },
    "Ocean": {
        "primary": "#2563EB", "accent": "#06B6D4",
        "bg1": "rgba(37, 99, 235, .38)", "bg2": "rgba(6, 182, 212, .40)",
        "bg3": "rgba(59, 130, 246, .28)", "bg4": "rgba(14, 165, 233, .28)",
        "blob1": "rgba(59, 130, 246, .85)", "blob2": "rgba(14, 165, 233, .85)", "blob3": "rgba(2, 132, 199, .75)"
    },
    "Sunset": {
        "primary": "#DB2777", "accent": "#F59E0B",
        "bg1": "rgba(219, 39, 119, .42)", "bg2": "rgba(245, 158, 11, .38)",
        "bg3": "rgba(244, 63, 94, .30)", "bg4": "rgba(251, 146, 60, .28)",
        "blob1": "rgba(244, 63, 94, .88)", "blob2": "rgba(251, 146, 60, .85)", "blob3": "rgba(217, 70, 239, .70)"
    },
    "Emerald": {
        "primary": "#059669", "accent": "#10B981",
        "bg1": "rgba(5, 150, 105, .40)", "bg2": "rgba(16, 185, 129, .38)",
        "bg3": "rgba(34, 197, 94, .32)", "bg4": "rgba(52, 211, 153, .28)",
        "blob1": "rgba(16, 185, 129, .90)", "blob2": "rgba(34, 197, 94, .85)", "blob3": "rgba(5, 150, 105, .75)"
    },
}

def apply_theme(tname: str, glow_intensity: float, vignette_on: bool, ornaments_on: bool):
    t = THEMES.get(tname, THEMES["Aurora"])
    css = BASE_CSS
    css = css.replace("VAR_PRIMARY", t["primary"]).replace("VAR_ACCENT", t["accent"])
    css = css.replace("VAR_BG1", t["bg1"]).replace("VAR_BG2", t["bg2"]).replace("VAR_BG3", t["bg3"]).replace("VAR_BG4", t["bg4"])
    css = css.replace("VAR_BLOB1", t["blob1"]).replace("VAR_BLOB2", t["blob2"]).replace("VAR_BLOB3", t["blob3"])
    css = css.replace("VAR_GLOW", f"0 0 {int(26*glow_intensity)}px {t['accent']}")
    st_html(css, height=0, scrolling=False)

    # Decoraciones (gradientes + blobs + mosaico + vignette)
    decorations = ['<div class="body-gradient"></div>']
    if ornaments_on:
        decorations += [
            '<div class="squares"></div>',
            '<div class="blob one"></div>',
            '<div class="blob two"></div>',
            '<div class="blob tri"></div>'
        ]
    if st.session_state.vignette_on:
        decorations += ['<div class="vignette"></div>']
    st_html("\n".join(decorations), height=0, scrolling=False)

apply_theme(st.session_state.theme_name, st.session_state.glow_intensity, st.session_state.vignette_on, st.session_state.ornaments_on)

# ─────────────────────────────────────────────────────────────────────────────
# Helpers UI
# ─────────────────────────────────────────────────────────────────────────────
def title(txt: str, sub: str = ""):
    st.markdown(f"<div class='h-title'>{txt}</div>", unsafe_allow_html=True)
    if sub: st.markdown(f"<div class='h-sub'>{sub}</div>", unsafe_allow_html=True)

def topbar():
    now = datetime.now().strftime("%d %b %Y • %H:%M")
    st.markdown(
        f"""
        <div class="topbar">
          <div class="brand">
            <div class="logo glow"></div>
            <div>Agente de Preconsulta</div>
          </div>
          <div class="kpis">
            <span class="badge">ES • MX</span>
            <span class="badge">Flujo previo a consulta</span>
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

def sticker(text: str):
    return f"<div class='sticker'>{text}</div>"

def patient_card(p: Patient, selected=False):
    sel = "selected" if selected else ""
    st.markdown(
        f"""
        <div class="select-card {sel} ribbon card">
          {sticker("Paciente")}
          <div class="ph-img">Imagen del paciente</div>
          <div style="margin-top:10px" class="kit-chips">
            <span class="chip">Ficha EHR</span>
            <span class="chip">Contexto</span>
            <span class="chip">Demográficos</span>
          </div>
          <div style="font-weight:900;margin-top:10px;font-size:1.02rem">{p.nombre}</div>
          <div class="small">{p.edad} años • {p.sexo}</div>
          <div class="small">Condición de base: <b>{p.condicion_base}</b></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def condition_card(c: Condition, selected=False):
    sel = "selected" if selected else ""
    st.markdown(
        f"""
        <div class="select-card {sel} card">
          {sticker("Condición")}
          <div style="font-weight:900;margin-bottom:6px">{c.titulo}</div>
          <div class="small">{c.descripcion}</div>
          <div class="kit-chips" style="margin-top:8px">
            <span class="chip">Guía</span>
            <span class="chip">Entrevista</span>
            <span class="chip">Hechos útiles</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def info_block(title_txt: str, body_md: str, chips: Optional[List[str]]=None, soft=False):
    cls = "card soft" if soft else "card"
    st.markdown(f'<div class="{cls}">', unsafe_allow_html=True)
    title(title_txt)
    if chips:
        st.markdown("<div class='kit-chips'>" + "".join([f"<span class='chip'>{c}</span>" for c in chips]) + "</div>", unsafe_allow_html=True)
    st.markdown(body_md)
    st.markdown("</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Topbar + Stepper + Separador
# ─────────────────────────────────────────────────────────────────────────────
topbar()
stepper(st.session_state.step)
st.markdown('<hr class="sep">', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Sidebar (controles estéticos y ritmo humano)
# ─────────────────────────────────────────────────────────────────────────────
st.sidebar.markdown("### 🎨 Apariencia")
theme_choice = st.sidebar.radio(
    "Tema de color",
    list(THEMES.keys()),
    index=list(THEMES.keys()).index(st.session_state.theme_name),
    horizontal=False,
)
if theme_choice != st.session_state.theme_name:
    st.session_state.theme_name = theme_choice
    apply_theme(st.session_state.theme_name, st.session_state.glow_intensity, st.session_state.vignette_on, st.session_state.ornaments_on)

st.session_state.glow_intensity = st.sidebar.slider("Intensidad de brillo", 0.0, 1.0, st.session_state.glow_intensity, 0.01)
if st.sidebar.toggle("Vignette", value=st.session_state.vignette_on):
    st.session_state.vignette_on = True
else:
    st.session_state.vignette_on = False

if st.sidebar.toggle("Ornamentos (mosaico/blobs)", value=st.session_state.ornaments_on):
    st.session_state.ornaments_on = True
else:
    st.session_state.ornaments_on = False

# Reaplica para reflejar cambios visuales al vuelo
apply_theme(st.session_state.theme_name, st.session_state.glow_intensity, st.session_state.vignette_on, st.session_state.ornaments_on)

st.sidebar.markdown("---")
st.sidebar.markdown("### ⏱️ Ritmo humano (para la entrevista)")
st.session_state.anim_on = st.sidebar.toggle("Animación de tipeo", value=st.session_state.anim_on)
st.session_state.agent_typing_speed = st.sidebar.slider("Velocidad de tipeo (agente)", 0.005, 0.05, st.session_state.agent_typing_speed, 0.001)
st.session_state.patient_thinking_delay = st.sidebar.slider("Pausa previa (paciente)", 0.2, 3.0, st.session_state.patient_thinking_delay, 0.05)
st.session_state.patient_typing_speed = st.sidebar.slider("Velocidad de tipeo (paciente)", 0.005, 0.05, st.session_state.patient_typing_speed, 0.001)
st.session_state.show_timestamps = st.sidebar.toggle("Mostrar hora en mensajes", value=st.session_state.show_timestamps)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🗒️ Notas del operador")
st.session_state.notes = st.sidebar.text_area(
    "Notas rápidas",
    value=st.session_state.notes,
    height=140,
    placeholder="Observaciones, recordatorios…"
)

st.sidebar.markdown("---")
c1, c2 = st.sidebar.columns(2)
with c1:
    if st.button("🔄 Reiniciar"):
        for k, v in DEFAULTS.items():
            st.session_state[k] = v
        st.rerun()
with c2:
    st.caption("Flujo: Selección → Intro → (Entrevista)")

# ─────────────────────────────────────────────────────────────────────────────
# STEP: SELECT (paciente y condición)
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.step == "select":
    # Bloque hero superior
    st.markdown('<div class="hero card">', unsafe_allow_html=True)
    L, R = st.columns([1.2, 1.0], gap="large")
    with L:
        title("Preconsulta asistida", "Selecciona paciente y una condición a explorar")
        st.markdown(
            """
            <div class="kit-chips" style="margin:8px 0 6px">
              <span class="chip">Colorido</span>
              <span class="chip">Tarjetas interactivas</span>
              <span class="chip">Sin filtros de datos</span>
            </div>
            """, unsafe_allow_html=True
        )
        st.markdown(
            """
            <div class="callout">
            <b>¿Qué hace?</b> En la siguiente vista, el sistema guía una entrevista simulada y compila un
            <b>reporte clínico</b> con Motivo, HPI, antecedentes y hechos útiles. En esta parte sólo seleccionas.
            </div>
            """, unsafe_allow_html=True
        )
    with R:
        st.markdown(
            """
            <div class="card" style="border-radius:18px;">
              <div class="kit-chips">
                <span class="chip">Seguro</span>
                <span class="chip">EHR</span>
                <span class="chip">Hechos útiles</span>
              </div>
              <div class="small" style="margin-top:8px">
                Personaliza el <b>tema</b> y el <b>ritmo humano</b> desde la barra lateral.
              </div>
              <div class="small" style="margin-top:4px">
                La entrevista no será minimalista: será <b>llamativa</b> y con pausas naturales (Parte 2).
              </div>
            </div>
            """, unsafe_allow_html=True
        )
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<hr class="sep">', unsafe_allow_html=True)

    # Grid de pacientes (mosaico cuadrado)
    title("Selecciona un paciente")
    grid_p = st.container()
    with grid_p:
        cols = st.columns(3, gap="large")
        for i, p in enumerate(PACIENTES):
            with cols[i % 3]:
                is_sel = (st.session_state.sel_patient == p.pid)
                patient_card(p, is_sel)
                label = "Seleccionado" if is_sel else "Elegir"
                key = f"pick_{p.pid}"
                if st.button(label, key=key, use_container_width=True):
                    st.session_state.sel_patient = p.pid
                    st.rerun()

    st.markdown('<hr class="sep">', unsafe_allow_html=True)

    # Grid de condiciones (tiles con chips)
    title("Explora una condición", "Elige la condición a evaluar")
    cols2 = st.columns(2, gap="large")
    for idx, c in enumerate(CONDICIONES):
        with cols2[idx % 2]:
            is_sel = (st.session_state.sel_condition == c.cid)
            condition_card(c, is_sel)
            label = "Seleccionada" if is_sel else "Elegir"
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

# ─────────────────────────────────────────────────────────────────────────────
# STEP: INTRO (presentación/ayuda previa a la entrevista)
# ─────────────────────────────────────────────────────────────────────────────
elif st.session_state.step == "intro":
    p = next(x for x in PACIENTES if x.pid == st.session_state.sel_patient)
    c = next(x for x in CONDICIONES if x.cid == st.session_state.sel_condition)

    # Sección principal “no minimalista”: layout con mosaicos y bloques
    topA, topB = st.columns([1.2, 1.0], gap="large")

    with topA:
        st.markdown('<div class="card ribbon">', unsafe_allow_html=True)
        title("Agente de preconsulta", "Recopila info clínica previa y estructura un resumen útil")
        st.markdown(
            "<div class='kit-chips' style='margin-top:8px'>"
            "<span class='chip'>Guía clínica</span>"
            "<span class='chip'>EHR (FHIR)</span>"
            "<span class='chip'>Resumen estructurado</span>"
            "<span class='chip'>Hechos útiles</span>"
            "</div>", unsafe_allow_html=True
        )
        st.markdown(
            """
            <div class="small" style="margin-top:6px">
              Esta versión enfatiza <b>color</b>, <b>brillos</b>, <b>mosaicos</b> y <b>chips</b> —evitando lo plano y minimalista.
            </div>
            """, unsafe_allow_html=True
        )
        st.markdown("</div>", unsafe_allow_html=True)

        info_block(
            "¿Cómo usarlo?",
            textwrap.dedent("""
            1) Confirma **paciente** y **condición**.  
            2) En la Parte 2, al pulsar **Iniciar entrevista**, los mensajes aparecerán con **pausas naturales**:  
               - **Pausa previa (paciente)** y **velocidades de tipeo** están en la barra lateral.  
               - El objetivo es que “se sienta humano”, no como ráfaga.  
            3) El **reporte** se arma durante la conversación (Motivo, HPI, antecedentes, medicaciones y hechos útiles).  
            4) Verás **faltantes** sugeridos al cierre para completar calidad clínica.
            """),
            chips=["Ritmo humano", "Exportación (en Parte 2)", "Bonito y llamativo"],
            soft=True
        )

    with topB:
        # Tarjeta paciente
        st.markdown('<div class="card">', unsafe_allow_html=True)
        title(f"Paciente: {p.nombre}", f"{p.edad} años • {p.sexo}")
        st.markdown("<div class='ph-img' style='height:180px;margin-top:6px'>Imagen del paciente</div>", unsafe_allow_html=True)
        st.markdown("<div class='small' style='margin-top:8px'>Condición base declarada: <b>"+p.condicion_base+"</b></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # Tarjeta condición
        st.markdown('<div class="card">', unsafe_allow_html=True)
        title("Condición a explorar", c.titulo)
        st.markdown(f"<div class='small'>{c.descripcion}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<hr class="sep">', unsafe_allow_html=True)

    # Bloques decorativos informativos
    g = st.container()
    with g:
        st.markdown('<div class="grid">', unsafe_allow_html=True)

        st.markdown('<div class="col-8">', unsafe_allow_html=True)
        info_block(
            "Ritmo humano activo",
            textwrap.dedent(f"""
            - **Animación de tipeo:** {"sí" if st.session_state.anim_on else "no"}  
            - **Velocidad (agente):** {st.session_state.agent_typing_speed:.3f} s/char  
            - **Pausa previa (paciente):** {st.session_state.patient_thinking_delay:.2f} s  
            - **Velocidad (paciente):** {st.session_state.patient_typing_speed:.3f} s/char  
            - **Timestamps:** {"sí" if st.session_state.show_timestamps else "no"}
            """),
            chips=["No-minimalista", "Natural", "Controlado"]
        )
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="col-4">', unsafe_allow_html=True)
        info_block(
            "Tema visual",
            textwrap.dedent(f"""
            - **Tema:** {st.session_state.theme_name}  
            - **Brillo:** {st.session_state.glow_intensity:.2f}  
            - **Vignette:** {"sí" if st.session_state.vignette_on else "no"}  
            - **Ornamentos:** {"sí" if st.session_state.ornaments_on else "no"}  
            """),
            chips=["Aurora", "Mosaicos", "Blobs"]
        )
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    # CTA
    st.markdown('<hr class="sep">', unsafe_allow_html=True)
    B1, B2, B3 = st.columns([1.1, 1.1, 2.8], gap="large")
    with B1:
        if st.button("◀ Regresar", use_container_width=True):
            st.session_state.step = "select"; st.rerun()
    with B2:
        # Deshabilitado hasta que pegues la PARTE 2 (para evitar fallos)
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
            unsafe_allow_html=True
        )

# ─────────────────────────────────────────────────────────────────────────────
# Footer sutil (decorativo)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div style="opacity:.65; margin:20px 0 8px; text-align:center" class="small">
      Hecho con ❤️ para entrevistas clínicas previas — UI llamativa, sin filtros de datos.
    </div>
    """,
    unsafe_allow_html=True
)
# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  FIN PARTE 1/2                                                             ║
# ╚════════════════════════════════════════════════════════════════════════════╝
# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  AGENTE DE PRECONSULTA — ES·MX                                              ║
# ║  PARTE 2/2 — Conversación + Reporte + Export                                ║
# ║  - Pausas naturales (paciente)                                              ║
# ║  - Velocidad de tipeo por rol                                               ║
# ║  - Progreso, reporte dinámico, faltantes, export MD                         ║
# ╚════════════════════════════════════════════════════════════════════════════╝

import time
from typing import List, Tuple

# Habilita el botón "Iniciar entrevista" definido en la PARTE 1
st.session_state.convo_enabled = True

# ─────────────────────────────────────────────────────────────────────────────
# Guiones de entrevista por condición (chat, reglas de extracción y faltantes)
# ─────────────────────────────────────────────────────────────────────────────
def script_ss():
    chat = [
        ("agent","Gracias por agendar. Te haré preguntas breves para preparar tu visita. ¿Cuál es tu principal molestia hoy?"),
        ("patient","Me siento muy agitado e inquieto; también un poco confundido."),
        ("agent","¿Desde cuándo notaste esto? ¿inicio súbito o progresivo?"),
        ("patient","Empezó hace dos días, de golpe."),
        ("agent","¿Has notado fiebre, sudoración, escalofríos o rigidez muscular?"),
        ("patient","Sí, sudo mucho, a veces tengo escalofríos y siento los músculos rígidos."),
        ("agent","¿Notas cambios visuales o movimientos oculares extraños?"),
        ("patient","Mis pupilas se ven grandes y siento que los ojos se mueven raro."),
        ("agent","¿Tomaste o cambiaste medicamentos, jarabes o suplementos recientemente?"),
        ("patient","Uso fluoxetina diario y anoche tomé un jarabe para la tos con dextrometorfano."),
        ("agent","¿Consumiste alcohol, estimulantes o drogas recreativas en los últimos días?"),
        ("patient","No, nada de eso."),
        ("agent","¿Náusea, diarrea o vómito?"),
        ("patient","Náusea leve, sin diarrea ni vómito."),
        ("agent","¿Has dormido menos o te sientes inusualmente inquieto?"),
        ("patient","Sí, casi no pude dormir."),
        ("agent","Gracias. Con esto elaboraré un reporte para tu médico."),
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
        "Signos vitales objetivos: temperatura, FC, TA.",
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
        ("agent","Gracias, con esto prepararé tu reporte."),
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
        "Historial de triptanos y eficacia.",
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
        "Temperatura y saturación de O₂.",
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

# ─────────────────────────────────────────────────────────────────────────────
# Estructura de reporte y helpers
# ─────────────────────────────────────────────────────────────────────────────
EHR_BASE = {
    "Historia clínica relevante": ["Antecedente crónico declarado en ficha del paciente"],
    "Medicaciones (EHR)": ["Medicación habitual según expediente (si aplica)"],
}

def _collect_facts(idx_limit: int, rules: List[Tuple[int,str,str]]):
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

def build_report_markdown(idx_limit: int, rules: List[Tuple[int,str,str]], p_name: str, c_title: str) -> str:
    facts = _collect_facts(idx_limit, rules)
    lines = []
    lines.append(f"# Reporte de Preconsulta\n")
    lines.append(f"**Paciente:** {p_name}  \n**Condición:** {c_title}\n")
    mp = facts["Motivo principal"][0] if facts["Motivo principal"] else "—"
    lines.append(f"**Motivo principal:** {mp}\n")
    lines.append("## Historia de la enfermedad actual (HPI)")
    lines += [f"- {x}" for x in facts["HPI"]] or ["- —"]
    lines.append("\n## Antecedentes relevantes (EHR)")
    lines += [f"- {x}" for x in facts["Historia clínica relevante"]] or ["- —"]
    lines.append("\n## Medicaciones")
    meds = [f"- {m}" for m in facts["Medicaciones (EHR)"]] + [f"- **{m}**" for m in facts["Medicaciones (entrevista)"]]
    lines += meds or ["- —"]
    utiles = facts["Signos autonómicos"] + facts["Signos oculares"] + facts["Historia dirigida"]
    if utiles:
        lines.append("\n## Hechos útiles")
        lines += [f"- {x}" for x in utiles]
    return "\n".join(lines)

def render_report(idx_limit: int, rules: List[Tuple[int,str,str]]):
    facts = _collect_facts(idx_limit, rules)

    def box(t, items):
        st.markdown('<div class="card" style="margin-bottom:12px">', unsafe_allow_html=True)
        st.markdown(f"**{t}:**", unsafe_allow_html=True)
        if isinstance(items, list):
            if items:
                st.markdown("<ul>"+ "".join([f"<li>{x}</li>" for x in items]) +"</ul>", unsafe_allow_html=True)
            else:
                st.markdown("—", unsafe_allow_html=True)
        else:
            st.markdown(items or "—", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    box("Motivo principal", (facts["Motivo principal"][0] if facts["Motivo principal"] else "—"))
    box("Historia de la enfermedad actual (HPI)", facts["HPI"])
    box("Antecedentes relevantes (EHR)", facts["Historia clínica relevante"])

    st.markdown('<div class="card" style="margin-bottom:12px">', unsafe_allow_html=True)
    st.markdown("**Medicaciones (EHR y entrevista):**", unsafe_allow_html=True)
    meds = [f"<li>{m}</li>" for m in facts["Medicaciones (EHR)"]]
    meds += [f"<li><span class='badge'>{m}</span></li>" for m in facts["Medicaciones (entrevista)"]]
    st.markdown("<ul>"+ "".join(meds) +"</ul>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    utiles = facts["Signos autonómicos"] + facts["Signos oculares"] + facts["Historia dirigida"]
    if utiles:
        box("Hechos útiles", utiles)

    # Faltantes solo al finalizar
    if idx_limit >= len(rules):
        st.markdown('<div class="card" style="border:1px solid #fde68a;background:#fffbeb;">', unsafe_allow_html=True)
        st.markdown("**Qué no se cubrió pero sería útil:**", unsafe_allow_html=True)
        for x in SCRIPTS[st.session_state.sel_condition]()[2]:
            st.markdown(f"- {x}", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Animación de tipeo (respeta switches de la barra lateral)
# ─────────────────────────────────────────────────────────────────────────────
def typewriter(placeholder, text, speed=0.012):
    """Escribe carácter por carácter si anim_on está activa; de lo contrario, imprime todo."""
    if not st.session_state.anim_on:
        placeholder.markdown(f"<div class='typing'>{text}</div>", unsafe_allow_html=True)
        return
    out = ""
    for ch in text:
        out += ch
        placeholder.markdown(f"<div class='typing'>{out}</div>", unsafe_allow_html=True)
        time.sleep(speed)

# ─────────────────────────────────────────────────────────────────────────────
# Vista de conversación (chat + reporte + exportación)
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.step == "convo":
    # Obtiene guion según condición seleccionada
    chat, rules, faltantes = SCRIPTS[st.session_state.sel_condition]()
    p = next(x for x in PACIENTES if x.pid == st.session_state.sel_patient)
    c = next(x for x in CONDICIONES if x.cid == st.session_state.sel_condition)

    # Encabezado con controles rápidos
    topL, topR = st.columns([2.8, 1.2], gap="large")
    with topL:
        title("Entrevista guiada", "Mensajes automáticos con pausas naturales y tipeo por rol")
    with topR:
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

    st.markdown('<hr class="sep">', unsafe_allow_html=True)

    # Progreso y contexto
    total_turns = len(chat)
    done = max(0, st.session_state.chat_idx + 1)
    pct = int(100 * done / total_turns)
    pcol, ccol = st.columns([0.72, 0.28])
    with pcol:
        st.progress(pct, text=f"Progreso de entrevista: {pct}%")
    with ccol:
        st.markdown(
            f"<div class='kpis' style='justify-content:flex-end'>"
            f"<span class='badge'>Paciente: {p.nombre}</span>"
            f"<span class='badge'>Condición: {c.titulo}</span>"
            f"</div>", unsafe_allow_html=True
        )

    st.markdown('<hr class="sep">', unsafe_allow_html=True)

    # Layout principal: chat vs reporte
    chat_col, rep_col = st.columns([1.45, 0.95], gap="large")

    # ---------------- CHAT ----------------
    with chat_col:
        st.markdown('<div class="chatwrap">', unsafe_allow_html=True)

        # Renderiza mensajes ya completados
        for i in range(st.session_state.chat_idx + 1):
            role, txt = chat[i]
            who = "Asistente" if role == "agent" else "Paciente"
            klass = "agent" if role == "agent" else "patient"
            hour = datetime.now().strftime('%H:%M') if st.session_state.show_timestamps else ""
            st.markdown(
                f"<div class='msg {klass}'><b>{who}:</b> {txt}"
                + (f"<br><small>{hour}</small>" if hour else "")
                + "</div>",
                unsafe_allow_html=True,
            )

        # Próximo mensaje (con pausas naturales)
        next_idx = st.session_state.chat_idx + 1
        if next_idx < total_turns:
            role, txt = chat[next_idx]
            who = "Asistente" if role == "agent" else "Paciente"
            klass = "agent" if role == "agent" else "patient"

            if not st.session_state.pause:
                # Tarjeta del mensaje
                st.markdown(f"<div class='msg {klass}'><b>{who}:</b> ", unsafe_allow_html=True)
                typ = st.empty()
                if st.session_state.show_timestamps:
                    st.markdown("<small>"+datetime.now().strftime("%H:%M")+"</small></div>", unsafe_allow_html=True)
                else:
                    st.markdown("</div>", unsafe_allow_html=True)

                # Pausa previa si habla el paciente (para que "parezca que piensa")
                if role == "patient":
                    time.sleep(max(0.0, st.session_state.patient_thinking_delay))

                # Velocidad por rol
                speed = st.session_state.agent_typing_speed if role == "agent" else st.session_state.patient_typing_speed
                typewriter(typ, txt, speed=speed)

                # Avanza índice y re-render
                st.session_state.chat_idx = next_idx
                time.sleep(0.1)
                st.rerun()
            else:
                st.markdown(f"<div class='msg {klass}'><b>{who}:</b> <span class='small'>[Pausado]</span></div>", unsafe_allow_html=True)
        else:
            st.success("Entrevista completa. El reporte quedó consolidado.")
            st.markdown(
                "<div class='kpis'><span class='badge'>Resumen listo</span>"
                "<span class='badge'>Confirma faltantes</span></div>",
                unsafe_allow_html=True
            )
            st.balloons()

        st.markdown('</div>', unsafe_allow_html=True)

    # ---------------- REPORTE ----------------
    with rep_col:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        title("Reporte generado", f"Paciente: {p.nombre} • Condición: {c.titulo}")
        render_report(st.session_state.chat_idx, rules)

        # Exportar a Markdown
        md = build_report_markdown(st.session_state.chat_idx, rules, p.nombre, c.titulo)
        st.download_button(
            "⬇️ Exportar reporte (.md)",
            data=md.encode("utf-8"),
            file_name=f"reporte_{p.pid}_{c.cid}.md",
            mime="text/markdown",
            use_container_width=True
        )
        st.markdown('</div>', unsafe_allow_html=True)

    # ---------------- Notas y guía ----------------
    st.markdown('<hr class="sep">', unsafe_allow_html=True)
    with st.expander("Notas y recomendaciones"):
        st.markdown("""
- El reporte se compone de **Motivo**, **HPI**, **Antecedentes (EHR)**, **Medicaciones** y **Hechos útiles**.
- Al finalizar, se listan **faltantes** que conviene documentar para cerrar calidad clínica.
- Desde la barra lateral puedes **pausar/reanudar**, **ajustar las velocidades** y **activar/desactivar timestamps**.
- Esta UI mantiene el estilo **llamativo y colorido**, evitando el look plano/minimalista.
""")

# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  FIN PARTE 2/2                                                             ║
# ╚════════════════════════════════════════════════════════════════════════════╝
