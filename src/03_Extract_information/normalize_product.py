import sys
sys.path.append('../..')

from file_management import get_files_dir,check_save_file
_, INPUT_DIR, OUTPUT_DIR = get_files_dir()

import pandas as pd
import unicodedata
import re

GENERAL_STRIP = r' .‘]”[‐,:)-’;(\\'


# Create a dictionary of Greek letters and their corresponding English names
greek_letters = {
    'α': 'alpha', 'β': 'beta', 'γ': 'gamma', 'δ': 'delta', 'ε': 'epsilon', 
    'ζ': 'zeta', 'η': 'eta', 'θ': 'theta', 'ι': 'iota', 'κ': 'kappa', 
    'λ': 'lambda', 'μ': 'mu', 'ν': 'nu', 'ξ': 'xi', 'ο': 'omicron', 
    'π': 'pi', 'ρ': 'rho', 'σ': 'sigma', 'τ': 'tau', 'υ': 'upsilon', 
    'φ': 'phi', 'χ': 'chi', 'ψ': 'psi', 'ω': 'omega',
    'Α': 'Alpha', 'Β': 'Beta', 'Γ': 'Gamma', 'Δ': 'Delta', 'Ε': 'Epsilon', 
    'Ζ': 'Zeta', 'Η': 'Eta', 'Θ': 'Theta', 'Ι': 'Iota', 'Κ': 'Kappa', 
    'Λ': 'Lambda', 'Μ': 'Mu', 'Ν': 'Nu', 'Ξ': 'Xi', 'Ο': 'Omicron', 
    'Π': 'Pi', 'Ρ': 'Rho', 'Σ': 'Sigma', 'Τ': 'Tau', 'Υ': 'Upsilon', 
    'Φ': 'Phi', 'Χ': 'Chi', 'Ψ': 'Psi', 'Ω': 'Omega','ß':'beta',
}

# Define a function to replace Greek letters in a string with their names using regular expressions
def replace_greek_letters_with_regex(string):
    pattern = "|".join(greek_letters.keys())
    regex = re.compile(pattern)
    new_text = regex.sub(lambda m: greek_letters[m.group()].lower(), string)
    return (new_text)

# Example usage
#text = "The equation Δ = α + Ω is used tO represent the change in a variable."
#text_with_names = replace_greek_letters_with_regex(text)
#print(text_with_names)
all_greek_letters = ''.join(greek_letters.keys())
inverted_all_greek = {fr'(^{v})': k for k, v in greek_letters.items()}

# Create a dictionary of Greek letters and their corresponding English names
greek_lower = {
    'α': 'alpha', 'β': 'beta', 'γ': 'gamma', 'δ': 'delta', 'ε': 'epsilon', 
    'ζ': 'zeta', 'η': 'eta', 'θ': 'theta', 'ι': 'iota', 'κ': 'kappa', 
    'λ': 'lambda', 'μ': 'mu', 'ν': 'nu', 'ξ': 'xi', 'ο': 'omicron', 
    'π': 'pi', 'ρ': 'rho', 'σ': 'sigma', 'τ': 'tau', 'υ': 'upsilon', 
    'φ': 'phi', 'χ': 'chi', 'ψ': 'psi', 'ω': 'omega'}

lower_greek_letters = ''.join(greek_lower.keys())
inverted_greek_lower = {v: k for k, v in greek_lower.items()}

# Define a function to replace Greek letters in a string with their names using regular expressions
def replace_greek_lower(string):
    pattern = "|".join(greek_lower.keys())
    regex = re.compile(pattern)
    new_text = regex.sub(lambda m: greek_lower[m.group()], string)
    return (new_text)


# Remove l- or d- (like d-lactate) or alpha-molecule
isomer = fr'^\d*[npdolʟʀr\+{all_greek_letters}]?-'
greek_start = fr'^[{all_greek_letters}]'

isomer_racemate = r'^rac-'
isomer_transemate = r'^(trans[-,])'
isomer_cisemate = r'^(cis[-,])+'


regular_expression = r'[()\[\],\.\{\} ]'
regular_expression_full = r'[()\+\-\[\],\.\{\} ]'


remove_end_weird = r'\(-\)$'
remove_end_weird2 = r'-$'

remove_start_weird = r'^\([pRrSsNno]\)[-,]'
remove_start_weird2 = r'^[pLlDdNno]?[-,]'
remove_start_weird3 = r'^\(?\d?[RrSsdD],\d?[RrSsdD]\)?[-,]'

remove_start_weird4 = r'^ʟʀ'
remove_start_weird5 = r'^,-'
remove_start_weird6 = r'^[sSrR][sSrR]-'
remove_start_weird7 = r'^-'
remove_start_weird8 = r'^\(?\d+,\d+\)?[-,]'

remove_middle_weird = r'--'
remove_middle_weird2 = r'-,-'

remove_start_weird_digits = r'^[sSrRdD](\d+)'

def format_series_products(product_series):
    # Normalize subindex
    product_series = product_series.str.replace(remove_end_weird, '', regex = True)
    product_series = product_series.str.replace(remove_end_weird2, '', regex = True)

    product_series = product_series.str.replace(remove_start_weird, '', regex = True)
    product_series = product_series.str.replace(remove_start_weird2, '', regex = True)
    product_series = product_series.str.replace(remove_start_weird3, '', regex = True)
    product_series = product_series.str.replace(remove_start_weird4, '', regex = True)
    product_series = product_series.str.replace(remove_start_weird5, '', regex = True)
    product_series = product_series.str.replace(remove_start_weird6, '', regex = True)
    product_series = product_series.str.replace(remove_start_weird7, '', regex = True)
    product_series = product_series.str.replace(remove_start_weird8, '', regex = True)

    product_series = product_series.str.replace(remove_middle_weird, '', regex = True)
    product_series = product_series.str.replace(remove_middle_weird2, '', regex = True)
    
    product_series = product_series.str.replace(remove_start_weird_digits, r'\1', regex=True)

    # turn alpha into α
    product_series = product_series.str.lower().replace(inverted_all_greek,regex=True)
    product_series = product_series.str.lower().str.replace(r'^r+',r'r', regex=True)

    product_series = product_series.str.replace(isomer_racemate,'', regex=True)
    product_series = product_series.str.replace(isomer_transemate,'', regex=True)
    product_series = product_series.str.replace(isomer_cisemate,'', regex=True)

    product_series = product_series.str.replace(greek_start,'', regex=True)

    product_series = product_series.str.replace(isomer,'', regex=True)
    product_series = product_series.str.replace(isomer,'', regex=True)
    

    product_series = product_series.str.lower().str.replace(regular_expression,'', regex=True)

    product_series = product_series.str.replace(regular_expression_full,'', regex=True)
    
    product_series = product_series.apply(lambda x: unicodedata.normalize('NFKC', x) if x is not None else x)

    return(product_series)



def standardize_product_names(products):
    """
    Standardize product names by replacing various formats and abbreviations
    with consistent naming conventions.
    
    Parameters:
    products (Series): Pandas Series containing product names to be standardized
    
    Returns:
    Series: Series with standardized product names
    """
    products = products.str.replace('(-hydroxybutyrate)','(hydroxybutyrate)', regex=False)
    products = products.str.replace('((hydroxybutyrate)','(hydroxybutyrate)', regex=False)
    products = products.str.replace(r'poly(hydroxyalkanoate)s?',r'polyhydroxyalkanoate', regex=True)
    products = products.str.replace(r'poly(hydroxyalkanoicacid)s?',r'polyhydroxyalkanoate', regex=True)

    products = products.str.replace(r'\bpolyhydroxyalkanoates?\b','pha', regex=True)
    products = products.str.replace(r'\bpolyhydroxyalkanoicacids?\b','pha', regex=True)

    products = products.str.replace(r'\bpolyhydroxyalkanoates?phas?\b','pha', regex=True)
    products = products.str.replace(r'\bpolyhydroxyalkanoicacids?phas?\b','pha', regex=True)

    
    #products = products.str.replace(r'\bpha\b','PHA', regex=True)
    products = products.str.replace(r'\bfattyacid(s)?fa\b','fattyacid', regex=True)
    
    products = products.str.replace('polyhydroxybutyrates?phb','polyhydroxybutyrate', regex=False)
    products = products.str.replace('poly(hydroxybutyrate)s?','polyhydroxybutyrate', regex=False)
    products = products.str.replace(r'\bpolyhydroxybutyrates?\b','phb', regex=True)
    #products = products.str.replace(r'\bphb\b','PHB', regex=True)
    
    products = products.str.replace('polyhydroxybutyratecohydroxyvalerate','phbv', regex=False)
    products = products.str.replace('copolymerphbcohv','phbv', regex=False)
    #products = products.str.replace(r'\bphbv\b','PHBV', regex=True)
    
    products = products.str.replace('polyhydroxybutyratecohydroxyhexanoate','phbhhx', regex=False)
    products = products.str.replace('phbcohhx','phbhhx', regex=False)
    products = products.str.replace('phbhhxphbhhx','phbhhx', regex=False)
    #products = products.str.replace(r'\bphbhhx\b','PHBHHx', regex=True)
    
    products = products.str.replace('gammaaminobutyrate','gamma-aminobutyric acid', regex=False)
    products = products.str.replace('rsbutanediol','butanediol', regex=False)
    products = products.str.replace('rrbutanediol','butanediol', regex=False)
    products = products.str.replace('ssbutanediol','butanediol', regex=False)
    products = products.str.replace('spropanediol','propanediol', regex=False)
    products = products.str.replace(r'\brbutanediol\b','butanediol', regex=True)
    products = products.str.replace('butane-diol','butanediol', regex=False)
    products = products.str.replace(r'\bbutanediolbdo\b','butanediol', regex=True)
    products = products.str.replace(r'\bbdo\b','butanediol', regex=True)
    
    products = products.str.replace(r'\bpropanediolpdo\b','propanediol', regex=True)
    products = products.str.replace(r'\bpdo\b','propanediol', regex=True)
    
    products = products.str.replace(r'\bdopa\b','dihydroxyphenylalanine', regex=True)
    products = products.str.replace('biofuels','biofuel', regex=False)
    products = products.str.replace('ssastaxanthin','astaxanthin', regex=False)
    
    products = products.str.replace('isobutanol','butanol', regex=False)
    products = products.str.replace('sbutanol','butanol', regex=False)
    products = products.str.replace('gbioethanol','ethanol', regex=False)
    products = products.str.replace('bioethanol','ethanol', regex=False)
    
    products = products.str.replace('acetyldneuraminate','acetylneuraminate', regex=False)
    products = products.str.replace('acetylneuraminates','acetylneuraminate', regex=False)
    
    products = products.str.replace('-diene','diene', regex=False)
    products = products.str.replace('dlactate','lactate', regex=False)
    products = products.str.replace(r'\bGA\b','gibberellin', regex=True)
    
    return products

# Usage example:
# df['product_column'] = standardize_product_names(df['product_column'])

def get_value(value, chebi_df):
    new_value = chebi_df.index[chebi_df['Synonym']==value]
    if not new_value.empty:
        return new_value[0]
    
    elif value.strip(GENERAL_STRIP).endswith('s') and value != 'biomass':
        new_value = chebi_df.index[chebi_df['Synonym']==value[:-1]]
        if not new_value.empty:

            return new_value[0]
        else:
            return value
    else:
        print(value)
        return value
        #return f'r_{value}'
        
        
def compare_words(word1, word2, max_diff=3):
    if abs(len(word1) - len(word2)) > max_diff:
        return False
    elif len(word1) == len(word2):
        diff_count = 0
        diff_letter = []
        for a, b in zip(word1, word2):
            if a != b:
                diff_count += 1
                diff_letter.append(f'{a} != {b}')
                if diff_count > max_diff:
                    return False
        if diff_count > 0:
            None
            #print(', '.join(diff_letter))
        return True
    else:
        if len(word1) < len(word2):
            word1, word2 = word2, word1
        i = 0
        j = 0
        diff_count = 0
        while i < len(word1) and j < len(word2):
            if word1[i] != word2[j]:
                diff_count += 1
                if diff_count > max_diff:
                    return False
                #print(f'{word1[i]} inserted')
                i += 1
            else:
                i += 1
                j += 1
        while i < len(word1):
            diff_count += 1
            if diff_count > max_diff:
                return False
            #print(f'{word1[i]} inserted')
            i += 1
        return True


        
        