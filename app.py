# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  AGENTE DE PRECONSULTA — ES·MX                                              ║
# ║  PARTE 1/2 — UI vistosa, compacta, colorida y animada (sin entrevista)      ║
# ║  - Sin filtros de datos                                                      ║
# ║  - Evita espacios vacíos grandes (layout compacto)                           ║
# ║  - Tarjetas “no tan rectangulares”, chips, ribbons, mosaicos y brillos       ║
# ║  - Sidebar: tema + ritmo humano (usado en la Parte 2)                        ║
# ╚════════════════════════════════════════════════════════════════════════════╝

import streamlit as st
from streamlit.components.v1 import html as st_html
from dataclasses import dataclass
from typing import List, Optional
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
    theme_name="Neón Aurora",
    glow_intensity=0.70,         # 0.0-1.0
    vignette_on=True,
    ornaments_on=True,
    compact_density=True,        # compacta paddings/márgenes

    # Ritmo humano (usado en la entrevista en la Parte 2)
    anim_on=True,
    agent_typing_speed=0.018,    # seg/char agente
    patient_thinking_delay=1.10, # seg antes de escribir paciente
    patient_typing_speed=0.024,  # seg/char paciente
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
]

CONDICIONES: List[Condition] = [
    Condition("flu", "Gripe", "Viral respiratoria: fiebre, mialgia, congestión y fatiga."),
    Condition("mal", "Malaria", "Fiebre intermitente con escalofríos; antecedente de viaje a zona endémica."),
    Condition("mig", "Migraña", "Cefalea pulsátil lateralizada con foto/fonofobia, posible náusea."),
    Condition("ss",  "Síndrome serotoninérgico", "Exceso de serotonina (p. ej., ISRS + dextrometorfano)."),
]

# ─────────────────────────────────────────────────────────────────────────────
# Paletas/temas llamativos (sin minimalismo)
# ─────────────────────────────────────────────────────────────────────────────
THEMES = {
    "Neón Aurora": {
        "primary": "#7C3AED", "accent": "#22D3EE", "accent2": "#EC4899",
        "bg1": "rgba(124,58,237,.36)", "bg2": "rgba(34,211,238,.40)",
        "bg3": "rgba(236,72,153,.30)", "bg4": "rgba(99,102,241,.28)",
        "blob1": "rgba(124,58,237,.85)", "blob2": "rgba(34,211,238,.80)", "blob3": "rgba(236,72,153,.76)"
    },
    "Cian Eléctrico": {
        "primary": "#0EA5E9", "accent": "#22D3EE", "accent2": "#06B6D4",
        "bg1": "rgba(14,165,233,.34)", "bg2": "rgba(34,211,238,.36)",
        "bg3": "rgba(6,182,212,.28)", "bg4": "rgba(59,130,246,.26)",
        "blob1": "rgba(14,165,233,.86)", "blob2": "rgba(34,211,238,.78)", "blob3": "rgba(6,182,212,.70)"
    },
    "Magenta Sunset": {
        "primary": "#DB2777", "accent": "#F59E0B", "accent2": "#F43F5E",
        "bg1": "rgba(219,39,119,.38)", "bg2": "rgba(245,158,11,.34)",
        "bg3": "rgba(244,63,94,.28)", "bg4": "rgba(251,146,60,.26)",
        "blob1": "rgba(244,63,94,.86)", "blob2": "rgba(251,146,60,.78)", "blob3": "rgba(217,70,239,.70)"
    },
    "Esmeralda": {
        "primary": "#059669", "accent": "#10B981", "accent2": "#34D399",
        "bg1": "rgba(5,150,105,.36)", "bg2": "rgba(16,185,129,.36)",
        "bg3": "rgba(34,197,94,.28)", "bg4": "rgba(52,211,153,.26)",
        "blob1": "rgba(16,185,129,.90)", "blob2": "rgba(34,197,94,.82)", "blob3": "rgba(5,150,105,.74)"
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# CSS — compacto, colorido y animado (sin grandes espacios vacíos)
# ─────────────────────────────────────────────────────────────────────────────
BASE_CSS = """
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800;900&display=swap" rel="stylesheet">
<style>
:root{
  --text:#0f172a; --muted:#5d6c83; --border:#e6e9f2; --card:#ffffff; --bg:#F4F6FB;
  --primary:VAR_PRIMARY; --accent:VAR_ACCENT; --accent2:VAR_ACCENT2;
  --chipfg:#1f2937; --chipbg:#eef2ff;
  --ok:#10b981; --warn:#f59e0b; --bad:#ef4444;
  --agent:#eef2ff; --patient:#f3f4f6;
  --glass:rgba(255,255,255,.86); --gbrd:rgba(255,255,255,.50);
  --glow:VAR_GLOW; --shadow:0 8px 22px rgba(0,0,0,.18);
}
/* Modo oscuro */
@media (prefers-color-scheme: dark){
  :root{
    --text:#EAF2FF; --muted:#9EB0CC; --border:#263652; --card:#0E1628; --bg:#060B17;
    --chipfg:#D7E4FF; --chipbg:#0f1a33;
    --agent:#0f1a33; --patient:#111827;
    --glass:rgba(10,16,29,.70); --gbrd:rgba(255,255,255,.08);
  }
}

/* Densidad compacta (reduce espacios vacíos verticales) */
body, html, [class*="css"]{
  background:var(--bg) !important; color:var(--text) !important;
  font-family:Inter,system-ui,-apple-system,Segoe UI,Roboto,Helvetica Neue,Arial,sans-serif;
  font-size:16.2px; line-height:1.35;
}
header{ visibility:hidden; }
.block-container{ padding-top:CLP_TOP; padding-bottom:CLP_BOTTOM; max-width:1250px; }
section.main>div{ padding-top:0 !important; }

/* Fondo dinámico fijo (no ocupa alto extra) */
.bg-aura{
  position:fixed; inset:-10vmax; z-index:-3; pointer-events:none;
  background: radial-gradient(120vmax 120vmax at 15% 12%, VAR_BG1, transparent 60%),
              radial-gradient(110vmax 110vmax at 85% 15%, VAR_BG2, transparent 60%),
              radial-gradient(100vmax 100vmax at 50% 85%, VAR_BG3, transparent 50%),
              radial-gradient(80vmax  80vmax  at 90% 80%, VAR_BG4, transparent 55%);
  filter: saturate(1.08) brightness(1.01);
  opacity:.55; animation: aura 40s linear infinite;
}
@keyframes aura{
  0%{ transform: translateX(0) }
  50%{ transform: translateX(6px) }
  100%{ transform: translateX(0) }
}

/* Malla sutil de cuadrados (no ocupa altura) */
.grid-squares{
  position: fixed; inset: 0; z-index:-4; pointer-events:none;
  background-image:
    linear-gradient(90deg, rgba(255,255,255,.05) 1px, transparent 1px),
    linear-gradient(0deg,  rgba(255,255,255,.05) 1px, transparent 1px);
  background-size: 26px 26px, 26px 26px; opacity:.45;
  animation: gridfloat 24s ease-in-out infinite;
}
@keyframes gridfloat{
  0%{ transform: translateY(0px); }
  50%{ transform: translateY(10px); }
  100%{ transform: translateY(0px); }
}

/* Vignette (opcional) */
.vignette:before{
  content:""; position:fixed; inset:0; pointer-events:none; z-index:-2;
  background: radial-gradient(ellipse at center, rgba(0,0,0,0) 30%, rgba(0,0,0,.12) 100%);
  mix-blend-mode:multiply;
}

/* Topbar compacto con glass + brillo */
.topbar{
  position:sticky; top:0; z-index:20; margin:0 0 10px 0;
  display:flex; align-items:center; justify-content:space-between; gap:12px;
  background:var(--glass); backdrop-filter: blur(10px) saturate(1.15);
  border:1px solid var(--gbrd); border-radius:14px; padding:10px 14px;
  box-shadow: 0 10px 28px rgba(0,0,0,.12), 0 0 0 2px rgba(255,255,255,.04) inset;
}
.brand{ display:flex; align-items:center; gap:10px; font-weight:900; letter-spacing:.2px; }
.brand .logo{
  width:34px; height:34px; border-radius:12px;
  background: conic-gradient(from 180deg, var(--primary), var(--accent), var(--accent2), var(--primary));
  box-shadow: 0 0 0 4px rgba(255,255,255,.06) inset, 0 0 22px var(--glow);
}
.kpis{ display:flex; gap:8px; flex-wrap:wrap; align-items:center; }
.badge{
  display:inline-flex; align-items:center; gap:6px; border-radius:999px; padding:5px 9px;
  background:var(--chipbg); color:var(--chipfg); border:1px solid var(--border);
  font-weight:800; font-size:.80rem;
}

/* Stepper con chips y animación */
.stepper{ display:flex; gap:6px; align-items:center; flex-wrap:wrap; margin-top:4px;}
.step{
  padding:7px 10px; border-radius:14px; border:1px solid var(--border); background:var(--card);
  font-weight:800; font-size:.84rem; position:relative; overflow:hidden;
  transition: transform .12s ease, box-shadow .12s ease;
}
.step:before{
  content:""; position:absolute; inset:auto auto 0 0; height:3px; width:100%;
  background: linear-gradient(90deg, var(--primary), var(--accent), var(--accent2));
  opacity:.35;
}
.step.active{ border-color:#c7d2fe; box-shadow:0 0 0 3px #a78bfa33 inset, 0 6px 20px rgba(0,0,0,.08); transform: translateY(-1px);}
.dot{ width:7px; height:7px; border-radius:999px; background:var(--muted); opacity:.6; }

/* Títulos y separadores fluidos */
.h-title{ font-weight:900; font-size:1.56rem; margin:0 0 4px; letter-spacing:.15px; }
.h-sub{ color:var(--muted); font-weight:600; margin-bottom:2px; }
.sep{
  height:1.5px; border:none; margin:12px 0 12px; opacity:.75;
  background:linear-gradient(90deg,var(--primary),var(--accent),var(--accent2));
  border-radius:2px;
}

/* Tarjetas y contenedores (compactos) */
.card{
  background:var(--card); border:1px solid var(--border); border-radius:18px;
  padding:12px; box-shadow: 0 1px 0 rgba(255,255,255,.04) inset, 0 10px 20px rgba(0,0,0,.06);
}

/* Tarjeta seleccionable con squircle + tilt + halo */
.select-card{
  position:relative; border-radius:20px; border:2px solid transparent; cursor:pointer;
  background:
    radial-gradient(120px 120px at 10% 10%, rgba(255,255,255,.12), transparent 60%) ,
    linear-gradient(var(--card), var(--card)) padding-box,
    linear-gradient(90deg, var(--primary), var(--accent), var(--accent2)) border-box;
  transition: transform .15s ease, box-shadow .15s ease;
  transform: perspective(900px) rotateX(0deg) rotateY(0deg);
}
.select-card:hover{
  transform: perspective(900px) rotateX(1.2deg) rotateY(-1.2deg) translateY(-2px);
  box-shadow: 0 24px 40px rgba(0,0,0,.18);
}
.select-card.selected{ box-shadow:0 0 0 4px #c7d2fe66 inset, 0 24px 48px rgba(0,0,0,.18); }
.sticker{
  position:absolute; top:-8px; left:-8px; background:var(--accent); color:#001018;
  font-weight:900; padding:5px 9px; border-radius:10px; transform: rotate(-7deg) scale(.98);
  box-shadow:0 4px 14px rgba(0,0,0,.18);
}

/* Placeholder imagen paciente (compacto) */
.ph-img{
  height:128px; border-radius:14px; display:flex; align-items:center; justify-content:center;
  background:
    radial-gradient(ellipse at top, rgba(127,127,170,.25), transparent 60%),
    var(--patient);
  color:var(--muted); border:1px dashed rgba(127,127,170,.35);
}

/* Chips y callouts */
.kit-chips{ display:flex; gap:6px; flex-wrap:wrap; }
.chip{
  display:inline-flex; align-items:center; gap:6px; padding:5px 9px; border-radius:999px;
  background: linear-gradient(180deg, rgba(255,255,255,.72), rgba(255,255,255,.50));
  border:1px solid var(--border); font-weight:800; font-size:.80rem;
}
.callout{
  border:1px solid var(--border); border-radius:16px; padding:10px 12px;
  background:linear-gradient(180deg, rgba(255,255,255,.70), rgba(255,255,255,.52));
  box-shadow: 0 0 0 3px #ffffff11 inset, 0 0 28px var(--glow);
}

/* Grids */
.grid{ display:grid; gap:12px; grid-template-columns: repeat(12, 1fr); }
.col-12{ grid-column: span 12; } .col-10{ grid-column: span 10; } .col-8{ grid-column: span 8; }
.col-6{ grid-column: span 6; }  .col-4{ grid-column: span 4; }  .col-3{ grid-column: span 3; }
@media (max-width:1200px){
  .col-6{ grid-column: span 12; } .col-4{ grid-column: span 6; } .col-3{ grid-column: span 6; }
}

/* Botones */
.stButton > button{
  border:none; border-radius:12px; padding:10px 12px; font-weight:900; color:#fff; background:var(--primary);
  box-shadow: 0 8px 22px rgba(0,0,0,.18), 0 0 0 3px #ffffff22 inset;
}
.stButton > button:hover{ filter:brightness(.97); transform: translateY(-1px); }
.btn-ghost{ border:1px solid var(--border) !important; background:transparent !important; color:var(--muted) !important; }

/* Etiquetas */
.small{ color:var(--muted); font-size:.90rem; }

/* Divisor ondulado compacto (SVG incrustado) */
.wave-sep{
  height:22px; margin:6px 0 8px;
  background:
    radial-gradient(12px 10px at 10px 12px, var(--accent) 40%, transparent 41%),
    radial-gradient(12px 10px at 34px 10px, var(--primary) 40%, transparent 41%),
    radial-gradient(12px 10px at 58px 12px, var(--accent2) 40%, transparent 41%);
  background-size: 68px 22px;
}

/* Chat placeholders (usado en parte 2) */
.chatwrap{ background:var(--card); border:1px solid var(--border); border-radius:16px; padding:10px; }
.msg{ border-radius:12px; padding:8px 10px; margin:6px 0; max-width:96%; border:1px solid var(--border); }
.msg.agent{ background:var(--agent); }
.msg.patient{ background:var(--patient); }
.typing{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace; }

/* Pequeño brillo utilitario */
.glow{ box-shadow: 0 0 18px var(--glow); }

/* —— Fin CSS —————————————————————————————————————————————————————————————— */
</style>
"""

def _density_css(compact: bool) -> tuple[str, str]:
    """Devuelve paddings top/bottom para el contenedor principal según densidad."""
    if compact:
        return ("0.35rem", "0.6rem")
    else:
        return ("0.9rem", "1.2rem")

def apply_theme():
    t = THEMES.get(st.session_state.theme_name, THEMES["Neón Aurora"])
    clp_top, clp_bottom = _density_css(st.session_state.compact_density)
    css = BASE_CSS
    css = css.replace("VAR_PRIMARY", t["primary"]).replace("VAR_ACCENT", t["accent"]).replace("VAR_ACCENT2", t["accent2"])
    css = css.replace("VAR_BG1", t["bg1"]).replace("VAR_BG2", t["bg2"]).replace("VAR_BG3", t["bg3"]).replace("VAR_BG4", t["bg4"])
    css = css.replace("VAR_GLOW", f"0 0 {int(26*st.session_state.glow_intensity)}px {t['accent']}")
    css = css.replace("CLP_TOP", clp_top).replace("CLP_BOTTOM", clp_bottom)
    st_html(css, height=0, scrolling=False)

    decorations = []
    decorations.append('<div class="bg-aura"></div>')
    if st.session_state.ornaments_on:
        decorations.append('<div class="grid-squares"></div>')
    if st.session_state.vignette_on:
        decorations.append('<div class="vignette"></div>')
    st_html("\n".join(decorations), height=0, scrolling=False)

apply_theme()

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

def sticker(text: str) -> str:
    return f"<div class='sticker'>{text}</div>"

def patient_card(p: Patient, selected=False):
    sel = "selected" if selected else ""
    st.markdown(
        f"""
        <div class="select-card {sel} card">
          {sticker("Paciente")}
          <div class="ph-img">Imagen del paciente</div>
          <div style="margin-top:8px" class="kit-chips">
            <span class="chip">Ficha EHR</span>
            <span class="chip">Contexto</span>
            <span class="chip">Demográficos</span>
          </div>
          <div style="font-weight:900;margin-top:8px;font-size:1.02rem">{p.nombre}</div>
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
    cls = "card"  # (mantengo un solo estilo compacto)
    st.markdown(f'<div class="{cls}">', unsafe_allow_html=True)
    title(title_txt)
    if chips:
        st.markdown("<div class='kit-chips'>" + "".join([f"<span class='chip'>{c}</span>" for c in chips]) + "</div>", unsafe_allow_html=True)
    st.markdown(body_md)
    st.markdown("</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Topbar + Stepper + separador (compactos)
# ─────────────────────────────────────────────────────────────────────────────
topbar()
stepper(st.session_state.step)
st.markdown('<div class="wave-sep"></div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Sidebar (tema + ritmo humano; sin filtros de datos)
# ─────────────────────────────────────────────────────────────────────────────
st.sidebar.markdown("### 🎨 Apariencia")
theme_choice = st.sidebar.radio(
    "Tema de color",
    list(THEMES.keys()),
    index=list(THEMES.keys()).index(st.session_state.theme_name),
)
if theme_choice != st.session_state.theme_name:
    st.session_state.theme_name = theme_choice
    apply_theme()

st.session_state.glow_intensity = st.sidebar.slider("Brillo/Glow", 0.0, 1.0, st.session_state.glow_intensity, 0.01)
st.session_state.compact_density = st.sidebar.toggle("Densidad compacta (recomendada)", value=st.session_state.compact_density)
st.session_state.vignette_on = st.sidebar.toggle("Vignette", value=st.session_state.vignette_on)
st.session_state.ornaments_on = st.sidebar.toggle("Mosaico y blobs", value=st.session_state.ornaments_on)
# Reaplicar cambios visuales
apply_theme()

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
    height=120,
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
# STEP: SELECT (paciente y condición) — layout compacto sin huecos grandes
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.step == "select":
    # Hero compacto (sin altos grandes)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    L, R = st.columns([1.25, 1.0], gap="large")
    with L:
        title("Preconsulta asistida", "Selecciona paciente y una condición a explorar")
        st.markdown(
            """
            <div class="kit-chips" style="margin:6px 0 6px">
              <span class="chip">Colorido</span>
              <span class="chip">Animaciones</span>
              <span class="chip">Compacto</span>
              <span class="chip">Sin filtros</span>
            </div>
            """, unsafe_allow_html=True
        )
        st.markdown(
            """
            <div class="callout">
              <b>Objetivo:</b> preparar una entrevista simulada (Parte 2) y un <b>reporte clínico</b>.
              Esta interfaz evita espacios vacíos y usa tarjetas con efecto tilt y “squircles”.
            </div>
            """, unsafe_allow_html=True
        )
    with R:
        st.markdown(
            """
            <div class="card" style="border-radius:16px;">
              <div class="kit-chips">
                <span class="chip">EHR</span>
                <span class="chip">Hechos útiles</span>
                <span class="chip">Diseño vivo</span>
              </div>
              <div class="small" style="margin-top:6px">
                Personaliza <b>tema</b> y <b>densidad</b> en la barra lateral.
              </div>
              <div class="small" style="margin-top:2px">
                La entrevista tendrá <b>pausas naturales</b> y <b>tipeo por rol</b> (Parte 2).
              </div>
            </div>
            """, unsafe_allow_html=True
        )
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div class="wave-sep"></div>', unsafe_allow_html=True)

    # Pacientes
    title("Selecciona un paciente")
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

    st.markdown('<div class="wave-sep"></div>', unsafe_allow_html=True)

    # Condiciones
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

    st.markdown('<div class="wave-sep"></div>', unsafe_allow_html=True)

    # CTA compacto
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
# STEP: INTRO (presentación; sigue compacto y colorido)
# ─────────────────────────────────────────────────────────────────────────────
elif st.session_state.step == "intro":
    p = next(x for x in PACIENTES if x.pid == st.session_state.sel_patient)
    c = next(x for x in CONDICIONES if x.cid == st.session_state.sel_condition)

    # Cabecera compacta
    headL, headR = st.columns([1.25, 1.0], gap="large")
    with headL:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        title("Agente de preconsulta", "Recopila info clínica previa y estructura un resumen útil")
        st.markdown(
            "<div class='kit-chips' style='margin-top:6px'>"
            "<span class='chip'>Guía clínica</span>"
            "<span class='chip'>EHR (FHIR)</span>"
            "<span class='chip'>Resumen</span>"
            "<span class='chip'>Hechos útiles</span>"
            "</div>", unsafe_allow_html=True
        )
        st.markdown("</div>", unsafe_allow_html=True)

        info_block(
            "¿Cómo usarlo?",
            textwrap.dedent("""
            1) Confirma **paciente** y **condición**.  
            2) En la Parte 2, al pulsar **Iniciar entrevista**, los mensajes aparecerán con **pausas naturales**:  
               - **Pausa previa (paciente)** y **velocidades de tipeo** se ajustan en la barra lateral.  
               - Buscamos que “se sienta humano”, no una ráfaga.  
            3) El **reporte** se arma durante la conversación (Motivo, HPI, antecedentes, medicaciones y hechos útiles).  
            4) Verás **faltantes** sugeridos al cierre para mejorar calidad clínica.
            """),
            chips=["Ritmo humano", "Exportación (Parte 2)", "Diseño llamativo"]
        )

    with headR:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        title(f"Paciente: {p.nombre}", f"{p.edad} años • {p.sexo}")
        st.markdown("<div class='ph-img' style='height:120px;margin-top:4px'>Imagen del paciente</div>", unsafe_allow_html=True)
        st.markdown("<div class='small' style='margin-top:6px'>Condición base: <b>"+p.condicion_base+"</b></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="card">', unsafe_allow_html=True)
        title("Condición a explorar", c.titulo)
        st.markdown(f"<div class='small'>{c.descripcion}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="wave-sep"></div>', unsafe_allow_html=True)

    # Estado de ritmo humano (compacto)
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
        chips=["Natural", "Controlado", "Sin prisas"]
    )
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="col-4">', unsafe_allow_html=True)
    info_block(
        "Tema visual",
        textwrap.dedent(f"""
        - **Tema:** {st.session_state.theme_name}  
        - **Brillo (glow):** {st.session_state.glow_intensity:.2f}  
        - **Densidad compacta:** {"sí" if st.session_state.compact_density else "no"}  
        - **Vignette:** {"sí" if st.session_state.vignette_on else "no"}  
        - **Mosaicos/blobs:** {"sí" if st.session_state.ornaments_on else "no"}  
        """),
        chips=["Neón", "Brillos", "Mosaicos"]
    )
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)  # /grid

    # CTA
    st.markdown('<div class="wave-sep"></div>', unsafe_allow_html=True)
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
            unsafe_allow_html=True
        )

# ─────────────────────────────────────────────────────────────────────────────
# Footer compacto decorativo
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div style="opacity:.65; margin:10px 0 6px; text-align:center" class="small">
      Hecho con ⚡️ colores y animaciones — UI compacta, sin espacios vacíos y <b>sin filtros</b>.
    </div>
    """,
    unsafe_allow_html=True
)
# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  FIN PARTE 1/2 (Pega debajo la PARTE 2 para habilitar la entrevista)       ║
# ╚════════════════════════════════════════════════════════════════════════════╝
