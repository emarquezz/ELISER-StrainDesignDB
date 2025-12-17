import pandas as pd

# ============================================================
# =====================  HELPER FUNCTIONS  ====================
# ============================================================

def get_xrefs(group):
    """Return set of uppercase XREFs."""
    return set(str(x).upper() for x in group["XREF"].dropna())

def get_all_ecs(group):
    """Return union of all EC sets in Matching_ECs column."""
    ec_sets = group["Matching_ECs"].dropna().tolist()
    return set().union(*ec_sets)

def ecs_equal_any(all_ecs, *targets):
    """Return True if all_ecs equals ANY of the given EC sets."""
    return any(all_ecs == t for t in targets)

def ecs_contain_all(all_ecs, *targets):
    """Return True if all_ecs contains ALL ECs from each target set."""
    return all(t.issubset(all_ecs) for t in targets)

def first_gene(group):
    """Lowercase gene name."""
    return str(group["Gene"].iloc[0]).lower()

def pick(group, condition, xrefs, case_name):
    """Universal picker with case label."""
    chosen = group[group["XREF"].isin(xrefs)].copy()
    chosen["Selection_Case"] = case_name
    return chosen if condition else None


# ============================================================
# =========================  RULES  ===========================
# ============================================================

# ------------------------------------------------------------
# 1. special_ldh_vs_mdh_rule
# ------------------------------------------------------------
def special_ldh_vs_mdh_rule(group):
    xrefs = get_xrefs(group)
    if not {"LDH_D", "MDH"}.issubset(xrefs):
        return None

    all_ecs = get_all_ecs(group)

    EC_1127 = {"1.1.1.27"}
    EC_1127_1419 = {"1.1.1.27", "1.4.1.9"}

    if ecs_equal_any(all_ecs, EC_1127, EC_1127_1419):
        gene = first_gene(group)
        if gene.startswith("ldh") or gene in ["cg3219", "lcte"]:
            return pick(group, True, ["LDH_D"], "SPECIAL_LDH_vs_MDH_RULE")
        else:
            print(group["Gene"].iloc[0], group["Paper_ID"].iloc[0])
            print(all_ecs)

    return None


# ------------------------------------------------------------
# 2. special_glycerol_rule
# ------------------------------------------------------------
def special_glycerol_rule(group):
    xrefs = get_xrefs(group)
    if not {"GLYCLTDX", "G3PD2"}.issubset(xrefs):
        return None

    all_ecs = get_all_ecs(group)
    gene = first_gene(group)

    EC_2 = {"1.1.1.8"}
    EC_2_23 = {"1.1.1.8", "1.2.1.12"}

    # Case 1
    if gene in ["gpd1", "gpd2"] and all_ecs == EC_2:
        return pick(group, True, ["G3PD2"], "SPECIAL_G3P_RULE")

    # Case 2
    if gene in ['gpd1', 'gpd2', 'tdh1', 'tdh2', 'gpd3', 'tdh3'] and all_ecs == EC_2_23:
        return pick(group, True, ["G3PD2", "GAPD"], "SPECIAL_G3P_RULE")

    # DEBUG
    #print("that")
    #print(group["Gene"].iloc[0], group["Paper_ID"].iloc[0])
    #print(all_ecs)
    #print(xrefs)

    return None


# ------------------------------------------------------------
# 3. special_yqef_acact_rule
# ------------------------------------------------------------
def special_yqef_acact_rule(group):
    xrefs = get_xrefs(group)
    if not {"ACACT1R", "ACACT2R"}.issubset(xrefs):
        return None

    all_ecs = get_all_ecs(group)

    EC_2 = {"2.3.1.9"}
    EC_2_23 = {"2.3.1.9", "2.3.1.16"}
    EC_23 = {"2.3.1.16"}

    if ecs_equal_any(all_ecs, EC_2, EC_2_23):
        return pick(group, True, ["ACACT1R"], "SPECIAL_ACACT1r_RULE")

    if all_ecs == EC_23:
        return pick(group, True, ["3OXCOAT"], "SPECIAL_3OXCOAT_RULE")

    return None


# ------------------------------------------------------------
# 4. special_pyk_pps_rule
# ------------------------------------------------------------
def special_pyk_pps_rule(group):
    xrefs = get_xrefs(group)
    if not {"PYK", "PPS"}.issubset(xrefs):
        return None

    if get_all_ecs(group) == {"2.7.1.40"}:
        return pick(group, True, ["PYK"], "SPECIAL_PYK_RULE")

    return None


# ------------------------------------------------------------
# 5. special_faco_rule
# ------------------------------------------------------------
def special_faco_rule(group):
    xrefs = get_xrefs(group)
    if not {"FACOAE80", "FACOAE60", "FACOAE181"}.issubset(xrefs):
        return None

    all_ecs = get_all_ecs(group)

    EC_3 = {"3.1.2.20"}
    EC_2 = {"2.3.1.84"}

    if ecs_contain_all(all_ecs, EC_3, EC_2):
        gene = first_gene(group)

        # ATF1 special case
        if gene.startswith("atf1"):
            chosen = group[group["XREF"] == "FACOAE80"].copy()
            dup = chosen.copy()
            dup["XREF"] = "OHACT1"
            result = pd.concat([chosen, dup], ignore_index=True)
            result["Selection_Case"] = "SPECIAL_FACOAE80_RULE_WITH_OHACT1"
            return result

        print(group["Gene"].iloc[0], group["Paper_ID"].iloc[0])
        print(all_ecs)

    return None


# ------------------------------------------------------------
# 6. special_ATPM_HEX2_rule
# ------------------------------------------------------------
def special_ATPM_HEX2_rule(group):
    xrefs = get_xrefs(group)
    if not {"ATPM", "HEX4"}.issubset(xrefs):
        return None

    if get_all_ecs(group) == {"2.7.1.1"}:
        return pick(group, True, ["HEX7", "HEX4", "HEX1"], "SPECIAL_ATPM_HEX2_RULE")

    return None


# ------------------------------------------------------------
# 7. special_ATPM_HEX_rule
# ------------------------------------------------------------
def special_ATPM_HEX_rule(group):
    xrefs = get_xrefs(group)
    if not {"ATPM", "HEX1"}.issubset(xrefs):
        return None

    if get_all_ecs(group) == {"2.7.1.2"}:
        return pick(group, True, ["HEX1", "HEX4"], "SPECIAL_ATPM_HEX_RULE")

    return None


# ------------------------------------------------------------
# 8. special_ptsG_rule
# ------------------------------------------------------------
def special_ptsG_rule(group):
    xrefs = get_xrefs(group)
    if not {"GLNTRS", "TREPTSPP"}.issubset(xrefs):
        return None

    all_ecs = get_all_ecs(group)
    EC_full = {"2.7.1.69", "6.1.1.18"}

    if all_ecs == EC_full and first_gene(group) == "ptsg":
        return pick(group, True, ["TREPTSPP"], "SPECIAL_G3P_RULE")

    return None


import pandas as pd

# ============================================================
# =====================  PRESENCE UTILITIES  ==================
# ============================================================

def presence_val(s):
    """Normalize Presence field into an integer 0/1/2/..."""
    try:
        if pd.isna(s):
            return 0
        if isinstance(s, bool):
            return int(s)
        return int(s)
    except Exception:
        if str(s).lower() in {"false", "nan", "none", ""}:
            return 0
        try:
            return int(float(s))
        except Exception:
            return 0

def add_presence_vals(df):
    """Utility to add normalized presence column."""
    df = df.copy()
    df["_presence_val"] = df["Presence"].apply(presence_val)
    return df


# ============================================================
# =====================  TIE-BREAKER BLOCKS  =================
# ============================================================

def break_ties_by_match(df):
    """Return df filtered to rows with highest Match_Count."""
    max_match = df["Match_Count"].max()
    return df[df["Match_Count"] == max_match].copy()

def break_ties_by_presence(df):
    """Return df filtered to rows with highest _presence_val."""
    max_p = df["_presence_val"].max()
    return df[df["_presence_val"] == max_p].copy()

def choose_if_single(df, case_name):
    """If df has one row, assign Selection_Case and return it; else None."""
    if len(df) == 1:
        out = df.copy()
        out["Selection_Case"] = case_name
        return out
    return None


# ============================================================
# ===============  NORMAL PICKING PRIOR TO SPECIALS  =========
# ============================================================

def normal_picker(group):
    """Main non-special picking logic (modularized)."""

    # ---- SPECIAL RULES THAT MUST RUN FIRST ----
    for special_rule in [
        special_glycerol_rule,
        special_ATPM_HEX2_rule,
        special_ATPM_HEX_rule,
    ]:
        out = special_rule(group)
        if out is not None:
            return out

    # ========================================================
    #               MAIN NUMERIC SELECTION LOGIC
    # ========================================================

    max_score = group["Specific_Match_Score"].max()
    scored = group[group["Specific_Match_Score"] == max_score].copy()
    scored = add_presence_vals(scored)

    # --- CASE: only one candidate ---
    single = choose_if_single(scored, "SINGLE_AFTER_SPECIFIC_SCORE")
    if single is not None:
        return single.drop(columns=["_presence_val"])

    # ========================================================
    # =============== CASE: Specific_Match_Score > 0 =========
    # ========================================================

    if max_score > 0:

        # Filter out rows not present in any model
        scored_nonfalse = scored[scored["Presence"] != False].copy()
        if not scored_nonfalse.empty:
            scored = scored_nonfalse

        # Pick highest Presence model
        top_rows = break_ties_by_presence(scored)
        single = choose_if_single(top_rows, "CASE_A: PREFER_TOP_MODEL (max_score>0)")
        if single is not None:
            return single.drop(columns=["_presence_val"])

        # Now use Match_Count tie-break
        match_tied = break_ties_by_match(top_rows)
        single = choose_if_single(match_tied, "CASE_B: SINGLE_BY_MATCHCOUNT")
        if single is not None:
            return single.drop(columns=["_presence_val"])

        # Last tie-break: Presence numeric
        presence_tied = break_ties_by_presence(match_tied)
        presence_tied["Selection_Case"] = "CASE_C: TIED_BY_MATCHCOUNT_KEEP_MODEL"
        return presence_tied.drop(columns=["_presence_val"])

    # ========================================================
    #          CASE: Specific_Match_Score == 0
    # ========================================================

    # First tie-break: Match_Count
    match_tied = break_ties_by_match(scored)
    single = choose_if_single(match_tied, "CASE_D: ZERO_SCORE_SINGLE_BY_MATCHCOUNT")
    if single is not None:
        return single.drop(columns=["_presence_val"])

    # Next: Presence level
    presence_tied = break_ties_by_presence(match_tied)

    # If multiple remain → return all from top model
    if len(presence_tied) > 1:
        presence_tied = presence_tied.copy()
        presence_tied["Selection_Case"] = "CASE_E: ZERO_SCORE_TIED_KEEP_MODEL"
        return presence_tied.drop(columns=["_presence_val"])

    # Final tie-break
    out = presence_tied.iloc[[0]].copy()
    out["Selection_Case"] = "CASE_F: ZERO_SCORE_FINAL_TIE_BREAK"
    return out.drop(columns=["_presence_val"])


# ============================================================
# ================  FINAL PICK: NORMAL + SPECIALS  ===========
# ============================================================

def pick_best_rows(group):
    """Pipeline of normal picker + late-order special rules."""
    group = normal_picker(group)

    # SECOND PASS OF SPECIAL RULES (those that require filtered groups)
    for special_rule in [
        special_ldh_vs_mdh_rule,
        special_yqef_acact_rule,
        special_faco_rule,
        special_pyk_pps_rule,
        special_ptsG_rule,
    ]:
        out = special_rule(group)
        if out is not None:
            return out

    return group



def process_best_matches(df_big_info, pick_best_rows):
    """
    Process a dataframe to select best rows per (Gene, Paper_ID), collapse ties,
    and compute alternative XREFs.

    Parameters
    ----------
    df_big_info : pandas.DataFrame
        Input dataframe containing columns like Gene, Paper_ID, Reaction_ID, XREF, etc.
    pick_best_rows : callable
        Function used to select the best rows within each (Gene, Paper_ID) group.

    Returns
    -------
    final_df : pandas.DataFrame
        Processed dataframe with chosen and alternative XREFs, and other computed fields.
    """

    # --- Apply selection per-group ---
    best_rows_expanded = (
        df_big_info.groupby(["Gene", "Paper_ID"], group_keys=False)
        .apply(pick_best_rows)
        .reset_index(drop=True)
    )

    # --- Collapse multiple tied rows into lists where applicable ---
    best_collapsed = (
        best_rows_expanded
        .groupby(["Gene", "Paper_ID"], as_index=False)
        .agg({
            "Reaction_ID": lambda x: list(x.unique()),
            "XREF": lambda x: list(x.unique()),
            "Specific_Match_Score": "first",
            "Match_Count": "first",
            "Presence": "first",
            "Corrected_Fraction_Matched": "first",
            "Reaction_Corrected_Fraction_Matched": "first",
            "Fraction_Matched": "first",
            "Reaction_Fraction_Matched": "first",
            "Selection_Case": "first"
        })
    )

    # --- Collect all XREFs for reference ---
    xref_lists = (
        df_big_info.groupby(["Gene", "Paper_ID"])["XREF"]
        .agg(list)
        .reset_index()
    )

    # --- Merge to get candidates ---
    best_with_candidates = best_collapsed.merge(
        xref_lists, on=["Gene", "Paper_ID"], suffixes=("", "_all")
    )

    # --- Compute Alternative XREFs ---
    best_with_candidates["Alternative_XREFs"] = best_with_candidates.apply(
        lambda r: [x for x in r["XREF_all"] if x not in r["XREF"]],
        axis=1
    )

    # --- Final cleanup & rename ---
    final_df = (
        best_with_candidates
        .drop(columns=["XREF_all"])
        .rename(columns={
            "XREF": "Chosen_XREF",
            "Reaction_ID": "Chosen_Reaction_ID"
        })
    )[
        [
            "Gene", "Paper_ID", "Chosen_Reaction_ID", "Chosen_XREF", "Alternative_XREFs",
            "Specific_Match_Score", "Match_Count", "Presence",
            "Corrected_Fraction_Matched", "Reaction_Corrected_Fraction_Matched",
            "Fraction_Matched", "Reaction_Fraction_Matched", "Selection_Case"
        ]
    ]

    return final_df


def add_matching_ecs_to_final(final_df, df_bigg_info):
    """
    For each (Gene, Paper_ID, Chosen_XREF) combination in final_df,
    find which Matching_ECs in df_bigg_info correspond to those XREFs.
    """

    def find_ecs(row):
        gene = row["Gene"]
        paper_id = row["Paper_ID"]
        chosen_xrefs = row["Chosen_XREF"]

        # Ensure list
        if not isinstance(chosen_xrefs, (list, tuple)):
            chosen_xrefs = [chosen_xrefs]

        # Filter the original df by Gene and Paper_ID
        subset = df_bigg_info[
            (df_bigg_info["Gene"] == gene)
            & (df_bigg_info["Paper_ID"] == paper_id)
        ]

        # Build dict: {XREF -> Matching_ECs}
        xref_to_ecs = {}
        for xref in chosen_xrefs:
            # Some XREFs may contain semicolon-separated IDs
            matching_rows = subset[subset["XREF"].str.contains(xref, na=False)]
            if not matching_rows.empty:
                ecs = sorted(
                    set(
                        ec
                        for ecs_list in matching_rows["Matching_ECs"]
                        if isinstance(ecs_list, list)
                        for ec in ecs_list
                    )
                )
                xref_to_ecs[xref] = ecs
            else:
                xref_to_ecs[xref] = []

        return xref_to_ecs

    final_df = final_df.copy()
    final_df["Chosen_XREF_to_Matching_ECs"] = final_df.apply(find_ecs, axis=1)
    return final_df

