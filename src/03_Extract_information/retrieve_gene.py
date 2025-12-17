# TODO update with new function in Gene_extraction.ipynb
# TODO save the format table
import requests
import sys
from io import StringIO
import re
import pandas as pd
import numpy as np

ORG_SYNONYM = {'Pichia pastoris':'Komagataella pastoris','Ralstonia eutropha':'Cupriavidus necator',
          "Streptomyces roseosporus":"Streptomyces filamentosus","Clostridium thermocellum":"Acetivibrio thermocellus",
          "Rhodobacter sphaeroides":"Cereibacter sphaeroides","Bacillus megaterium":"Priestia megaterium",
           "Bacillus circulans":"Niallia circulans",'Lactobacillus casei':'Lacticaseibacillus casei'}

fake_genes = ['aci', 'acid', 'act', 'add', 'air', 'ale', 'alpha', 'atp', 'beta', 'can', 'case', 'cat',
              'cell', 'coa', 'core', 'dead', 'downstream', 'dye', 'eco', 'enzyme', 'era', 'family',
              'far', 'fit', 'fold', 'frame', 'fusion', 'gap', 'gene', 'had', 'heme', 'high', 'hold',
              'hypothetical','infection', 'internal', 'iron', 'last', 'like', 'mCherry', 'many', 'map',
              'mode', 'mutation', 'nine', 'nisin', 'operon','old', 'para', 'partial', 'past', 'per',
              'plasmid','product', 'protein', 'pure', 'putative', 'reverse', 'rna', 'ros', 'smal',
              'small', 'sub', 'subunit', 'synthase', 'tag', 'this', 'top', 'transport', 'truncated', 
              'well', 'year','alpha','com','rec','pro','flanking','nat','pre','alkaline','con','ORF',
              'ref','iso','gfp','transporter','peptide','permease','chemotaxis','assembly','membrane',
              'variant', 'virulence', 'signal', 'endonuclease', 'transcriptase', 'associated', 'hit',
              'transportase', 'dehydrogenase', 'DNA', 'unknown', 'polymerase', 'endoglucanase',
              'predicted', 'clone', 'etc', 'tmRNA', 'end', 'homolog', 'orf', 'replication', 'xylanase',
              'element', 'fig', 'set', 'hydrolase', 'sigma', 'theta', 'nuclease', 'surface', 'bar',
              'mate', 'pol', 'domain', 'initiation', 'reading', 'regulatory', 'cellobiohydrolase',
              'precursor', 'serine', 'coA', 'NADH','NADPH', 'mRNA', 'GFP', 'homologue', 'lipase',
              'pumilus', 'Bacillus', 'transposase', 'restriction', 'stability', 'exported', 'exporter',
              'delta', 'cistron', 'serine', 'cytoplasmic', 'regulator', 'fructose', 'phytol', 'glycosyltransferase',
              'allele', 'conserved', 'trehalose', 'class', 'open', 'type', 'pink', 'sugar', 'chat', 'zeta',
              'omega','exo'
             ]
# is coA and NADH right? probably not...

# do not trust con and alpha... com and nat
fake_genes  += [word.capitalize() for word in fake_genes ]

REPLACEMENTS = {
    r'\b[cC]an be\b': ' ',
    r'\b[sS]o far\b': ' ',
    r'\b[Tt]hus far\b': ' ',
    r'Δ': ' ',
    r'\b[Pp]er year\b': '',
    r'\b[Pp]r cell\b': '',
    r'\b[Pp]er L\b': ' ',
    r'\b[Pp]er litre\b': '',
    # also remove numbers
    r'\b\d+\b': '',
    # Remove heterologous things
    r'\([\+\-]\/[\-\+]\)': ''

}

def generate_url(taxid, reviewed=True):
    #start_url = 'https://rest.uniprot.org/uniprotkb/stream?fields=accession%2Creviewed%2Cid%2Cprotein_name%2Cgene_names%2Corganism_name%2Cgene_synonym&format=tsv&query=%28%28taxonomy_id%3A'
    if reviewed:
        reviewed_url = '%20AND%20%28reviewed%3Atrue%29'
    else:
        reviewed_url = ''
    start_url = 'https://rest.uniprot.org/uniprotkb/stream?fields=accession%2Cid%2Cgene_names%2Corganism_name%2Cec%2Crhea%2Cxref_kegg%2Cxref_geneid%2Cxref_ko%2Cxref_brenda%2Cxref_unipathway%2Cgo_id%2Cgene_synonym&format=tsv&query=%28%28taxonomy_id%3A'

    end_url = '%29%29'
    url = start_url+taxid+end_url+reviewed_url
    return(url)

def retrieve_data(url):
    try:
        all_fastas = requests.get(url)
        TESTDATA = StringIO(all_fastas.text)
        genes_pd = pd.read_table(TESTDATA)
    except:
        genes_pd = pd.DataFrame()

    return(genes_pd)


def remove_uninformative_genes(organisms_df):
    temp_df = organisms_df.groupby('superset_genes').agg('sum').reset_index()
    pattern = r'[a-zA-Z0-9]{2,6}_[a-zA-Z]{0,3}[0-9]{2,6}'
    temp_df = temp_df[~temp_df['superset_genes'].str.contains(pattern, regex=True)]
    pattern = r'^[0-9_-]+$'
    temp_df = temp_df[~temp_df['superset_genes'].str.contains(pattern, regex=True)]
    pattern = r'^(ORF|orf)\d+$'
    temp_df = temp_df[~temp_df['superset_genes'].str.contains(pattern, regex=True)]
    pattern = r'^S\d+$'
    temp_df = temp_df[~temp_df['superset_genes'].str.contains(pattern, regex=True)]
    #remove cas1 cas2....
    pattern = r'^cas\d+$'
    temp_df = temp_df[~temp_df['superset_genes'].str.contains(pattern, regex=True)]
    return(temp_df)

def all_gene_names(genes_pd):
    gene_names = genes_pd.loc[:,'Gene Names'].dropna().values
    gene_syn = genes_pd.loc[:,'Gene Names (synonym)'].dropna().values
    all_genes = list(gene_names)
    all_genes.extend(list(gene_syn))
    genes = set(' '.join(all_genes).split(' '))
    return(genes)

def get_synonym_dict(genes_pd):
    genes_pd = genes_pd.astype({'Gene Names':'str'})
    genes_w_synon_list = genes_pd.loc[:,'Gene Names'].str.split().to_list()
    #print(genes_w_synon_list)
    genes_w_synon_repeat = pd.DataFrame([ pd.Series(value) for value in genes_w_synon_list ])
    if not genes_w_synon_repeat.empty:
        genes_w_synon_repeat.rename(columns ={0:'Original_name'}, inplace=True)
        genes_w_synon_repeat.set_index('Original_name', inplace= True)

        group_synon = genes_w_synon_repeat.groupby('Original_name')

        synonyms = {}
        for grupito in group_synon.groups:
            genes = group_synon.get_group(grupito)
            new_genes = genes.dropna(axis=1,how='all')
            if not new_genes.empty:
                synonyms[grupito] = new_genes.unstack().dropna().values

        gene_synonyms = pd.DataFrame({ key:pd.Series(value) for key, value in synonyms.items() })
        return(gene_synonyms)
    

def download_genes_per_organism(top_organisms):
    """
    Downloads gene information for a set of top organisms.

    Parameters
    ----------
    top_organisms : dict
        A dictionary containing the names of the top organisms as keys and their corresponding
        taxonomy IDs as values.

    Returns
    -------
    tuple
        A tuple containing three dictionaries: (1) a dictionary of Pandas series where each series 
        contains the gene names for an organism, (2) a dictionary of Pandas dataframes where each 
        dataframe contains the synonyms for the genes of an organism, and (3) a dictionary of Pandas 
        dataframes where each dataframe contains the full UniProt information for the genes of an organism.

    Raises
    ------
    Exception
        If the data cannot be downloaded or processed for any of the specified organisms, an exception is raised.

    Notes
    -----
    This function downloads gene information for the top organisms specified in the input dictionary.
    It first tries to read pre-existing files containing the gene information for each organism, and if
    those files do not exist, it downloads the information from the UniProt website. The gene information 
    is saved in three different formats: a Pandas series containing only the gene names, a Pandas 
    dataframe containing the synonyms for the genes, and a Pandas dataframe containing the full UniProt 
    information for the genes. The resulting dictionaries contain the gene information for each organism.
    """
    series = {}
    series_synonyms = {}
    full_table={}
    faulty = {}
    # Loop through each organism and download or read the gene information
    for organism,taxid in top_organisms.items():
        
        file_name = organism.replace(' ', '_')+'.csv'
        
        try:
            # Full_table
            #genes_pd = pd.read_csv('./Full_UniProt/'+file_name, dtype=str)
            formated_table = pd.read_csv('../Genes/'+file_name, dtype=str)
            full_table[organism] = formated_table
            
        except:
            print('Fail1',file_name)
            try:
                print('holi')
                genes_pd = pd.read_csv('../Full_UniProt/'+file_name, dtype=str)
            except:
                print('Fail2')
                # If pre-existing files do not exist, download gene information from UniProt website
                #print('no file, lets retrieve it')
                url = generate_url(taxid, reviewed=False)
                print(url)
                genes_pd = retrieve_data(url)
                if genes_pd.empty:
                    print(f'\nNo reviewed UniProt info for {organism} with taxid: {taxid}')
                    url = generate_url(taxid, reviewed=False)
                    genes_pd = retrieve_data(url)
                    if genes_pd.empty:
                        print(f'No UniProt info for {organism} with taxid: {taxid}')
                        faulty[organism] = taxid
                        continue
                    else:
                        print('Using unreviewed data instead')
                        genes_pd.to_csv('../Full_UniProt/'+file_name, index=False)
                else:
                    genes_pd.to_csv('../Full_UniProt/'+file_name, index=False)

                #genes_filter.sort()
                # Save gene information to files


            #KEGG id (full table, maybe add it to synonyms or genes?)
            formated_table, valid_genes = format_all_genes_new(genes_pd)
            if not valid_genes:
                print(f'No gene names in uniprot for the {organism}')
                faulty[organism] = taxid
                continue
            full_table[organism] = formated_table
            formated_table.to_csv('../Genes/'+file_name, index=False)
            
    
    # Swap the keys and values of All_gene_names_x
    #swap_dict = {v: k for k, v in indexed_concatenated_df.All_gene_names_x.to_dict().items()}
        
    return(full_table,faulty)
# Add organisms to fake genes
# Add restriction enzymes
# Remove also cas genes?



def search_cap_variants(sentence, organism_data):
    # Capitalize (leave the rest the same)
    organism_first_cap = organism_data.copy().assign(superset_genes=organism_data['superset_genes'].str[0].str.upper()+organism_data['superset_genes'].str[1:])
    organism_first_cap = organism_first_cap.drop_duplicates()
    # Filter out already capitalized gene names

    mask = organism_first_cap['superset_genes'] != organism_data['superset_genes']
            
    #Search
    filtered_genes = organism_first_cap.loc[mask]
    genes_found = search_gene(sentence, filtered_genes)
    return organism_first_cap, genes_found


def search_last_cap_variants(sentence, organism_data):
    # lower and cap the last letter
    organism_last_cap = organism_data.copy().assign(superset_genes=organism_data['superset_genes'].str[0:-1].str.lower()+organism_data['superset_genes'].str[-1].str.upper())
    organism_last_cap = organism_last_cap.drop_duplicates()
    # Filter out already capitalized gene names
    mask = organism_last_cap['superset_genes'] != organism_data['superset_genes']
            
    #Search
    filtered_genes = organism_last_cap.loc[mask]
    genes_found = search_gene(sentence, filtered_genes)
    return organism_last_cap, genes_found

def search_upper_variants(sentence, organism_data, organism_first_cap):
    
    # Make upper
    organism_upper = organism_data.copy().assign(superset_genes=organism_data['superset_genes'].str.upper())
    organism_upper = organism_upper.drop_duplicates()
    # Filter out already capitalized gene names
    mask = organism_upper['superset_genes'] != organism_data['superset_genes']
                
    #organism_first_cap = organism_first_cap.loc[mask] 
    mask2 = organism_upper['superset_genes'] != organism_first_cap['superset_genes']

    #Search
    filtered_genes = organism_upper.loc[mask & mask2]
    genes_found = search_gene(sentence, filtered_genes)
    return organism_upper, genes_found

def search_gene(sentence, organism_data):
    genes_series = organism_data.superset_genes.dropna()
    genus_mask = np.isin(sentence, genes_series)
    prob_genes = sentence.loc[genus_mask]
    prob_genes = prob_genes.loc[~np.isin(prob_genes, fake_genes)]
    if not prob_genes.empty:
        genes_found_uniprot = organism_data.loc[organism_data.superset_genes.isin(prob_genes)]
        return(genes_found_uniprot.values)
    else:
        return([['Try_again']])

def get_genes_from_text(sentence, organism, organism_genes):
    """
    Extracts gene names from a given sentence that match a specific organism's genes.

    Parameters:
    -----------
    sentence : pd.Series
        A pandas Series of strings representing the input sentence(s) to extract gene names from.
    organism : str
        A string representing the name of the organism for which gene names will be extracted.
    organism_genes : dict
        A dictionary where keys are the names of organisms and values are pandas Series 
        of gene names for each respective organism.

    Returns:
    --------
    A list of strings representing gene names that were found in the input sentence(s) 
    and match the gene names for the specified organism. If no gene names were found, 
    returns None.

    Raises:
    -------
    KeyError: If the organism name provided is not found in the organism_genes dictionary.
    """
    
    if organism in organism_genes.keys():
        sentence  = sentence.dropna().drop_duplicates()
        sentence = sentence.loc[sentence.str.len()>2]
        
        organism_data = organism_genes[organism].groupby('superset_genes').agg(sum).reset_index()
        
        genes_found = search_gene(sentence, organism_data)
        
        if  genes_found[0][0] != 'try_again':
            return(genes_found)
        else:
            # Instead of searching araC, search AraC
            first_cap = organism_data.superset_genes.str[0].str.upper()+organism_data.superset_genes.str[1:]
            organism_first_cap = organism_data.loc[organism_data.superset_genes != first_cap]
            
            genes_found = search_gene(sentence, organism_first_cap)
            
            if  genes_found[0][0] != 'try_again':
                return(genes_found)
            else:
                # Searh lower just in case
                lower_cap = organism_data.superset_genes.str.lower()
                organism_lower_cap = organism_data.loc[organism_data.superset_genes != lower_cap]
                
                sentence = sentence.str.lower()
                
                genes_found = search_gene(sentence, organism_lower_cap)
                
                if  genes_found[0][0] != 'try_again':
                    return(genes_found)
    else:
        
        print(f'Organism {organism} not found')
        
        
def get_genes_mlp(texto, genes):
    excluded_genes = ['mutation', 'can', 'tag', 'era', 'act', 'dye', 'fit', 'far', 'air', 'add', 'truncated', 'downstream', 'fusion', 'gene']
    genes = genes.loc[~genes.isin(excluded_genes)]
    genes = genes.str.replace('(','\\(',regex='False')
    genes = genes.str.replace(')','\\)',regex='False')

    genes = '\\b|\\b'.join(genes.values)
    genes = '\\b'+genes+'\\b'
    re_genes = re.compile(genes)
    
    full_text = texto
    full_text = full_text.replace(' can be ', '')
    full_text = full_text.replace(' so far ', '')
    full_text = full_text.replace(' thus far ', '')
    full_text = full_text.replace('Δ',' ')

    pos_genes = []
    results = []

    found_genes = []
    text = full_text
    match =re_genes.search(text)
    while match:
        found_genes.append(match.group())
        if match.group() == 'miau':
            print(text)
        text = re.sub(match.group(),'',text)
        match =re_genes.search(text)

    return found_genes


def get_genes_specific_organism(texto,organism,organism_genes):
    if organism in organism_genes.keys():
        genes_series = organism_genes[organism].astype({organism:'str'}) 


        genes_series = genes_series.dropna()
        genes = get_genes_mlp(texto, genes_series)
        return(genes)
    else:
        return([])

    
def format_all_genes_new(genes_pd: pd.DataFrame) -> pd.DataFrame:
    """
    Cleaner reimplementation of format_all_genes.
    Keeps the same output schema/format, now also handling EC numbers.
    """

    # --- Step 1: Prepare input ---
    df = genes_pd.copy()
    df = df.set_index("Entry")

    # Merge main + synonym names
    df["All_gene_names"] = (
        df["Gene Names"].fillna("").astype(str) + " " +
        df["Gene Names (synonym)"].fillna("").astype(str)
    ).str.strip()

    # --- NEW: Drop rows with no gene names at all ---
    df = df[df["All_gene_names"] != ""]
    if df.empty:
        return None, False   # flag = True → no valid gene names    
    
    # Keep only relevant cols
    df = df[["All_gene_names", "KEGG", "EC number"]].drop_duplicates()

    # Tokenize and clean gene names
    df["All_gene_names"] = df["All_gene_names"].str.strip().str.split()
    df = df.explode("All_gene_names").drop_duplicates()
    df = df[df["All_gene_names"].str.len() > 2]
    df["All_gene_names"] = df["All_gene_names"].str.replace(r"['()]", "", regex=True)
    df = df.drop_duplicates().reset_index()  # restore Entry as column

    # --- Step 2: Groupings ---

    # Helper: split EC numbers into sets
    def split_ec(series):
        out = set()
        for val in series.dropna():
            for ec in str(val).split(";"):
                ec = ec.strip()
                if ec:
                    out.add(ec)
        return out

    # For each gene
    gene_groups = df.groupby("All_gene_names").agg({
        "Entry": set,
        "KEGG": lambda x: set(x.dropna()),
        "EC number": split_ec
    }).rename(columns={
        "Entry": "Entry_Set",
        "KEGG": "KEGG_genes_set",
        "EC number": "EC_genes_set"
    })

    # For each entry
    entry_groups = df.groupby("Entry").agg({
        "All_gene_names": set,
        "KEGG": lambda x: set(x.dropna()),
        "EC number": split_ec
    }).rename(columns={
        "All_gene_names": "Genes_set",
        "KEGG": "KEGG_entry_set",
        "EC number": "EC_entry_set"
    })

    # Merge back into df
    merged = df.merge(gene_groups, left_on="All_gene_names", right_index=True)
    merged = merged.merge(entry_groups, on="Entry")

    # Supersets
    superset_entry = merged.groupby("Entry")["Entry_Set"].apply(lambda sets: set.union(*sets)).rename("superset_entry")
    superset_genes = merged.groupby("All_gene_names")["Genes_set"].apply(lambda sets: set.union(*sets)).rename("superset_genes")

    merged = merged.merge(superset_entry, on="Entry")
    merged = merged.merge(superset_genes, left_on="All_gene_names", right_index=True)

    # KEGG + EC supersets
    merged["KEGG_union_superset"] = merged.apply(
        lambda row: row["KEGG_entry_set"].union(row["KEGG_genes_set"]), axis=1
    )
    merged["EC_union_superset"] = merged.apply(
        lambda row: row["EC_entry_set"].union(row["EC_genes_set"]), axis=1
    )

    # --- Step 3: Format output ---
    values = merged.loc[:, ["superset_entry", "superset_genes", "KEGG_union_superset", "EC_union_superset"]]

    values["superset_entry"] = values["superset_entry"].apply(lambda x: "_".join(sorted(list(x))))
    values["superset_genes"] = values["superset_genes"].apply(list)

    # KEGG: same as old function (concatenate without delimiter)
    values["KEGG_union_superset"] = values["KEGG_union_superset"].apply(
        lambda x: "".join(sorted([v for v in x if v]))
    )

    # EC: always join with ";" for clarity, and ensure trailing ";"
    values["EC_union_superset"] = values["EC_union_superset"].apply(
        lambda x: ";".join(sorted([v for v in x if v])) + (";" if x else "")
    )

    # One row per gene
    final_table = values.explode("superset_genes").drop_duplicates()

    # Legacy behavior: group and concat with sum
    return final_table.groupby("superset_genes").agg(sum).reset_index(), True