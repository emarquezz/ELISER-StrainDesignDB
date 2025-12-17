import pandas as pd

CURATED_MODIFICATIONS = ['express', 'delet', 'overexpress', 'increas', 'knock', 'disrupt',
       'introduc', 'engineer', 'insert', 'mutat', 'enhanc', 'regulat',
       'inactivat', 'upregulat', 'downregulat', 'induc', 'mutant', 'remov',
       'repress', 'lack', 'mutants', 'introduct', 'overexpr', 'coexpress',
       'increas express', 'block', 'induc express', 'enhanc express',
       'regulat express', 'modulat', 'repress express', 'mutagenes',
       'inducibl', 'not increas', 'not express', 'attenuat', 'blocks',
       'inducibl express', 'downregulat express', 'modulat express',
       'not induc', 'inducibl overexpress', 'decreas express',
       'upregulat express', 'inhibit express', 'not enhanc', 'lacks',
       'not delet', 'induct express', 'not overexpress', 'not disrupt',
       'reintroduc', 'not upregulat', 'not overexpr', 'not repress',
       'not regulat', 'cooverexpress', 'introduc express', 'coregulat',
       'des express']



def classify_modification(row):
    # Handle both dictionary-style and attribute-style access
    if hasattr(row, 'KO_modifications'):
        action_str = row.KO_modifications
    else:
        action_str = row['KO_modifications']
    
    action = action_str.split('->')[-1].strip().lower()
    original_action = action
    
    # Define base positive and negative actions (complete words)
    positive_base = {'express', 'overexpress', 'increas', 'upregulat', 'enhanc', 
                    'insert', 'introduc', 'induc', 'coexpress', 'upregulate'}
    
    negative_base = {'delet', 'disrupt', 'knock', 'downregulat', 'repress', 
                    'remov', 'inactivat', 'block', 'decreas', 'attenuat', 'lack', 'inhibit', 'downregulate'}
    
    # Truly ambiguous terms (standalone terms that could go either way)
    ambiguous_base = {'mutat', 'mutant', 'mutants', 'mutagenes', 'regulat', 'modulat', 'regulate', 'modulate',  'engineer'}
    
    # Check for negation patterns first
    negation_indicators = {'not ', 'lack', 'no '}
    
    # If action contains negation + positive term, it's negative
    for negator in negation_indicators:
        if negator in action:
            for positive_term in positive_base:
                if positive_term in action.replace(negator, ''):
                    print(f"'{original_action}' -> Negative (negation of positive term: '{positive_term}')")
                    return 'Negative'
            for negative_term in negative_base:
                if negative_term in action.replace(negator, ''):
                    print(f"'{original_action}' -> Positive (negation of negative term: '{negative_term}')")
                    return 'Positive'
    
    # Check for specific patterns with "not" prefix
    if action.startswith('not '):
        base_action = action[4:]  # Remove "not "
        if any(term in base_action for term in ['increas', 'express', 'overexpress', 'enhanc', 'upregulat', 'induc']):
            print(f"'{original_action}' -> Negative (negation of positive action)")
            return 'Negative'
        elif any(term in base_action for term in ['delet', 'repress', 'downregulat', 'decreas']):
            print(f"'{original_action}' -> Positive (negation of negative action)")
            return 'Positive'
    
    # Check for ambiguous terms - if starts with ambiguous term, return Other regardless
    words = action.split()
    
    # If the entire action is exactly an ambiguous term, return Other
    if len(words) == 1 and action in ambiguous_base:
        print(f"'{original_action}' -> Other (standalone ambiguous term)")
        return 'Other'
    
    # If the action starts with an ambiguous term, return Other (these are too ambiguous to classify)
    if len(words) > 0 and words[0] in ambiguous_base:
        print(f"'{original_action}' -> Other (starts with ambiguous term)")
        return 'Other'
    
    # Check for compound terms - prioritize negative terms when both are present
    has_negative = any(term in action for term in negative_base)
    has_positive = any(term in action for term in positive_base)
    
    # If both negative and positive terms exist, negative takes priority
    if has_negative and has_positive:
        # But check if it's a negation case first
        if not action.startswith('not ') and 'not ' not in action:
            print(f"'{original_action}' -> Negative (negative term dominates: '{action}')")
            return 'Negative'
    
    # Direct positive actions (only if no negative terms)
    if has_positive and not has_negative:
        # But exclude negated versions
        if not action.startswith('not ') and 'not ' not in action:
            print(f"'{original_action}' -> Positive (direct positive action)")
            return 'Positive'
    
    # Direct negative actions (only if no positive terms or positive terms are subordinate)
    if has_negative and not has_positive:
        # But exclude negated versions
        if not action.startswith('not ') and 'not ' not in action:
            print(f"'{original_action}' -> Negative (direct negative action)")
            return 'Negative'
    
    print(f"'{original_action}' -> Other (no clear classification)")
    return 'Other'



def classify_mod_dict(ec_mod_norm_dict):
    """
    Classify modifications in the nested dictionary format produced after normalization:
    {
        gene: {
            'EC_numbers': [...],
            'Normalized_Modifications': [...]
        }
    }

    Returns a new dictionary:
    {
        gene: {
            'EC_numbers': [...],
            'Classified_Modifications': [
                {'mod': 'express', 'class': 'Positive'},
                {'mod': 'delet', 'class': 'Negative'}
            ]
        }
    }
    """
    if not isinstance(ec_mod_norm_dict, dict):
        return None

    classified_dict = {}

    for gene, data in ec_mod_norm_dict.items():
        ecs = data.get('EC_numbers', [])
        mods = data.get('Normalized_Modifications', [])

        classified_mods = []
        #print(mods)
        #print(gene)
        for mod in mods:
            try:
                # only classify if it's in the "important modifications" list
                if mod in CURATED_MODIFICATIONS:
                    # emulate the same logic as before
                    row = {'KO_modifications': f"{gene} -> {mod}"}
                    category = classify_modification(row)
                    classified_mods.append({'mod': mod, 'class': category})
                else:
                    # ignore unimportant ones
                    continue
            except Exception as e:
                classified_mods.append({'mod': mod, 'class': 'Error'})

        classified_dict[gene] = {
            'EC_numbers': ecs,
            'Classified_Modifications': classified_mods
        }

    return classified_dict


def extract_relevant_dict(classified_dict):
    """
    Extract relevant genes that have EC numbers.
    Keeps dictionary format:
    {
        gene: {
            'EC_numbers': [...],
            'Classified_Modifications': [...]
        }
    }
    """
    if not isinstance(classified_dict, dict):
        return None

    new_dict = {}

    for gene, data in classified_dict.items():
        ecs = data.get('EC_numbers', [])
        classified_mods = data.get('Classified_Modifications', [])

        # Only keep if the gene has at least one EC number
        if ecs:
            new_dict[gene] = {
                'EC_numbers': ecs,
                'Classified_Modifications': classified_mods
            }

    return new_dict if new_dict else None


import re

def extract_complete_EC_numbers_dict(classified_dict):
    """
    Keep only entries where EC numbers are complete (e.g., '1.1.1.1').
    Remove genes whose EC list becomes empty after filtering.
    """
    if not isinstance(classified_dict, dict):
        return None

    ec_pattern = re.compile(r'^\d+\.\d+\.\d+\.\d+$')
    filtered_dict = {}

    for gene, data in classified_dict.items():
        ecs = data.get('EC_numbers', [])
        classified_mods = data.get('Classified_Modifications', [])

        # Keep only complete EC numbers
        valid_ecs = [ec for ec in ecs if ec_pattern.match(str(ec))]

        # Only keep genes that still have valid EC numbers
        if valid_ecs:
            filtered_dict[gene] = {
                'EC_numbers': valid_ecs,
                'Classified_Modifications': classified_mods
            }

    # Return None if nothing valid remains
    return filtered_dict if filtered_dict else None



def explode_ec_modifications_with_paper_id(df, col_name="EC_Modifications_Classified_min_relv"):
    """
    Explodes the nested EC_Modifications_Classified_min_relv dict column
    into rows of Paper_ID, Gene, EC_number, Modification, and Classification.
    Keeps track of original row index in 'Paper_ID'.
    """
    records = []

    for idx, item in df[col_name].items():
        if not isinstance(item, dict):
            continue  # skip None or invalid entries

        for gene, data in item.items():
            ecs = data.get("EC_numbers", [])
            classified_mods = data.get("Classified_Modifications", [])
            
            for mod_entry in classified_mods:
                    mod = mod_entry.get("mod")
                    cls = mod_entry.get("class")
                    records.append({
                        "Paper_ID": idx,
                        "Gene": gene,
                        "EC_number": ecs,
                        "Modification": mod,
                        "Classification": cls
                    })

    exploded_df = pd.DataFrame(records)
    return exploded_df



def apply_classification(df):
    classifications = []
    for _, row in df.iterrows():
        mod = row["Modification"]
        
        # only classify if modification is in your important list
        if mod in CURATED_MODIFICATIONS:
            row_input = {'KO_modifications': f"{row['Gene']} -> {mod}"}
            classification = classify_modification(row_input)
        else:
            classification = "Other"
            
        classifications.append(classification)
    
    return classifications
