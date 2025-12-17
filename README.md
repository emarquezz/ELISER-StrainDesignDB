# A database of over 16,000 strain design publications reveals a conserved set of metabolic engineering targets

**Authors**: Elisa Márquez-Zavala¹, Francesca Di Bartolomeo², Daniel Machado¹(*)  
¹ Department of Biotechnology and Food Science, NTNU, Trondheim, Norway  
² SINTEF Industry, Trondheim, Norway  
(*) Corresponding author: daniel.machado@ntnu.no

## Summary

Microbial biotechnology can drive sustainable production of industrially relevant compounds. We compiled a **database of experimentally validated strain design strategies** from over **16,000** research articles, including **host strain**, **target compounds**, and **gene modifications**. We observe a **conserved set of target metabolic genes** in central carbon metabolism (upper glycolysis, pentose phosphate pathway, TCA, fermentative routes). The key differentiator is not **which genes** are targeted, but **how** (up- vs down-regulation), underscoring the role of **branch-point control** and **redox balancing**. This database serves as a starting point for new strain design projects.

> **Repository goals**
> - Provide data, code, and figures supporting the manuscript.
> - Enable reproducible extraction, classification, and normalization of literature-derived strain designs.
> - Offer convenient summaries and visualizations for practitioners.

## Table of Contents
- [Repository Structure](#repository-structure)
- [Installation](#installation)
- [Data Pipeline](#data-pipeline)
- [Core Data Schemas](#core-data-schemas)
- [How to Reproduce](#how-to-reproduce)
- [Figures & Visualizations](#figures--visualizations)
- [License](#license)
- [Citation](#citation)
- [Contact](#contact)

## Repository Structure

```
├── README.md
├── docs/
│   ├── figures/
│   ├── methods.md
│   ├── data_dictionary.md
│   └── pipeline.md
├── files/
│   ├── Input/
│   │   ├── Journals/
│   │   ├── LASER/
│   │   ├── Products/
│   │   └── Taxonomy/
│   └── Output/
│       ├── Articles/
│       ├── KEGG/
│       ├── Models/
│       ├── UniProt/
│       └── readme.txt
└── src/
    ├── 01_Create_init_files/
    ├── 02_Classify_articles/
    ├── 03_Extract_information/
    ├── 04_Figures/
    ├── Mapa/
    ├── data_viz/
    ├── file_management.py
    └── text_analysis.py
```

## Installation

We recommend using **conda**:

```bash
conda create -n strain-db python=3.10 -y
conda activate strain-db
pip install -r requirements.txt
```

> Large files (PDFs, models) may require **Git LFS**:
```bash
git lfs install
git lfs track "*.pdf" "*.pickle" "*.model" "*.json"
```

## Data Pipeline

**Stages**
1. **Create initial files**: build seeds for journals, products, taxonomy.
2. **Classify articles**: fetch metadata, train classifier, label strain-design-relevant articles.
3. **Extract information**: retrieve full text, extract product, organism, gene targets, and modification directions; normalize via KEGG/UniProt/NCBI.
4. **Figures**: generate histograms, Sankey plots, and summary visuals.

## Core Data Schemas

**Articles Table**
- `article_id`, `doi`, `pmid`, `title`, `journal`, `year`, `is_strain_design`, `has_full_text`, `url_pdf`, `license`, `source`

**Entities Table**
- `article_id`, `host_taxon_id`, `host_name`, `product_id`, `product_name`, `evidence_section`, `confidence`

**Gene Modifications Table**
- `article_id`, `gene_symbol`, `locus_tag`, `uniprot_id`, `kegg_gene_id`, `ec_number`, `pathway`, `mod_type`, `direction`, `evidence_text`, `confidence`

## How to Reproduce

### Option A — Notebooks
Run notebooks in `src/02_Classify_articles/` and `src/03_Extract_information/` in order.

### Option B — Makefile
```bash
make init
make classify
make extract
make figures
```

## Figures & Visualizations

- `Organism_histogram.ipynb` — host distribution
- `Product_sankey.ipynb` — host/product/target flows

## License

This repository is released under the **MIT License** (see `LICENSE`).

## Citation

```
@article{MarquezZavala2025StrainDesignDB,
  title   = {A database of over 16,000 strain design publications reveals a conserved set of metabolic engineering targets},
  author  = {Márquez-Zavala, Elisa and Di Bartolomeu, Francesca and Machado, Daniel},
  journal = {TODO},
  year    = {2025},
  doi     = {TODO}
}
```

## Contact

For questions, please open an **Issue** or contact the corresponding author: **daniel.machado@ntnu.no**.
