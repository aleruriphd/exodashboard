"""Exoplanet Population Dashboard — data from the NASA Exoplanet Archive.

By Alejandro Ruiz Rivera, PhD.
"""

import datetime
import os
import textwrap
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
CATEGORY_ICONS = {
    "Gas giants": "🪐",
    "Ice giants": "❄️",
    "Super-Earths": "🌏",
    "Terrestrial": "🪨",
    "Unclassified": "❔",
    "Total": "✨",
}

CARD_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&display=swap');
.cat-row {
    display: flex;
    gap: 14px;
    flex-wrap: wrap;
    margin: 6px 0 10px 0;
}
.cat-card {
    flex: 1 1 130px;
    min-width: 130px;
    background: rgba(128, 128, 128, 0.09);
    border: 1px solid rgba(128, 128, 128, 0.25);
    border-top: 4px solid var(--accent);
    border-radius: 14px;
    padding: 14px 10px 12px 10px;
    text-align: center;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.18);
}
.cat-icon { font-size: 1.7rem; line-height: 1.2; }
.cat-label {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.78rem;
    font-weight: 500;
    letter-spacing: 0.09em;
    text-transform: uppercase;
    opacity: 0.7;
    margin-top: 4px;
}
.cat-value {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 2.1rem;
    font-weight: 700;
    color: var(--accent);
    line-height: 1.15;
}
.cat-value.txt { font-size: 1.3rem; padding-top: 0.35rem; }
.pl-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 2rem;
    font-weight: 700;
    line-height: 1.2;
    background: linear-gradient(90deg, #5aa9e6, #b8a2e3);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    margin: 6px 0 6px 0;
}
.pl-meta {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.86rem;
    opacity: 0.85;
    margin-bottom: 10px;
}
.pl-chip {
    display: inline-block;
    font-size: 0.74rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--accent);
    border: 1px solid var(--accent);
    border-radius: 999px;
    padding: 2px 10px;
    margin-left: 6px;
}
</style>
"""


def category_card(icon: str, label: str, value: str, accent: str, small: bool = False) -> str:
    value_cls = "cat-value txt" if small else "cat-value"
    return (
        f'<div class="cat-card" style="--accent:{accent}">'
        f'<div class="cat-icon">{icon}</div>'
        f'<div class="cat-label">{label}</div>'
        f'<div class="{value_cls}">{value}</div>'
        f"</div>"
    )


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


@st.cache_data(show_spinner=False, ttl=7 * 24 * 3600, max_entries=500)
def fetch_nasa_artwork(planet_name: str):
    """Look up the planet's page on NASA's Exoplanet Catalog and return
    (image_url, page_url) for its artist's-concept render, or None.

    NASA catalog slugs are lowercase with spaces as hyphens,
    e.g. 'Beta Pictoris d' -> 'beta-pictoris-d'.
    """
    import re as _re

    slug = _re.sub(r"[^a-z0-9]+", "-", planet_name.lower()).strip("-")
    page_url = f"https://science.nasa.gov/exoplanet-catalog/{slug}/"
    try:
        resp = requests.get(
            page_url,
            timeout=8,
            headers={"User-Agent": "Mozilla/5.0 (exodashboard; Streamlit app)"},
        )
        if resp.status_code != 200:
            return None
        match = _re.search(
            r'<meta[^>]+property="og:image"[^>]+content="([^"]+)"', resp.text
        ) or _re.search(
            r'<meta[^>]+content="([^"]+)"[^>]+property="og:image"', resp.text
        )
        if match and "assets.science.nasa.gov" in match.group(1):
            return match.group(1), page_url
    except requests.RequestException:
        pass
    return None


data_file, snapshot_date = ensure_data()
planets_df = load_dataframe(data_file, str(snapshot_date))


# ---------------------------------------------------------------------------
# Sidebar — branding, links and data provenance
# ---------------------------------------------------------------------------
with st.sidebar:
    SIDEBAR_HEADER_CSS = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&display=swap');
    .sb-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.55rem;
        font-weight: 700;
        line-height: 1.25;
        margin-bottom: 8px;
    }
    .sb-title .sb-grad {
        background: linear-gradient(90deg, #5aa9e6, #b8a2e3);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
    }
    .sb-caption {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 0.8rem;
        opacity: 0.75;
        margin-bottom: 14px;
    }
    .sb-caption a { color: #7fc4ff; text-decoration: none; }
    .sb-caption a:hover { color: #b8a2e3; text-decoration: underline; }
    .sb-stat {
        font-family: 'Space Grotesk', sans-serif;
        background: rgba(128, 128, 128, 0.09);
        border: 1px solid rgba(128, 128, 128, 0.25);
        border-left: 4px solid #5aa9e6;
        border-radius: 14px;
        padding: 12px 16px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.18);
    }
    .sb-stat-label {
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        color: #b8a2e3;
    }
    .sb-stat-value {
        font-size: 2.1rem;
        font-weight: 700;
        line-height: 1.15;
        background: linear-gradient(90deg, #5aa9e6, #b8a2e3);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
    }
    </style>
    """

    sb_header_html = (
        '<div class="sb-title">🪐 <span class="sb-grad">Exoplanet Population Dashboard</span></div>'
        '<div class="sb-caption">Data: <a href="https://exoplanetarchive.ipac.caltech.edu/index.html" '
        f'target="_blank">NASA Exoplanet Archive</a> · snapshot of <b>{snapshot_date}</b></div>'
        '<div class="sb-stat"><div class="sb-stat-label">Confirmed exoplanets</div>'
        f'<div class="sb-stat-value">{len(planets_df):,}</div></div>'
    )
    st.markdown(textwrap.dedent(SIDEBAR_HEADER_CSS) + sb_header_html, unsafe_allow_html=True)

    st.divider()

    SIDEBAR_CSS = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&display=swap');
    .author-box { font-family: 'Space Grotesk', sans-serif; }
    .author-eyebrow {
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        color: #b8a2e3;
        margin: 14px 0 4px 0;
    }
    .author-name {
        font-size: 1.25rem;
        font-weight: 700;
        line-height: 1.25;
        background: linear-gradient(90deg, #5aa9e6, #b8a2e3);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
        margin-bottom: 2px;
    }
    .author-tagline { font-size: 0.82rem; opacity: 0.7; margin-bottom: 6px; }
    .author-links { list-style: none; padding: 0; margin: 4px 0 0 0; }
    .author-links li { margin: 7px 0; }
    .author-links a {
        color: #7fc4ff;
        text-decoration: none;
        font-size: 0.92rem;
        font-weight: 500;
        transition: color 0.15s ease;
    }
    .author-links a:hover { color: #b8a2e3; text-decoration: underline; }
    .author-links .li-icon { margin-right: 7px; }
    </style>
    """

    author_html = (
        '<div class="author-box">'
        '<div class="author-eyebrow">About the author</div>'
        '<div class="author-name">Alejandro Ruiz Rivera, PhD</div>'
        '<div class="author-tagline">Telecommunications engineer · science communicator</div>'
        '<ul class="author-links">'
        '<li><span class="li-icon">📝</span><a href="https://medium.com/@ruizrivera.alejandro" target="_blank">Medium</a></li>'
        '<li><span class="li-icon">💼</span><a href="https://www.linkedin.com/in/alejandro-ruiz-ph-d/" target="_blank">LinkedIn</a></li>'
        '<li><span class="li-icon">🎓</span><a href="https://scholar.google.com.au/citations?user=zi4G4pUAAAAJ&hl=en" target="_blank">Google Scholar</a></li>'
        "</ul>"
        '<div class="author-eyebrow">YouTube channels</div>'
        '<ul class="author-links">'
        '<li><span class="li-icon">▶️</span><a href="https://www.youtube.com/@TheWowContact" target="_blank">The WOW Contact</a></li>'
        '<li><span class="li-icon">▶️</span><a href="https://www.youtube.com/@Elcontactowow" target="_blank">El Contacto WOW</a></li>'
        "</ul>"
        '<div class="author-eyebrow">Books</div>'
        '<ul class="author-links">'
        '<li><span class="li-icon">📖</span><a href="https://books2read.com/more-than-5000-worlds" target="_blank">A Story of More Than 5000 Worlds</a></li>'
        '<li><span class="li-icon">📖</span><a href="https://books2read.com/mas-de-5000-mundos" target="_blank">Una historia de más de 5000 mundos</a></li>'
        "</ul></div>"
    )
    st.markdown(textwrap.dedent(SIDEBAR_CSS) + author_html, unsafe_allow_html=True)
    if os.path.exists("images/caratulas libros.png"):
        st.image("images/caratulas libros.png", width="stretch")


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
HWC_FILES = ("hwc.csv", "hwc_full.csv", "hwc_simplified.csv")


@st.cache_data(show_spinner=False)
def load_hwc(cache_key: str):
    """Load the PHL Habitable Worlds Catalog CSV bundled in the repo.

    Column names have varied across HWC releases (p_name vs P_NAME etc.),
    so downstream code resolves columns case-insensitively.
    """
    for path in HWC_FILES:
        if os.path.exists(path):
            return pd.read_csv(path, low_memory=False)
    return None


def hwc_col(df: pd.DataFrame, *candidates: str):
    """Return the first column matching any candidate name, case-insensitively."""
    lookup = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in lookup:
            return lookup[cand.lower()]
    return None


def hwc_num(row, colname, decimals: int = 2) -> str:
    """Numeric HWC field -> display string ('—' when missing/non-numeric)."""
    if colname is None:
        return "—"
    val = pd.to_numeric(pd.Series([row[colname]]), errors="coerce").iloc[0]
    return fmt(float(val), decimals) if pd.notna(val) else "—"


PC_TO_LY = 3.26156


tab4, tab1, tab2, tab3, tab5 = st.tabs(
    [
        "🛰️ Detection methods",
        "📊 Population statistics",
        "🔎 Planet explorer",
        "🌌 Mass vs orbit",
        "🌿 Habitable exoplanets explorer",
    ]
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

    # --- Category cards (labels and values always paired correctly) ---
    cards = [
        category_card(
            CATEGORY_ICONS[CATEGORY_LABELS[cat]],
            CATEGORY_LABELS[cat],
            f"{count:,}",
            CATEGORY_COLORS[CATEGORY_LABELS[cat]],
        )
        for cat, count in category_counts.items()
    ]
    cards.append(
        category_card(
            CATEGORY_ICONS["Total"], "Total", f"{category_counts.sum():,}", "#b8a2e3"
        )
    )
    st.markdown(
        CARD_CSS + '<div class="cat-row">' + "".join(cards) + "</div>",
        unsafe_allow_html=True,
    )

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
            chart_data["Percentage"] = (
                chart_data["Planets"] / chart_data["Planets"].sum() * 100
            )
            chart_data["pct_label"] = chart_data["Percentage"].map(
                lambda p: f"{p:.1f}%"
            )

            color_scale = alt.Color(
                "Category:N",
                scale=alt.Scale(
                    domain=list(chart_data["Category"]),
                    range=[CATEGORY_COLORS[c] for c in chart_data["Category"]],
                ),
                legend=alt.Legend(orient="right", title=None),
            )
            tooltip = [
                "Category:N",
                alt.Tooltip("Planets:Q", format=","),
                alt.Tooltip("Percentage:Q", format=".1f", title="Percentage (%)"),
            ]

            base = alt.Chart(chart_data).encode(
                theta=alt.Theta("Planets:Q", stack=True),
                color=color_scale,
                tooltip=tooltip,
            )
            arcs = base.mark_arc(innerRadius=65, outerRadius=130)
            labels = base.mark_text(
                radius=152, size=15, fontWeight="bold"
            ).encode(text="pct_label:N")

            donut = (
                (arcs + labels)
                .properties(title=chart_title, height=400, padding={"top": 10, "bottom": 25, "left": 10, "right": 10})
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

    cat_label = CATEGORY_LABELS.get(row["category"], row["category"])
    cat_color = CATEGORY_COLORS.get(cat_label, "#8a8a8a")
    cat_icon = CATEGORY_ICONS.get(cat_label, "❔")

    # NOTE: this HTML must stay on flush-left single lines — leading
    # indentation makes st.markdown treat it as a literal code block.
    header_html = (
        f'<div class="pl-title">{selected_planet}</div>'
        f'<div class="pl-meta">Detected by <b>{row["discoverymethod"]}</b> · '
        f'Discovered in <b>{"—" if pd.isna(row.get("disc_year")) else int(row["disc_year"])}</b>'
        f'<span class="pl-chip" style="--accent:{cat_color}">{cat_icon} {cat_label}</span></div>'
    )
    st.markdown(CARD_CSS + header_html, unsafe_allow_html=True)

    JUPITER_SVG = (
        '<svg width="27" height="27" viewBox="0 0 27 27" style="vertical-align:middle">'
        '<defs><clipPath id="jclip"><circle cx="13.5" cy="13.5" r="12.5"/></clipPath></defs>'
        '<circle cx="13.5" cy="13.5" r="12.5" fill="#d9a066"/>'
        '<g clip-path="url(#jclip)">'
        '<rect x="0" y="4" width="27" height="3" fill="#c98a4b"/>'
        '<rect x="0" y="9" width="27" height="2.4" fill="#f0d9b5"/>'
        '<rect x="0" y="13" width="27" height="3.2" fill="#b5723a"/>'
        '<rect x="0" y="18" width="27" height="2.4" fill="#f0d9b5"/>'
        '<rect x="0" y="22" width="27" height="2.6" fill="#c98a4b"/>'
        '<ellipse cx="18.5" cy="17.5" rx="3.4" ry="2.1" fill="#c0492b"/>'
        "</g></svg>"
    )

    STAR_COLOR = "#e8c468"
    planet_cards = [
        category_card("📏", "Radius (Earth radii)", fmt(row["pl_rade"]), cat_color),
        category_card("🌍", "Mass (Earth masses)", fmt(row["pl_bmasse"]), cat_color),
        category_card(JUPITER_SVG, "Mass (Jupiter masses)", fmt(row["pl_bmassj"], 3), cat_color),
        category_card("🛰️", "Semi-major axis (AU)", fmt(row["pl_orbsmax"], 3), cat_color),
    ]
    dist_pc = row.get("sy_dist")
    dist_ly = (
        fmt(float(dist_pc) * PC_TO_LY, 0) if pd.notna(dist_pc) else "—"
    )
    star_cards = [
        category_card("🌡️", "Equilibrium temp. (K)", fmt(row["pl_eqt"], 0), cat_color),
        category_card("✨", "Distance (light-years)", dist_ly, "#b8a2e3"),
        category_card("⭐", "Host star", fmt(row["hostname"]), STAR_COLOR, small=True),
        category_card("🌈", "Star spectral type", fmt(row["st_spectype"]), STAR_COLOR, small=True),
        category_card("☀️", "Star effective temp. (K)", fmt(row["st_teff"], 0), STAR_COLOR),
    ]
    artwork = fetch_nasa_artwork(selected_planet)

    if artwork:
        img_url, nasa_page = artwork
        col_cards, col_art = st.columns((3, 2), gap="large")
        with col_art:
            st.image(img_url, width="stretch")
            st.caption(
                "Artist's concept, representative of this planet type "
                "(credit: NASA). "
                f"[Explore the interactive 3D model on NASA's catalog]({nasa_page})."
            )
    else:
        col_cards = st.container()

    with col_cards:
        st.markdown(
            '<div class="cat-row">' + "".join(planet_cards) + "</div>"
            '<div class="cat-row">' + "".join(star_cards) + "</div>",
            unsafe_allow_html=True,
        )

    st.divider()
    with st.expander("Look up any other parameter for this planet"):
        column_list = [
            c for c in planets_df.columns if c not in ("pl_name_lower", "category")
        ]
        default_col = column_list.index("pl_orbper") if "pl_orbper" in column_list else 0
        selected_column = st.selectbox(
            "Archive column", column_list, index=default_col
        )
        st.markdown(
            '<div class="cat-row">'
            + category_card("🔭", selected_column, fmt(row[selected_column]), "#b8a2e3", small=True)
            + "</div>",
            unsafe_allow_html=True,
        )


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


# ---------------------------------------------------------------------------
# Tab 4 — Detection methods
# ---------------------------------------------------------------------------
with tab4:
    st.subheader("How confirmed exoplanets were discovered")

    method_counts = (
        planets_df["discoverymethod"]
        .value_counts()
        .rename_axis("Method")
        .reset_index(name="Planets")
    )
    method_counts["Percentage"] = (
        method_counts["Planets"] / method_counts["Planets"].sum() * 100
    )
    # Only label slices large enough to have room; small ones use tooltip/table
    method_counts["pct_label"] = np.where(
        method_counts["Percentage"] >= 2.0,
        method_counts["Percentage"].map(lambda p: f"{p:.1f}%"),
        "",
    )

    col_chart, col_table = st.columns((3, 2), gap="large")

    with col_chart:
        method_color = alt.Color(
            "Method:N",
            scale=alt.Scale(scheme="tableau20"),
            sort=alt.EncodingSortField("Planets", order="descending"),
            legend=alt.Legend(orient="right", title=None),
        )
        method_tooltip = [
            "Method:N",
            alt.Tooltip("Planets:Q", format=","),
            alt.Tooltip("Percentage:Q", format=".2f", title="Percentage (%)"),
        ]

        method_base = alt.Chart(method_counts).encode(
            theta=alt.Theta("Planets:Q", stack=True),
            order=alt.Order("Planets:Q", sort="descending"),
            color=method_color,
            tooltip=method_tooltip,
        )
        method_arcs = method_base.mark_arc(innerRadius=65, outerRadius=130)
        method_labels = method_base.mark_text(
            radius=152, size=15, fontWeight="bold"
        ).encode(text="pct_label:N")

        method_donut = (
            (method_arcs + method_labels)
            .properties(
                title="Share of confirmed exoplanets by detection method",
                height=400,
                padding={"top": 10, "bottom": 25, "left": 10, "right": 10},
            )
        )
        st.altair_chart(method_donut, width="stretch")
        st.caption(
            "Slices under 2% are unlabelled to avoid clutter — "
            "hover them or use the table for exact figures."
        )

    with col_table:
        table_view = method_counts[["Method", "Planets", "Percentage"]].copy()
        table_view["Percentage"] = table_view["Percentage"].map(lambda p: f"{p:.2f}%")
        table_view["Planets"] = table_view["Planets"].map(lambda n: f"{n:,}")
        st.dataframe(table_view, hide_index=True, width="stretch", height=430)

    st.download_button(
        label="⬇️ Download this breakdown as CSV",
        data=method_counts[["Method", "Planets", "Percentage"]]
        .to_csv(index=False)
        .encode("utf-8"),
        file_name="exoplanets_by_detection_method.csv",
        mime="text/csv",
    )


# ---------------------------------------------------------------------------
# Tab 5 — Habitable exoplanets explorer (PHL Habitable Worlds Catalog)
# ---------------------------------------------------------------------------
with tab5:
    hwc_key = ""
    for _p in HWC_FILES:
        if os.path.exists(_p):
            hwc_key = f"{_p}:{os.path.getmtime(_p)}"
            break
    hwc_df = load_hwc(hwc_key)

    if hwc_df is None:
        st.markdown(
            CARD_CSS
            + '<div class="pl-title">Habitable exoplanets explorer</div>'
            '<div class="pl-meta">Powered by the <b>Habitable Worlds Catalog</b> '
            "(PHL @ UPR Arecibo)</div>",
            unsafe_allow_html=True,
        )
        st.info(
            "**The HWC data file isn't bundled with this app yet.** To enable this tab:\n\n"
            "1. Download the *Full Catalog — all exoplanets (CSV)* from the "
            "[PHL Habitable Worlds Catalog data page](https://phl.upr.edu/hwc/data).\n"
            "2. Rename the file to `hwc.csv`.\n"
            "3. Commit it to the root of this repository and redeploy.\n\n"
            "The catalog flags potentially habitable planets with `p_habitable > 0` "
            "(1 = conservative sample, 2 = optimistic sample)."
        )
    else:
        # --- Resolve columns across HWC naming variants -------------------
        c_name = hwc_col(hwc_df, "p_name", "name", "pl_name")
        c_hab = hwc_col(hwc_df, "p_habitable")
        c_esi = hwc_col(hwc_df, "p_esi", "esi")
        c_type = hwc_col(hwc_df, "p_type")
        c_mass = hwc_col(hwc_df, "p_mass")
        c_radius = hwc_col(hwc_df, "p_radius")
        c_period = hwc_col(hwc_df, "p_period")
        c_sma = hwc_col(hwc_df, "p_semi_major_axis", "p_sma")
        c_tsurf = hwc_col(hwc_df, "p_temp_surf")
        c_teq = hwc_col(hwc_df, "p_temp_equil")
        c_sname = hwc_col(hwc_df, "s_name", "hostname")
        c_stype = hwc_col(hwc_df, "s_type", "s_spec_type")
        c_dist = hwc_col(hwc_df, "s_distance", "p_distance", "sy_dist")
        c_detection = hwc_col(hwc_df, "p_detection", "p_detection_method")
        c_year = hwc_col(hwc_df, "p_year", "p_discovery_year")

        if c_name is None:
            st.error(
                "The bundled `hwc.csv` doesn't look like the PHL Habitable Worlds "
                "Catalog (no planet-name column found). Please re-download it from "
                "[phl.upr.edu/hwc/data](https://phl.upr.edu/hwc/data)."
            )
            st.stop()

        # --- Potentially habitable subset, sorted by ESI ------------------
        hab_df = hwc_df.copy()
        if c_hab is not None:
            hab_flags = pd.to_numeric(hab_df[c_hab], errors="coerce").fillna(0)
            hab_df = hab_df[hab_flags > 0].copy()
            hab_df["_sample"] = np.where(
                pd.to_numeric(hab_df[c_hab], errors="coerce") == 1,
                "Conservative",
                "Optimistic",
            )
        else:
            hab_df["_sample"] = "—"
        if c_esi is not None:
            hab_df["_esi"] = pd.to_numeric(hab_df[c_esi], errors="coerce")
            hab_df = hab_df.sort_values("_esi", ascending=False)

        n_cons = int((hab_df["_sample"] == "Conservative").sum())
        n_opt = int((hab_df["_sample"] == "Optimistic").sum())

        # --- Overview cards ----------------------------------------------
        st.markdown(
            CARD_CSS
            + '<div class="pl-title">Habitable exoplanets explorer</div>'
            '<div class="pl-meta">Potentially habitable worlds from the '
            '<b><a href="https://phl.upr.edu/hwc" target="_blank" '
            'style="color:#7fc4ff">Habitable Worlds Catalog</a></b> '
            "(PHL @ UPR Arecibo), ranked by Earth Similarity Index</div>"
            + '<div class="cat-row">'
            + category_card("🌍", "Potentially habitable", f"{len(hab_df):,}", "#7bc86c")
            + category_card("🌿", "Conservative sample", f"{n_cons:,}", "#7bc86c")
            + category_card("🌊", "Optimistic sample", f"{n_opt:,}", "#5aa9e6")
            + "</div>",
            unsafe_allow_html=True,
        )
        st.divider()

        # --- Planet picker (sorted by ESI, best first) --------------------
        hab_names = hab_df[c_name].dropna().astype(str).tolist()
        selected_hab = st.selectbox(
            "Search for a potentially habitable exoplanet",
            hab_names,
            index=0,
            help="Ordered by Earth Similarity Index — the most Earth-like first.",
        )
        hrow = hab_df[hab_df[c_name].astype(str) == selected_hab].iloc[0]

        sample = hrow["_sample"]
        sample_color = "#7bc86c" if sample == "Conservative" else "#5aa9e6"
        sample_icon = "🌿" if sample == "Conservative" else "🌊"
        ptype = str(hrow[c_type]) if c_type is not None and pd.notna(hrow[c_type]) else ""

        meta_bits = []
        if c_detection is not None and pd.notna(hrow[c_detection]):
            meta_bits.append(f"Detected by <b>{hrow[c_detection]}</b>")
        if c_year is not None and pd.notna(hrow[c_year]):
            try:
                meta_bits.append(f"Discovered in <b>{int(float(hrow[c_year]))}</b>")
            except (TypeError, ValueError):
                pass
        if ptype:
            meta_bits.append(f"PHL type: <b>{ptype}</b>")

        header_html = (
            f'<div class="pl-title">{selected_hab}</div>'
            f'<div class="pl-meta">{" · ".join(meta_bits)}'
            f'<span class="pl-chip" style="--accent:{sample_color}">'
            f"{sample_icon} {sample} sample</span></div>"
        )
        st.markdown(header_html, unsafe_allow_html=True)

        # --- Distance in light-years -------------------------------------
        hab_dist_ly = "—"
        if c_dist is not None:
            dval = pd.to_numeric(pd.Series([hrow[c_dist]]), errors="coerce").iloc[0]
            if pd.notna(dval):
                hab_dist_ly = fmt(float(dval) * PC_TO_LY, 0)

        HAB_GREEN = "#7bc86c"
        hab_planet_cards = [
            category_card("🌐", "Earth Similarity Index", hwc_num(hrow, c_esi), "#b8a2e3"),
            category_card("📏", "Radius (Earth radii)", hwc_num(hrow, c_radius), HAB_GREEN),
            category_card("🌍", "Mass (Earth masses)", hwc_num(hrow, c_mass), HAB_GREEN),
            category_card("🔄", "Orbital period (days)", hwc_num(hrow, c_period, 1), HAB_GREEN),
        ]
        hab_star_cards = [
            category_card("🌡️", "Surface temp. (K)*", hwc_num(hrow, c_tsurf, 0), HAB_GREEN)
            if c_tsurf is not None
            else category_card("🌡️", "Equilibrium temp. (K)", hwc_num(hrow, c_teq, 0), HAB_GREEN),
            category_card("✨", "Distance (light-years)", hab_dist_ly, "#b8a2e3"),
            category_card("⭐", "Host star", str(hrow[c_sname]) if c_sname is not None and pd.notna(hrow[c_sname]) else "—", STAR_COLOR, small=True),
            category_card("🌈", "Star type", str(hrow[c_stype]) if c_stype is not None and pd.notna(hrow[c_stype]) else "—", STAR_COLOR, small=True),
        ]

        hab_artwork = fetch_nasa_artwork(selected_hab)
        if hab_artwork:
            himg, hpage = hab_artwork
            hcol_cards, hcol_art = st.columns((3, 2), gap="large")
            with hcol_art:
                st.image(himg, width="stretch")
                st.caption(
                    "Artist's concept, representative of this planet type "
                    f"(credit: NASA). [Interactive 3D model]({hpage})."
                )
        else:
            hcol_cards = st.container()

        with hcol_cards:
            st.markdown(
                '<div class="cat-row">' + "".join(hab_planet_cards) + "</div>"
                '<div class="cat-row">' + "".join(hab_star_cards) + "</div>",
                unsafe_allow_html=True,
            )

        if c_tsurf is not None:
            st.caption(
                "*Modeled surface temperature assuming an Earth-like atmosphere "
                "(PHL). Actual temperatures depend on the real atmosphere."
            )

        with st.expander("What do 'conservative' and 'optimistic' mean?"):
            st.markdown(
                "The HWC considers planets orbiting within their star's optimistic "
                "habitable zone. The **conservative sample** (≤ 1.6 Earth radii or "
                "≤ 3 Earth masses) contains planets more likely to be rocky and to "
                "support surface liquid water. The **optimistic sample** includes "
                "larger planets — possible super-Earths, ocean worlds, or "
                "mini-Neptunes — that are less likely to be rocky. Habitable-zone "
                "limits follow Kopparapu et al. (2014); none of this guarantees a "
                "planet is actually habitable."
            )

        st.download_button(
            label="⬇️ Download the potentially habitable list (CSV)",
            data=hab_df.drop(columns=["_sample", "_esi"], errors="ignore")
            .to_csv(index=False)
            .encode("utf-8"),
            file_name="potentially_habitable_exoplanets_hwc.csv",
            mime="text/csv",
        )
        st.caption(
            "Data: [Habitable Worlds Catalog](https://phl.upr.edu/hwc), "
            "PHL @ UPR Arecibo (CC). Please cite PHL when reusing this data."
        )
