# Journal Filtering from PubMed Metadata

## Overview

The `src/01_Create_init_files/01_Journals` directory contains Jupyter notebooks and scripts designed to process PubMed journal metadata and generate lists of journals to **exclude** or **keep** based on keyword analysis. The workflow involves downloading journal metadata from NCBI, applying keyword-based filtering, and saving batched lists of journal IDs for downstream processing.

## Table of Contents

- [Directory Structure](#directory-structure)
- [Input Files](#input-files)
- [Output Files](#output-files)
- [Workflow Overview](#workflow-overview)
  - [1. Keyword Loading](#1-keyword-loading)
  - [2. Synonym Exploration](#2-synonym-exploration)
  - [3. Journal Metadata Parsing](#3-journal-metadata-parsing)
  - [4. Save Filtered Lists](#4-save-filtered-lists)
- [Parameters](#parameters)
- [Dependencies](#dependencies)

---

## Directory Structure

```
src/Journal_filtering/
├── Journal_filtering_pubmed.ipynb
├── ...
```

---

## Input Files

The following files and resources are used as input:

- **`../../files/Journals/Avoid/key_words_avoid.txt`**: Local keyword list used to identify journals to exclude.
- **Remote Source**:  
  `https://ftp.ncbi.nih.gov/pubmed/J_Medline.txt`  
  Contains PubMed journal metadata (titles, NLM IDs, etc.).

---

## Output Files

The notebook generates JSON files containing batched lists of journal IDs:

- **`list_journals_avoid.json`**: Journals flagged for exclusion.
- **`list_journals_possible.json`**: Journals considered acceptable.

These files are saved under:
- `../../files/Journals/Avoid/`
- `../../files/Journals/Keep/`

---

## Workflow Overview

### 1. Keyword Loading
**Notebook Section**: *Files → Input*  
Loads keywords from `key_words_avoid.txt` and normalizes them (lowercase, stripped quotes). Additional domain-specific keywords are appended manually.

### 2. Synonym Exploration
**Notebook Section**: *Synonym exploration*  
Uses semantic similarity to identify related terms for exclusion. This step is exploratory and does not automatically modify the keyword list.

### 3. Journal Metadata Parsing
**Notebook Section**: *Parse PubMed journal metadata*  
Downloads `J_Medline.txt` from NCBI and scans line by line:
- If any avoid keyword appears in a journal block → journal flagged for exclusion.
- Captures NLM IDs for both excluded and accepted journals.

### 4. Save Filtered Lists
**Notebook Section**: *Save list*  
Batches journal IDs into fixed-size groups (default: 2000 per batch) and saves them as JSON files for downstream processing.

---

## Parameters
- **Batch Size**: `JOURNAL_BATCH_SIZE = 2000`
- **SSL Context**: Disabled certificate verification for FTP access.

---

## Dependencies
- `pandas`
- Custom modules: `file_management`, `text_analysis`
