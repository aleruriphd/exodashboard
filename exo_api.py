"""Exoplanet Population Dashboard — data from the NASA Exoplanet Archive.

By Alejandro Ruiz Rivera, PhD.
"""

import datetime
import os
from io import BytesIO

import altair as alt
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
import streamlit as st

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Exoplanet Population Dashboard",
    page_icon="🪐",
    layout="wide",
    initial_sidebar_state="expanded",
)

alt.theme.enable("dark")

ARCHIVE_URL = (
    "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
    "?query=select+*+from+ps&format=csv"
)
LOCAL_FILE = "full_table_nasa_url.csv"
FALLBACK_FILE = "confirmed_exoplanets_data.csv"

CATEGORY_ORDER = ["gas_giants", "ice_giants", "super_earths", "terrestrial"]
CATEGORY_LABELS = {
    "gas_giants": "Gas giants",
    "ice_giants": "Ice giants",
    "super_earths": "Super-Earths",
    "terrestrial": "Terrestrial",
    "unclassified": "Unclassified",
}
CATEGORY_COLORS = {
    "Gas giants": "#e4794a",
    "Ice giants": "#5aa9e6",
    "Super-Earths": "#7bc86c",
    "Terrestrial": "#c9a227",
    "Unclassified": "#8a8a8a",
}


# ---------------------------------------------------------------------------
# Data loading (no UI calls inside cached functions)
# ---------------------------------------------------------------------------
def download_archive() -> bool:
    """Download today's archive snapshot. Returns True on success."""
    try:
        response = requests.get(ARCHIVE_URL, timeout=300)
        if response.status_code == 200:
            with open(LOCAL_FILE, "wb") as fh:
                fh.write(response.content)
            return True
    except requests.RequestException:
        pass
    return False


def categorize_by_size_and_mass(radius: pd.Series, mass: pd.Series) -> np.ndarray:
    conditions = [
        (radius > 4.5) | (mass >= 159),
        ((radius > 2.1) & (radius <= 4.5)) | ((mass >= 10) & (mass < 159)),
        ((radius > 1.0) & (radius <= 2.1)) | ((mass >= 1) & (mass < 10)),
        ((radius > 0.1) & (radius <= 1.0)) | ((mass > 0.1) & (mass < 1)),
    ]
    return np.select(conditions, CATEGORY_ORDER, default="unclassified")


@st.cache_data(show_spinner=False)
def load_dataframe(csv_file: str, cache_key: str) -> pd.DataFrame:
    """Load the archive CSV, keep default parameter sets, add categories.

    `cache_key` (the snapshot date) makes the cache refresh when new data
    is downloaded.
    """
    df = pd.read_csv(csv_file, low_memory=False)

    if "default_flag" in df.columns:
        df = df[df["default_flag"] > 0]

    df = df.reset_index(drop=True).copy()
    df.index += 1

    df["category"] = categorize_by_size_and_mass(df["pl_rade"], df["pl_bmasse"])
    df["pl_name_lower"] = df["pl_name"].str.lower()
    return df


def ensure_data() -> tuple[str, datetime.date]:
    """Make sure we have a data file; download a fresh one if outdated."""
    today = datetime.date.today()

    if os.path.exists(LOCAL_FILE):
        mod_date = datetime.date.fromtimestamp(os.path.getmtime(LOCAL_FILE))
        if mod_date == today:
            return LOCAL_FILE, mod_date
        with st.spinner("A newer snapshot is available — downloading today's NASA Exoplanet Archive…"):
            if download_archive():
                return LOCAL_FILE, today
        return LOCAL_FILE, mod_date  # keep the outdated copy if download failed

    with st.spinner("Downloading the NASA Exoplanet Archive (first run can take a minute)…"):
        if download_archive():
            return LOCAL_FILE, today

    # Fall back to the snapshot bundled with the repository
    mod_date = datetime.date.fromtimestamp(os.path.getmtime(FALLBACK_FILE))
    st.warning(
        "Could not reach the NASA Exoplanet Archive. "
        f"Showing the bundled snapshot from {mod_date}."
    )
    return FALLBACK_FILE, mod_date


def fmt(value, decimals: int = 2) -> str:
    """Format a value for display, handling missing data gracefully."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "—"
    if isinstance(value, (int, np.integer)):
        return f"{value:,}"
    if isinstance(value, (float, np.floating)):
        return f"{value:,.{decimals}f}"
    return str(value)


data_file, snapshot_date = ensure_data()
planets_df = load_dataframe(data_file, str(snapshot_date))


# ---------------------------------------------------------------------------
# Sidebar — branding, links and data provenance
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("🪐 Exoplanet Population Dashboard")
    st.caption(
        f"Data: [NASA Exoplanet Archive]"
        f"(https://exoplanetarchive.ipac.caltech.edu/index.html) · "
        f"snapshot of **{snapshot_date}**"
    )
    st.metric("Confirmed exoplanets", f"{len(planets_df):,}")

    st.divider()
    st.subheader("About the author")
    st.write("**Alejandro Ruiz Rivera, PhD**")
    st.markdown(
        "- [Medium](https://medium.com/@ruizrivera.alejandro)\n"
        "- [LinkedIn](https://www.linkedin.com/in/alejandro-ruiz-ph-d/)\n"
        "- [Google Scholar](https://scholar.google.com.au/citations?user=zi4G4pUAAAAJ&hl=en)"
    )

    st.divider()
    st.subheader("Books")
    st.markdown(
        "- [A Story of More Than 5000 Worlds](https://books2read.com/more-than-5000-worlds)\n"
        "- [Una historia de más de 5000 mundos](https://books2read.com/mas-de-5000-mundos)"
    )
    if os.path.exists("images/caratulas libros.png"):
        st.image("images/caratulas libros.png", width="stretch")


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab1, tab2, tab3 = st.tabs(
    ["📊 Population statistics", "🔎 Planet explorer", "🌌 Mass vs orbit"]
)


# ---------------------------------------------------------------------------
# Tab 1 — Population statistics by detection method
# ---------------------------------------------------------------------------
with tab1:
    method_list = ["All"] + sorted(planets_df["discoverymethod"].dropna().unique())
    selected_method = st.selectbox(
        "Detection method",
        method_list,
        index=0,
        help="Filter the population by the technique used to discover each planet.",
    )

    if selected_method == "All":
        df_selected = planets_df
        chart_title = "All confirmed exoplanets by category"
    else:
        df_selected = planets_df[planets_df["discoverymethod"] == selected_method]
        chart_title = f"Exoplanets discovered by {selected_method}, by category"

    category_counts = (
        df_selected["category"].value_counts().reindex(
            CATEGORY_ORDER + ["unclassified"], fill_value=0
        )
    )

    # --- Metrics row (labels and values always paired correctly) ---
    metric_cols = st.columns(len(category_counts) + 1)
    for col, (cat, count) in zip(metric_cols, category_counts.items()):
        col.metric(CATEGORY_LABELS[cat], f"{count:,}")
    metric_cols[-1].metric("Total", f"{category_counts.sum():,}")

    st.divider()

    col_left, col_right = st.columns((1, 1), gap="large")

    with col_left:
        image_path = f"images/{selected_method}.png"
        if os.path.exists(image_path):
            st.image(image_path, width="stretch")

        with st.expander("How are planets categorised?"):
            st.markdown(
                "Categories use radius (Earth radii) **or** mass (Earth masses):\n\n"
                "| Category | Radius | Mass |\n"
                "|---|---|---|\n"
                "| Gas giants | > 4.5 | ≥ 159 |\n"
                "| Ice giants | 2.1 – 4.5 | 10 – 159 |\n"
                "| Super-Earths | 1.0 – 2.1 | 1 – 10 |\n"
                "| Terrestrial | 0.1 – 1.0 | 0.1 – 1 |\n\n"
                "Planets with insufficient radius and mass data are *unclassified* "
                "and excluded from the chart."
            )

    with col_right:
        chart_data = (
            category_counts.drop("unclassified")
            .rename(index=CATEGORY_LABELS)
            .rename_axis("Category")
            .reset_index(name="Planets")
        )
        chart_data = chart_data[chart_data["Planets"] > 0]

        if chart_data.empty:
            st.info("No categorised planets for this detection method yet.")
        else:
            donut = (
                alt.Chart(chart_data)
                .mark_arc(innerRadius=70)
                .encode(
                    theta=alt.Theta("Planets:Q"),
                    color=alt.Color(
                        "Category:N",
                        scale=alt.Scale(
                            domain=list(chart_data["Category"]),
                            range=[CATEGORY_COLORS[c] for c in chart_data["Category"]],
                        ),
                        legend=alt.Legend(orient="bottom"),
                    ),
                    tooltip=["Category:N", alt.Tooltip("Planets:Q", format=",")],
                )
                .properties(title=chart_title, height=380)
            )
            st.altair_chart(donut, width="stretch")
            st.caption("*Unclassified exoplanets are not included in the chart. Hover a slice for exact counts.")

    st.download_button(
        label="⬇️ Download this selection as CSV",
        data=df_selected.to_csv(index_label="ID").encode("utf-8"),
        file_name=f"{selected_method}_confirmed_exoplanets.csv",
        mime="text/csv",
    )


# ---------------------------------------------------------------------------
# Tab 2 — Planet explorer
# ---------------------------------------------------------------------------
with tab2:
    planet_names = sorted(planets_df["pl_name"].dropna().unique())
    default_planet = "Kepler-167 e"
    default_index = (
        planet_names.index(default_planet) if default_planet in planet_names else 0
    )

    selected_planet = st.selectbox(
        "Search for an exoplanet",
        planet_names,
        index=default_index,
        help="Start typing to search the full list of confirmed exoplanets.",
    )

    row = planets_df[planets_df["pl_name"] == selected_planet].iloc[0]

    st.title(selected_planet)
    st.caption(
        f"Detection method: **{row['discoverymethod']}** · "
        f"Discovered in **{fmt(row.get('disc_year'), 0)}** · "
        f"Category: **{CATEGORY_LABELS.get(row['category'], row['category'])}**"
    )
    st.divider()

    r1 = st.columns(4)
    r1[0].metric("Radius (Earth radii)", fmt(row["pl_rade"]))
    r1[1].metric("Mass (Earth masses)", fmt(row["pl_bmasse"]))
    r1[2].metric("Mass (Jupiter masses)", fmt(row["pl_bmassj"], 3))
    r1[3].metric("Semi-major axis (AU)", fmt(row["pl_orbsmax"], 3))

    r2 = st.columns(4)
    r2[0].metric("Equilibrium temp. (K)", fmt(row["pl_eqt"], 0))
    r2[1].metric("Host star", fmt(row["hostname"]))
    r2[2].metric("Star spectral type", fmt(row["st_spectype"]))
    r2[3].metric("Star effective temp. (K)", fmt(row["st_teff"], 0))

    st.divider()
    with st.expander("Look up any other parameter for this planet"):
        column_list = [
            c for c in planets_df.columns if c not in ("pl_name_lower", "category")
        ]
        default_col = column_list.index("pl_orbper") if "pl_orbper" in column_list else 0
        selected_column = st.selectbox(
            "Archive column", column_list, index=default_col
        )
        st.metric(selected_column, fmt(row[selected_column]))


# ---------------------------------------------------------------------------
# Tab 3 — Mass vs semi-major axis
# ---------------------------------------------------------------------------
with tab3:
    categories_available = ["All categories"] + [
        CATEGORY_LABELS[c] for c in CATEGORY_ORDER
    ]
    label_to_key = {v: k for k, v in CATEGORY_LABELS.items()}

    ctrl_cols = st.columns((2, 3))
    with ctrl_cols[0]:
        selected_label = st.selectbox("Planet category", categories_available, index=0)

    scatter_df = planets_df[["pl_name", "category", "pl_orbsmax", "pl_bmasse"]].copy()
    scatter_df = scatter_df.dropna(subset=["pl_orbsmax", "pl_bmasse"])
    scatter_df = scatter_df[(scatter_df["pl_orbsmax"] > 0) & (scatter_df["pl_bmasse"] > 0)]
    scatter_df = scatter_df[scatter_df["category"] != "unclassified"]
    scatter_df["Category"] = scatter_df["category"].map(CATEGORY_LABELS)

    if selected_label != "All categories":
        scatter_df = scatter_df[scatter_df["category"] == label_to_key[selected_label]]

    st.caption(
        f"{len(scatter_df):,} planets with measured mass and orbit shown "
        "(log–log scale). Hover a point for details; scroll to zoom, drag to pan."
    )

    scatter = (
        alt.Chart(scatter_df)
        .mark_circle(size=45, opacity=0.55)
        .encode(
            x=alt.X(
                "pl_orbsmax:Q",
                scale=alt.Scale(type="log"),
                title="Semi-major axis (AU)",
            ),
            y=alt.Y(
                "pl_bmasse:Q",
                scale=alt.Scale(type="log"),
                title="Mass (Earth masses)",
            ),
            color=alt.Color(
                "Category:N",
                scale=alt.Scale(
                    domain=[CATEGORY_LABELS[c] for c in CATEGORY_ORDER],
                    range=[CATEGORY_COLORS[CATEGORY_LABELS[c]] for c in CATEGORY_ORDER],
                ),
                legend=alt.Legend(orient="bottom"),
            ),
            tooltip=[
                alt.Tooltip("pl_name:N", title="Planet"),
                alt.Tooltip("Category:N"),
                alt.Tooltip("pl_orbsmax:Q", title="Semi-major axis (AU)", format=".3f"),
                alt.Tooltip("pl_bmasse:Q", title="Mass (M⊕)", format=",.2f"),
            ],
        )
        .interactive()
        .properties(height=520, title=f"Mass vs semi-major axis — {selected_label}")
    )
    st.altair_chart(scatter, width="stretch")

    dl_cols = st.columns((1, 1, 3))
    with dl_cols[0]:
        st.download_button(
            label="⬇️ Download data (CSV)",
            data=scatter_df.drop(columns=["category"]).to_csv(index=False).encode("utf-8"),
            file_name=f"{selected_label.replace(' ', '_').lower()}_mass_vs_orbit.csv",
            mime="text/csv",
        )
    with dl_cols[1]:
        # Static PNG for users who want an image file
        fig, ax = plt.subplots(figsize=(10, 6))
        for cat in scatter_df["Category"].unique():
            sub = scatter_df[scatter_df["Category"] == cat]
            ax.scatter(
                sub["pl_orbsmax"], sub["pl_bmasse"],
                s=12, alpha=0.55, label=cat,
                color=CATEGORY_COLORS[cat],
            )
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel("Semi-major axis (AU)")
        ax.set_ylabel("Mass (Earth masses)")
        ax.set_title(f"Mass vs semi-major axis — {selected_label}")
        ax.legend()
        buf = BytesIO()
        fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)
        st.download_button(
            label="⬇️ Download chart (PNG)",
            data=buf,
            file_name=f"{selected_label.replace(' ', '_').lower()}_scatter.png",
            mime="image/png",
        )
