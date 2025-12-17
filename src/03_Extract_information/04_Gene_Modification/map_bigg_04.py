import pandas as pd
import numpy as np
from os.path import exists
from requests import get
import cobra

import re



def get_MetaNetX(database, dirname="./metanetx"):
    """filter_df_by_model
    Load MetaNetX table with YOUR format:
    columns = ['XREF', 'MNX_ID', 'Evidence', 'Description']
    """
    valid = ['reac_xref','chem_xref','reac_prop','chem_prop']
    filepath = f"{dirname}/{database}.tsv"

    if not exists(filepath) and database in valid:
        with open(filepath, "wb") as fh, get(
            f"https://www.metanetx.org/cgi-bin/mnxget/mnxref/{database}.tsv",
            stream=True
        ) as r:
            for chunk in r.iter_content(1024):
                fh.write(chunk)

    return pd.read_table(
        filepath,
        comment="#",
        names=['XREF','MNX_ID','Evidence','Description']
    )




def filter_df_by_model(df, model):
    keep_list = [rxn.id for rxn in model.reactions]

    dup_mnx = df['MNX_ID'][df['MNX_ID'].duplicated(keep=False)].unique()
    to_keep = []

    for mnx in dup_mnx:
        subset = df[df['MNX_ID'] == mnx]

        if any(subset['XREF'].isin(keep_list)):
            # keep only matching
            to_keep.append(subset[subset['XREF'].isin(keep_list)])
        else:
            to_keep.append(subset)

    processed = pd.concat(to_keep, ignore_index=True)
    nondup = df[~df['MNX_ID'].isin(dup_mnx)]

    return pd.concat([processed, nondup], ignore_index=True)



def get_tables(dir_data_metanetx):

        # --- Load reaction cross-references ---
        rxns_xref = get_MetaNetX('reac_xref', dir_data_metanetx)

        # Separate KEGG and BiGG reactions
        BIGG_rxn_info = rxns_xref[
            (rxns_xref['XREF'].str.startswith('bigg.reaction')) |
            (rxns_xref['XREF'].str.startswith('biggR'))
        ].copy()

        # Clean up XREF fields
        BIGG_rxn_info['XREF'] = BIGG_rxn_info['XREF'].str.split(':').str[1]

        # Clean BiGG data
        BIGG_rxn_info.replace('EMPTY', np.nan, inplace=True)
        BIGG_rxn_info.dropna(subset=['MNX_ID'], inplace=True)
        BIGG_rxn_info = BIGG_rxn_info[~BIGG_rxn_info['XREF'].str.startswith('R_')]
        BIGG_rxn_info = BIGG_rxn_info.drop_duplicates()


        # --- Load and process reaction properties ---
        reac_prop = get_MetaNetX('reac_prop', dir_data_metanetx)
        rxn_prop = (
            reac_prop
            .reset_index()
            .rename(columns={'level_0': 'MNX_ID', 'level_1': 'MNX_Formula', 'MNX_ID': 'EC_number'})
        )
        
        return(BIGG_rxn_info, rxn_prop)
    
    
    
    

def merge_by_mnx(df):
    """
    Merge rows with the same MNX_ID by concatenating XREFs (and
    other duplicate info if desired).
    """
    merged = (
        df.groupby('MNX_ID', as_index=False)
          .agg({'XREF': lambda x: ';'.join(sorted(set(x)))})
    )
    return merged



def clean_bigg_ecs(ec_str):
    """
    Clean EC numbers:
    - Split by ';'
    - Remove empty and malformed entries
    - Exclude entries containing '-'
    - Keep only valid EC numbers with up to 4 numeric levels
    - Prefer fully specified 4-level EC numbers if available
    """
    if pd.isna(ec_str):
        return set()
    
    ecs = [e.strip() for e in ec_str.split(";") if e.strip()]
    
    # Keep only valid EC format entries like 1.1.1.1 or 2.7.7
    valid_pattern = re.compile(r'^\d+(\.\d+){1,3}$')
    ecs = [e for e in ecs if valid_pattern.match(e)]
    
    # Prefer 4-level EC numbers if any exist
    full_ecs = [e for e in ecs if len(e.split(".")) == 4]
    if full_ecs:
        return set(full_ecs)
    
    # Otherwise, keep all valid ECs (even if less specific)
    return set(ecs)



def compute_all_metrics(row, too_general,gene_ec_lookup,rxn_ec_lookup):
    gene_ecs = gene_ec_lookup[row["Gene"]]
    rxn_ecs = rxn_ec_lookup[row["MNX_ID"]]
    matched = row["Matching_ECs"]

    # --- Unmatched ECs ---
    unmatched_gene = gene_ecs - matched
    unmatched_rxn = rxn_ecs - matched

    # --- Gene-based metrics ---
    total_gene_ec = len(gene_ecs)
    match_count_gene = len(matched)
    fraction_gene = round(match_count_gene / total_gene_ec, 3) if total_gene_ec else 0

    corrected_gene_ecs = [ec for ec in gene_ecs if not (ec in too_general and ec in unmatched_gene)]
    corrected_matched_gene = [ec for ec in matched if ec in corrected_gene_ecs]
    corrected_total_gene = len(corrected_gene_ecs)
    corrected_fraction_gene = round(len(corrected_matched_gene) / corrected_total_gene, 3) if corrected_total_gene else 0

    # --- Reaction-based metrics ---
    total_rxn_ec = len(rxn_ecs)
    match_count_rxn = len(matched)
    fraction_rxn = round(match_count_rxn / total_rxn_ec, 3) if total_rxn_ec else 0

    corrected_rxn_ecs = [ec for ec in rxn_ecs if not (ec in too_general and ec in unmatched_rxn)]
    corrected_matched_rxn = [ec for ec in matched if ec in corrected_rxn_ecs]
    corrected_total_rxn = len(corrected_rxn_ecs)
    corrected_fraction_rxn = round(len(corrected_matched_rxn) / corrected_total_rxn, 3) if corrected_total_rxn else 0

    return pd.Series({
        "Unmatched_Gene_ECs": unmatched_gene,
        "Unmatched_Reaction_ECs": unmatched_rxn,
        "Gene_EC_Total": total_gene_ec,
        "Reaction_EC_Total": total_rxn_ec,
        "Match_Count": len(matched),
        "Fraction_Matched": fraction_gene,
        "Corrected_Fraction_Matched": corrected_fraction_gene,
        "Reaction_Fraction_Matched": fraction_rxn,
        "Reaction_Corrected_Fraction_Matched": corrected_fraction_rxn,
    })
