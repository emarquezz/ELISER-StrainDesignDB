import calendar
import re
import pandas as pd
# ── 1. Compile all regexes ───────────────────────────────────────────────

# Month Day [optional: , Year]
months = list(calendar.month_name)[1:]
month_pattern = '|'.join(months)
date_re = re.compile(
    rf'\b(?:{month_pattern})\s+\d{{1,2}}(?:\s*,?\s*\d{{4}})?\b',
    flags=re.IGNORECASE
)

# Just digits
plain_number_re = re.compile(r'^>?<?~?(units-)?\d+$')

# [digits] including optional spaces or parentheses
#bracketed_number_re = re.compile(r'^\[\s*\d+\s*\]$|\(?\d+\)?$')
bracketed_number_re = re.compile(r'^\[\s*\d+\s*\]$|\(?\d+(-units)?-?1?%?\)?$')

# vol. <number> (with or without space)
vol_re = re.compile(r'^vol\.?\s*\d+$', flags=re.IGNORECASE)
#tral
#chiral
#tural
#Maybe not ant? 
ending_pattern = rf'(?:tion|ment|ness|ary|ence|ent|bly|ade|wide|ant|metric|ries|ties|ble|ity|ous|lar|cial|rial|tral|chiral|tural|ical|ple|ory|tor)(?:al)?s?'
# Words ending in "tion", "ment", "ness", or "ary" (plus optional "al" or plural "s")
suffix_word_re = re.compile(r'\b\w+{ending_pattern}\b$', flags=re.IGNORECASE)

# Single word check for 'tion', 'ment', 'ness', 'ary'
single_suffix_word_re = re.compile(r'^\w+{ending_pattern}$', flags=re.IGNORECASE)

# ── 2. Enhanced cleaning and logging ──────────────────────────────────────

#removed_log = []

def clean_product_list(idx, lst,removed_log):
    if not isinstance(lst, list):
        return lst

    removed_items = []
    cleaned = []

    for item in lst:
        if not isinstance(item, str):
            cleaned.append(item)
            continue

        stripped = item.strip()

        # Rule: Remove dates
        if date_re.fullmatch(stripped):
            removed_items.append((item, "date-like"))
            continue

        # Rule: Remove plain numbers
        if plain_number_re.fullmatch(stripped):
            removed_items.append((item, "plain-number"))
            continue

        # Rule: Remove bracketed numbers
        if bracketed_number_re.fullmatch(stripped):
            removed_items.append((item, "bracketed-number"))
            continue

        # Rule: Remove vol. numbers
        if vol_re.fullmatch(stripped):
            removed_items.append((item, "vol-number"))
            continue

        words = stripped.split()

        # Rule: If the entire product is just a suffix word (discard)
        if len(words) == 1 and single_suffix_word_re.match(words[0]):
            removed_items.append((item, "single suffix word"))
            continue

        # Rule: Remove suffix word at the start
        if len(words) >= 1 and re.search(rf'{ending_pattern}$', words[0], flags=re.IGNORECASE):
            removed_items.append((words[0], "removed leading suffix word"))
            words = words[1:]

        # Rule: Remove suffix word at the end
        if len(words) >= 1 and re.search(rf'{ending_pattern}$', words[-1], flags=re.IGNORECASE):
            removed_items.append((words[-1], "removed trailing suffix word"))
            words = words[:-1]

        if not words:
            # If all words were trimmed, drop the item
            removed_items.append((item, "all words removed by suffix rules"))
            continue

        cleaned.append(' '.join(words))

    if removed_items:
        removed_log.append({
            'row_index': idx,
            'original_list': lst,
            'removed_items': removed_items
        })

    return cleaned if cleaned else pd.NA


def split_acid_related_products(lst):
    if not isinstance(lst, list):
        return lst

    new_list = []

    # Rule 1: multiple 'Xic acid' compounds
    acid_acid_pattern = re.compile(r'(\b\w+?ic\b)\s+(acid)', flags=re.IGNORECASE)

    # Modifier pattern (e.g., N-acyl, ethyl, butyl, etc.)
    modifier_pattern = re.compile(r'(?:\bN-?acyl\b|\b\w+yl\b)\s*$', flags=re.IGNORECASE)

    # Rule 2: 'acid' followed by word ending in ine or one
    acid_ine_one_re = re.compile(r'\bacid\s+(\w+(?:ine|one))\b', flags=re.IGNORECASE)

    # Rule 2.1: 'acid' followed by optional parentheses + ine/one
    acid_complex_ine_one_re = re.compile(
        r'\bacid(?:\s+\([^\)]+\))?\s+([^\s]+(?:ine|one))\b',
        flags=re.IGNORECASE
    )

    # Exception: fatty acid followed by 'yl', 'ester(s)', short abbreviation, or parentheses
    fatty_acid_exception_re = re.compile(
        r'\bfatty acid\s+(?:\w+yl\b|\w+ester(?:s)?\b|\(?[a-z]{1,4}\)?\b)',
        re.IGNORECASE
    )

    # Rule 3: 'acid' followed by compound, but exclude (sialate)-style parentheses and fatty acid exceptions
    acid_followed_by_chemical_re = re.compile(
        r'\bacid(?!\s+\([\w\-]+\))\s+(?=\(?[\w\d\-]+(?:ine|one|acid|lactone|ol|al|ate|amide)?\b)',
        re.IGNORECASE
    )
    
    # Rule 4 — two words ending in 'ate'

    ate_pattern = re.compile(r'\b\w+ate\b', flags=re.IGNORECASE)

    for item in lst:
        if not isinstance(item, str):
            new_list.append(item)
            continue

        # Rule 1 — multiple "Xic acid" compounds
        acid_matches = list(acid_acid_pattern.finditer(item))
        if len(acid_matches) > 1:
            split_points = []
            for m in acid_matches[1:]:  # Skip first match, focus on where we split
                cut_index = m.start()

                # Check if there's a modifier just before this acid
                pre_text = item[:cut_index].rstrip()
                modifier_match = modifier_pattern.search(pre_text)
                if modifier_match:
                    cut_index = modifier_match.start()  # Cut before the modifier

                split_points.append(cut_index)

            # Add end of string to simplify slicing
            split_points.append(len(item))

            # Build the splits
            split_acids = []
            prev = 0
            for split_point in split_points:
                compound = item[prev:split_point].strip()
                if compound:
                    split_acids.append(compound)
                prev = split_point

            print(f"📎 SPLIT (Rule 1 - multiple acids): '{item}' → {split_acids}")
            new_list.extend(split_acids)
            continue

        # Rule 2 — 'acid' + ine/one
        m2 = acid_ine_one_re.search(item)
        if m2:
            split_idx = m2.start(1)
            part1 = item[:split_idx].strip()
            part2 = item[split_idx:].strip()
            split_parts = [part1, part2]
            print(f"📎 SPLIT (Rule 2 - acid + ine/one): '{item}' → {split_parts}")
            new_list.extend(split_parts)
            continue

        # Rule 2.1 — 'acid' + (optional parentheses) + ine/one
        m2_1 = acid_complex_ine_one_re.search(item)
        if m2_1:
            split_idx = m2_1.start(1)
            part1 = item[:split_idx].strip()
            part2 = item[split_idx:].strip()
            split_parts = [part1, part2]
            print(f"📎 SPLIT (Rule 2.1 - acid + complex ine/one): '{item}' → {split_parts}")
            new_list.extend(split_parts)
            continue

        # Skip Rule 3 if it's a "fatty acid ester/yl" case
        if fatty_acid_exception_re.search(item):
            new_list.append(item)
            continue

        # Rule 3 — 'acid' + compound
        m3 = acid_followed_by_chemical_re.search(item)
        if m3:
            acid_end = m3.start() + len("acid")
            part1 = item[:acid_end].strip()
            part2 = item[acid_end:].strip()
            split_parts = [part1, part2]
            print(f"📎 SPLIT (Rule 3 - acid + compound): '{item}' → {split_parts}")
            new_list.extend(split_parts)
            continue
            
        # Rule 4: two 'ate' words
        ate_matches = list(ate_pattern.finditer(item))
        if len(ate_matches) >= 2:
            first_ate = ate_matches[0]
            second_ate = ate_matches[1]
            if ate_matches[0].string[ate_matches[0].end()] == '-' or ate_matches[0].string[ate_matches[0].end()]=='(':
                continue
                
            before_first = item[:first_ate.start()].strip().split()
            after_first = item[first_ate.end():second_ate.start()].strip().split()
            second_word = item[second_ate.start():second_ate.end()]
            
            # Case A: after first -ate, we see '...ase'
            if after_first and re.search(r'\w+ase$', after_first[-1], re.IGNORECASE):
                split_idx = item.index(after_first[-1]) + len(after_first[-1])
                part1, part2 = item[:split_idx].strip(), item[split_idx:].strip()
                split_parts = [part1, part2]
                print(f"📎 SPLIT (Rule 4 - ate + ase): '{item}' → {split_parts}")
                new_list.extend(split_parts)
                continue

            # Case B: before first -ate we see 'isoamyl'
            if before_first and  before_first[-1].endswith("yl"):
                split_idx = first_ate.end()
                part1, part2 = item[:split_idx].strip(), item[split_idx:].strip()
                split_parts = [part1, part2]
                print(f"📎 SPLIT (Rule 4 - isoamyl + ate): '{item}' → {split_parts}")
                new_list.extend(split_parts)
                continue

            # Case C: second -ate is phosphate or carboxylate → don't split
            if second_word.lower() in {"phosphate", "carboxylate"}:
                new_list.append(item)
                continue

            # Default case: split between first and second -ate
            split_idx = first_ate.end()
            part1, part2 = item[:split_idx].strip(), item[split_idx:].strip()
            split_parts = [part1, part2]
            print(f"📎 SPLIT (Rule 4 - default ate split): '{item}' → {split_parts}")
            new_list.extend(split_parts)
            continue
        # No rule matched
        new_list.append(item)

    return new_list if new_list else pd.NA

def split_antibiotic_related_products(lst):
    if not isinstance(lst, list):
        return lst

    new_list = []

    # Rule: antibiotic + word ending in 'in' (with optional parentheses)
    antibiotic_pattern = re.compile(
        r'\b(antibiotic|anti-?parasitic)s?(?:\s+\([^)]+\))?\s+(\w+in)\b',
        re.IGNORECASE
    )

    # Words/phrases to ignore if found as context
    ignore_context = {
        "broad-spectrum", "anticancer", "peptide",
        "cyclic lipopeptide", "polyketide", "macrocyclic peptide",
        "polyene macrolide", "beta-lactam", "macrolide", "nucleoside",
        "antifungal polyketide"
    }

    # Pattern to detect "X antibiotic(s)" without a real name
    generic_antibiotic_pattern = re.compile(
        r'^(?:' + "|".join(map(re.escape, ignore_context)) + r')?\s*antibiotics?\s*$', 
        re.IGNORECASE
    )

    for item in lst:
        if not isinstance(item, str):
            new_list.append(item)
            continue

        # Rule 0: skip "antibiotic resistance"
        if re.search(r'\bantibiotic\s+resistance\b', item, re.IGNORECASE):
            print(f"📎 SKIP (Rule 0 - antibiotic resistance): '{item}' → []")
            continue

        matches = list(antibiotic_pattern.finditer(item))

        if matches:
            prev = 0
            for m in matches:
                start, end = m.span()

                # context before antibiotic
                if start > prev:
                    context = item[prev:start].strip()
                    if context and context.lower() not in ignore_context:
                        print(f"📎 KEEP (Rule 1 - context): '{context}' in '{item}'")
                        new_list.append(context)
                    elif context.lower() in ignore_context:
                        print(f"📎 IGNORE (Rule 1 - context): '{context}' in '{item}'")

                # antibiotic name
                antibiotic_name = m.group(2)
                print(f"📎 EXTRACT (Rule 2 - antibiotic): '{item}' → '{antibiotic_name}'")
                new_list.append(antibiotic_name)

                prev = end

            # trailing context after last antibiotic
            if prev < len(item):
                rest = item[prev:].strip()
                if rest:
                    if rest.lower() in ignore_context:
                        print(f"📎 IGNORE (Rule 3 - trailing context): '{rest}' in '{item}'")
                    else:
                        print(f"📎 KEEP (Rule 3 - trailing context): '{rest}' in '{item}'")
                        new_list.append(rest)

        else:
            # Rule 5: collapse "peptide antibiotic(s)" etc. → "antibiotic"
            if generic_antibiotic_pattern.match(item.strip()):
                print(f"📎 COLLAPSE (Rule 5 - generic antibiotic): '{item}' → 'antibiotic'")
                new_list.append("antibiotic")
            else:
                # No antibiotic pattern matched → keep item as-is
                new_list.append(item)

    return new_list if new_list else pd.NA



def split_if_multiple_top_terms(lst, top_terms):
    # If input is already a list, process each item
    if isinstance(lst, list):
        new_list = []
        flagged_cases = []
        for item in lst:
            cleaned, flagged = split_if_multiple_top_terms(item, top_terms)
            if isinstance(cleaned, list):
                new_list.extend(cleaned)
            else:
                new_list.append(cleaned)
            flagged_cases.extend(flagged)
        return new_list, flagged_cases
    
    # Original single item processing logic
    new_list = []
    flagged_cases = []
    
    # Define replacement patterns in order from longest to shortest
    replacement_patterns = [
        ('fatty acid ethyl ester', 'fatty-acid-ethyl-ester'),
        ('fatty acid isopropyl ester', 'fatty-acid-isopropyl-ester'),
        ('fatty acid', 'fatty-acid'),
        ('amino acid', 'amino-acid')
    ]
    
    # Process top_terms with replacements
    processed_top_terms = []
    for term in top_terms:
        processed_term = term
        for old, new in replacement_patterns:
            processed_term = processed_term.replace(old, new)
        processed_top_terms.append(processed_term)
    top_terms = processed_top_terms
    
    item = lst  # Now lst is the single item
    
    if not isinstance(item, str):
        new_list.append(item)
        return new_list, flagged_cases
        
    # Process the item with the same replacements
    processed_item = item
    for old, new in replacement_patterns:
        processed_item = processed_item.replace(old, new)
    
    words = processed_item.split()
    
    if len(words) == 1 or 'precursor' in item:
        # Single word → keep as-is
        new_list.append(item)
        return new_list, flagged_cases

    # Collect words that contain any top term
    found_words = []
    for w in words:
        if any(re.search(rf"{re.escape(term)}s?\b", w) for term in top_terms):
            found_words.append(w)

    if len(found_words) > 1:
        # ✅ Multiple → split
        print(f"📎 SPLIT: '{item}' → {found_words}")
        new_list.extend(found_words)
    elif len(found_words) == 1:
        # Check if any other word ends with 'in'
        other_words_end_with_in = any(
            w not in found_words and w.endswith('in') 
            for w in words
        )
        
        other_words_end_with_nen = any(
            w not in found_words and w.endswith('in') 
            for w in words
        )
        
        if other_words_end_with_in:
            # ✅ Split because other word ends with 'in'
            print(f"📎 SPLIT (ends with 'in'): '{item}' → {words}")
            new_list.extend(words)
        else:
            # ⚠️ Only one → flag
            print(f"⚠️ FLAG: '{item}' (only found {found_words[0]})")
            new_list.append(item)
            flagged_cases.append(item)
    else:
        # No match → keep as-is
        new_list.append(item)

    return new_list, flagged_cases
