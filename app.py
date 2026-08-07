import json
import numpy as np
import streamlit as st
from collections import Counter
from src.db_manager import get_connection
from src.config import DATA_DIR

st.set_page_config(page_title="Dota Draft Advisor", page_icon="🛡️", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    div[data-testid="stVerticalBlockBorderWrapper"] { transition: transform 0.3s ease, box-shadow 0.3s ease, border-color 0.3s ease; }
    div[data-testid="stVerticalBlockBorderWrapper"]:hover { transform: translateY(-4px); box-shadow: 0 8px 20px rgba(214, 54, 50, 0.25) !important; border-color: #d63632 !important; }
    div[data-testid="stMetricValue"] { font-size: 2rem !important; font-weight: 800 !important; }
    .block-container { padding-top: 2rem !important; }
</style>
""", unsafe_allow_html=True)

st.title("🛡️ Dota 2 Draft Advisor")
st.caption("Sistema avanzado de evaluación de matchups impulsado por IA y analítica de datos. (Versión de Producción)")
st.divider()

conn = get_connection()
conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
cur = conn.cursor()

my_pool_dir = DATA_DIR / "my_pool"
my_pool_filenames = [f.stem.replace("_", " ").title() for f in my_pool_dir.glob("*.json")]

if my_pool_filenames:
    cur.execute(f"""
        SELECT hero_id, name FROM heroes 
        WHERE replace(lower(name), ' ', '') IN ({','.join(['replace(lower(?), " ", "")'] * len(my_pool_filenames))})
        ORDER BY name
    """, tuple(my_pool_filenames))
else:
    cur.execute("SELECT hero_id, name FROM heroes WHERE 0")
    
own_pool_rows = cur.fetchall()
own_pool_heroes = {h["name"]: h["hero_id"] for h in own_pool_rows}

tab1, tab2, tab3, tab4 = st.tabs(["⚔️ Simulador de Draft", "🎯 Explorador Individual", "📋 Top 5 Global", "📈 Meta Stats"])

EXCLUSIVE_ITEM_GROUPS = [{"item_boots", "item_phase_boots", "item_power_treads", "item_arcane_boots", "item_tranquil_boots", "item_boots_of_travel", "item_boots_of_travel_2", "item_guardian_greaves", "boots", "phase_boots", "power_treads", "arcane_boots", "tranquil_boots", "boots_of_travel", "boots_of_travel_2", "guardian_greaves"}]
UPGRADE_FAMILIES = [
    {"base": ["item_basher", "basher", "item_skull_basher", "skull_basher"], "upgrades": ["item_abyssal_blade", "abyssal_blade"]},
    {"base": ["item_blink", "blink", "item_blink_dagger", "blink_dagger"], "upgrades": ["item_swift_blink", "swift_blink", "item_overwhelming_blink", "overwhelming_blink", "item_arcane_blink", "arcane_blink"]},
    {"base": ["item_echo_sabre", "echo_sabre"], "upgrades": ["item_harpoon", "harpoon"]},
    {"base": ["item_maelstrom", "maelstrom"], "upgrades": ["item_mjollnir", "mjollnir", "item_gleipnir", "gleipnir"]},
    {"base": ["item_invis_sword", "invis_sword", "item_shadow_blade", "shadow_blade"], "upgrades": ["item_silver_edge", "silver_edge"]},
    {"base": ["item_dragon_lance", "dragon_lance", "item_force_staff", "force_staff"], "upgrades": ["item_hurricane_pike", "hurricane_pike"]},
    {"base": ["item_diffusal_blade", "diffusal_blade"], "upgrades": ["item_disperser", "disperser"]},
    {"base": ["item_lesser_crit", "lesser_crit", "item_crystalys", "crystalys"], "upgrades": ["item_greater_crit", "greater_crit", "item_daedalus", "daedalus", "item_bloodthorn", "bloodthorn"]},
    {"base": ["item_yasha", "yasha"], "upgrades": ["item_manta", "manta", "item_manta_style", "manta_style", "item_sange_and_yasha", "sange_and_yasha"]},
    {"base": ["item_sange", "sange"], "upgrades": ["item_heavens_halberd", "heavens_halberd", "item_sange_and_yasha", "sange_and_yasha", "item_kaya_and_sange", "kaya_and_sange"]},
    {"base": ["item_orchid", "orchid", "item_orchid_malevolence", "orchid_malevolence"], "upgrades": ["item_bloodthorn", "bloodthorn"]},
    {"base": ["item_vanguard", "vanguard"], "upgrades": ["item_crimson_guard", "crimson_guard", "item_abyssal_blade", "abyssal_blade"]}
]
SKIP_ITEMS = {"item_boots", "boots", "item_phase_boots", "phase_boots", "item_power_treads", "power_treads", "item_arcane_boots", "arcane_boots", "item_tranquil_boots", "tranquil_boots", "item_magic_wand", "magic_wand", "item_bracer", "bracer", "item_wraith_band", "wraith_band", "item_null_talisman", "null_talisman"}

def get_volatility_badge(sigma):
    """Devuelve el diseño del badge según el valor matemático precalculado en la BD"""
    if sigma < 1.0: return "Estable", "green", "🟢"
    elif sigma < 2.2: return "Moderada", "yellow", "🟡"
    elif sigma < 3.5: return "Alta", "orange", "🟠"
    else: return "Extrema", "red", "🔴"

with tab1:
    st.markdown("### 🧠 Analizador de Enemigos en Vivo")
    with st.container(border=True):
        cols = st.columns(5)
        selected_enemies_draft = []
        for i in range(5):
            with cols[i]:
                e_pos = st.selectbox(f"Posición {i+1}", ["pos1", "pos2", "pos3", "pos4", "pos5"], key=f"draft_pos_{i}")
                cur.execute("SELECT h.hero_id, h.name FROM heroes h JOIN hero_positions hp ON h.hero_id = hp.hero_id WHERE hp.position = ? AND hp.is_own_pool = 0 ORDER BY h.name", (e_pos,))
                position_enemies = {h["name"]: h["hero_id"] for h in cur.fetchall()}
                e_name = st.selectbox(f"Enemigo {i+1}", ["-- Seleccionar --"] + list(position_enemies.keys()), key=f"draft_hero_{i}")
                if e_name != "-- Seleccionar --": selected_enemies_draft.append({"hero_id": position_enemies[e_name], "name": e_name, "position": e_pos})

    if selected_enemies_draft:
        st.write("") 
        if st.button("🔍 Calcular Mejores Picks", type="primary", use_container_width=True):
            st.divider()
            hero_totals = []
            for own_name, own_id in own_pool_heroes.items():
                total_score = 0.0
                matchup_details = []
                for enemy in selected_enemies_draft:
                    # AHORA LEEMOS LOS NUEVOS CAMPOS DESDE LA BASE DE DATOS
                    cur.execute("""
                        SELECT score_laning, score_midgame, score_lategame, recommended_items, volatility_score
                        FROM matchups WHERE own_hero_id = ? AND enemy_hero_id = ? AND enemy_position = ?
                    """, (own_id, enemy["hero_id"], enemy["position"]))
                    row = cur.fetchone()
                    if row:
                        is_pos1 = row["score_laning"] is None
                        global_score = (row["score_midgame"] + row["score_lategame"]) / 2.0 if is_pos1 else (row["score_laning"] + row["score_midgame"] + row["score_lategame"]) / 3.0
                        total_score += global_score
                        
                        matchup_details.append({
                            "enemy_name": enemy["name"], "position": enemy["position"], "score_global": global_score,
                            "score_laning": row["score_laning"], "score_midgame": row["score_midgame"], "score_lategame": row["score_lategame"],
                            "sigma": row.get("volatility_score", 0.0), "items": json.loads(row["recommended_items"] or "[]")
                        })
                
                if matchup_details:
                    hero_totals.append({"name": own_name, "id": own_id, "score_total": round(total_score / len(matchup_details), 2), "details": matchup_details})
            
            hero_totals.sort(key=lambda x: x["score_total"], reverse=True)
            if hero_totals:
                st.markdown("## 🏆 Recomendaciones del Sistema")
                rec_cols = st.columns(min(3, len(hero_totals)))
                for idx, rec in enumerate(hero_totals[:3]):
                    with rec_cols[idx]:
                        with st.container(border=True):
                            st.subheader(f"#{idx+1}: {rec['name']}")
                            st.metric("Puntaje Global", f"{rec['score_total']}")
                            
                            with st.expander("📊 Ver desglose de puntajes"):
                                for det in rec["details"]:
                                    l_str = "N/A" if det['score_laning'] is None else f"{det['score_laning']:+.1f}"
                                    
                                    # Generar badge visual
                                    vol_str = ""
                                    if det['sigma'] >= 1.0:
                                        lvl, color, icon = get_volatility_badge(det['sigma'])
                                        vol_str = f" | {icon} Volatilidad: :{color}[{lvl} (σ: {det['sigma']})]"
                                        
                                    st.markdown(f"**vs {det['enemy_name']}** -> Global: `{det['score_global']:.1f}`{vol_str}")
                                    st.caption(f"L: {l_str} | M: {det['score_midgame']:+.1f} | L: {det['score_lategame']:+.1f}")
                                    st.markdown("---")
                                    
                            with st.expander("🎒 Build Recomendada Inteligente"):
                                item_weights = {}
                                for det in rec["details"]:
                                    peso_amenaza = max(1, int(10 - det["score_global"]))
                                    for item in det["items"]:
                                        if isinstance(item, dict) and "item_id" in item:
                                            i_id = item["item_id"]
                                            item_weights[i_id] = item_weights.get(i_id, 0) + peso_amenaza
                                
                                for family in UPGRADE_FAMILIES:
                                    mejoras_presentes = [upg for upg in family["upgrades"] if upg in item_weights]
                                    bases_presentes = [b for b in family["base"] if b in item_weights]
                                    if mejoras_presentes and bases_presentes:
                                        mejora_principal = max(mejoras_presentes, key=lambda x: item_weights[x])
                                        for b in bases_presentes:
                                            item_weights[mejora_principal] += item_weights[b]
                                            del item_weights[b]
                                
                                if item_weights:
                                    items_ordenados = sorted(item_weights.items(), key=lambda x: x[1], reverse=True)
                                    build_final = []
                                    grupos_usados = set()
                                    for i_id, peso in items_ordenados:
                                        if i_id in SKIP_ITEMS: continue
                                        if len(build_final) >= 6: break
                                        conflicto = False
                                        grupo_index = -1
                                        for idx_g, grupo in enumerate(EXCLUSIVE_ITEM_GROUPS):
                                            if i_id in grupo:
                                                grupo_index = idx_g
                                                if idx_g in grupos_usados: conflicto = True
                                                break
                                        if not conflicto:
                                            build_final.append((i_id, peso))
                                            if grupo_index != -1: grupos_usados.add(grupo_index)

                                    if build_final:
                                        max_peso = build_final[0][1]
                                        for i_id, peso in build_final:
                                            ratio = peso / max_peso
                                            if ratio >= 0.75: estrellas = "⭐⭐⭐ (Vital)"
                                            elif ratio >= 0.40: estrellas = "⭐⭐ (Importante)"
                                            else: estrellas = "⭐ (Situacional)"
                                            st.markdown(f"- **{i_id.replace('item_', '').replace('_', ' ').title()}** {estrellas}")
                                    else:
                                        st.info("Sin items recomendados tras aplicar filtros.")
                                else:
                                    st.info("Sin items registrados.")

with tab2:
    st.markdown("### 🔎 Buscar Matchup Específico")
    if not own_pool_heroes:
        st.warning("No se encontraron héroes.")
    else:
        with st.container(border=True):
            col1, col2 = st.columns(2)
            with col1: selected_hero_name = st.selectbox("Tu Héroe (Pos 1):", list(own_pool_heroes.keys()), key="t1_hero")
            with col2: position = st.selectbox("Contra Posición enemiga:", ["pos1", "pos2", "pos3", "pos4", "pos5"], key="t1_pos")
            
        selected_hero_id = own_pool_heroes[selected_hero_name]
        
        # AHORA LEEMOS LOS NUEVOS CAMPOS DESDE LA BASE DE DATOS
        cur.execute("""
            SELECT e.name as enemy_name, m.score_laning, m.score_midgame, m.score_lategame, m.analisis_mecanico_previo, m.clean_razon, m.recommended_items, m.volatility_score
            FROM matchups m JOIN heroes e ON m.enemy_hero_id = e.hero_id
            WHERE m.own_hero_id = ? AND m.enemy_position = ?
            ORDER BY CASE WHEN m.score_laning IS NULL THEN (m.score_midgame + m.score_lategame) / 2.0
            ELSE (m.score_laning + m.score_midgame + m.score_lategame) / 3.0 END DESC
        """, (selected_hero_id, position))
        
        rows = cur.fetchall()
        
        if rows:
            for r in rows:
                is_pos1 = r["score_laning"] is None
                score_global = (r["score_midgame"] + r["score_lategame"]) / 2.0 if is_pos1 else (r["score_laning"] + r["score_midgame"] + r["score_lategame"]) / 3.0
                laning_str = "N/A" if is_pos1 else f"{r['score_laning']:+.1f}"
                sigma = r.get("volatility_score", 0.0)
                
                with st.container(border=True):
                    c_h, c_s, c_f = st.columns([2, 1, 2])
                    with c_h: st.markdown(f"**⚔️ vs {r['enemy_name']}**")
                    with c_s: st.markdown(f"**Global:** :{'green' if score_global >= 0 else 'red'}[{score_global:.1f}]")
                    with c_f: st.caption(f"Fases: [L: {laning_str} | M: {r['score_midgame']:+.1f} | L: {r['score_lategame']:+.1f}]")
                    
                    with st.expander("Ver Justificación de la IA"): 
                        if sigma >= 1.0:
                            lvl, color, icon = get_volatility_badge(sigma)
                            st.markdown(f"**Índice de Volatilidad:** {icon} :{color}[{lvl}] *(Score Matemático de Dispersión: {sigma})*")
                            
                        st.caption(r["analisis_mecanico_previo"])
                        st.markdown(r["clean_razon"], unsafe_allow_html=True) # Imprimimos el texto purificado
                        
                        items_crudos = json.loads(r["recommended_items"] or "[]")
                        if items_crudos:
                            lista_items = [i.get("item_id", "").replace("item_", "").replace("_", " ").title() for i in items_crudos if isinstance(i, dict) and "item_id" in i]
                            if lista_items:
                                st.markdown(f"**🎒 Ítems Clave Sugeridos:** `{', '.join(lista_items)}`")
        else:
            st.info("No hay datos generados para este cruce específico.")

with tab3:
    st.markdown("### 👑 Fuerza Global de tu Pool")
    if len(own_pool_rows) >= 5:
        # Usamos el motor SQL para un promedio matemáticamente perfecto
        cur.execute("""
            SELECT h.name, 
                   AVG(CASE WHEN m.score_laning IS NULL THEN (m.score_midgame + m.score_lategame) / 2.0 
                            ELSE (m.score_laning + m.score_midgame + m.score_lategame) / 3.0 END) as promedio
            FROM heroes h 
            JOIN matchups m ON h.hero_id = m.own_hero_id 
            WHERE h.is_own_pool = 1 
            GROUP BY h.hero_id, h.name 
            ORDER BY promedio DESC
        """)
        hero_global_averages = cur.fetchall()
        
        cols = st.columns(5)
        for idx, hero in enumerate(hero_global_averages[:5]):
            with cols[idx]:
                with st.container(border=True): 
                    st.metric(f"#{idx+1} {hero['name']}", f"{hero['promedio']:.2f}")
with tab4:
    st.markdown("### 📊 Tableros de Riesgo")
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        with st.container(border=True):
            st.markdown("#### 🥇 Rendimiento General")
            cur.execute("SELECT h.name as 'Héroe', AVG(CASE WHEN m.score_laning IS NULL THEN (m.score_midgame + m.score_lategame) / 2.0 ELSE (m.score_laning + m.score_midgame + m.score_lategame) / 3.0 END) as Promedio FROM heroes h JOIN matchups m ON h.hero_id = m.own_hero_id WHERE h.is_own_pool = 1 GROUP BY h.hero_id, h.name ORDER BY Promedio DESC")
            datos_pool = cur.fetchall()
            if datos_pool: st.dataframe([{"Héroe": f["Héroe"], "Puntaje": f"{f['Promedio']:+.2f}"} for f in datos_pool], use_container_width=True, hide_index=True)
    with col_t2:
        with st.container(border=True):
            st.markdown("#### 💀 Peligros del Meta (Counters)")
            cur.execute("SELECT e.name as 'Enemigo', UPPER(m.enemy_position) as 'Rol', AVG(CASE WHEN m.score_laning IS NULL THEN (m.score_midgame + m.score_lategame) / 2.0 ELSE (m.score_laning + m.score_midgame + m.score_lategame) / 3.0 END) as Promedio FROM matchups m JOIN heroes e ON m.enemy_hero_id = e.hero_id GROUP BY m.enemy_hero_id, e.name, m.enemy_position ORDER BY Promedio ASC")
            datos_enemigos = cur.fetchall()
            if datos_enemigos: st.dataframe([{"Enemigo": f["Enemigo"], "Rol": f["Rol"], "Daño Promedio": f"{f['Promedio']:+.2f}"} for f in datos_enemigos], use_container_width=True, hide_index=True)

conn.close()