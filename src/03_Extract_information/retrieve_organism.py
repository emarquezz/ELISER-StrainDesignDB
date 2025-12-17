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


taxonomy = INPUT_DIR+'/Taxonomy/Filtered_taxonomy.csv'
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

fake_organism = ['C reinhardtii', 'C elegans', 'C roseus',
                 'M separata','O furnacalis','P sibirica',
                'E superba']





import re

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
        if (len(word) > 2 and word not in seen) or (len(word)==1 and word in genus_abbr_list.to_list()):
            seen.add(word)
            unique_words.append(word)

    return unique_words



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
