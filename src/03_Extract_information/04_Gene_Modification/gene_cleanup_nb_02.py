"""
Text-cleaning utilities for gene–action relations extracted from scientific text.

Functions in this module:
    - clean_uppercase_pathway_genes()
    - clean_non_gene_products()
    - remove_known_metabolites()
    - clean_modifications_list()
    - extract_paper_modifications()
    - fix_negation_mismatches_in_modifications()
    - check_modification_negation()
    - get_negative_modification()
    - clean_mod_set()
"""



import re
import pandas as pd

def clean_uppercase_pathway_genes(df_or_series: pd.Series) -> pd.Series:
    """
    Cleans a pandas Series where each entry is a list of (text, relations) tuples.
    """

    def clean_entry(entry):
        cleaned = []
        for text, relations in entry:
            new_relations = []
            for rel in relations:
                gene, action = rel.split(" -> ")

                if gene.isupper():
                    # Patterns for pathway/cycle/synthesis removal
                    pattern_before = rf'[\(\[\{{]?\b{gene}\b[\)\]\}}]?\s+(?:pathway|cycle)\b(?!\s+genes)'
                    pattern_after = rf'\b(?:pathway|cycle)\s+[\(\[\{{]?\b{gene}\b[\)\]\}}]?'
                    pattern_synthesis = rf'\b{gene}\b\s+synthesis'

                    if (re.search(pattern_before, text, flags=re.IGNORECASE)
                        or re.search(pattern_after, text, flags=re.IGNORECASE)
                        or re.search(pattern_synthesis, text, flags=re.IGNORECASE)):
                        continue

                    # Pattern for 'genes' removal
                    pattern_genes = rf'\b{gene}\b\s+(?:pathway\s+genes|cycle\s+genes|genes)\b'
                    
                    if re.search(pattern_genes, text, flags=re.IGNORECASE):
                        # Check if preceded by keep words using a different approach
                        should_remove = True
                        
                        # Find all occurrences of the gene pattern
                        for match in re.finditer(pattern_genes, text, flags=re.IGNORECASE):
                            start_pos = match.start()
                            
                            # Look at what comes immediately before this match
                            if start_pos > 0:
                                # Get the text before the gene
                                before_text = text[:start_pos].rstrip()
                                
                                # Extract the last word before the gene
                                last_word_match = re.search(r'(\b\w+\b)\s*$', before_text)
                                if last_word_match:
                                    last_word = last_word_match.group(1)
                                    
                                    # Check if last word is a keep word
                                    if (last_word.lower() in ['and', 'or', 'and/or'] or 
                                        re.match(r'^[A-Z0-9-]+$', last_word)):
                                        should_remove = False
                                        print(f"Keeping {gene!r} due to preceding word '{last_word}': {text}")
                                        break
                            
                            # If at start of string or no preceding keep word, remove
                            if should_remove:
                                print(f"Removing {gene!r} from text (followed by 'genes' pattern): {text}")
                                break
                        
                        if should_remove:
                            continue

                new_relations.append(rel)
            cleaned.append((text, new_relations))
        return cleaned

    if isinstance(df_or_series, pd.Series):
        return df_or_series.apply(clean_entry)
    else:
        raise TypeError("Input must be a pandas Series (e.g., a row or column from a DataFrame).")
        
        
        

def clean_non_gene_products(df_or_series: pd.Series) -> pd.Series:
    """
    Removes uppercase 'genes' that are actually products or metabolites.
    Includes heuristics for 'availability', 'synthase (Gene)', 'production/biosynthesis', etc.
    Retains uppercase tokens if they clearly refer to enzymes or genes (expression, activity, substrate contexts).
    """

    def clean_entry(entry):
        cleaned = []
        for text, relations in entry:
            new_relations = []
            for rel in relations:
                gene, action = rel.split(" -> ")

                # Define a flexible regex for gene mentions (allowing parentheses, brackets, braces)
                gene_surrounding = rf'[\(\[\{{]?\b{re.escape(gene)}\b[\)\]\}}]?'

                if gene.isupper():
                    # --- Rule: availability/pool context (single or multiple metabolites) ---
                    if re.search(
                        rf'\b{gene}\b(?:[\s,]+(?:and|or)\s+[A-Z0-9]{{2,6}})?\s+(pool|availability|bioavailability|content|tolerance|transport|supply|formation|accumulation|excretion)\b',
                        text,
                        re.IGNORECASE
                    ):
                        print(f"❌ Removing {gene} (availability/pool context) in:\n{text}\n")
                        continue
                    # --- Rule 1: availability/pool/production → product/metabolite ---
                    if re.search(rf'{gene_surrounding}\s+((bio)?availability|pool|content|tolerance|transport|supply|formation|accumulation)', text, re.IGNORECASE):
                        print(f"❌ 2Removing {gene} (availability/pool context) in:\n{text}\n")
                        continue

                    # --- Rule: production/biosynthesis context ---
                    if re.search(
                        rf'\b{gene}\b(?:[\s,]+(?:and|or)\s+[A-Z0-9]{{2,6}})?\s+(production|biosynthesis|productivity)\b',
                        text,
                        re.IGNORECASE
                    ):
                        print(f"❌ Removing {gene} (production/biosynthesis context) in:\n{text}\n")
                        continue

                    if re.search(rf'{gene_surrounding}\s+(production|biosynthesis|productivity)', text, re.IGNORECASE):
                        # print(f"❌ Removing {gene} (production/biosynthesis context) in:\n{text}\n")
                        continue

                        
                    enzyme_terms = r'(synthase|decarboxylase|transferase|kinase|carboxykinase|dehydrogenase|carboxylase|isomerase|mutase|reductase|oxidase|hydrogenase|lyase|ligase)'

                    # --- Rule 2a: uppercase token precedes enzyme term "synthase (RealGeneName)" ---
                    if re.search(rf'{gene_surrounding}[-\s]+\w*{enzyme_terms}\s*\(\w+\)', text, re.IGNORECASE):
                        continue

                    # --- Rule 2b: uppercase abbreviation appears inside parentheses before enzyme name ---
                    # e.g., "phosphoenolpyruvate (PEP) synthase"
                    if re.search(rf'\w+\s*\({gene_surrounding}\)[-\s]+\w*{enzyme_terms}', text, re.IGNORECASE):
                        continue

                    # --- Rule 2c: uppercase token directly attached to enzyme name (e.g., "PEP-carboxykinase") ---
                    if re.search(rf'\b{gene_surrounding}[-\s]*{enzyme_terms}', text, re.IGNORECASE):
                        continue

                    # --- Rule 3: short all-caps metabolite near increase/reduce/enhance --- 
                    
                    #increase|reduce|enhance|
                    if len(gene) <= 5 and re.search(rf'(converting)\s+{gene_surrounding}', text, re.IGNORECASE):
                        
                        # ✅ Exception 1: gene-related contexts (expression, activity, gene, promoter, transcript)
                        if re.search(rf'{gene_surrounding}\s+(expression|activity|gene|promoter|transcript)', text, re.IGNORECASE):
                            pass  # keep — gene expression context
                        
                        # ✅ Exception 2: enzyme contexts (substrate, enzyme, catalyze, modeling, etc.)
                        elif re.search(rf'{gene_surrounding}\s+(substrate|enzyme|catalyze|catalyses|active site|kinetic|mutant|modeling|structure)', text, re.IGNORECASE):
                            pass  # keep — enzyme context
                        
                        # Otherwise, it's probably a metabolite
                        else:
                            print(f"❌ Removing {gene} (likely metabolite, not gene) in:\n{text}\n")
                            continue

                new_relations.append(rel)
            cleaned.append((text, new_relations))
        return cleaned

    if isinstance(df_or_series, pd.Series):
        return df_or_series.apply(clean_entry)
    else:
        raise TypeError("Input must be a pandas Series (e.g., a column from a DataFrame).")
        
        
        
        
        
def remove_known_metabolites(df_or_series: pd.Series) -> pd.Series:
    """
    Removes relations involving known metabolites (e.g., PEP, GAP, E4P)
    when they appear in typical metabolite-related contexts like
    'pool of', 'formation of', 'accumulation of', etc.
    """

    known_metabolites = {
        #"PEP": ["phosphoenolpyruvate"],
        "GAP": ["glyceraldehyde-3-phosphate"],
        "E4P": ["erythrose-4-phosphate"],
        "F6P": ["fructose-6-phosphate"],
        "PGA": ["3-phosphoglycerate"],
        "NADH": ["nicotinamide adenine dinucleotide"],
        "NADPH": ["nicotinamide adenine dinucleotide phosphate"],
        "ATP": ["adenosine triphosphate"],
        "ADP": ["adenosine diphosphate"],
        "AMP": ["adenosine monophosphate","adenosine 5'-monophosphate"],
        "FAD": ["flavin adenine dinucleotide"],
        #"ALA": ["aminolevulinic acid"]
        #"IPP": ["isopentenyl diphosphate"],
        #"DMAPP": ["dimethylallyl diphosphate"]
    }
    def clean_entry(entry):
        cleaned = []
        for text, relations in entry:
            new_relations = []
            for rel in relations:
                gene, action = rel.split(" -> ")
                
                if gene in ["PEP","IPP","DMAPP","DCW","ALA",'fed','ACP','PCA']:
                    print(f"❌ Removing {gene} (always a metabolite) in:\n{text}\n")
                    continue
                    
                gene_surrounding = rf'[\(\[\{{]?\b{gene}\b[\)\]\}}]?'

                if gene in known_metabolites:
                    fullnames = known_metabolites[gene]

                    # --- 1️⃣ Full name nearby (e.g., phosphoenolpyruvate (PEP)) ---
                    if any(re.search(rf'\b{name}\b', text, re.IGNORECASE) for name in fullnames):
                        print(f"❌ Removing {gene} (known metabolite full name nearby) in:\n{text}\n")
                        continue

                    # --- 2️⃣ Metabolite context phrases ---
                    if re.search(rf'(pool|availability|accumulation|formation|amount|supply|content|level|available|compound|precursor|metabol)\s+(of\s+)?{gene_surrounding}', text, re.IGNORECASE):
                        print(f"❌ Removing {gene} (metabolite context) in:\n{text}\n")
                        continue

                    # --- 3️⃣ Upstream biosynthetic or catalytic context ---
                    #if re.search(rf'({gene_surrounding}.*(pathway|synthesis|biosynthesis|conversion|flux|metabol|precursor|intermediate))', text, re.IGNORECASE):
                        #print(f"❌ Removing {gene} (biosynthetic context) in:\n{text}\n")
                        #continue

                new_relations.append(rel)
            cleaned.append((text, new_relations))
        return cleaned

    if isinstance(df_or_series, pd.Series):
        return df_or_series.apply(clean_entry)
    else:
        raise TypeError("Input must be a pandas Series (e.g., a column from a DataFrame).")

        
        
def clean_modifications_list(modifications_list):
    """
    Clean modifications list by removing entries with no modifications.
    If the entire list becomes empty, return None.
    """
    if not modifications_list:
        return None
    
    # Remove entries with empty modification lists
    cleaned_list = [(text, gene_mods) for text, gene_mods in modifications_list if gene_mods]
    
    # If everything was removed, return None
    if not cleaned_list:
        return None
    
    return cleaned_list


def extract_paper_modifications(df,column):
    """
    Extracts all paper modifications from a DataFrame.
    
    Each row in the DataFrame is expected to have:
      - Column 0: An iterable (like a list) of sentences,
        where each sentence is a tuple/list and the second element (index 1)
        contains an iterable of modifications.

    Parameters:
        df (pd.DataFrame): The DataFrame to process.

    Returns:
        dict: A dictionary mapping row indices to a set of modifications.
    """
    all_paper_modifications = {}

    for n, paper in df.iterrows():
        modification = set()
        if paper[column]:  # Ensure column 0 is not empty/None
            for sentence in paper[column]:
                modification.update(sentence[1])
            all_paper_modifications[n] = modification

    return all_paper_modifications






def fix_negation_mismatches_in_modifications(modifications_list):
    """
    Fix negation mismatches in the modifications list structure.
    Checks if the specific modification word has negation between it and the closest was/were.
    Only applies to modifications that contain was/were.
    """
    cleaned_modifications = []
    
    for text, gene_mods in modifications_list:
        filtered_gene_mods = []
        
        for gene_mod in gene_mods:
            gene, modification = gene_mod.split(' -> ')
            
            # Check if THIS specific modification is negated in the text
            is_negated = check_modification_negation(text, modification)
            
            if is_negated:
                negation_type = is_negated
                print(f"🔄 Removing positive modification for negated gene: {gene}")
                print(f"   Text: '{text}'")
                print(f"   Positive: '{modification}'")
                print(f"   Negation: '{negation_type}'")
                
                # Replace with negative modification - pass original modification to keep the word
                negative_mod = get_negative_modification(negation_type, gene, modification)
                filtered_gene_mods.append(negative_mod)
                print(f"➕ Replaced with: {negative_mod}")
            else:
                filtered_gene_mods.append(gene_mod)
        
        if filtered_gene_mods:
            cleaned_modifications.append((text, filtered_gene_mods))
    
    return cleaned_modifications

def check_modification_negation(text, modification):
    """
    Check if the specific modification word has negation between it and the closest was/were.
    Only applies to modifications that contain was/were.
    """
    # Only check for was/were negation patterns if the modification contains was/were
    if not re.search(r'\b(was|were)\s+\w+', modification, re.IGNORECASE):
        return None
    
    # Get the exact word after was/were from modification (e.g., "overexpressed" from "was overexpressed")
    words = modification.split()
    if len(words) < 2:
        return None
    
    # Find the word after was/were
    modification_word = None
    for i, word in enumerate(words):
        if word.lower() in ['was', 'were'] and i + 1 < len(words):
            modification_word = words[i + 1]
            break
    
    if not modification_word:
        return None
    
    # Find all occurrences of this exact modification word in the text
    for match in re.finditer(rf'\b{modification_word}\b', text, re.IGNORECASE):
        keyword_start = match.start()
        
        # Look backwards to find the closest "was" or "were" before this keyword
        text_before_keyword = text[:keyword_start]
        
        # Find the last "was" or "were" before our keyword
        was_were_match = None
        for was_match in re.finditer(r'\b(was|were)\b', text_before_keyword, re.IGNORECASE):
            was_were_match = was_match
        
        if not was_were_match:
            continue
            
        # Check the text between was/were and our modification word for negation
        text_between = text[was_were_match.end():keyword_start].strip()
        
        # Check if there's negation between the was/were and our keyword
        negation_patterns = [
            r'\bnot\b',
            r'\bnever\b', 
            r'\bno\b',
            r'\bfailed\s+to\b',
        ]
        
        for pattern in negation_patterns:
            if re.search(pattern, text_between, re.IGNORECASE):
                if 'not' in pattern:
                    return 'was_not'
                elif 'never' in pattern:
                    return 'was_never'
                elif 'no' in pattern:
                    return 'no'
                elif 'failed' in pattern:
                    return 'failed_to'
    
    return None

def get_negative_modification(negation_type, gene, original_modification):
    """
    Convert negation type to appropriate negative modification string.
    Keep the original modification word (induced, expressed, enhanced, etc.)
    """
    # Get the original modification word (e.g., "induced" from "was induced")
    original_word = original_modification.split()[-1]
    
    negation_map = {
        'was_not': f'{gene} -> was not {original_word}',
        'was_never': f'{gene} -> was never {original_word}', 
        'no': f'{gene} -> no {original_word}',
        'failed_to': f'{gene} -> failed to {original_word}'
    }
    return negation_map.get(negation_type, f'{gene} -> was not {original_word}')




def clean_mod_set(mod_set):
    """Clean a set of modification strings by removing duplicated gene names."""
    cleaned_set = set()
    changed = False
    changes_made = []  # Track what changes were made
    
    for mod in mod_set:
        original_mod = mod
        
        # Pattern 1: "gene -> modification gene" (gene at end)
        match1 = re.match(r"(\b[a-zA-Z0-9_]+)\s*->\s*([a-zA-Z0-9_\s]+?)\s*\1\b", mod)
        # Pattern 2: "gene -> gene modification" (gene at beginning)  
        match2 = re.match(r"(\b[a-zA-Z0-9_]+)\s*->\s*\1\s+([a-zA-Z0-9_\s]+)\b", mod)
        
        if match1:
            # Pattern: "gene -> modification gene"
            new_mod = f"{match1.group(1)} -> {match1.group(2).strip()}"
            cleaned_set.add(new_mod)
            changes_made.append(f"  '{original_mod}' -> '{new_mod}'")
            changed = True
        elif match2:
            # Pattern: "gene -> gene modification"  
            new_mod = f"{match2.group(1)} -> {match2.group(2).strip()}"
            cleaned_set.add(new_mod)
            changes_made.append(f"  '{original_mod}' -> '{new_mod}'")
            changed = True
        else:
            cleaned_set.add(mod)
            
    return cleaned_set, changed, changes_made