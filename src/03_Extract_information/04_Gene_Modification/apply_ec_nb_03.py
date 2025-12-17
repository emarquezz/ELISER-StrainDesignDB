import pandas as pd

def process_ec_df(df):
    df = df.copy()

    # --- Step 1: Align ECs with all organisms in each row ---
    def align_ecs(row):
        orgs = row['Organism']
        ecs = row['EC_search']
        return [(org, set(ecs)) for org in orgs]
    
    df['aligned'] = df.apply(align_ecs, axis=1)
    df_safe = df.explode('aligned').reset_index(drop=True)
    df_safe[['Organism', 'EC_search']] = pd.DataFrame(df_safe['aligned'].tolist(), index=df_safe.index)
    df_safe = df_safe.drop(columns=['aligned'])

    # --- Step 2: Aggregate ECs per gene-organism ---
    df_agg = df_safe.groupby(['Genes', 'Organism'], as_index=False).agg({'EC_search': lambda x: set().union(*x)})

    # --- Step 3: Get ECs from single-organism entries only ---
    single_org_rows = df[df['Organism'].map(len) == 1].copy()
    single_org_rows = single_org_rows.explode('Organism').explode('EC_search')

    single_org_ecs = (
        single_org_rows.groupby(['Genes', 'Organism'])['EC_search']
        .agg(set)
        .reset_index()
    )

    # Convert to dict for fast lookup
    single_org_dict = {(row['Genes'], row['Organism']): row['EC_search'] for _, row in single_org_ecs.iterrows()}

    # --- Step 4: Filter ECs ---
    def filter_ecs(row):
        key = (row['Genes'], row['Organism'])
        if key in single_org_dict:
            # Keep only ECs confirmed by single-organism evidence
            return row['EC_search'].intersection(single_org_dict[key])
        # No single-organism evidence -> ambiguous -> remove all ECs
        return set()

    df_final = df_agg.copy()
    df_final['EC_search'] = df_final.apply(filter_ecs, axis=1)

    # --- Step 5: Drop rows with no ECs left ---
    df_final = df_final[df_final['EC_search'].map(len) > 0].reset_index(drop=True)
    
    return df_final

# === Example datasets ===




import pandas as pd
import re
import numpy as np
import os

# ===============================================================
# 1️⃣ CONFIGURATION
# ===============================================================

POPULAR_ORGANISMS = [
    "Escherichia coli", 
    "Saccharomyces cerevisiae", 
    "Corynebacterium glutamicum",
    "Bacillus subtilis", 
    "Yarrowia lipolytica", 
    "Pseudomonas putida",
    "Komagataella pastoris",
    "Cupriavidus necator",
    "Synechococcus elongatus",
    "Lactococcus lactis"
]

# Global cache for gene lookups across all rows
# Now keyed by (organism, gene)
GLOBAL_GENE_CACHE = {}

# ===============================================================
# 2️⃣ LOAD POPULAR ORGANISM EC DATA
# ===============================================================

def load_popular_organism_ec_data(organism_name, base_path='../Genes/'):
    """
    Load EC data for a popular organism from a CSV file.
    Expects columns: 'superset_genes', 'EC_union_superset'
    """
    try:
        filename = organism_name.lower().replace(' ', '_') + '.csv'
        file_path = os.path.join(base_path, filename)
        
        if not os.path.exists(file_path):
            print(f"⚠️ File not found: {file_path}")
            return None
            
        df = pd.read_csv(file_path)
        df = df.dropna(subset=['EC_union_superset']).loc[:, ['superset_genes', 'EC_union_superset']]
        df['EC_union_superset'] = (
            df['EC_union_superset']
            .str.rstrip(';')
            .str.split(';')
            .apply(set)
        )
        df = df.explode('EC_union_superset').drop_duplicates()
        
        print(f"✅ Loaded {len(df)} gene–EC mappings for {organism_name}")
        return df
        
    except Exception as e:
        print(f"❌ Error loading data for {organism_name}: {e}")
        return None


    
print("📦 Loading organism-specific EC reference data...")

popular_organism_dfs = {
    org: load_popular_organism_ec_data(org)
    for org in POPULAR_ORGANISMS
}

# ===============================================================
# 3️⃣ SEARCH IN POPULAR ORGANISM DATABASES
# ===============================================================

def search_popular_organism_ec(gene, popular_organism_dfs):
    """
    Search for EC numbers for a given gene across all popular organism databases.
    Returns: set of EC numbers found
    """
    found_ecs = set()
    
    for organism_name, ec_df in popular_organism_dfs.items():
        if ec_df is None:
            continue
        
        matches = ec_df[ec_df['superset_genes'] == gene]
        if matches.empty:
            continue

        ecs = matches['EC_union_superset'].dropna().unique()
        ecs = [str(ec).strip() for ec in ecs if ec and ec != '0']
        found_ecs.update(ecs)
        
        if found_ecs:
            print(f"🔍 Found EC for {gene} in {organism_name}: {', '.join(found_ecs)}")
            break  # stop after first organism with results

    return found_ecs




# ===============================================================
# 5️⃣ MAIN EC MAPPING FUNCTION
# ===============================================================

def map_modifications_to_ec_fixed(row, ec_df, verbose=False, allow_cross_organism_fallback=True):
    """
    Optimized mapping function:
    - Handles list structures
    - Uses per-row and global organism-specific caching
    - Searches popular organism DBs only when needed
    - If organism is popular, searches large DB if not found in ec_df
    - Cross-organism fallback is optional (set allow_cross_organism_fallback=False to disable)
    """
    mods_value = row.get('Modifications', [])
    if not isinstance(mods_value, list) or not mods_value:
        return []
    
    organisms = row.get('Organism', [])
    if not isinstance(organisms, list) or not organisms:
        return []
    
    mapped_ecs = []
    row_cache = {}  # cache for this row only: {(organism, gene): [ECs]}
    
    for mod in mods_value:
        if not isinstance(mod, str):
            continue
        
        match = re.match(r"([\w-]+)\s*->\s*(.+)", mod)
        if not match:
            mapped_ecs.append(mod)
            continue
        
        gene, action = match.groups()

        found_ecs = set()

        # Search per organism
        for organism in organisms:
            if not isinstance(organism, str):
                continue
            
            cache_key = (organism, gene)

            # Step 0: Global cache check
            if cache_key in GLOBAL_GENE_CACHE:
                ecs = GLOBAL_GENE_CACHE[cache_key]
                for ec in ecs:
                    mapped_ecs.append(f"{ec} -> {action}")
                if verbose and ecs and ecs != [gene]:
                    print(f"[Cache hit] {organism}:{gene} -> {len(ecs)} ECs")
                continue

            # Step 1: Row-level cache check
            if cache_key in row_cache:
                ecs = row_cache[cache_key]
                for ec in ecs:
                    mapped_ecs.append(f"{ec} -> {action}")
                continue

            organism_ecs = set()
            found_in_original = False

            # Step 2: Search in main EC dataframe
            ec_matches = ec_df[
                (ec_df['Organism'] == organism) &
                (ec_df['Genes'] == gene)
            ]
            if not ec_matches.empty:
                ec_values = ec_matches['EC_search'].dropna().unique()
                ec_values = [str(ec).strip() for ec in ec_values if ec and ec != '0']
                organism_ecs.update(ec_values)
                found_in_original = True

            # Step 3: If organism is popular and not found, search its large DB
            if not found_in_original and organism in POPULAR_ORGANISMS:
                external_ecs = search_popular_organism_ec(gene, popular_organism_dfs)
                if external_ecs:
                    organism_ecs.update(external_ecs)
                    found_in_original = True

            # Step 4: (Optional) Try cross-organism fallback only if allowed
            if allow_cross_organism_fallback and not found_in_original and not organism_ecs:
                gene_matches = ec_df[
                    (ec_df['Genes'] == gene) &
                    (ec_df['Organism'].isin(POPULAR_ORGANISMS))
                ]
                if not gene_matches.empty:
                    ec_values = gene_matches['EC_search'].dropna().unique()
                    ec_values = [str(ec).strip() for ec in ec_values if ec and ec != '0']
                    organism_ecs.update(ec_values)

            # Cache results
            ecs_to_store = organism_ecs if organism_ecs else [gene]
            row_cache[cache_key] = ecs_to_store
            GLOBAL_GENE_CACHE[cache_key] = ecs_to_store

            # Build modification strings
            for ec in ecs_to_store:
                mapped_ecs.append(f"{ec} -> {action}")

            if verbose and organism_ecs:
                print(f"[Row {row.name}] {organism}:{gene} -> {len(organism_ecs)} ECs: {', '.join(organism_ecs)}")

    return mapped_ecs


# ===============================================================
# 6️⃣ APPLY TO MERGED DATAFRAME
# ===============================================================

# Example (uncomment when ready to use):
# merged_df['EC_Modifications'] = merged_df.apply(
#     lambda row: map_modifications_to_ec_fixed(
#         row, check, verbose=False, allow_cross_organism_fallback=False
#     ),
#     axis=1
# )




def map_modifications_to_ec_fixed(row, ec_df, verbose=False, allow_cross_organism_fallback=True):
    """
    Optimized mapping function returning dictionary structure:
    {
        gene: {
            'EC_numbers': [...],
            'Modifications': [...]
        }
    }
    """
    mods_value = row.get('Modifications', [])
    if not isinstance(mods_value, list) or not mods_value:
        return {}

    organisms = row.get('Organism', [])
    if not isinstance(organisms, list) or not organisms:
        return {}

    result_dict = {}
    row_cache = {}

    for mod in mods_value:
        if not isinstance(mod, str):
            continue

        match = re.match(r"([\w-]+)\s*->\s*(.+)", mod)
        if not match:
            continue

        gene, action = match.groups()
        found_ecs = set()

        for organism in organisms:
            if not isinstance(organism, str):
                continue

            cache_key = (organism, gene)

            # Step 0: Global cache check
            if cache_key in GLOBAL_GENE_CACHE:
                ecs = GLOBAL_GENE_CACHE[cache_key]
                found_ecs.update(ecs)
                if verbose:
                    print(f"[Cache hit] {organism}:{gene} -> {len(ecs)} ECs")
                continue

            # Step 1: Row cache check
            if cache_key in row_cache:
                ecs = row_cache[cache_key]
                found_ecs.update(ecs)
                continue

            organism_ecs = set()
            found_in_original = False

            # Step 2: Search in main EC dataframe
            ec_matches = ec_df[
                (ec_df['Organism'] == organism) &
                (ec_df['Genes'] == gene)
            ]
            if not ec_matches.empty:
                ec_values = ec_matches['EC_search'].dropna().unique()
                ec_values = [str(ec).strip() for ec in ec_values if ec and ec != '0']
                organism_ecs.update(ec_values)
                found_in_original = True

            # Step 3: Popular organism fallback
            if not found_in_original and organism in POPULAR_ORGANISMS:
                external_ecs = search_popular_organism_ec(gene, popular_organism_dfs)
                if external_ecs:
                    organism_ecs.update(external_ecs)
                    found_in_original = True

            # Step 4: Cross-organism fallback
            if allow_cross_organism_fallback and not found_in_original and not organism_ecs:
                gene_matches = ec_df[
                    (ec_df['Genes'] == gene) &
                    (ec_df['Organism'].isin(POPULAR_ORGANISMS))
                ]
                if not gene_matches.empty:
                    ec_values = gene_matches['EC_search'].dropna().unique()
                    ec_values = [str(ec).strip() for ec in ec_values if ec and ec != '0']
                    organism_ecs.update(ec_values)

            # Cache results
            # Cache results — only if we found ECs
            if organism_ecs:
                ecs_to_store = organism_ecs
                row_cache[cache_key] = ecs_to_store
                GLOBAL_GENE_CACHE[cache_key] = ecs_to_store
                found_ecs.update(ecs_to_store)
            else:
                # Cache an empty list to avoid re-searching, but don't include gene name
                row_cache[cache_key] = []
                GLOBAL_GENE_CACHE[cache_key] = []
                if verbose:
                    print(f"[No EC found] {organism}:{gene}")


        # Add to result dictionary
        if gene not in result_dict:
            result_dict[gene] = {"EC_numbers": [], "Modifications": []}

        # Avoid duplicates
        for ec in found_ecs:
            if ec not in result_dict[gene]["EC_numbers"]:
                result_dict[gene]["EC_numbers"].append(ec)

        result_dict[gene]["Modifications"].append(action)

        if verbose and found_ecs:
            print(f"[Row {row.name}] {gene} -> ECs: {', '.join(found_ecs)}")

    return result_dict



import re

def normalize_modification(text):
    text = str(text).lower().strip()
    #check the last ones, specially would
    filler_re = re.compile(r'\b(?:was|were|is|are|be|been|being|the|a|an|in|or|and|for|of|when|both|with|further|its|to|would|gene)\b')
    nonalpha_re = re.compile(r'[^a-z\s-]+')
    last_vowel_re = re.compile(r'[aeiou](?!.*[aeiou])')  # matches the last vowel

    text = filler_re.sub('', text)
    text = re.sub(r'\s+', ' ', text).strip()
    text = nonalpha_re.sub('', text)
    single_words = ['block','coexpress','express','mutant','knock','repress',
                              'disrupt','not','engineer', 'lack','insert']
    single_words += [word+'s' for word in single_words]
    words = []

    for word in text.split():
        m = last_vowel_re.search(word)
        
        if m and word not in single_words:
            last_vowel_index = m.start()
            # If there's an 'i' immediately before the last vowel, cut before that 'i'
            cut_index = last_vowel_index - 1 if last_vowel_index > 0 and word[last_vowel_index - 1] in ['i','o'] else last_vowel_index
            trimmed = word[:cut_index]
            words.append(trimmed if trimmed else word[:max(1, cut_index)])
        else:
            words.append(word)
    return " ".join(words).strip()


def extract_and_normalize_dict(ec_mod_dict):
    """
    Normalize modifications inside a dictionary like:
    {
        gene: {
            'EC_numbers': [...],
            'Modifications': [...]
        }
    }

    Returns a new dictionary with normalized modification text.
    """
    if not isinstance(ec_mod_dict, dict):
        return None

    normalized_dict = {}

    for gene, data in ec_mod_dict.items():
        ecs = data.get('EC_numbers', [])
        mods = data.get('Modifications', [])

        normalized_mods = [normalize_modification(m) for m in mods if isinstance(m, str)]

        normalized_dict[gene] = {
            'EC_numbers': ecs,
            'Normalized_Modifications': normalized_mods
        }

    return normalized_dict