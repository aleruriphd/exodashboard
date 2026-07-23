# 🪐 Exoplanet Population Dashboard

An interactive web dashboard for exploring the NASA Exoplanet Archive and discovering potentially habitable worlds across the galaxy.

Built with [Streamlit](https://streamlit.io) by [Alejandro Ruiz Rivera, PhD](https://www.linkedin.com/in/alejandro-ruiz-ph-d/) — Telecommunications Engineer & Science Communicator

---

## What's Inside

This dashboard provides five interactive tabs to explore exoplanet data:

1. **🛰️ Detection Methods** — Visualize how confirmed exoplanets were discovered and the distribution across detection techniques
2. **📊 Population Statistics** — Browse exoplanet populations by category (gas giants, ice giants, super-Earths, terrestrial) and detection method
3. **🔎 Planet Explorer** — Search for any confirmed exoplanet and view detailed physical properties, host star info, and NASA artwork
4. **🌌 Mass vs Orbit** — Interactive scatter plot of exoplanet mass against semi-major axis (orbital distance); log–log scale with zoom and pan
5. **🌿 Habitable Exoplanets Explorer** — Browse potentially habitable worlds from the PHL Habitable Worlds Catalog, ranked by Earth Similarity Index

---

## Quick Start

### Prerequisites
- Python 3.8+
- pip

### Installation & Run

```bash
# Clone the repository
git clone https://github.com/aleruriphd/exodashboard.git
cd exodashboard

# Install dependencies
pip install -r requirements.txt

# Launch the Streamlit app
streamlit run exo_api.py
```

The app will open in your browser at `http://localhost:8501`

**Note:** On first run, the app downloads the latest NASA Exoplanet Archive snapshot (may take ~1 minute). Subsequent runs refresh only if a newer snapshot is available that day. If the download fails, it falls back to the bundled CSV snapshot.

---

## Optional: Enable Habitable Worlds Tab

To populate the **Habitable Exoplanets Explorer** tab with PHL catalog data:

1. Download the **Full Catalog — all exoplanets (CSV)** from [phl.upr.edu/hwc/data](https://phl.upr.edu/hwc/data)
2. Rename the file to `hwc.csv`
3. Place it in the repository root
4. Redeploy or refresh the app

---

## Data Sources

- **NASA Exoplanet Archive** ([exoplanetarchive.ipac.caltech.edu](https://exoplanetarchive.ipac.caltech.edu)) — Official catalog of confirmed exoplanets
- **PHL Habitable Worlds Catalog** ([phl.upr.edu/hwc](https://phl.upr.edu/hwc)) — Potentially habitable exoplanet candidates ranked by Earth Similarity Index (ESI)
- **NASA Exoplanet Catalog** ([science.nasa.gov/exoplanet-catalog](https://science.nasa.gov/exoplanet-catalog/)) — Artist's-concept images

---

## How Planets Are Categorized

The dashboard classifies exoplanets by **radius (Earth radii) OR mass (Earth masses)**:

| Category | Radius | Mass |
|---|---|---|
| **Gas Giants** | > 4.5 | ≥ 159 |
| **Ice Giants** | 2.1 – 4.5 | 10 – 159 |
| **Super-Earths** | 1.0 – 2.1 | 1 – 10 |
| **Terrestrial** | 0.1 – 1.0 | 0.1 – 1 |

Planets with insufficient data are marked *Unclassified* and excluded from category charts.

---

## Key Features

✨ **Live Data** — Automatically fetches today's NASA snapshot; updates daily  
🔍 **Full-Text Search** — Find any exoplanet by name from 5,000+ worlds  
📈 **Interactive Charts** — Altair donut charts, scatter plots, and data tables with hover details  
🎨 **Dark Mode** — Sleek, modern UI with gradient headers and custom styling  
📥 **Export Data** — Download filtered datasets as CSV for further analysis  
🖼️ **NASA Artwork** — Artist's-concept renders and links to NASA's 3D interactive catalog  
🌿 **Habitability Ranking** — ESI-sorted habitable worlds with conservative/optimistic classifications  

---

## Stack

- **Language:** Python 3
- **Framework:** Streamlit
- **Data Processing:** pandas, NumPy
- **Visualization:** Altair (interactive), Matplotlib (static exports)
- **HTTP:** requests
- **API:** NASA Exoplanet Archive TAP/Sync API

---

## Project Structure

```
exodashboard/
├── exo_api.py                    Main Streamlit application
├── exo_api.ipynb                 Jupyter notebook (exploratory)
├── requirements.txt              Python package dependencies
├── confirmed_exoplanets_data.csv Bundled NASA snapshot fallback (~18 MB)
├── terrestrial_planets_data.csv  Terrestrial exoplanet subset
├── hwc.csv                       PHL Habitable Worlds Catalog (optional)
├── images/                       Pre-rendered detection method charts
└── README.md                     This file
```

---

## About the Author

**Alejandro Ruiz Rivera, PhD**  
Telecommunications Engineer & Science Communicator

- 📝 [Medium](https://medium.com/@ruizrivera.alejandro)
- 💼 [LinkedIn](https://www.linkedin.com/in/alejandro-ruiz-ph-d/)
- 🎓 [Google Scholar](https://scholar.google.com.au/citations?user=zi4G4pUAAAAJ&hl=en)

### Content Channels
- ▶️ [The WOW Contact](https://www.youtube.com/@TheWowContact) — English YouTube channel
- ▶️ [El Contacto WOW](https://www.youtube.com/@Elcontactowow) — Spanish YouTube channel

### Books
- 📖 [A Story of More Than 5000 Worlds](https://books2read.com/more-than-5000-worlds) — English
- 📖 [Una historia de más de 5000 mundos](https://books2read.com/mas-de-5000-mundos) — Spanish

---

## License

This project is open source and available for personal and educational use.

---

## Acknowledgments

- NASA Exoplanet Archive for the authoritative exoplanet catalog
- PHL (Planetary Habitability Laboratory) @ UPR Arecibo for the Habitable Worlds Catalog
- Streamlit for the elegant and powerful data-app framework
- Altair for beautiful, interactive visualizations

---

## Questions or Feedback?

Open an issue or reach out through the author's social channels above. Happy exploring! 🌌
