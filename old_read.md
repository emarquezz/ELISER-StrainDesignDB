

# A database of over 15,000 strain design publications reveals a conserved set of metabolic engineering targets 🎯

<p align="center">
  <img src="img/Ecoli_cerevisiae.png" width="500">
</p>

**Authors**: Elisa Márquez-Zavala¹, Francesca Di Bartolomeo², Daniel Machado¹(\*)  
¹ Department of Biotechnology and Food Science, NTNU, Trondheim, Norway  
² SINTEF Industry, Trondheim, Norway  
(\*) Corresponding author: daniel.machado@ntnu.no

## Abstract
Microbial biotechnology has the potential to address several societal issues through the sustainable production of industrially relevant compounds. Despite decades of successful cases, rational engineering of microbial metabolism is still a complex process due to the fine balance between nutrient supply, allocation of cellular resources, energy demand and redox balancing. In this work, we implemented a text-mining workflow for metabolic engineering and compiled a **database of experimentally validated strain design strategies** from over **15.000** research articles, which includes information on **host strain**, **target compounds**, and **gene modifications**. This large dataset reveals trends on the selection of suitable hosts for different kinds of products and the respective gene targets. Despite the wide variety of microbes and products, we observe a **conserved set of target metabolic genes** associated with central carbon metabolism, especially in upper glycolysis, pentose-phosphate pathway, citric acid cycle, and fermentative pathways. The most distinguishing feature among strain design strategies seems not to be **which genes are targeted**, but rather the **direction** in which they are modified (increased or decreased expression). Controlling flux at **key branching points** and **redox balancing** reactions is thus a critical engineering step to steer metabolism. Our collection of 25 years of literature can provide a stepping stone for starting new strain design projects without reinventing the wheel.

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
    ├── data_viz/
    ├── file_management.py
    └── text_analysis.py
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

###  Notebooks
Run notebooks in `src/02_Classify_articles/` and `src/03_Extract_information/` in order.

## Figures & Visualizations

- `Organism_histogram.ipynb` — host distribution
- `Product_sankey.ipynb` — host/product/target flows

## License

This repository is released under the **MIT License** (see `LICENSE`).

## Citation

```

@article{MarquezZavala2025StrainDesignDB,
  title   = {A database of over 15,000 strain design publications reveals a conserved set of metabolic engineering targets across microbial hosts and products},
  author  = {Márquez-Zavala, Elisa and Di Bartolomeo, Francesca and Machado, Daniel},
  journal = {bioRxiv},
  year    = {2025},
  doi     = {10.64898/2025.12.15.694291},
  note    = {Preprint, not peer-reviewed}
}

```

## Contact

For questions, please open an **Issue** or contact the corresponding author: **daniel.machado@ntnu.no**.
