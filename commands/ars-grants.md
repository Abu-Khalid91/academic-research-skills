---
description: ARS grant finder — discover and rank NIH/HHS funding opportunities for computational research
---

Launch the Research Grant Finder Agent to discover, score, and rank NIH funding opportunities relevant to computational and data-science research. Uses multi-source ingestion (NIH Guide, Grants.gov, NIH RePORTER), explainable relevance scoring, and interactive Streamlit dashboard.

**Quick start (CLI):**
```
cd grant-finder
pip install -e .
python -m nih_grant_matcher run --source nih-guide --keyword "machine learning"
```

**Interactive dashboard:**
```
cd grant-finder
streamlit run streamlit_app.py
```

Tool location: `grant-finder/` directory.
