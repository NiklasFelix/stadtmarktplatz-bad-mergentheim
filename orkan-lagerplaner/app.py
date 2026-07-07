"""
OrKan-System – KI-gestütztes Lagerplanungs-Tool
Stufe 1: Dateneingabe, Strukturierung und Zusammenfassung
"""

import json
import math
import re
import streamlit as st
import pandas as pd
from storage import list_projects, load_project, save_project, delete_project, new_project
from zone_taxonomy import ZONE_DEFAULTS, ZONE_CODE_OPTIONS, CATEGORY_OPTIONS, RACK_TYPES, CATEGORY_COLORS

st.set_page_config(
    page_title="OrKan – Lagerplanungs-Tool",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Styling ──────────────────────────────────────────────────────────────────

st.markdown("""
<style>
  [data-testid="stSidebar"] { background: #1b4f8a; }
  [data-testid="stSidebar"] * { color: white !important; }
  [data-testid="stSidebar"] .stSelectbox label { color: #d5e2f5 !important; }
  [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color: #d5e2f5 !important; }
  .metric-card { background: #f8fafc; border-radius: 8px; padding: 12px 16px; border-left: 4px solid #1b4f8a; margin-bottom: 8px; }
  .warn-card { background: #fef9ec; border-radius: 8px; padding: 12px 16px; border-left: 4px solid #f59e0b; margin-bottom: 8px; }
  .zone-chip { display:inline-block; padding: 2px 10px; border-radius: 12px; font-size:12px; font-weight:600; margin: 2px; }
</style>
""", unsafe_allow_html=True)

# ─── Session State ─────────────────────────────────────────────────────────────

def _init_state():
    if "project" not in st.session_state:
        st.session_state.project = None
    if "dirty" not in st.session_state:
        st.session_state.dirty = False

_init_state()

# ─── Sidebar – Projektverwaltung ──────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🏭 OrKan Lagerplaner")
    st.markdown("---")

    st.markdown("### Neues Projekt")
    new_name = st.text_input("Projektbezeichnung", placeholder="z. B. Sanitär Bauer GmbH")
    new_customer = st.text_input("Kunde / Betrieb", placeholder="z. B. Bauer GmbH Mannheim")
    if st.button("➕ Projekt erstellen", use_container_width=True):
        if new_name.strip():
            proj = new_project(new_name.strip(), new_customer.strip())
            save_project(proj)
            st.session_state.project = proj
            st.session_state.dirty = False
            st.rerun()
        else:
            st.error("Bitte Projektbezeichnung angeben.")

    st.markdown("---")
    st.markdown("### Vorhandene Projekte")
    all_projects = list_projects()
    if all_projects:
        options = {f"{p['name']} ({p['customer']})": p["id"] for p in all_projects}
        selected_label = st.selectbox(
            "Projekt laden",
            options=list(options.keys()),
            index=None,
            placeholder="— Projekt wählen —",
        )
        if selected_label:
            loaded = load_project(options[selected_label])
            if loaded and (st.session_state.project is None or loaded["id"] != st.session_state.project.get("id")):
                st.session_state.project = loaded
                st.session_state.dirty = False
                st.rerun()
    else:
        st.info("Noch keine Projekte vorhanden.")

    if st.session_state.project:
        st.markdown("---")
        st.markdown(f"**Aktiv:** {st.session_state.project['name']}")
        if st.session_state.dirty:
            st.warning("⚠ Ungespeicherte Änderungen")
        if st.button("💾 Projekt speichern", use_container_width=True):
            save_project(st.session_state.project)
            st.session_state.dirty = False
            st.success("Gespeichert ✓")

# ─── Main ─────────────────────────────────────────────────────────────────────

if st.session_state.project is None:
    st.title("OrKan-System – Lagerplanungs-Tool")
    st.info("👈 Bitte links ein neues Projekt erstellen oder ein vorhandenes laden.")
    st.markdown("""
    **Workflow (Stufe 1 – Dateneingabe):**
    1. Neues Projekt anlegen (Kunde + Bezeichnung)
    2. **Raum** erfassen: Grundriss-Eckpunkte, Höhe, Stützen, Tore/Türen
    3. **Zonen** definieren: Welche Warengruppe wo, wie viel Fläche, welcher Regaltyp
    4. **Zusammenfassung** prüfen und als JSON exportieren

    Ab Stufe 2 berechnet das Tool automatisch einen Platzierungsvorschlag.
    """)
    st.stop()

proj = st.session_state.project

st.title(f"🏭 {proj['name']}")
if proj.get("customer"):
    st.caption(f"Kunde: {proj['customer']}  ·  Projekt-ID: {proj['id']}")

tab_raum, tab_zonen, tab_summary = st.tabs(["📐 Raum", "📦 Zonen-Bedarf", "📋 Zusammenfassung"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 – RAUM
# ══════════════════════════════════════════════════════════════════════════════

with tab_raum:
    room = proj["room"]

    col_l, col_r = st.columns([1, 1])

    with col_l:
        st.subheader("Raumparameter")
        room["height_m"] = st.number_input(
            "Lichte Raumhöhe (m)", min_value=2.0, max_value=15.0,
            value=float(room.get("height_m", 4.0)), step=0.1,
        )
        room["min_aisle_m"] = st.number_input(
            "Mindest-Gangbreite (m)", min_value=0.6, max_value=5.0,
            value=float(room.get("min_aisle_m", 1.0)), step=0.1,
            help="Minimale Gangbreite zwischen Zonen (gilt global). Für Staplerverkehr mind. 2,5 m.",
        )

    with col_r:
        st.subheader("Grundriss-Vorschau")
        # Berechne Raumfläche via Shoelace-Formel
        pts = room.get("outline", [])
        if len(pts) >= 3:
            n = len(pts)
            area = abs(sum(
                pts[i]["x"] * pts[(i+1) % n]["y"] - pts[(i+1) % n]["x"] * pts[i]["y"]
                for i in range(n)
            )) / 2.0
            # Bounding box
            xs = [p["x"] for p in pts]
            ys = [p["y"] for p in pts]
            bbox_w = max(xs) - min(xs)
            bbox_h = max(ys) - min(ys)
            st.metric("Bruttofläche (berechnet)", f"{area:.1f} m²")
            st.caption(f"Bounding-Box: {bbox_w:.1f} m × {bbox_h:.1f} m")
        else:
            st.info("Bitte Grundriss-Eckpunkte eingeben (mind. 3 Punkte).")

    st.markdown("---")
    st.subheader("Grundriss – Eckpunkte (im Uhrzeigersinn)")
    st.caption("Koordinaten in Metern. Startpunkt = linke untere Ecke (0, 0). Polygonzug wird automatisch geschlossen.")

    outline_df = pd.DataFrame(room.get("outline", [{"x": 0.0, "y": 0.0}]))
    edited_outline = st.data_editor(
        outline_df,
        column_config={
            "x": st.column_config.NumberColumn("X (m)", min_value=0.0, format="%.2f"),
            "y": st.column_config.NumberColumn("Y (m)", min_value=0.0, format="%.2f"),
        },
        num_rows="dynamic",
        use_container_width=True,
        key="outline_editor",
    )
    room["outline"] = edited_outline.dropna().to_dict("records")

    st.markdown("---")
    st.subheader("Hindernisse (Stützen, Säulen, feste Einbauten)")
    st.caption("Alle Maße in Metern. Position = Mittelpunkt. Radius für runde Stützen, Breite+Tiefe für rechteckige.")

    obs_defaults = pd.DataFrame(room.get("obstacles", []), columns=["type", "x", "y", "radius_m", "width_m", "depth_m"])
    edited_obs = st.data_editor(
        obs_defaults if len(obs_defaults) > 0 else pd.DataFrame(columns=["type", "x", "y", "radius_m", "width_m", "depth_m"]),
        column_config={
            "type": st.column_config.SelectboxColumn("Typ", options=["Stütze rund", "Stütze eckig", "Pfeiler", "Sonstiges"]),
            "x": st.column_config.NumberColumn("X (m)", format="%.2f"),
            "y": st.column_config.NumberColumn("Y (m)", format="%.2f"),
            "radius_m": st.column_config.NumberColumn("Radius (m)", format="%.2f", help="Nur für runde Stützen"),
            "width_m": st.column_config.NumberColumn("Breite (m)", format="%.2f", help="Nur für eckige Stützen"),
            "depth_m": st.column_config.NumberColumn("Tiefe (m)", format="%.2f", help="Nur für eckige Stützen"),
        },
        num_rows="dynamic",
        use_container_width=True,
        key="obs_editor",
    )
    room["obstacles"] = edited_obs.dropna(how="all").to_dict("records")

    st.markdown("---")
    st.subheader("Öffnungen (Tore, Türen, Fenster)")
    st.caption(
        "**Wandindex**: 0 = Wand von Punkt 0→1, 1 = von Punkt 1→2, usw. "
        "**Abstand** = Meter von Anfang der Wand. "
        "Für rechteckige Räume: Wand 0 = Südwand (unten), 1 = Ostwand (rechts), 2 = Nordwand (oben), 3 = Westwand (links)."
    )

    open_defaults = pd.DataFrame(room.get("openings", []), columns=["type", "wall_index", "offset_m", "width_m", "notes"])
    edited_openings = st.data_editor(
        open_defaults if len(open_defaults) > 0 else pd.DataFrame(columns=["type", "wall_index", "offset_m", "width_m", "notes"]),
        column_config={
            "type": st.column_config.SelectboxColumn("Typ", options=["Tor", "Tür", "Fenster", "Ladezone", "Sonstiges"]),
            "wall_index": st.column_config.NumberColumn("Wand-Index", min_value=0, step=1),
            "offset_m": st.column_config.NumberColumn("Abstand von Wandanfang (m)", min_value=0.0, format="%.2f"),
            "width_m": st.column_config.NumberColumn("Breite (m)", min_value=0.1, format="%.2f"),
            "notes": st.column_config.TextColumn("Anmerkung"),
        },
        num_rows="dynamic",
        use_container_width=True,
        key="openings_editor",
    )
    room["openings"] = edited_openings.dropna(how="all").to_dict("records")

    proj["room"] = room
    st.session_state.dirty = True

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 – ZONEN-BEDARF
# ══════════════════════════════════════════════════════════════════════════════

with tab_zonen:
    st.subheader("Zonen-Bedarf für dieses Projekt")
    st.caption(
        "Definiert, welche Warengruppen gelagert werden sollen. "
        "Beim Auswählen eines bekannten Zonencodes werden Standardwerte vorausgefüllt."
    )

    # ── Zone hinzufügen ────────────────────────────────────────────────────────
    with st.expander("➕ Zone hinzufügen", expanded=len(proj.get("zones", [])) == 0):
        col1, col2 = st.columns([1, 2])
        with col1:
            preset_code = st.selectbox(
                "Zonencode aus Taxonomie wählen (Vorausfüllung)",
                options=["— manuell eingeben —"] + ZONE_CODE_OPTIONS,
                key="preset_zone_code",
            )
        with col2:
            if preset_code and preset_code != "— manuell eingeben —":
                defaults = ZONE_DEFAULTS[preset_code]
                st.info(f"**{preset_code} – {defaults['name']}** | Kategorie: {defaults['category']}")

        c1, c2, c3 = st.columns(3)
        with c1:
            zone_code = st.text_input(
                "Zonencode*",
                value=preset_code if preset_code != "— manuell eingeben —" else "",
                key="new_zone_code",
            )
            zone_name = st.text_input(
                "Bezeichnung*",
                value=ZONE_DEFAULTS[preset_code]["name"] if preset_code in ZONE_DEFAULTS else "",
                key="new_zone_name",
            )
            zone_category = st.selectbox(
                "Kategorie*",
                options=CATEGORY_OPTIONS + ["— Sonstige —"],
                index=CATEGORY_OPTIONS.index(ZONE_DEFAULTS[preset_code]["category"]) if preset_code in ZONE_DEFAULTS else 0,
                key="new_zone_cat",
            )

        with c2:
            zone_area = st.number_input(
                "Benötigte Fläche (m²)*",
                min_value=0.5, max_value=500.0, step=0.5,
                value=float(ZONE_DEFAULTS[preset_code]["typical_area_m2"]) if preset_code in ZONE_DEFAULTS else 10.0,
                key="new_zone_area",
            )
            zone_wall_len = st.number_input(
                "Benötigte Wandlänge (m)",
                min_value=0.0, max_value=50.0, step=0.5,
                value=float(ZONE_DEFAULTS[preset_code]["needs_wall_length_m"]) if preset_code in ZONE_DEFAULTS else 0.0,
                key="new_zone_wall",
                help="0 = kein Wandanschluss nötig",
            )
            zone_min_depth = st.number_input(
                "Mindest-Tiefe (m)",
                min_value=0.3, max_value=10.0, step=0.1,
                value=float(ZONE_DEFAULTS[preset_code]["min_depth_m"]) if preset_code in ZONE_DEFAULTS else 0.6,
                key="new_zone_min_depth",
            )
            zone_max_depth = st.number_input(
                "Max. Tiefe (m)",
                min_value=0.3, max_value=20.0, step=0.1,
                value=float(ZONE_DEFAULTS[preset_code]["max_depth_m"]) if preset_code in ZONE_DEFAULTS else 3.0,
                key="new_zone_max_depth",
            )

        with c3:
            zone_racks = st.multiselect(
                "Bevorzugte Regaltypen",
                options=RACK_TYPES,
                default=ZONE_DEFAULTS[preset_code]["preferred_rack_types"] if preset_code in ZONE_DEFAULTS else [],
                key="new_zone_racks",
            )
            zone_priority = st.selectbox(
                "Priorität",
                options=[("1 – Muss platziert werden", 1), ("2 – Sollte platziert werden", 2), ("3 – Optional", 3)],
                index=int(ZONE_DEFAULTS[preset_code]["priority"]) - 1 if preset_code in ZONE_DEFAULTS else 0,
                format_func=lambda x: x[0],
                key="new_zone_prio",
            )
            zone_adj = st.multiselect(
                "Nachbarschaft bevorzugt (Zonencodes)",
                options=ZONE_CODE_OPTIONS,
                default=[z for z in (ZONE_DEFAULTS[preset_code]["adjacency_preference"] if preset_code in ZONE_DEFAULTS else []) if z in ZONE_CODE_OPTIONS],
                key="new_zone_adj",
            )
            zone_needs_wall = st.checkbox(
                "Wandmontage erforderlich (Kragarmregal o. ä.)",
                value=ZONE_DEFAULTS[preset_code]["needs_wall"] if preset_code in ZONE_DEFAULTS else False,
                key="new_zone_needs_wall",
            )

        zone_notes = st.text_area(
            "Anmerkungen / Sonderanforderungen",
            value=ZONE_DEFAULTS[preset_code]["notes"] if preset_code in ZONE_DEFAULTS else "",
            key="new_zone_notes",
            height=60,
        )

        if st.button("✅ Zone übernehmen", type="primary"):
            if not zone_code.strip() or not zone_name.strip():
                st.error("Zonencode und Bezeichnung sind Pflichtfelder.")
            elif any(z["zone_code"] == zone_code.strip() for z in proj.get("zones", [])):
                st.error(f"Zonencode '{zone_code.strip()}' existiert bereits in diesem Projekt.")
            else:
                new_zone = {
                    "zone_code": zone_code.strip(),
                    "name": zone_name.strip(),
                    "category": zone_category,
                    "required_area_m2": zone_area,
                    "needs_wall_length_m": zone_wall_len,
                    "min_depth_m": zone_min_depth,
                    "max_depth_m": zone_max_depth,
                    "preferred_rack_types": zone_racks,
                    "priority": zone_priority[1],
                    "adjacency_preference": zone_adj,
                    "needs_wall": zone_needs_wall,
                    "notes": zone_notes.strip(),
                }
                if "zones" not in proj:
                    proj["zones"] = []
                proj["zones"].append(new_zone)
                save_project(proj)
                st.session_state.dirty = False
                st.success(f"Zone {zone_code} – {zone_name} hinzugefügt ✓")
                st.rerun()

    # ── Vorhandene Zonen ────────────────────────────────────────────────────────
    zones = proj.get("zones", [])

    if not zones:
        st.info("Noch keine Zonen definiert. Bitte oben Zone hinzufügen.")
    else:
        st.markdown(f"**{len(zones)} Zone(n) definiert**")

        for i, z in enumerate(zones):
            cat_color = CATEGORY_COLORS.get(z.get("category", ""), "#6b7280")
            prio_label = {1: "🔴 Muss", 2: "🟡 Sollte", 3: "⚪ Optional"}.get(z.get("priority", 1), "")
            with st.expander(
                f"{z['zone_code']} – {z['name']}  ·  {z['required_area_m2']} m²  ·  {prio_label}",
                expanded=False,
            ):
                col_a, col_b, col_c = st.columns([2, 2, 2])
                with col_a:
                    new_name_z = st.text_input("Bezeichnung", value=z["name"], key=f"z_name_{i}")
                    new_cat = st.selectbox(
                        "Kategorie", options=CATEGORY_OPTIONS + ["— Sonstige —"],
                        index=CATEGORY_OPTIONS.index(z["category"]) if z["category"] in CATEGORY_OPTIONS else 0,
                        key=f"z_cat_{i}",
                    )
                    new_notes = st.text_area("Anmerkungen", value=z.get("notes", ""), height=60, key=f"z_notes_{i}")
                with col_b:
                    new_area = st.number_input("Fläche (m²)", value=float(z["required_area_m2"]), min_value=0.5, step=0.5, key=f"z_area_{i}")
                    new_wall = st.number_input("Wandlänge (m)", value=float(z.get("needs_wall_length_m", 0)), min_value=0.0, step=0.5, key=f"z_wall_{i}")
                    new_min_d = st.number_input("Mindest-Tiefe (m)", value=float(z.get("min_depth_m", 0.6)), min_value=0.1, step=0.1, key=f"z_mind_{i}")
                    new_max_d = st.number_input("Max. Tiefe (m)", value=float(z.get("max_depth_m", 3.0)), min_value=0.3, step=0.1, key=f"z_maxd_{i}")
                with col_c:
                    new_racks = st.multiselect("Regaltypen", options=RACK_TYPES, default=z.get("preferred_rack_types", []), key=f"z_racks_{i}")
                    new_prio = st.selectbox(
                        "Priorität",
                        options=[("1 – Muss", 1), ("2 – Sollte", 2), ("3 – Optional", 3)],
                        index=int(z.get("priority", 1)) - 1,
                        format_func=lambda x: x[0],
                        key=f"z_prio_{i}",
                    )
                    new_adj = st.multiselect(
                        "Nachbarschaft", options=ZONE_CODE_OPTIONS,
                        default=[x for x in z.get("adjacency_preference", []) if x in ZONE_CODE_OPTIONS],
                        key=f"z_adj_{i}",
                    )
                    new_needs_wall = st.checkbox("Wandmontage erforderlich", value=z.get("needs_wall", False), key=f"z_nw_{i}")

                col_save, col_del = st.columns([1, 1])
                with col_save:
                    if st.button("💾 Speichern", key=f"z_save_{i}"):
                        proj["zones"][i] = {
                            **z,
                            "name": new_name_z,
                            "category": new_cat,
                            "required_area_m2": new_area,
                            "needs_wall_length_m": new_wall,
                            "min_depth_m": new_min_d,
                            "max_depth_m": new_max_d,
                            "preferred_rack_types": new_racks,
                            "priority": new_prio[1],
                            "adjacency_preference": new_adj,
                            "needs_wall": new_needs_wall,
                            "notes": new_notes,
                        }
                        save_project(proj)
                        st.session_state.dirty = False
                        st.success("Zone gespeichert ✓")
                        st.rerun()
                with col_del:
                    if st.button("🗑 Zone löschen", key=f"z_del_{i}"):
                        proj["zones"].pop(i)
                        save_project(proj)
                        st.session_state.dirty = False
                        st.rerun()

        st.session_state.dirty = True

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 – ZUSAMMENFASSUNG
# ══════════════════════════════════════════════════════════════════════════════

with tab_summary:
    st.subheader("Projektübersicht")

    room = proj["room"]
    zones = proj.get("zones", [])

    # ── Raumkennzahlen ─────────────────────────────────────────────────────────
    pts = room.get("outline", [])
    room_area = 0.0
    if len(pts) >= 3:
        n = len(pts)
        room_area = abs(sum(
            pts[i]["x"] * pts[(i+1) % n]["y"] - pts[(i+1) % n]["x"] * pts[i]["y"]
            for i in range(n)
        )) / 2.0

    total_zone_area = sum(z.get("required_area_m2", 0) for z in zones)
    prio1_area = sum(z.get("required_area_m2", 0) for z in zones if z.get("priority", 1) == 1)
    utilization = (total_zone_area / room_area * 100) if room_area > 0 else 0
    aisle_area_estimate = room_area * 0.25  # grobe Schätzung: 25% Gangfläche

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Raumfläche (brutto)", f"{room_area:.0f} m²")
    col2.metric("Zonenfläche gesamt", f"{total_zone_area:.0f} m²", help="Summe aller definierten Zonen")
    col3.metric("Davon Prio-1-Zonen", f"{prio1_area:.0f} m²")
    col4.metric("Planungsauslastung", f"{utilization:.0f} %", help="Zonenfläche / Raumfläche (ohne Gangabzug)")

    # Warnungen
    warnings = []
    if utilization > 80:
        warnings.append(f"⚠ Gesamtzonenfläche ({total_zone_area:.0f} m²) überschreitet 80 % der Raumfläche – Gangbreiten könnten unterschritten werden.")
    if room_area > 0 and (total_zone_area + aisle_area_estimate) > room_area:
        warnings.append(f"⚠ Zonen + geschätzte Gangfläche ({(total_zone_area + aisle_area_estimate):.0f} m²) übersteigen Raumfläche ({room_area:.0f} m²). Bitte Zonenbedarfe reduzieren oder prüfen.")
    wall_zones = [z for z in zones if z.get("needs_wall")]
    if wall_zones:
        total_wall_needed = sum(z.get("needs_wall_length_m", 0) for z in wall_zones)
        # Grobe Schätzung verfügbarer Wandlänge (Umfang minus Öffnungen)
        if len(pts) >= 2:
            n = len(pts)
            perimeter = sum(
                math.sqrt((pts[(i+1) % n]["x"] - pts[i]["x"])**2 + (pts[(i+1) % n]["y"] - pts[i]["y"])**2)
                for i in range(n)
            )
            open_width = sum(float(o.get("width_m", 0)) for o in room.get("openings", []))
            available_wall = perimeter - open_width
            if total_wall_needed > available_wall * 0.7:
                warnings.append(f"⚠ Wandbedarf aller Zonen ({total_wall_needed:.0f} m) ist hoch relativ zur verfügbaren Wandlänge (~{available_wall:.0f} m Gesamtumfang). Stage 2 wird prüfen, ob Platzierung möglich ist.")

    if warnings:
        for w in warnings:
            st.warning(w)

    # ── Raumdetails ────────────────────────────────────────────────────────────
    st.markdown("---")
    col_rd1, col_rd2 = st.columns(2)
    with col_rd1:
        st.markdown("**Raumgeometrie**")
        st.markdown(f"- Höhe: **{room.get('height_m', '—')} m**")
        st.markdown(f"- Mindest-Gangbreite: **{room.get('min_aisle_m', '—')} m**")
        st.markdown(f"- Eckpunkte: {len(pts)}")
        st.markdown(f"- Hindernisse: {len(room.get('obstacles', []))}")
        st.markdown(f"- Öffnungen: {len(room.get('openings', []))}")
        if room.get("openings"):
            for o in room["openings"]:
                st.markdown(f"  - {o.get('type','?')}: Wand {o.get('wall_index','?')}, +{o.get('offset_m','?')} m, Breite {o.get('width_m','?')} m")

    with col_rd2:
        st.markdown("**Eckpunkte Grundriss**")
        if pts:
            pts_df = pd.DataFrame(pts)
            pts_df.index = [f"P{i}" for i in range(len(pts))]
            st.dataframe(pts_df, use_container_width=True, height=min(200, 35 + len(pts) * 35))

    # ── Zonenliste ─────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("**Zonen-Übersicht**")

    if not zones:
        st.info("Noch keine Zonen definiert.")
    else:
        # Sortiert: Prio 1 → 2 → 3, dann nach Kategorie
        sorted_zones = sorted(zones, key=lambda z: (z.get("priority", 2), z.get("category", ""), z.get("zone_code", "")))

        for z in sorted_zones:
            cat_color = CATEGORY_COLORS.get(z.get("category", ""), "#6b7280")
            prio_icon = {1: "🔴", 2: "🟡", 3: "⚪"}.get(z.get("priority", 1), "")
            rack_str = ", ".join(z.get("preferred_rack_types", [])) or "—"
            adj_str = ", ".join(z.get("adjacency_preference", [])) or "—"
            wall_str = f"{z.get('needs_wall_length_m', 0):.1f} m" if z.get("needs_wall_length_m") else "—"
            depth_str = f"{z.get('min_depth_m', '?')}–{z.get('max_depth_m', '?')} m"

            st.markdown(
                f"""<div class="metric-card">
                <span style="color:{cat_color};font-weight:700">{z['zone_code']}</span>&nbsp;
                <strong>{z['name']}</strong>&nbsp;
                <span style="color:#6b7280;font-size:13px">{z.get('category','')}</span>&nbsp;&nbsp;
                {prio_icon} &nbsp;
                <span style="background:{cat_color}22;color:{cat_color};border-radius:12px;padding:1px 8px;font-size:12px;font-weight:600">
                  {z['required_area_m2']:.0f} m²
                </span>
                <br><span style="font-size:12px;color:#374151">
                  Regale: {rack_str} &nbsp;|&nbsp; Tiefe: {depth_str} &nbsp;|&nbsp;
                  Wandlänge: {wall_str} &nbsp;|&nbsp; Nachbarn: {adj_str}
                </span>
                {f'<br><span style="font-size:11px;color:#6b7280">💬 {z["notes"]}</span>' if z.get("notes") else ''}
                </div>""",
                unsafe_allow_html=True,
            )

        # Kategorieübersicht
        st.markdown("---")
        st.markdown("**Flächenbedarf nach Kategorie**")
        cat_summary: dict[str, float] = {}
        for z in zones:
            cat = z.get("category", "Sonstige")
            cat_summary[cat] = cat_summary.get(cat, 0) + z.get("required_area_m2", 0)

        cat_df = pd.DataFrame(
            [{"Kategorie": k, "Fläche (m²)": v, "Anteil (%)": f"{v / total_zone_area * 100:.1f}" if total_zone_area > 0 else "0"}
             for k, v in sorted(cat_summary.items(), key=lambda x: -x[1])]
        )
        st.dataframe(cat_df, use_container_width=True, hide_index=True)

    # ── JSON-Export ─────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("**JSON-Daten**")
    col_exp1, col_exp2 = st.columns([2, 1])
    with col_exp1:
        with st.expander("Vollständiges Projekt-JSON anzeigen"):
            st.json(proj)
    with col_exp2:
        st.download_button(
            label="⬇ Projekt als JSON herunterladen",
            data=json.dumps(proj, ensure_ascii=False, indent=2),
            file_name=f"{proj['id']}.json",
            mime="application/json",
        )
        if st.button("💾 Projekt jetzt speichern", type="primary", use_container_width=True):
            save_project(proj)
            st.session_state.dirty = False
            st.success("✓ Gespeichert")

    # ── Vorbereitung Stage 2 ────────────────────────────────────────────────────
    st.markdown("---")
    with st.expander("ℹ Bereit für Stufe 2?"):
        checks = [
            ("✅ Raumkontur definiert", len(pts) >= 3),
            ("✅ Raumhöhe angegeben", room.get("height_m", 0) > 0),
            ("✅ Mindestens 1 Öffnung (Tor/Tür) definiert", len(room.get("openings", [])) > 0),
            ("✅ Mindestens 1 Zone definiert", len(zones) > 0),
            ("✅ Alle Prio-1-Zonen mit Fläche > 0", all(z.get("required_area_m2", 0) > 0 for z in zones if z.get("priority", 1) == 1)),
            ("⚠ Gesamtzonenfläche < 85 % Raumfläche", total_zone_area <= room_area * 0.85 if room_area > 0 else False),
        ]
        all_ok = all(c[1] for c in checks)
        for label, ok in checks:
            icon = "✅" if ok else "❌"
            st.markdown(f"{icon} {label.replace('✅ ', '').replace('⚠ ', '')}")
        if all_ok:
            st.success("Alle Pflichtfelder erfüllt – Projekt bereit für Stufe 2 (Platzierungsalgorithmus).")
        else:
            st.warning("Bitte obige Punkte prüfen, bevor Stufe 2 gestartet wird.")
