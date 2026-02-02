#TODO REMOVE SUPPLEMENTARY MATERIALS 
import re
import pandas as pd
import sys
sys.path.append('..')

from file_management import get_files_dir,check_save_file
_, INPUT_DIR, OUTPUT_DIR = get_files_dir()

def nospecial(text):
    """
    Remove HTML tags and special characters from a string.

    Parameters:
    text (str): The string to clean.

    Returns:
    str: The cleaned string.
    """
    html_tags = re.compile(r'<.*?>')
    text = re.sub(html_tags, '', text)
    text = re.sub(r"[^a-zA-Z0-9 ]+", " ",text)
    text = re.sub(r"\.", " ",text)
    
    return text


taxonomy = INPUT_DIR+'/Taxonomy/Filtered_taxonomy_new_v.csv'
taxonomy = pd.read_csv(taxonomy)
true_species = taxonomy.Full_name.dropna().drop_duplicates()
true_genus = taxonomy.Genus.dropna().drop_duplicates()

#full_species= true_species.str.split(' ').str[0:2].str.join(' ').drop_duplicates()
full_species = true_species.sort_values().str.split(' ').str[0:2].str.join(' ').drop_duplicates()
full_species = full_species.apply(nospecial)
full_species = full_species.str.rstrip()
full_species = full_species.drop_duplicates(keep='first')
full_species = full_species.loc[~full_species.str.match(r'^\d.*')]

#true_genus = taxonomy.Genus.dropna().drop_duplicates()


species_list = true_species
species_list = species_list.str.split(' ').str[1].drop_duplicates().str.lower()
species_list = species_list.loc[~species_list.str.contains('degrading') ]


genus_list = true_genus
genus_list = genus_list.str.split('/').explode().drop_duplicates()


# Make the search faster byputting the most common ones on top
important_values = ['Escherichia','Saccharomyces','Corynobacterium','Bacillus','Synechocystis','Yarrowia','Pseudomonas']
important_series = genus_list[genus_list.index.isin(important_values)]
other_series = genus_list[~genus_list.index.isin(important_values)]
genus_list = important_series._append(other_series)


important_values = ['coli','cerevisiae','glutamicum','sp','lipolytica','subtilis','putida','pcc']
important_series = species_list[species_list.isin(important_values)]
other_series = species_list[~species_list.isin(important_values)]
species_list = pd.concat([important_series,other_series])


abbrev = genus_list.str[0].str.upper().unique()[1:-3]
range_a = range(len(genus_list),len(genus_list)+len(abbrev))
genus_abbr_list = pd.Series(abbrev, index=range_a)
sm_genus_full_species = full_species.str[0].str.cat(true_species.str.split(' ').str[1], sep=" ").drop_duplicates()
sm_genus_full_species =  sm_genus_full_species.str.rstrip('.')




genus_list_cap = genus_list.str.capitalize()

genus_abbr_list_cap = genus_abbr_list.str.capitalize()
FULL_SPECIES_SET = set(full_species.dropna().astype(str).str.lower())
SM_FULL_SPECIES_SET = set(sm_genus_full_species.dropna().astype(str).str.lower())
SPECIES_CODE_SET = set(species_list.dropna().astype(str).str.lower())
GENERAL_SET = {"pcc", "spp", "sp"}

other_list = true_species
other = other_list.str.split(' ').str[-1].drop_duplicates().str.lower()
SPECIES_CODE_SET.update(set(other.dropna().astype(str).str.lower()))



def append_species_to_list(species, species_list):
    """
    Append a list of species names to an existing list of species names.

    Parameters:
    species (list): The list of species names to append.
    species_list (pandas.Series): The existing list of species names.

    Returns:
    pandas.Series: The updated list of species names.
    """
    for s in species:
        thermo = pd.Series({len(species_list): s})
        species_list = species_list._append(thermo)
    return species_list

species = ['thermocellum', 'thermoautotrophicum', 'heterothallicus',
           'typhimurium', 'famata', 'roseosporus', 'glycerinogenes',
           'spp', 'pcc6803', 'oleaginosus', 'novicida', 'crescentus',
           'pcc', 'RQ7', 'atcc','PCC']
species_list = append_species_to_list(species, species_list)
#fake_organism = ['C reinhardtii', 'C elegans', 'C roseus',
#                 'M separata','O furnacalis','P sibirica',
#                'E superba']

fake_organism = [ 'C elegans', 'C roseus',
                 'M separata','O furnacalis','P sibirica',
                'E superba']



import re

genus_set = set(genus_list.to_list())
def make_list(text):
    """
    Convert a string into a filtered list of unique words while maintaining the original order.

    Parameters:
    text (str): The string to convert.

    Returns:
    list: A list of unique words in their original order.
    """
    # Remove unwanted words
    text = re.sub(r'\b([Bb]io)?[Ee]ngineer\w*\b', '', text)
    text = re.sub(r'\b[Oo]verexpress\w*\b', '', text)
    text = re.sub(r'\b[Ee]nhanc\w*\b', '', text)
    text = re.sub(r'\b[Uu]tiliz\w*\b', '', text)
    text = re.sub(r'\b[Mm]etabol\w*\b', '', text)
    text = re.sub(r'\b[Ee]ffect\w*\b', '', text)
    text = re.sub(r'\b[Ii]ncreas\w*\b', '', text)
    text = re.sub(r'\b[Ii]mprov\w*\b', '', text)
    text = re.sub(r'\b([Bb]io)?[Ss]ynth\w*\b', '', text)
    text = re.sub(r'\b([Bb]io)?[Pp]roduc\w*\b', '', text)
    # text = re.sub(r'\b[Ee]scherichia\b', '', text)
    text = re.sub(r'\b[Ss]train\w*\b', '', text)
    text = re.sub(r'\b[Pp]athway\w*\b', '', text)
    text = re.sub(r'\bNADH\b', '', text)
    text = re.sub(r'\bNAD\b', '', text)
    text = re.sub(r'\b[Ee]xpression\b', '', text)
    text = re.sub(r'\b[Aa]nalysis\b', '', text)
    text = re.sub(r'\b[Cc]ell\b', '', text)
    text = re.sub(r'\b[Gg]enome\b', '', text)
    text = re.sub(r'\b[Gg]ene\b', '', text)
    text = re.sub(r'\b[Vv]ia\b', '', text)

    text = re.sub(r'\b[Uu]sing\b', '', text)


    # Split the text into words based on spaces
    text_list = text.split()

    # Filter out short words (length <= 2) and remove duplicates while maintaining order
    seen = set()
    unique_words = []
    for word in text_list:
        if (len(word) > 2 and word not in seen)\
        or (len(word)<=2 and word.isnumeric())\
        or (len(word)==1 and word in genus_abbr_list.to_list())\
        or word=='sp' or word in genus_set:
            seen.add(word)
            unique_words.append(word)

    return unique_words




def format_file(dataframe, column):
    # Remove specific special characters without altering word order
    classified_data_org = dataframe[column].str.replace('\xa0', ' ', regex=False)
    classified_data_org = classified_data_org.str.replace('\u2009', ' ', regex=False)
    classified_data_org = classified_data_org.str.replace('-', ' ', regex=False)
    
    # Remove special char
    classified_data_org = classified_data_org.apply(nospecial)
    
    # Ensure specific phrases remain intact
    classified_data_org = classified_data_org.str.replace('sp strain ', 'sp strain', regex=False)
    
    # Split strings into lists while maintaining word order
    classified_data_org = classified_data_org.apply(make_list)
    
    # Convert the list of words into a DataFrame
    classified_data_org = classified_data_org.apply(pd.Series)
    
    return classified_data_org


def find_species(sentence):
    """
    Find the indices of words in a list that are likely to be species names.

    Parameters:
    sentence (pandas.Series): A list of words.

    Returns:
    tuple: Two pandas.Index objects representing the likely species names and subspecies names, respectively.
    """
    prob_specie_bool = sentence.isin(species_list) | sentence.str.startswith('spstrain')
    specie_pos = sentence.loc[prob_specie_bool].index
    subspecie_bool = sentence.isin(['sp','spp'])
    subspecie_bool = subspecie_bool 
    subesp_pos = sentence.loc[subspecie_bool]
    if sum(subspecie_bool):
        subesp_pos = sentence.loc[subspecie_bool].index+1

        subesp_pos = subesp_pos[subesp_pos<(len(sentence)-1)]
        #if not subesp_pos.empty:
        #    valid_supesp = sentence.loc[subesp_pos].isin(species_list)
        #    subesp_pos = subesp_pos[valid_supesp]
                    
    return(specie_pos,subesp_pos)


import numpy as np

def find_genus(sentence, verify_species=True):
    """
    Find the indices of words in a list that are likely to be genus names.

    Parameters:
    sentence (pandas.Series): Columns of words.

    Returns:
    pandas.Index: The indices of the likely genus names.
    """
    sentence = sentence.str.capitalize()
    genus_mask = np.isin(sentence, genus_list)
    genus_pos = sentence.index[genus_mask]
    
    if verify_species and not genus_mask.any():
        genus_abbr_mask = np.isin(sentence, genus_abbr_list)
        genus_pos = sentence.index[genus_abbr_mask]
        
    return genus_pos


def find_full_organism_by_genus(sentence):
    """
    Find organism names in a list by searching for likely genus names and species names.

    Parameters:
    sentence (pandas.Series): A series of words.

    Returns:
    list: A list of organism names.
    """
    sentence = sentence.dropna()
    genus_pos = find_genus(sentence.str.capitalize())
    
    # Check this is not the last element
    genus_pos = genus_pos[genus_pos!=(len(sentence)-1)]
    
    prob_genus = sentence.loc[genus_pos]
    prob_specie = sentence.loc[genus_pos+1]
    
    # Join possible organisms
    prob_full_name = pd.concat([prob_genus.reset_index(drop=True), prob_specie.reset_index(drop=True)],axis=1)
    prob_full_name.columns = ['genus','species']
    prob_full_name["Full_name"] = prob_full_name["genus"].str.cat(prob_full_name["species"], sep=" ")
    
    # Check if in species data
    bool_idx = prob_full_name.Full_name.str.lower().isin(full_species.str.lower())
    bool_idx_general = prob_full_name.species.str.lower().isin(['pcc','spp','sp'])
    organisms = prob_full_name.Full_name[bool_idx|bool_idx_general].to_list()
    if organisms:
        return(organisms)
    
    else:
        bool_idx = prob_full_name.Full_name.str.lower().isin(sm_genus_full_species.str.lower())
    
        organisms = prob_full_name.Full_name[bool_idx].to_list()
        if organisms:
            return(organisms)
        else:
            if 'yeast' in sentence.to_list():
                return('yeast')
        
        
        
        
def find_organism_by_genus(sentence):
    """
    Find organism names in a list by searching for likely genus names and species names.

    Parameters:
    sentence (pandas.Series): A list of words.

    Returns:
    list: A list of organism names.
    """
    sentence = sentence.dropna()
    genus_pos = find_genus(sentence.str.capitalize())
    genus_pos = genus_pos[genus_pos!=(len(sentence)-1)]
    prob_genus = sentence.loc[genus_pos]

    prob_specie = sentence.loc[genus_pos+1]
    
    specie_pos,subesp_pos = find_species(prob_specie)
    
    valid =  genus_pos[genus_pos.isin(specie_pos-1)]
    specie = sentence.loc[valid+1].reset_index().iloc[:,1]
    #specie = specie.str.lower()
    genus = sentence.loc[valid].reset_index().iloc[:,1]
    genus = genus.str.lower().str.capitalize()
    
    organism = pd.concat([genus,specie],axis=1)
    organism = [' '.join([x, y]) for x, y in zip(genus, specie)]
    if len(organism):
        return(organism)
    
def find_organism_by_species(sentence):
    """
    Find organism names in a list by searching for likely species names and genus names.

    Parameters:
    sentence (pandas.Series): A list of words.

    Returns:
    list: A list of organism names. If no valid organism names are found, returns None.
    """
    sentence = sentence.dropna().str.lower()
    specie_pos,subespos  = find_species(sentence)
    specie_pos = specie_pos[specie_pos!=0]
    prob_specie = sentence.loc[specie_pos]
    prob_genus = sentence.loc[specie_pos-1]
    genus_pos = find_genus(prob_genus.str.capitalize())
    
    valid =  specie_pos[specie_pos.isin(genus_pos+1)]
    specie = sentence.loc[valid].reset_index().iloc[:,1]
    genus = sentence.loc[valid-1].reset_index().iloc[:,1]
    genus = genus.str.capitalize()
    #if not subespos.empty:
     #   valid_sp =  valid[valid.isin(subespos+2)]
      #  subesp = sentence.loc[valid_sp].reset_index().iloc[:,1]
      #  if not subesp.empty:
      #      organism = [' '.join([x, y,z]) for x, y,z in zip(genus, specie,subesp)]
      #  else:
      #      organism = [' '.join([x, y]) for x, y in zip(genus, specie)]
            
    #else:
     #   organism = [' '.join([x, y]) for x, y in zip(genus, specie)]
    organism = [' '.join([x, y]) for x, y in zip(genus, specie)]

    organism = list(set(organism))

    if organism and organism[0] not in fake_organism:
        return(organism)
    else:
        return(None)
    
    
def make_name_dictionary(organisms):
    dictionary = {}
    for organism in sorted(set(organisms)):
        tax = organism.split(' ')
        genre = tax[0]
        species = tax[1]

        if len(genre)>1:
            #print(genre[0]+' '+species),
            #print(organism)
            dictionary[genre[0]+' '+species] =  genre+' '+species
    return(dictionary)

def get_full_name(lista, organisms=None, name_dictionary=None):
    
    if not name_dictionary:
        name_dictionary = make_name_dictionary(organisms)
        
    new_lista = []
    if lista:
        for org in lista:
            tax = org.split(' ')
            genre = tax[0]
            if len(genre)==1 and org not in ['C roseus','M separata',
                                             'O furnacalis','P sibirica',
                                            'E superba']:
                try:
                    new_lista.append(name_dictionary[org])
                except:
                    new_lista.append(None)
            else:
                new_lista.append(org)
        full_name = list(filter(None, new_lista))
        if full_name:
            return(full_name)
        else:
            return None
    else:
        return None
    
    
    
    
    
    
# Vectorized version

def detect_organisms_vectorized(
    df: pd.DataFrame,
    *,
    FULL_SPECIES_SET=FULL_SPECIES_SET,
    SM_FULL_SPECIES_SET=SM_FULL_SPECIES_SET,
    SPECIES_CODE_SET=SPECIES_CODE_SET,
    GENERAL_SET=GENERAL_SET,
    genus_list_cap=genus_list_cap,
    genus_abbr_list_cap=genus_abbr_list_cap,
) -> pd.Series:

    tok = df.fillna("").astype(str).to_numpy(object)
    n, m = tok.shape
    flat = tok.ravel()

    # Build ONE Series view for all .str ops
    sflat = pd.Series(flat, copy=False)

    # Non-empty adjacency from original tokens (cheaper than from lowercase)
    nonempty = (tok != "")
    nonempty2 = nonempty[:, :-1] & nonempty[:, 1:]
    nonempty3 = nonempty[:, :-2] & nonempty[:, 1:-1] & nonempty[:, 2:]

    # Length + digit-start masks (aligned later)
    flat_len = sflat.str.len().to_numpy(np.int16)
    len_mat = flat_len.reshape(n, m)

    flat_digitstart = sflat.str.match(r"^\d").to_numpy(bool)
    digitstart_mat = flat_digitstart.reshape(n, m)

    # make valid_pair INCLUDE nonempty2 (so you don't repeat & nonempty2 everywhere)
    short_pair = (len_mat[:, :-1] == 1) & (len_mat[:, 1:] == 1)
    valid_pair = nonempty2 & ~short_pair

    # Ban genus starting with digit (aligned to genus position p where p+1 exists)
    genus_ok = nonempty2 & ~digitstart_mat[:, :-1]

    # Lowercase factorization
    flat_lc = sflat.str.lower().to_numpy(object)
    ids_lc, uniques_lc = pd.factorize(flat_lc, sort=False)
    ids_lc = ids_lc.reshape(n, m).astype(np.int64)
    u_lc = pd.Index(uniques_lc)

    # Capitalized factorization for genus detection
    flat_cap = sflat.str.capitalize().to_numpy(object)
    ids_cap, uniques_cap = pd.factorize(flat_cap, sort=False)
    ids_cap = ids_cap.reshape(n, m).astype(np.int64)
    u_cap = pd.Index(uniques_cap)

    # helper: avoid list() for arraylikes
    def map_to_ids(index: pd.Index, items) -> np.ndarray:
        if isinstance(items, (set, frozenset)):
            arr = np.asarray(tuple(items), dtype=object)
        else:
            arr = np.asarray(items, dtype=object)
        idx = index.get_indexer(arr)
        idx = idx[idx >= 0].astype(np.int64)
        return np.unique(idx) if idx.size else idx

    general_ids = map_to_ids(u_lc, GENERAL_SET)
    code_ids    = map_to_ids(u_lc, SPECIES_CODE_SET)

    genus_ids      = map_to_ids(u_cap, genus_list_cap)
    genus_abbr_ids = map_to_ids(u_cap, genus_abbr_list_cap)

    # Species set -> bigram codes
    V = len(u_lc) + 1

    def species_set_to_bigram_codes_lc(species_set) -> np.ndarray:
        gens, specs = [], []
        for s in species_set:
            parts = s.split()
            if len(parts) >= 2:
                gens.append(parts[0])
                specs.append(parts[1])
        if not gens:
            return np.empty(0, dtype=np.int64)
        gi = u_lc.get_indexer(np.asarray(gens, dtype=object))
        si = u_lc.get_indexer(np.asarray(specs, dtype=object))
        ok = (gi >= 0) & (si >= 0)
        codes = gi[ok].astype(np.int64) * V + si[ok].astype(np.int64)
        return np.unique(codes) if codes.size else codes

    full_bigram_codes = species_set_to_bigram_codes_lc(FULL_SPECIES_SET)
    sm_bigram_codes   = species_set_to_bigram_codes_lc(SM_FULL_SPECIES_SET)

    # Genus detection with fallback-to-abbrev rule
    cap_g = ids_cap[:, :-1]
    genus_mask = np.isin(cap_g, genus_ids) & nonempty2
    has_any_genus = genus_mask.any(axis=1)

    abbr_mask = np.isin(cap_g, genus_abbr_ids) & nonempty2
    is_genus = (genus_mask | (abbr_mask & (~has_any_genus)[:, None])) & genus_ok

    # Bigram codes on lowercase ids
    g = ids_lc[:, :-1]
    s = ids_lc[:,  1:]
    bigram_code = g * V + s

    # Main masks (valid_pair already includes nonempty2 + removes H 2 / M N)
    is_full    = is_genus & np.isin(bigram_code, full_bigram_codes) & valid_pair
    is_general = is_genus & np.isin(s, general_ids) & valid_pair
    is_sm      = is_genus & np.isin(bigram_code, sm_bigram_codes) & valid_pair

    # general + code trigram
    third = ids_lc[:, 2:]
    is_code = np.isin(third, code_ids)
    is_general_code = is_general[:, :-1] & is_code & nonempty3

    # Yeast last (needs lowercase; reuse flat_lc without reshaping a second time)
    lc_mat = flat_lc.reshape(n, m)
    is_yeast = (lc_mat == "yeast").any(axis=1)

    # Assemble
    out = [None] * n
    for i in range(n):
        pos = np.flatnonzero(is_full[i] | is_general[i])
        if pos.size:
            orgs = []
            for p in pos:
                if p < m - 2 and is_general_code[i, p]:
                    orgs.append(f"{tok[i, p]} {tok[i, p+1]} {tok[i, p+2]}")
                else:
                    orgs.append(f"{tok[i, p]} {tok[i, p+1]}")
            out[i] = orgs
            continue

        pos2 = np.flatnonzero(is_sm[i])
        if pos2.size:
            out[i] = [f"{tok[i, p]} {tok[i, p+1]}" for p in pos2]
            continue

        out[i] = "yeast" if is_yeast[i] else None

    return pd.Series(out, index=df.index)

