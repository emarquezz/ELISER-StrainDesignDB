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


# ============================================================
#   1. CLEAN PATHWAY/CYCLE "GENE" MISLABELS
# ============================================================

def clean_uppercase_pathway_genes(series: pd.Series) -> pd.Series:
    """
    Clean a pandas Series where each element is a list of (text, relations) tuples.

    This function processes each entry and removes specific gene–action relations
    when the gene name is uppercase and appears in textual patterns associated with
    pathways, cycles, synthesis, or "genes" phrases. The removal rules rely entirely
    on regex pattern detection within the text string.

    Parameters
    ----------
    series : pd.Series
        A pandas Series where each value is structured as:
        [
            (text: str, relations: List[str])
        ]
        Each relation must be formatted as "GENE -> action".

    Returns
    -------
    pd.Series
        A pandas Series of the same structure, with filtered relations for each entry.

    Raises
    ------
    TypeError
        If the input is not a pandas Series.
    """

    def clean_entry(entry):
        cleaned_entries = []

        for text, relations in entry:
            filtered_relations = []

            for relation in relations:
                gene, action = relation.split(" -> ")

                if gene.isupper():
                    # Patterns for pathway/cycle/synthesis removal
                    pattern_before = rf'[\(\[\{{]?\b{gene}\b[\)\]\}}]?\s+(?:pathway|cycle)\b(?!\s+genes)'
                    pattern_after = rf'\b(?:pathway|cycle)\s+[\(\[\{{]?\b{gene}\b[\)\]\}}]?'
                    pattern_synthesis = rf'\b{gene}\b\s+synthesis'

                    if (
                        re.search(pattern_before, text, flags=re.IGNORECASE)
                        or re.search(pattern_after, text, flags=re.IGNORECASE)
                        or re.search(pattern_synthesis, text, flags=re.IGNORECASE)
                    ):
                        continue

                    # Pattern for "genes" removal
                    pattern_genes = rf'\b{gene}\b\s+(?:pathway\s+genes|cycle\s+genes|genes)\b'

                    if re.search(pattern_genes, text, flags=re.IGNORECASE):
                        should_remove = True

                        # Check preceding context for keep-words
                        for match in re.finditer(pattern_genes, text, flags=re.IGNORECASE):
                            start_pos = match.start()

                            if start_pos > 0:
                                before_text = text[:start_pos].rstrip()
                                last_word_match = re.search(r'(\b\w+\b)\s*$', before_text)

                                if last_word_match:
                                    last_word = last_word_match.group(1)

                                    if (
                                        last_word.lower() in ["and", "or", "and/or"]
                                        or re.match(r'^[A-Z0-9-]+$', last_word)
                                    ):
                                        should_remove = False
                                        print(
                                            f"Keeping {gene!r} due to preceding word "
                                            f"'{last_word}': {text}"
                                        )
                                        break

                            if should_remove:
                                print(
                                    f"Removing {gene!r} from text "
                                    f"(followed by 'genes' pattern): {text}"
                                )
                                break

                        if should_remove:
                            continue

                filtered_relations.append(relation)

            cleaned_entries.append((text, filtered_relations))

        return cleaned_entries

    if isinstance(series, pd.Series):
        return series.apply(clean_entry)
    else:
        raise TypeError("Input must be a pandas Series (e.g., a row or column from a DataFrame).")
        


# ============================================================
#   2. REMOVE NON-GENE PRODUCTS (metabolites misread as genes)
# ============================================================
def clean_non_gene_products(series: pd.Series) -> pd.Series:
    """
    Remove uppercase tokens that look like genes but are actually metabolites
    or other non-gene biological products.

    This function applies heuristic pattern matching to identify cases where
    an uppercase token (GENE) refers to a metabolite or product rather than
    a gene or enzyme. It removes relations from (text, relations) tuples
    only when the surrounding text indicates non-gene contexts such as
    availability, pool size, production, biosynthesis, formation, transport,
    etc.

    Gene-related contexts (expression, activity, promoter, transcript) and
    enzyme contexts (substrate, catalysis, enzyme names) are preserved.

    Parameters
    ----------
    series : pd.Series
        A pandas Series where each element contains:
        [
            (text: str, relations: List[str])
        ]
        Each relation must be of the form "GENE -> action".

    Returns
    -------
    pd.Series
        A pandas Series of the same structure with filtered relations.

    Raises
    ------
    TypeError
        If the input is not a pandas Series.
    """

    def clean_entry(entry):
        cleaned_entries = []

        for text, relations in entry:
            filtered_relations = []

            for relation in relations:
                gene, action = relation.split(" -> ")

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
                    if re.search(
                        rf'{gene_surrounding}\s+((bio)?availability|pool|content|tolerance|transport|supply|formation|accumulation)',
                        text,
                        re.IGNORECASE
                    ):
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

                    if re.search(
                        rf'{gene_surrounding}\s+(production|biosynthesis|productivity)',
                        text,
                        re.IGNORECASE
                    ):
                        continue

                    enzyme_terms = (
                        r'(synthase|decarboxylase|transferase|kinase|carboxykinase|'
                        r'dehydrogenase|carboxylase|isomerase|mutase|reductase|oxidase|'
                        r'hydrogenase|lyase|ligase)'
                    )

                    # --- Rule 2a: uppercase token precedes enzyme term "synthase (RealGeneName)" ---
                    if re.search(
                        rf'{gene_surrounding}[-\s]+\w*{enzyme_terms}\s*\(\w+\)',
                        text,
                        re.IGNORECASE
                    ):
                        continue

                    # --- Rule 2b: uppercase abbreviation inside parentheses before enzyme name ---
                    # e.g., "phosphoenolpyruvate (PEP) synthase"
                    if re.search(
                        rf'\w+\s*\({gene_surrounding}\)[-\s]+\w*{enzyme_terms}',
                        text,
                        re.IGNORECASE
                    ):
                        continue

                    # --- Rule 2c: uppercase token directly attached to enzyme name ---
                    if re.search(
                        rf'\b{gene_surrounding}[-\s]*{enzyme_terms}',
                        text,
                        re.IGNORECASE
                    ):
                        continue

                    # --- Rule 3: short all-caps metabolite near increase/reduce/enhance ---
                    if len(gene) <= 5 and re.search(
                        rf'(converting)\s+{gene_surrounding}',
                        text,
                        re.IGNORECASE
                    ):

                        # ✅ Exception 1: gene-related context
                        if re.search(
                            rf'{gene_surrounding}\s+(expression|activity|gene|promoter|transcript)',
                            text,
                            re.IGNORECASE
                        ):
                            pass

                        # ✅ Exception 2: enzyme context
                        elif re.search(
                            rf'{gene_surrounding}\s+(substrate|enzyme|catalyze|catalyses|active site|kinetic|mutant|modeling|structure)',
                            text,
                            re.IGNORECASE
                        ):
                            pass

                        # Otherwise remove — likely metabolite
                        else:
                            print(f"❌ Removing {gene} (likely metabolite, not gene) in:\n{text}\n")
                            continue

                filtered_relations.append(relation)

            cleaned_entries.append((text, filtered_relations))

        return cleaned_entries

    if isinstance(series, pd.Series):
        return series.apply(clean_entry)
    else:
        raise TypeError("Input must be a pandas Series (e.g., a column from a DataFrame).")
        


# ============================================================
#   3. REMOVE KNOWN METABOLITES
# ============================================================
def remove_known_metabolites(series: pd.Series) -> pd.Series:
    """
    Remove relations involving known metabolites (e.g., GAP, E4P, F6P, NADH)
    when the uppercase token appears in metabolite-related textual contexts.

    This function checks whether the uppercase token represents a known metabolite
    (from the internal metabolite dictionary) and removes it when the surrounding
    text suggests metabolite meaning rather than a gene. Examples of such contexts
    include:
    - "pool of"
    - "formation of"
    - "accumulation of"
    - "content of"
    - "supply of"
    - "precursor"
    - Full metabolite names occurring nearby (e.g., "glyceraldehyde-3-phosphate (GAP)")

    Parameters
    ----------
    series : pd.Series
        A pandas Series where each element is a list of `(text, relations)` tuples.
        Each relation must follow the format "GENE -> action".

    Returns
    -------
    pd.Series
        A pandas Series with metabolite-related relations removed.

    Raises
    ------
    TypeError
        If the input is not a pandas Series.
    """

    known_metabolites = {
        # "PEP": ["phosphoenolpyruvate"],
        "GAP": ["glyceraldehyde-3-phosphate"],
        "E4P": ["erythrose-4-phosphate"],
        "F6P": ["fructose-6-phosphate"],
        "PGA": ["3-phosphoglycerate"],
        "NADH": ["nicotinamide adenine dinucleotide"],
        "NADPH": ["nicotinamide adenine dinucleotide phosphate"],
        "ATP": ["adenosine triphosphate"],
        "ADP": ["adenosine diphosphate"],
        "AMP": ["adenosine monophosphate", "adenosine 5'-monophosphate"],
        "FAD": ["flavin adenine dinucleotide"],
        # "ALA": ["aminolevulinic acid"]
        # "IPP": ["isopentenyl diphosphate"],
        # "DMAPP": ["dimethylallyl diphosphate"]
    }

    def clean_entry(entry):
        cleaned_entries = []

        for text, relations in entry:
            filtered_relations = []

            for relation in relations:
                gene, action = relation.split(" -> ")

                if gene in ["PEP", "IPP", "DMAPP", "DCW", "ALA", 'fed', 'ACP', 'PCA']:
                    print(f"❌ Removing {gene} (always a metabolite) in:\n{text}\n")
                    continue

                gene_surrounding = rf'[\(\[\{{]?\b{gene}\b[\)\]\}}]?'

                if gene in known_metabolites:
                    fullnames = known_metabolites[gene]

                    # --- 1️⃣ Full name nearby (e.g., phosphoenolpyruvate (PEP)) ---
                    if any(
                        re.search(rf'\b{name}\b', text, re.IGNORECASE)
                        for name in fullnames
                    ):
                        print(f"❌ Removing {gene} (known metabolite full name nearby) in:\n{text}\n")
                        continue

                    # --- 2️⃣ Metabolite context phrases ---
                    if re.search(
                        rf'(pool|availability|accumulation|formation|amount|supply|content|level|available|compound|precursor|metabol)\s+(of\s+)?{gene_surrounding}',
                        text,
                        re.IGNORECASE
                    ):
                        print(f"❌ Removing {gene} (metabolite context) in:\n{text}\n")
                        continue

                    # --- 3️⃣ Upstream biosynthetic or catalytic context ---
                    # if re.search(
                    #     rf'({gene_surrounding}.*(pathway|synthesis|biosynthesis|conversion|flux|metabol|precursor|intermediate))',
                    #     text,
                    #     re.IGNORECASE
                    # ):
                    #     print(f"❌ Removing {gene} (biosynthetic context) in:\n{text}\n")
                    #     continue

                filtered_relations.append(relation)

            cleaned_entries.append((text, filtered_relations))

        return cleaned_entries

    if isinstance(series, pd.Series):
        return series.apply(clean_entry)
    else:
        raise TypeError("Input must be a pandas Series (e.g., a column from a DataFrame).")


# ============================================================
#   4. CLEAN EMPTY MODIFICATION LISTS
# ============================================================

def clean_modifications_list(modifications_list):
    """
    Clean a list of `(text, gene_modifications)` tuples by removing entries
    where the modification list is empty. If all entries are removed,
    return None.

    Parameters
    ----------
    modifications_list : list
        A list in the form:
        [
            (text: str, gene_modifications: list)
        ]

    Returns
    -------
    list or None
        The cleaned list if entries remain, otherwise None.
    """
    if not modifications_list:
        return None

    # Remove entries with empty modification lists
    cleaned_list = [
        (text, gene_mods)
        for text, gene_mods in modifications_list
        if gene_mods
    ]

    # If everything was removed, return None
    if not cleaned_list:
        return None

    return cleaned_list


# ============================================================
#   5. EXTRACT MODIFICATIONS PER PAPER
# ============================================================

def extract_paper_modifications(df, column):
    """
    Extract all gene modification labels from a DataFrame column.

    Each row in the DataFrame is expected to contain, in the specified column,
    an iterable (e.g., list) of sentences. Each sentence must be a tuple/list
    where:
        - sentence[0] = text
        - sentence[1] = iterable of modifications

    This function gathers all modifications found across those sentences.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame to process.
    column : str or int
        Name or integer index of the column containing the sentences.

    Returns
    -------
    dict
        A dictionary mapping:
            row_index  →  set of modifications
    """
    all_paper_modifications = {}

    for idx, paper in df.iterrows():
        modifications = set()

        if paper[column]:  # Ensure the cell is not empty or None
            for sentence in paper[column]:
                modifications.update(sentence[1])

            all_paper_modifications[idx] = modifications

    return all_paper_modifications


# ============================================================
#   6. FIX NEGATION MISMATCHES ("was not", "never", etc.)
# ============================================================

def fix_negation_mismatches_in_modifications(modifications_list):
    """
    Correct mismatches where a modification appears as a positive action
    even though the surrounding text indicates negation.

    For each modification entry (formatted as "GENE -> modification"),
    this function checks whether the specific modification term is negated
    in the associated text using `check_modification_negation()`.

    If the modification is negated:
        - The positive modification is removed.
        - A negative modification string is generated using
          `get_negative_modification()`, preserving the original
          modification keyword.
        - That negative modification replaces the original.

    Only modifications whose textual context includes "was" or "were"
    are evaluated for negation by the helper functions.

    Parameters
    ----------
    modifications_list : list
        List of (text, gene_modifications) tuples, where each element
        looks like:
            (text: str, gene_modifications: list[str])
        and each gene_modification is:
            "GENE -> modification"

    Returns
    -------
    list
        Cleaned list with corrected modification negations.
    """

    cleaned_modifications = []

    for text, gene_mods in modifications_list:
        filtered_gene_mods = []

        for gene_mod in gene_mods:
            gene, modification = gene_mod.split(" -> ")

            # Check if THIS specific modification is negated in the text
            is_negated = check_modification_negation(text, modification)

            if is_negated:
                negation_type = is_negated
                print(f"🔄 Removing positive modification for negated gene: {gene}")
                print(f"   Text: '{text}'")
                print(f"   Positive: '{modification}'")
                print(f"   Negation: '{negation_type}'")

                # Replace with negative modification - preserve original modification keyword
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
    Determine whether a specific modification (e.g., 'was overexpressed')
    is negated in the surrounding text.

    This function only applies to modifications that already contain
    the keywords "was" or "were". It checks whether there is a negation
    (e.g., 'not', 'never', 'no', 'failed to') between the closest
    preceding "was/were" and the modification word itself.

    Parameters
    ----------
    text : str
        Full sentence or text block in which the modification appears.
    modification : str
        Modification string, typically formatted like:
            "was upregulated"
            "were overexpressed"

    Returns
    -------
    str or None
        A negation label such as:
            'was_not', 'was_never', 'no', 'failed_to'
        or None if no negation is detected.
    """

    # Only check for was/were negation patterns if the modification contains was/were
    if not re.search(r'\b(was|were)\s+\w+', modification, re.IGNORECASE):
        return None

    # Get the exact word after was/were from the modification string
    words = modification.split()
    if len(words) < 2:
        return None

    # Identify the modification word following "was/were"
    modification_word = None
    for i, word in enumerate(words):
        if word.lower() in ["was", "were"] and i + 1 < len(words):
            modification_word = words[i + 1]
            break

    if not modification_word:
        return None

    # Find all occurrences of this modification keyword in the text
    for match in re.finditer(rf'\b{modification_word}\b', text, re.IGNORECASE):
        keyword_start = match.start()

        # Look backwards to find the closest "was" or "were"
        text_before_keyword = text[:keyword_start]

        was_were_match = None
        for ww_match in re.finditer(r'\b(was|were)\b', text_before_keyword, re.IGNORECASE):
            was_were_match = ww_match

        if not was_were_match:
            continue

        # Text between the closest "was/were" and the modification keyword
        text_between = text[was_were_match.end():keyword_start].strip()

        # Check for negation patterns
        negation_patterns = [
            r'\bnot\b',
            r'\bnever\b',
            r'\bno\b',
            r'\bfailed\s+to\b',
        ]

        for pattern in negation_patterns:
            if re.search(pattern, text_between, re.IGNORECASE):
                if "not" in pattern:
                    return "was_not"
                elif "never" in pattern:
                    return "was_never"
                elif "no" in pattern:
                    return "no"
                elif "failed" in pattern:
                    return "failed_to"

    return None


def get_negative_modification(negation_type, gene, original_modification):
    """
    Convert a negation type into the correct negative modification string.

    Parameters
    ----------
    negation_type : str
        Detected negation category (e.g., 'was_not', 'no', 'failed_to').
    gene : str
        Gene name.
    original_modification : str
        Original modification phrase (e.g., "was induced").

    Notes
    -----
    The original modification keyword (e.g., "induced", "expressed", "enhanced")
    is preserved.

    Returns
    -------
    str
        A formatted negative modification, e.g.:
        "GENE -> was not induced"
    """

    # Extract the modification keyword (last token)
    original_word = original_modification.split()[-1]

    negation_map = {
        "was_not":   f"{gene} -> was not {original_word}",
        "was_never": f"{gene} -> was never {original_word}",
        "no":        f"{gene} -> no {original_word}",
        "failed_to": f"{gene} -> failed to {original_word}",
    }

    return negation_map.get(negation_type, f"{gene} -> was not {original_word}")




# ============================================================
#   7. REMOVE DUPLICATED GENE NAMES IN MOD SET
# ============================================================

def clean_mod_set(mod_set):
    """
    Clean a set of modification strings by removing duplicated gene names.

    This function catches patterns such as:
        "GENE -> modification GENE"
        "GENE -> GENE modification"
    and rewrites them to:
        "GENE -> modification"

    Returns
    -------
    cleaned_set : set
        The cleaned modification strings.
    changed : bool
        True if at least one replacement occurred.
    changes_made : list of str
        Human-readable list of transformations.
    """

    cleaned_set = set()
    changed = False
    changes_made = []

    for mod in mod_set:
        original_mod = mod

        # Pattern 1: "gene -> modification gene"
        match1 = re.match(r"(\b[a-zA-Z0-9_]+)\s*->\s*([a-zA-Z0-9_\s]+?)\s*\1\b", mod)

        # Pattern 2: "gene -> gene modification"
        match2 = re.match(r"(\b[a-zA-Z0-9_]+)\s*->\s*\1\s+([a-zA-Z0-9_\s]+)\b", mod)

        if match1:
            new_mod = f"{match1.group(1)} -> {match1.group(2).strip()}"
            cleaned_set.add(new_mod)
            changes_made.append(f"  '{original_mod}' -> '{new_mod}'")
            changed = True

        elif match2:
            new_mod = f"{match2.group(1)} -> {match2.group(2).strip()}"
            cleaned_set.add(new_mod)
            changes_made.append(f"  '{original_mod}' -> '{new_mod}'")
            changed = True

        else:
            cleaned_set.add(mod)

    return cleaned_set, changed, changes_made