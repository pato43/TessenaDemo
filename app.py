# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  AGENTE DE PRECONSULTA — ES·MX                                              ║
# ║  PARTE 1/2 — UI HIPERCOLOR + ANIMADA (SIN ENTREVISTA AÚN)                   ║
# ║  - Fuerza colores (nunca B/N), gradientes animados, glow, ribbons           ║
# ║  - Layout compacto (sin huecos grandes), nada minimalista                   ║
# ║  - Sin filtros de datos                                                     ║
# ║  - “Iniciar entrevista” se habilita cuando pegues la PARTE 2                ║
# ╚════════════════════════════════════════════════════════════════════════════╝

import streamlit as st
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
# Estado (session_state)
# ─────────────────────────────────────────────────────────────────────────────
DEFAULTS = dict(
    step="select",               # select → intro → (convo en parte 2)
    sel_patient=None,
    sel_condition=None,
    chat_idx=-1,
    pause=False,

    # Apariencia/tema
    theme_name="HyperNeon",
    glow_intensity=0.75,         # 0-1
    density_compact=True,        # quitar huecos
    vignette_on=True,
    ornaments_on=True,           # blobs + grid
    stripes_on=True,             # rayas diagonales

    # Ritmo humano (usado en Parte 2)
    anim_on=True,
    agent_typing_speed=0.018,
    patient_thinking_delay=1.10,
    patient_typing_speed=0.023,
    show_timestamps=True,

    notes="",
    convo_enabled=False,         # habilita Parte 2
)
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────────────────────────────────────────
# Datos
# ─────────────────────────────────────────────────────────────────────────────
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
    Condition("flu", "Gripe", "Viral respiratoria: fiebre, mialgia, congestión y fatiga."),
    Condition("mal", "Malaria", "Fiebre intermitente con escalofríos; antecedente de viaje a zona endémica."),
    Condition("mig", "Migraña", "Cefalea pulsátil lateralizada con foto/fonofobia, posible náusea."),
    Condition("ss",  "Síndrome serotoninérgico", "Exceso de serotonina (p. ej., ISRS + dextrometorfano)."),
]

# ─────────────────────────────────────────────────────────────────────────────
# Temas súper coloridos (ninguno minimalista)
# ─────────────────────────────────────────────────────────────────────────────
THEMES = {
    "HyperNeon": {
        "primary": "#7C3AED", "accent": "#22D3EE", "accent2": "#EC4899",
        "bg1": "rgba(124,58,237,.50)", "bg2": "rgba(34,211,238,.45)",
        "bg3": "rgba(236,72,153,.38)", "bg4": "rgba(99,102,241,.38)",
        "blob1":"rgba(124,58,237,.90)", "blob2":"rgba(34,211,238,.85)", "blob3":"rgba(236,72,153,.82)",
        "stripeA":"rgba(124,58,237,.12)", "stripeB":"rgba(34,211,238,.10)"
    },
    "OceanGlow": {
        "primary": "#2563EB", "accent": "#06B6D4", "accent2": "#22D3EE",
        "bg1": "rgba(37,99,235,.48)", "bg2": "rgba(6,182,212,.44)",
        "bg3": "rgba(59,130,246,.36)", "bg4": "rgba(14,165,233,.34)",
        "blob1":"rgba(59,130,246,.90)", "blob2":"rgba(14,165,233,.85)", "blob3":"rgba(2,132,199,.80)",
        "stripeA":"rgba(37,99,235,.12)", "stripeB":"rgba(6,182,212,.10)"
    },
    "SunsetPulse": {
        "primary": "#DB2777", "accent": "#F59E0B", "accent2": "#FB7185",
        "bg1": "rgba(219,39,119,.50)", "bg2": "rgba(245,158,11,.44)",
        "bg3": "rgba(244,63,94,.36)",  "bg4": "rgba(251,146,60,.34)",
        "blob1":"rgba(244,63,94,.92)", "blob2":"rgba(251,146,60,.86)", "blob3":"rgba(217,70,239,.82)",
        "stripeA":"rgba(219,39,119,.14)", "stripeB":"rgba(245,158,11,.12)"
    },
    "EmeraldBeam": {
        "primary": "#059669", "accent": "#10B981", "accent2": "#34D399",
        "bg1": "rgba(5,150,105,.48)", "bg2": "rgba(16,185,129,.44)",
        "bg3": "rgba(34,197,94,.36)", "bg4": "rgba(52,211,153,.34)",
        "blob1":"rgba(16,185,129,.92)", "blob2":"rgba(34,197,94,.86)", "blob3":"rgba(5,150,105,.82)",
        "stripeA":"rgba(5,150,105,.14)", "stripeB":"rgba(16,185,129,.12)"
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# CSS (inyectado con st.markdown —sí toma efecto global)
# ─────────────────────────────────────────────────────────────────────────────
def inject_css():
    t = THEMES[st.session_state.theme_name]
    glow = f"0 0 {int(28*st.session_state.glow_intensity)}px {t['accent']}"
    pad_top = "0.35rem" if st.session_state.density_compact else "0.9rem"
    pad_bottom = "0.6rem" if st.session_state.density_compact else "1.3rem"

    CSS = f"""
<style>
/* ======= RESET + TIPOGRAFÍA ======= */
:root {{
  --text:#0f172a; --muted:#5d6c83; --card:#ffffff; --bg:#F2F5FB; --border:#e6e9f2;
  --primary:{t['primary']}; --accent:{t['accent']}; --accent2:{t['accent2']};
  --chipfg:#1f2937; --chipbg:#eef2ff;
  --ok:#10b981; --warn:#f59e0b; --bad:#ef4444;
  --agent:#eef2ff; --patient:#f3f4f6;
  --glass:rgba(255,255,255,.88); --gbrd:rgba(255,255,255,.52);
  --glow:{glow};
}}
@media (prefers-color-scheme: dark){{
  :root{{
    --text:#EAF2FF; --muted:#9EB0CC; --card:#0F172A; --bg:#080D19; --border:#263652;
    --chipfg:#D7E4FF; --chipbg:#0f1a33; --agent:#0f1a33; --patient:#111827;
    --glass:rgba(10,16,29,.74); --gbrd:rgba(255,255,255,.08);
  }}
}}
html, body, [class*="css"]{{ background:var(--bg)!important; color:var(--text)!important; font-family:Inter,system-ui,-apple-system,Segoe UI,Roboto,Helvetica Neue,Arial,sans-serif; }}
header{{ visibility:hidden; }}
.block-container{{ padding-top:{pad_top}; padding-bottom:{pad_bottom}; max-width:1260px; }}

/* ======= FONDO ANIMADO (gradiente + blobs + rayas) ======= */
.bg-gradient{{ position:fixed; inset:-12vmax; z-index:-5; pointer-events:none;
  background:
    radial-gradient(120vmax 120vmax at 12% 10%, {t['bg1']}, transparent 60%),
    radial-gradient(110vmax 110vmax at 88% 13%, {t['bg2']}, transparent 60%),
    radial-gradient(100vmax 100vmax at 50% 88%, {t['bg3']}, transparent 55%),
    radial-gradient(90vmax  90vmax  at 90% 78%, {t['bg4']}, transparent 52%);
  filter:saturate(1.1) brightness(1.02); animation:bgfloat 36s ease-in-out infinite;
}}
@keyframes bgfloat{{ 0%{{transform:translateX(0)}} 50%{{transform:translateX(10px)}} 100%{{transform:translateX(0)}} }}

.grid-dots{{ position:fixed; inset:0; z-index:-6; pointer-events:none; opacity:.45;
  background-image: linear-gradient(90deg, rgba(255,255,255,.06) 1px, transparent 1px),
                    linear-gradient(0deg,  rgba(255,255,255,.06) 1px, transparent 1px);
  background-size: 26px 26px, 26px 26px; animation:gridfloat 22s ease-in-out infinite;
}}
@keyframes gridfloat{{ 0%{{transform:translateY(0)}} 50%{{transform:translateY(10px)}} 100%{{transform:translateY(0)}} }}

.blob{{ position:fixed; border-radius:999px; filter:blur(50px); mix-blend-mode:screen; z-index:-4; }}
.blob.one{{ width:420px;height:420px; left:8%; top:12%; background:{t['blob1']}; animation:sway 16s ease-in-out infinite; }}
.blob.two{{ width:360px;height:360px; right:10%; top:18%; background:{t['blob2']}; animation:sway 18s ease-in-out infinite; animation-delay:-6s; }}
.blob.three{{ width:520px;height:520px; left:42%; bottom:-8%; background:{t['blob3']}; animation:sway 20s ease-in-out infinite; animation-delay:-10s; }}
@keyframes sway{{ 0%{{transform:translate(0,0) scale(1)}} 50%{{transform:translate(10px,-8px) scale(1.05)}} 100%{{transform:translate(0,0) scale(1)}} }}

.vignette:before{{ content:""; position:fixed; inset:0; pointer-events:none; z-index:-3;
  background: radial-gradient(ellipse at center, rgba(0,0,0,0) 35%, rgba(0,0,0,.14) 100%);
  mix-blend-mode:multiply;
}}

.diag-stripes{{ position:fixed; inset:0; z-index:-7; pointer-events:none; opacity:.5;
  background-image: repeating-linear-gradient(135deg, {t['stripeA']} 0px, {t['stripeA']} 14px, {t['stripeB']} 14px, {t['stripeB']} 28px);
}}

/* ======= TOPBAR + STEPPER ======= */
.topbar{{ position:sticky; top:0; z-index:20; margin:0 0 10px 0;
  display:flex; align-items:center; justify-content:space-between; gap:12px;
  background:var(--glass); backdrop-filter: blur(12px) saturate(1.15);
  border:1px solid var(--gbrd); border-radius:16px; padding:10px 14px;
  box-shadow: 0 12px 28px rgba(0,0,0,.14), 0 0 0 2px rgba(255,255,255,.04) inset;
}}
.brand{{ display:flex; align-items:center; gap:10px; font-weight:900; letter-spacing:.2px; }}
.brand .logo{{ width:36px;height:36px;border-radius:12px;
  background: conic-gradient(from 180deg, var(--primary), var(--accent), var(--accent2), var(--primary));
  box-shadow: 0 0 0 4px rgba(255,255,255,.06) inset, 0 0 22px var(--glow);
}}
.kpis{{ display:flex; gap:8px; flex-wrap:wrap; align-items:center; }}
.badge{{ display:inline-flex; align-items:center; gap:6px; border-radius:999px; padding:6px 10px;
  background:var(--chipbg); color:var(--chipfg); border:1px solid var(--border);
  font-weight:800; font-size:.82rem; }}

.stepper{{ display:flex; gap:8px; align-items:center; flex-wrap:wrap; margin-top:4px; }}
.step{{ padding:8px 12px; border-radius:14px; border:1px solid var(--border); background:var(--card);
  font-weight:800; font-size:.86rem; position:relative; overflow:hidden; transition: transform .12s ease, box-shadow .12s ease; }}
.step:before{{ content:""; position:absolute; inset:auto auto 0 0; height:3px; width:100%;
  background: linear-gradient(90deg, var(--primary), var(--accent), var(--accent2)); opacity:.38; }}
.step.active{{ border-color:#c7d2fe; box-shadow:0 0 0 3px #a78bfa33 inset, 0 6px 20px rgba(0,0,0,.10); transform: translateY(-1px); }}
.dot{{ width:7px; height:7px; border-radius:999px; background:var(--muted); opacity:.6; }}

/* ======= TARJETAS, CHIPS, RIBBONS ======= */
.card{{ background:var(--card); border:1px solid var(--border); border-radius:18px; padding:12px;
  box-shadow: 0 1px 0 rgba(255,255,255,.04) inset, 0 10px 20px rgba(0,0,0,.06); }}
.ribbon{{ position:relative; overflow:hidden; }}
.ribbon:after{{ content:""; position:absolute; top:10px; right:-30px; width:160px; height:22px;
  background: linear-gradient(90deg,var(--primary),var(--accent),var(--accent2)); transform: rotate(12deg); border-radius:8px; opacity:.4; }}

.select-card{{ position:relative; border-radius:20px; border:2px solid transparent; cursor:pointer;
  background: radial-gradient(120px 120px at 10% 10%, rgba(255,255,255,.12), transparent 60%),
             linear-gradient(var(--card), var(--card)) padding-box,
             linear-gradient(90deg, var(--primary), var(--accent), var(--accent2)) border-box;
  transition: transform .14s ease, box-shadow .14s ease;
  transform: perspective(900px) rotateX(0deg) rotateY(0deg);
}}
.select-card:hover{{ transform: perspective(900px) rotateX(1.2deg) rotateY(-1.2deg) translateY(-2px); box-shadow: 0 24px 40px rgba(0,0,0,.18); }}
.select-card.selected{{ box-shadow:0 0 0 4px #c7d2fe66 inset, 0 24px 48px rgba(0,0,0,.18); }}
.sticker{{ position:absolute; top:-8px; left:-8px; background:var(--accent); color:#001018;
  font-weight:900; padding:5px 9px; border-radius:10px; transform: rotate(-7deg) scale(.98); box-shadow:0 4px 14px rgba(0,0,0,.18); }}

.ph-img{{ height:128px; border-radius:14px; display:flex; align-items:center; justify-content:center;
  background:radial-gradient(ellipse at top, rgba(127,127,170,.25), transparent 60%), var(--patient);
  color:var(--muted); border:1px dashed rgba(127,127,170,.35); }}

.kit-chips{{ display:flex; gap:6px; flex-wrap:wrap; }}
.chip{{ display:inline-flex; align-items:center; gap:6px; padding:5px 9px; border-radius:999px;
  background: linear-gradient(180deg, rgba(255,255,255,.72), rgba(255,255,255,.50)); border:1px solid var(--border);
  font-weight:800; font-size:.80rem; }}

.h-title{{ font-weight:900; font-size:1.58rem; margin:0 0 4px; letter-spacing:.15px; }}
.h-sub{{ color:var(--muted); font-weight:600; margin-bottom:2px; }}
.sep{{ height:1.5px; border:none; margin:12px 0 12px; opacity:.85;
  background:linear-gradient(90deg,var(--primary),var(--accent),var(--accent2)); border-radius:2px; }}

/* ======= GRID COMPACTO ======= */
.grid{{ display:grid; gap:12px; grid-template-columns: repeat(12, 1fr); }}
.col-12{{ grid-column: span 12; }} .col-10{{ grid-column: span 10; }} .col-8{{ grid-column: span 8; }}
.col-6{{ grid-column: span 6; }}  .col-4{{ grid-column: span 4; }}  .col-3{{ grid-column: span 3; }}
@media (max-width:1200px){{ .col-6{{grid-column:span 12}} .col-4{{grid-column:span 6}} .col-3{{grid-column:span 6}} }}

/* ======= BOTONES ======= */
.stButton > button{{ border:none; border-radius:12px; padding:10px 12px; font-weight:900; color:#fff; background:var(--primary);
  box-shadow: 0 8px 22px rgba(0,0,0,.18), 0 0 0 3px #ffffff22 inset; }}
.stButton > button:hover{{ filter:brightness(.97); transform: translateY(-1px); }}
.btn-ghost{{ border:1px solid var(--border)!important; background:transparent!important; color:var(--muted)!important; }}
.small{{ color:var(--muted); font-size:.90rem; }}

/* ======= SEPARADOR ONDULADO (compacto) ======= */
.wave-sep{{ height:22px; margin:6px 0 8px; background:
  radial-gradient(12px 10px at 10px 12px, var(--accent) 40%, transparent 41%),
  radial-gradient(12px 10px at 34px 10px, var(--primary) 40%, transparent 41%),
  radial-gradient(12px 10px at 58px 12px, var(--accent2) 40%, transparent 41%);
  background-size: 68px 22px;
}}

/* ======= PLACEHOLDERS CHAT (usado en Parte 2) ======= */
.chatwrap{{ background:var(--card); border:1px solid var(--border); border-radius:16px; padding:10px; }}
.msg{{ border-radius:12px; padding:8px 10px; margin:6px 0; max-width:96%; border:1px solid var(--border); }}
.msg.agent{{ background:var(--agent); }} .msg.patient{{ background:var(--patient); }}
.typing{{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace; }}

/* ======= FOOTER ======= */
.footer-note{{ opacity:.7; margin:10px 0 6px; text-align:center; }}
</style>
"""
    st.markdown(CSS, unsafe_allow_html=True)

    # Decoraciones (añadimos como divs reales fuera de iframe)
    deco = []
    deco.append('<div class="bg-gradient"></div>')
    if st.session_state.ornaments_on:
        deco += ['<div class="grid-dots"></div>',
                 '<div class="blob one"></div>',
                 '<div class="blob two"></div>',
                 '<div class="blob three"></div>']
    if st.session_state.vignette_on:
        deco.append('<div class="vignette"></div>')
    if st.session_state.stripes_on:
        deco.append('<div class="diag-stripes"></div>')
    st.markdown("".join(deco), unsafe_allow_html=True)

inject_css()

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
            <div class="logo"></div>
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
        <div class="select-card {sel} card ribbon">
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

def info_block(title_txt: str, body_md: str, chips: Optional[List[str]]=None):
    st.markdown('<div class="card">', unsafe_allow_html=True)
    title(title_txt)
    if chips:
        st.markdown("<div class='kit-chips'>" + "".join([f"<span class='chip'>{c}</span>" for c in chips]) + "</div>", unsafe_allow_html=True)
    st.markdown(body_md)
    st.markdown("</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Sidebar — solo tema/ritmo (sin filtros)
# ─────────────────────────────────────────────────────────────────────────────
st.sidebar.markdown("### 🎨 Apariencia")
theme_choice = st.sidebar.radio(
    "Tema de color",
    list(THEMES.keys()),
    index=list(THEMES.keys()).index(st.session_state.theme_name),
)
if theme_choice != st.session_state.theme_name:
    st.session_state.theme_name = theme_choice
    inject_css()

st.session_state.glow_intensity = st.sidebar.slider("Intensidad de brillo", 0.0, 1.0, st.session_state.glow_intensity, 0.01); inject_css()
st.session_state.density_compact = st.sidebar.toggle("Densidad compacta (recomendada)", value=st.session_state.density_compact); inject_css()
st.session_state.vignette_on = st.sidebar.toggle("Vignette", value=st.session_state.vignette_on); inject_css()
st.session_state.ornaments_on = st.sidebar.toggle("Mosaico + blobs", value=st.session_state.ornaments_on); inject_css()
st.session_state.stripes_on = st.sidebar.toggle("Rayas diagonales", value=st.session_state.stripes_on); inject_css()

st.sidebar.markdown("---")
st.sidebar.markdown("### ⏱️ Ritmo humano (Parte 2)")
st.session_state.anim_on = st.sidebar.toggle("Animación de tipeo", value=st.session_state.anim_on)
st.session_state.agent_typing_speed = st.sidebar.slider("Velocidad de tipeo (agente)", 0.005, 0.05, st.session_state.agent_typing_speed, 0.001)
st.session_state.patient_thinking_delay = st.sidebar.slider("Pausa previa (paciente)", 0.2, 3.0, st.session_state.patient_thinking_delay, 0.05)
st.session_state.patient_typing_speed = st.sidebar.slider("Velocidad de tipeo (paciente)", 0.005, 0.05, st.session_state.patient_typing_speed, 0.001)
st.session_state.show_timestamps = st.sidebar.toggle("Mostrar hora en mensajes", value=st.session_state.show_timestamps)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🗒️ Notas del operador")
st.session_state.notes = st.sidebar.text_area("Notas rápidas", value=st.session_state.notes, height=120, placeholder="Observaciones, recordatorios…")

st.sidebar.markdown("---")
c1, c2 = st.sidebar.columns(2)
with c1:
    if st.button("🔄 Reiniciar"):
        for k, v in DEFAULTS.items(): st.session_state[k] = v
        st.rerun()
with c2:
    st.caption("Flujo: Selección → Intro → (Entrevista)")

# ─────────────────────────────────────────────────────────────────────────────
# Topbar + Stepper + separador
# ─────────────────────────────────────────────────────────────────────────────
topbar()
stepper(st.session_state.step)
st.markdown('<div class="sep"></div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# STEP: SELECT
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.step == "select":
    # HERO COLORIDO (compacto)
    st.markdown('<div class="card ribbon">', unsafe_allow_html=True)
    L, R = st.columns([1.25, 1.0], gap="large")
    with L:
        title("Preconsulta asistida", "Selecciona paciente y condición (UI hipercolor)")
        st.markdown(
            """
            <div class="kit-chips" style="margin:6px 0 6px">
              <span class="chip">Neón</span>
              <span class="chip">Animaciones</span>
              <span class="chip">Compacto</span>
              <span class="chip">Sin filtros</span>
            </div>
            """, unsafe_allow_html=True
        )
        st.markdown(
            """
            <div class="card" style="border-radius:14px; border:1px dashed var(--border); background:linear-gradient(180deg, rgba(255,255,255,.70), rgba(255,255,255,.52));">
              <b>Objetivo:</b> en la Parte 2 verás una entrevista con <b>pausas naturales</b> y <b>tipeo por rol</b>,
              generando un <b>reporte clínico</b> en paralelo. Aquí solo eliges.
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
                Personaliza <b>tema</b>, <b>glow</b> y <b>ornamentos</b> desde la barra lateral.
              </div>
              <div class="small" style="margin-top:2px">
                Nada minimalista: gradientes, brillos y “squircles” con tilt.
              </div>
            </div>
            """, unsafe_allow_html=True
        )
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div class="wave-sep"></div>', unsafe_allow_html=True)

    # PACIENTES
    title("Selecciona un paciente")
    cols = st.columns(3, gap="large")
    for i, p in enumerate(PACIENTES):
        with cols[i % 3]:
            is_sel = (st.session_state.sel_patient == p.pid)
            patient_card(p, is_sel)
            label = "Seleccionado" if is_sel else "Elegir"
            if st.button(label, key=f"pick_{p.pid}", use_container_width=True):
                st.session_state.sel_patient = p.pid
                st.rerun()

    st.markdown('<div class="wave-sep"></div>', unsafe_allow_html=True)

    # CONDICIONES
    title("Explora una condición", "Elige la condición a evaluar")
    cols2 = st.columns(2, gap="large")
    for idx, c in enumerate(CONDICIONES):
        with cols2[idx % 2]:
            is_sel = (st.session_state.sel_condition == c.cid)
            condition_card(c, is_sel)
            label = "Seleccionada" if is_sel else "Elegir"
            if st.button(label, key=f"cond_{c.cid}", use_container_width=True):
                st.session_state.sel_condition = c.cid
                st.rerun()

    st.markdown('<div class="wave-sep"></div>', unsafe_allow_html=True)

    # CTA
    CTA1, CTA2, CTA3 = st.columns([1.1, 1.1, 2.8], gap="large")
    with CTA1:
        can_go = st.session_state.sel_patient and st.session_state.sel_condition
        if st.button("Continuar", disabled=not can_go, use_container_width=True):
            st.session_state.step = "intro"; st.rerun()
    with CTA2:
        if st.button("Volver a inicio", use_container_width=True):
            st.session_state.sel_patient = None; st.session_state.sel_condition = None; st.rerun()
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
# STEP: INTRO
# ─────────────────────────────────────────────────────────────────────────────
elif st.session_state.step == "intro":
    p = next(x for x in PACIENTES if x.pid == st.session_state.sel_patient)
    c = next(x for x in CONDICIONES if x.cid == st.session_state.sel_condition)

    headL, headR = st.columns([1.25, 1.0], gap="large")
    with headL:
        st.markdown('<div class="card ribbon">', unsafe_allow_html=True)
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
               - Queremos que se sienta **humano**, no una ráfaga.  
            3) El **reporte** se arma durante la conversación (Motivo, HPI, antecedentes, medicaciones y hechos útiles).  
            4) Verás **faltantes** sugeridos al cierre para calidad clínica.
            """),
            chips=["Ritmo humano", "Exportación (en Parte 2)", "Diseño hipercolor"]
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
        - **Glow:** {st.session_state.glow_intensity:.2f}  
        - **Densidad compacta:** {"sí" if st.session_state.density_compact else "no"}  
        - **Vignette:** {"sí" if st.session_state.vignette_on else "no"}  
        - **Mosaicos/blobs:** {"sí" if st.session_state.ornaments_on else "no"}
        - **Rayas diagonales:** {"sí" if st.session_state.stripes_on else "no"}  
        """),
        chips=["Neón", "Brillos", "Animación"]
    )
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="wave-sep"></div>', unsafe_allow_html=True)

    # CTAs
    B1, B2, B3 = st.columns([1.1, 1.1, 2.8], gap="large")
    with B1:
        if st.button("◀ Regresar", use_container_width=True):
            st.session_state.step = "select"; st.rerun()
    with B2:
        if st.session_state.convo_enabled:
            if st.button("Iniciar entrevista", use_container_width=True):
                st.session_state.step = "convo"; st.session_state.chat_idx = -1; st.session_state.pause = False; st.rerun()
        else:
            st.button("Iniciar entrevista", key="start_disabled", use_container_width=True, disabled=True)
            st.caption("Pega la PARTE 2 para habilitar la entrevista.")
    with B3:
        st.markdown(
            f"<div class='kpis'>"
            f"<span class='badge'>Paciente: {p.nombre}</span>"
            f"<span class='badge'>Condición: {c.titulo}</span>"
            f"<span class='badge'>Conversación guiada</span>"
            f"</div>", unsafe_allow_html=True
        )

# ─────────────────────────────────────────────────────────────────────────────
# Footer
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    "<div class='footer-note small'>Hecho con ⚡ colores/animaciones — UI compacta, cero huecos, <b>sin filtros</b>.</div>",
    unsafe_allow_html=True,
)
# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  FIN PARTE 1/2                                                             ║
# ╚════════════════════════════════════════════════════════════════════════════╝
