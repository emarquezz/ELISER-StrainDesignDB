# A database of over 15,000 strain design publications reveals a conserved set of metabolic engineering targets across microbial hosts and products 🎯

**Authors:** Elisa Márquez-Zavala, Francesca Di Bartolomeo, and Daniel Machado  
**Published in:** *Metabolic Engineering* 96 (2026), 225–233  
**Article:** [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S1096717626000510) · [DOI: 10.1016/j.ymben.2026.03.017](https://doi.org/10.1016/j.ymben.2026.03.017)

<p align="center">
  <a href="https://emarquezz.github.io/ELISER-StrainDesignDB/">
    <img
      src="docs/og.png"
      alt="Open the ELISER Strain Design Explorer"
      width="760"
    >
  </a>
</p>

<h2 align="center">Explore the database online</h2>

<p align="center">
  <a href="https://emarquezz.github.io/ELISER-StrainDesignDB/">
    <img
      src="https://img.shields.io/badge/Open_the_interactive_ELISER_Explorer-4E2C73?style=for-the-badge"
      alt="Open the interactive ELISER Strain Design Explorer"
    >
  </a>
</p>

<p align="center">
  Search 15,798 strain-design publications by organism, product, gene,
  modification direction, and year.
</p>

## Overview

ELISER is a literature-derived database of experimentally reported microbial
strain-design strategies. It connects host organisms and target products with
the genes researchers increased, decreased, or otherwise modified.

The collection spans 25 years of literature and reveals recurring metabolic
engineering targets across diverse microbial hosts and products, particularly
at central-carbon branch points and reactions involved in redox balance.

## Repository goals

- Provide the data, code, and figures supporting the published article.
- Enable reproducible extraction, classification, and normalization of
  literature-derived strain designs.
- Make the database accessible through an interactive, browser-based explorer.
- Provide a practical starting point for new strain-engineering projects.

## Quick links

- [Explore the interactive database](https://emarquezz.github.io/ELISER-StrainDesignDB/)
- [Read the published article](https://www.sciencedirect.com/science/article/pii/S1096717626000510)
- [Download the authoritative database](files/Output/ELISER_DB_v3.csv)
- [Browse the source code](src/)
- [Open an issue](https://github.com/emarquezz/ELISER-StrainDesignDB/issues)

## Repository structure

```text
ELISER-StrainDesignDB/
├── docs/                         # GitHub Pages explorer
│   ├── index.html
│   ├── app.js
│   ├── styles.css
│   ├── favicon.svg
│   ├── og.png
│   ├── assets/
│   └── data/
│       └── eliser.json           # Browser-ready database
├── files/
│   ├── Input/                    # Input resources used by the pipeline
│   └── Output/
│       └── ELISER_DB_v3.csv      # Authoritative database
├── img/                          # Repository and manuscript figures
├── scripts/
│   └── build_web_data.py         # CSV-to-JSON website data builder
├── src/                          # Extraction, classification, and analysis code
├── LICENSE
└── README.md
```

## Database fields

The main database, [`files/Output/ELISER_DB_v3.csv`](files/Output/ELISER_DB_v3.csv),
contains the following core fields:

| Field | Description |
| --- | --- |
| `PMID` | PubMed identifier for the source publication |
| `Title` | Publication title |
| `Year` | Publication year |
| `Organism` | Reported microbial host or hosts |
| `Product` | Target product or products |
| `Genes_and_modifications` | Extracted gene targets and their modification directions |

The CSV is the authoritative dataset. `docs/data/eliser.json` is a structured,
browser-friendly representation used by the interactive explorer.

## Interactive explorer

The static JavaScript explorer supports:

- Full-text search across titles, organisms, products, and genes.
- Filters for organism, product, gene, modification direction, and year.
- Direction-aware gene filtering.
- Sorting, pagination, live summaries, and filtered CSV export.
- Direct links from individual records to PubMed.

Because all filtering happens in the browser, the explorer does not require a
database server or user account.

## Updating the webpage data

After updating `files/Output/ELISER_DB_v3.csv`, regenerate the browser-ready
JSON from the repository root:

```bash
python scripts/build_web_data.py
```

This writes:

```text
docs/data/eliser.json
```

Commit and push the regenerated JSON. GitHub Pages will automatically deploy
the updated explorer from the `/docs` folder on the `main` branch.

## Data pipeline

The source pipeline is organized into four broad stages:

1. Create the input resources used for journals, products, and taxonomy.
2. Classify publications for strain-design relevance.
3. Extract and normalize organisms, products, genes, and modification directions.
4. Generate database outputs, summaries, and manuscript figures.

The corresponding code is available under [`src/`](src/).

## License

This repository is released under the [MIT License](LICENSE).

## Citation

If you use ELISER or its associated database, please cite the published article:

> Márquez-Zavala, E., Di Bartolomeo, F., & Machado, D. (2026). A database of
> over 15,000 strain design publications reveals a conserved set of metabolic
> engineering targets across microbial hosts and products. *Metabolic
> Engineering, 96*, 225–233.
> https://doi.org/10.1016/j.ymben.2026.03.017

```bibtex
@article{MarquezZavala2026ELISER,
  title   = {A database of over 15,000 strain design publications reveals a conserved set of metabolic engineering targets across microbial hosts and products},
  author  = {Márquez-Zavala, Elisa and Di Bartolomeo, Francesca and Machado, Daniel},
  journal = {Metabolic Engineering},
  volume  = {96},
  pages   = {225--233},
  year    = {2026},
  doi     = {10.1016/j.ymben.2026.03.017},
  url     = {https://www.sciencedirect.com/science/article/pii/S1096717626000510}
}
```

## Contact

For questions, suggestions, or problems, please
[open an issue](https://github.com/emarquezz/ELISER-StrainDesignDB/issues) or
contact the corresponding author at `daniel.machado@ntnu.no`.

