# ChEBI Products — Initialization

## Overview

The `src/01_Create_init_files/03_ChEBI_Products` folder contains a single Jupyter notebook used to build a **local ChEBI database** from the official flat files hosted by EBI. The workflow downloads the required TSV.gz files, decompresses them, loads and cleans compound names and English synonyms, and saves a compact JSON database for downstream tasks.

## Table of Contents

- [Directory Structure](#directory-structure)
- [Input Files](#input-files)
- [Output Files](#output-files)
- [Workflow Overview](#workflow-overview)
  - [1. Download ChEBI files](#1-download-chebi-files)
  - [2. Gather and clean data](#2-gather-and-clean-data)
  - [3. Save DB](#3-save-db)
- [Parameters & Assumptions](#parameters--assumptions)
- [Dependencies](#dependencies)

---

## Directory Structure

```
ELISER-StrainDesignDB/
└─ src/01_Create_init_files/03_ChEBI_Products/
   ├─ Extract_ChEBI_data.ipynb
   └─ ...
```

> Note: Data files are stored under the project `files` directory resolved by `get_files_dir()`.

---

## Input Files

### Remote sources
- **ChEBI names** (English synonyms and preferred names; gzipped TSV):
  - `.../chebi/flat_files/names.tsv.gz`
- **ChEBI compounds** (core compound table; gzipped TSV):
  - `.../chebi/flat_files/compounds.tsv.gz`

*(The notebook downloads and decompresses these to the local ChEBI folder.)*

### Local paths used by the notebook
- `../../files/ChEBI/` — local directory created if missing
- After download & extraction:
  - `../../files/ChEBI/names.tsv`
  - `../../files/ChEBI/compounds.tsv`

---

## Output Files

- `../../files/ChEBI/chebi.json` — consolidated database with:
  - **index**: ChEBI compound `id`
  - **columns**: `name` (preferred compound name), `Synonym` (cleaned English synonym list), `Full_synonym` (raw/complete list before cleaning, when available)

---

## Workflow Overview

### 1. Download ChEBI files
**Notebook section**: *Download ChEBI files*
- Helper: `download_and_gunzip(url, out_dir)`
  - Downloads `names.tsv.gz` and `compounds.tsv.gz` to `../../files/ChEBI/`
  - Decompresses to `names.tsv` and `compounds.tsv`
  - Skips download if the decompressed file already exists

### 2. Gather and clean data
**Notebook section**: *Gather and clean data*
- **Load compounds**: `compounds.tsv` (read as strings; index on `id`) → keep `name` column
- **Load synonyms**: `names.tsv` (index on `compound_id`)
  - Filter to English (`language_code=='en'`) and select `type`/`name`
  - Drop duplicate rows
  - Group by `compound_id` to aggregate synonyms as lists
  - Create `Synonym` (cleaned) and `Full_synonym` (original list)
- **Cleaning** (`clean_chebi_name`):
  - Remove simple HTML tags (regex for `<...>`)
  - Collapse whitespace and trim
- **Combine**: concatenate `name` (from compounds) with `Synonym` and `Full_synonym` (from names)
- **Finalize**: fill missing synonym lists with the preferred `name`

### 3. Save DB
**Notebook section**: *Save DB*
- Persist the assembled DataFrame to `chebi.json` under `../../files/ChEBI/` using `check_save_file`

---

## Parameters & Assumptions
- The project paths `(ROOT, INPUT_DIR, OUTPUT_DIR)` are resolved by `get_files_dir()`.
- Remote downloads require internet access; the notebook assumes EBI FTP over HTTPS is reachable.
- Encoding is handled by pandas default TSV reader with `dtype=str` to preserve identifiers as strings.
- Basic HTML-like markup may appear in synonym text; the regex cleaner removes simple tags.

---

## Dependencies
- `pandas`, `gzip`, `shutil`, `urllib.request`, `re`, `pathlib`
- Project helpers: `file_management` → `get_files_dir`, `check_save_file`

