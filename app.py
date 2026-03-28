import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from pathlib import Path

st.set_page_config(page_title="TUP LUDIP Dashboard", layout="wide")

DATA_DIR = Path(__file__).parent / "data"
FACILITY_FILE = DATA_DIR / "facility_inputs.csv"
BUILDING_FILE = DATA_DIR / "building_inventory.csv"


def load_csv_or_default(path: Path, default_df: pd.DataFrame) -> pd.DataFrame:
    try:
        if path.exists():
            return pd.read_csv(path)
    except Exception:
        pass
    return default_df.copy()


def safe_pct(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 100.0
    return (numerator / denominator) * 100.0


def classify_gap(deficit: float) -> str:
    if deficit > 0:
        return "Deficit"
    if deficit < 0:
        return "Surplus"
    return "Balanced"


def fmt_num(x: float) -> str:
    return f"{x:,.0f}"


def compute_facility_metrics(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    numeric_cols = [
        "existing_floor_area_sqm",
        "population",
        "proposed_floor_area_per_floor_sqm",
        "number_of_floors",
        "standard_sqm_per_person",
    ]
    for col in numeric_cols:
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0)

    out["required_floor_area_sqm"] = out["population"] * out["standard_sqm_per_person"]
    out["proposed_total_floor_area_sqm"] = (
        out["proposed_floor_area_per_floor_sqm"] * out["number_of_floors"]
    )
    out["future_total_area_sqm"] = (
        out["existing_floor_area_sqm"] + out["proposed_total_floor_area_sqm"]
    )
    out["deficit_sqm"] = out["required_floor_area_sqm"] - out["future_total_area_sqm"]
    out["surplus_sqm"] = out["future_total_area_sqm"] - out["required_floor_area_sqm"]
    out["compliance_pct"] = out.apply(
        lambda row: safe_pct(row["future_total_area_sqm"], row["required_floor_area_sqm"]),
        axis=1,
    )
    out["status"] = out["deficit_sqm"].apply(classify_gap)
    out["priority_rank"] = out["deficit_sqm"].rank(method="dense", ascending=False)
    return out


def compute_building_metrics(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    numeric_cols = [
        "existing_gfa_sqm",
        "proposed_additional_gfa_sqm",
        "floors",
        "population_served",
    ]
    for col in numeric_cols:
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0)
    out["future_gfa_sqm"] = out["existing_gfa_sqm"] + out["proposed_additional_gfa_sqm"]
    return out


def bar_chart_area(df: pd.DataFrame):
    folded = df.melt(
        id_vars=["facility_type"],
        value_vars=["existing_floor_area_sqm", "future_total_area_sqm", "required_floor_area_sqm"],
        var_name="area_type",
        value_name="area_sqm",
    )
    mapping = {
        "existing_floor_area_sqm": "Existing Area",
        "future_total_area_sqm": "Future Total Area",
        "required_floor_area_sqm": "Required Area",
    }
    folded["area_type"] = folded["area_type"].map(mapping)
    return (
        alt.Chart(folded)
        .mark_bar()
        .encode(
            x=alt.X("facility_type:N", title="Facility"),
            y=alt.Y("area_sqm:Q", title="Area (sqm)"),
            color=alt.Color("area_type:N", title="Legend"),
            tooltip=["facility_type", "area_type", alt.Tooltip("area_sqm:Q", format=",.0f")],
        )
        .properties(height=420, title="Existing vs Future vs Required Area")
    )


def deficit_chart(df: pd.DataFrame):
    return (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("facility_type:N", title="Facility"),
            y=alt.Y("deficit_sqm:Q", title="Deficit / Surplus (sqm)"),
            color=alt.condition(
                alt.datum.deficit_sqm > 0,
                alt.value("#e74c3c"),
                alt.value("#2ecc71"),
            ),
            tooltip=[
                "facility_type",
                alt.Tooltip("required_floor_area_sqm:Q", format=",.0f"),
                alt.Tooltip("future_total_area_sqm:Q", format=",.0f"),
                alt.Tooltip("deficit_sqm:Q", format=",.0f"),
                "status",
            ],
        )
        .properties(height=420, title="Facility Deficit / Surplus")
    )


def compliance_chart(df: pd.DataFrame):
    base = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("facility_type:N", title="Facility"),
            y=alt.Y("compliance_pct:Q", title="Compliance (%)"),
            color=alt.condition(
                alt.datum.compliance_pct >= 100,
                alt.value("#2ecc71"),
                alt.condition(alt.datum.compliance_pct >= 75, alt.value("#f1c40f"), alt.value("#e74c3c")),
            ),
            tooltip=["facility_type", alt.Tooltip("compliance_pct:Q", format=".1f")],
        )
        .properties(height=420, title="Compliance by Facility")
    )
    text = base.mark_text(dy=-10).encode(text=alt.Text("compliance_pct:Q", format=".1f"))
    return base + text


DEFAULT_FACILITY_DF = pd.DataFrame([
    {
        "facility_type": "Classroom",
        "existing_floor_area_sqm": 1200,
        "population": 800,
        "proposed_floor_area_per_floor_sqm": 300,
        "number_of_floors": 2,
        "standard_sqm_per_person": 1.5,
    },
    {
        "facility_type": "Laboratory",
        "existing_floor_area_sqm": 500,
        "population": 400,
        "proposed_floor_area_per_floor_sqm": 250,
        "number_of_floors": 2,
        "standard_sqm_per_person": 2.0,
    },
    {
        "facility_type": "Library",
        "existing_floor_area_sqm": 250,
        "population": 800,
        "proposed_floor_area_per_floor_sqm": 150,
        "number_of_floors": 2,
        "standard_sqm_per_person": 0.3,
    },
    {
        "facility_type": "Admin",
        "existing_floor_area_sqm": 400,
        "population": 100,
        "proposed_floor_area_per_floor_sqm": 120,
        "number_of_floors": 1,
        "standard_sqm_per_person": 6.0,
    },
    {
        "facility_type": "Faculty Room",
        "existing_floor_area_sqm": 180,
        "population": 80,
        "proposed_floor_area_per_floor_sqm": 100,
        "number_of_floors": 1,
        "standard_sqm_per_person": 4.0,
    },
])

DEFAULT_BUILDING_DF = pd.DataFrame([
    {
        "building_name": "IT Building",
        "college_owner": "IT",
        "existing_gfa_sqm": 2500,
        "proposed_additional_gfa_sqm": 500,
        "floors": 5,
        "population_served": 800,
    },
    {
        "building_name": "Admin Building",
        "college_owner": "Admin",
        "existing_gfa_sqm": 900,
        "proposed_additional_gfa_sqm": 300,
        "floors": 3,
        "population_served": 120,
    },
])

if "facility_df" not in st.session_state:
    st.session_state.facility_df = load_csv_or_default(FACILITY_FILE, DEFAULT_FACILITY_DF)
if "building_df" not in st.session_state:
    st.session_state.building_df = load_csv_or_default(BUILDING_FILE, DEFAULT_BUILDING_DF)

st.title("TUP LUDIP Dashboard - Dynamic Package")
st.caption("Interactive planning dashboard for floor area requirements, deficits, standards, and motivation visuals")

with st.sidebar:
    st.header("Controls")
    campus_name = st.text_input("Campus", value="TUP Manila")
    scenario = st.selectbox("Scenario", ["Current", "2027 Plan", "2030 Plan", "Full Build-Out"], index=1)
    show_deficit_only = st.checkbox("Show deficit items only", value=False)
    st.markdown("---")
    st.subheader("Quick Actions")
    if st.button("Reset to sample data"):
        st.session_state.facility_df = DEFAULT_FACILITY_DF.copy()
        st.session_state.building_df = DEFAULT_BUILDING_DF.copy()
        st.rerun()

overview_tab, facility_tab, building_tab, visual_tab = st.tabs([
    "Overview",
    "Facility Planning Input",
    "Building Inventory",
    "Gap Analysis Visuals",
])

with facility_tab:
    st.subheader("Dynamic Facility Planning Input")
    st.write("Add, edit, or delete rows. The dashboard automatically updates required floor area, future area, deficit, and compliance.")

    edited_facility_df = st.data_editor(
        st.session_state.facility_df,
        use_container_width=True,
        num_rows="dynamic",
        hide_index=True,
        column_config={
            "facility_type": st.column_config.TextColumn("Facility Type", required=True),
            "existing_floor_area_sqm": st.column_config.NumberColumn("Existing Floor Area (sqm)", min_value=0.0, step=10.0),
            "population": st.column_config.NumberColumn("Population", min_value=0, step=10),
            "proposed_floor_area_per_floor_sqm": st.column_config.NumberColumn("Proposed Floor Area / Floor (sqm)", min_value=0.0, step=10.0),
            "number_of_floors": st.column_config.NumberColumn("No. of Floors", min_value=0, step=1),
            "standard_sqm_per_person": st.column_config.NumberColumn("Standard (sqm / person)", min_value=0.0, step=0.1, format="%.2f"),
        },
    )
    st.session_state.facility_df = edited_facility_df.copy()

    computed_facility_df = compute_facility_metrics(st.session_state.facility_df)
    if show_deficit_only:
        display_facility_df = computed_facility_df[computed_facility_df["deficit_sqm"] > 0].copy()
    else:
        display_facility_df = computed_facility_df.copy()

    st.markdown("### Computed Table")
    st.dataframe(
        display_facility_df[[
            "facility_type",
            "population",
            "existing_floor_area_sqm",
            "proposed_floor_area_per_floor_sqm",
            "number_of_floors",
            "standard_sqm_per_person",
            "required_floor_area_sqm",
            "proposed_total_floor_area_sqm",
            "future_total_area_sqm",
            "deficit_sqm",
            "compliance_pct",
            "status",
        ]],
        use_container_width=True,
        hide_index=True,
    )

    export_csv = computed_facility_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download facility gap analysis CSV",
        export_csv,
        file_name="tup_ludip_facility_gap_analysis.csv",
        mime="text/csv",
    )

with building_tab:
    st.subheader("Dynamic Building Inventory")
    edited_building_df = st.data_editor(
        st.session_state.building_df,
        use_container_width=True,
        num_rows="dynamic",
        hide_index=True,
        column_config={
            "building_name": st.column_config.TextColumn("Building Name", required=True),
            "college_owner": st.column_config.TextColumn("College / Unit Owner"),
            "existing_gfa_sqm": st.column_config.NumberColumn("Existing GFA (sqm)", min_value=0.0, step=10.0),
            "proposed_additional_gfa_sqm": st.column_config.NumberColumn("Proposed Additional GFA (sqm)", min_value=0.0, step=10.0),
            "floors": st.column_config.NumberColumn("Floors", min_value=1, step=1),
            "population_served": st.column_config.NumberColumn("Population Served", min_value=0, step=10),
        },
    )
    st.session_state.building_df = edited_building_df.copy()

    computed_building_df = compute_building_metrics(st.session_state.building_df)
    st.dataframe(computed_building_df, use_container_width=True, hide_index=True)

with overview_tab:
    computed_facility_df = compute_facility_metrics(st.session_state.facility_df)
    computed_building_df = compute_building_metrics(st.session_state.building_df)

    total_buildings = len(computed_building_df)
    total_existing_gfa = computed_building_df["existing_gfa_sqm"].sum()
    total_future_gfa = computed_building_df["future_gfa_sqm"].sum()
    total_population = computed_facility_df["population"].sum()
    total_required = computed_facility_df["required_floor_area_sqm"].sum()
    total_existing_area = computed_facility_df["existing_floor_area_sqm"].sum()
    total_future_area = computed_facility_df["future_total_area_sqm"].sum()
    total_deficit = max(total_required - total_future_area, 0)
    overall_compliance = safe_pct(total_future_area, total_required)
    deficit_count = int((computed_facility_df["deficit_sqm"] > 0).sum())

    st.subheader(f"{campus_name} - {scenario} Overview")
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Buildings", f"{total_buildings}")
    c2.metric("Existing GFA (sqm)", fmt_num(total_existing_gfa))
    c3.metric("Future GFA (sqm)", fmt_num(total_future_gfa))
    c4.metric("Total Population", fmt_num(total_population))
    c5.metric("Required Area (sqm)", fmt_num(total_required))
    c6.metric("Overall Compliance", f"{overall_compliance:,.1f}%")

    d1, d2, d3 = st.columns(3)
    d1.metric("Existing Functional Area (sqm)", fmt_num(total_existing_area))
    d2.metric("Future Functional Area (sqm)", fmt_num(total_future_area))
    d3.metric("Facilities with Deficit", deficit_count)

    st.markdown("### LUDIP Completion Motivation")
    progress_value = min(max(overall_compliance, 0), 100) / 100
    st.progress(progress_value, text=f"Campus planning compliance progress: {min(overall_compliance, 100):.1f}%")

    if overall_compliance < 60:
        st.warning("The current plan is still far below the computed area requirements. More programming and facility expansion are needed.")
    elif overall_compliance < 90:
        st.info("The campus is improving, but several facilities still need additional space to meet standards.")
    else:
        st.success("The campus is nearing or already meeting the target area requirements for many facilities.")

    st.markdown("### Top Priority Facilities")
    priority_df = computed_facility_df.sort_values("deficit_sqm", ascending=False)
    st.dataframe(
        priority_df[[
            "facility_type",
            "required_floor_area_sqm",
            "future_total_area_sqm",
            "deficit_sqm",
            "compliance_pct",
            "status",
        ]],
        use_container_width=True,
        hide_index=True,
    )

with visual_tab:
    st.subheader("Gap Analysis Visuals")
    computed_facility_df = compute_facility_metrics(st.session_state.facility_df)
    vis_df = computed_facility_df.copy()
    if show_deficit_only:
        vis_df = vis_df[vis_df["deficit_sqm"] > 0].copy()

    col1, col2 = st.columns(2)
    with col1:
        st.altair_chart(bar_chart_area(vis_df), use_container_width=True)
    with col2:
        st.altair_chart(deficit_chart(vis_df), use_container_width=True)

    st.altair_chart(compliance_chart(vis_df), use_container_width=True)
