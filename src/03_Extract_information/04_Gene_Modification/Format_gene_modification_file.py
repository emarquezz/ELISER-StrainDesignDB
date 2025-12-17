import sys
import re
import logging

import spacy

from spacy.tokens import Span
from spacy.language import Language
# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

# Add paths and import external functions
sys.path.append('../')
sys.path.append('../..')
from retrieve_product import big_file_split, process_raw_data, re_pat, nlp, stop_words_and
#split_sentence


re_pat = re.compile(re_pat.pattern.replace('express|',''))
re_pat = re.compile(re_pat.pattern.replace('activ|',''))
re_pat = re.compile(re_pat.pattern.replace('effect|',''))
re_pat = re.compile(re_pat.pattern.replace('increas|',''))
re_pat = re.compile(re_pat.pattern.replace('accumulat|',''))
re_pat = re.compile(re_pat.pattern.replace('engineer|','frequen|'))
re_pat = re.compile(re_pat.pattern.replace('enhanc|','additionally|'))


# Define regex patterns and replacements
GENE_PATTERN = re.compile(r'genes? of (?:[^()]+) \((.+?)\)(?: and (?:[^()]+) \((.+?)\))?')
OTHER_GENE_PATTERN = re.compile(r'the (?:[^()]+)ase genes? \((.+?)\)(?: and (?:[^()]+)ase genes? \((.+?)\))?')
OTHER_GENE_PATTERN_2 = re.compile(r'the (?:[^()]+)ase \((.+?)\) genes?(?: and (?:[^()]+)ase genes? \((.+?)\))?')
#sub_sentence = re.sub(OTHER_GENE_PATTERN_2, simplify_genes_other, ' the aspartate ammonia-lyase (ansB) gene increased the the aspartate ammonialyase (ansB) gene increased')
#sub_sentence
#sub_sentence = re.sub(OTHER_GENE_PATTERN, simplify_genes_other, 'the asdjaklsdase genes (asdA) increases')
#sub_sentence


# Define the words to replace (e.g., "native", "repressor")
WORDS_TO_REPLACE = ["native", "repressor", 'key']

# Define the pattern for replacing "the <word_to_replace> <gene-related terms>"
WORDS_REPLACE_PATTERN = re.compile(
    rf"the ({'|'.join(WORDS_TO_REPLACE)}) (\w{{1,6}}\w,?\s?){{1,4}}(?: or )?(\w{{1,6}}\w)? genes?"
)
# Define the pattern for replacing "the <optional word> <word>ase gene(s)"
ASE_GENE_PATTERN = re.compile(r"the\s?([a-z]+)?\s(\w+)ase\sgenes?")
REMOVE_FROM_GENE = '.,*-;() '

#REMOVE_FROM_GENE = ',.* ()'
COMMON_WORDS = {"and", "or", "if", "the", "a", "an", "for","encoding"}




# Define replacement functions
def simplify_genes(match):
    """Simplifies gene patterns in text."""
    gene1, gene2 = match.group(1), match.group(2)
    return f"genes of {gene1} and {gene2}" if gene2 else f"genes of {gene1}"

def simplify_genes_other(match):
    """Simplifies other gene patterns in text."""
    gene1, gene2 = match.group(1), match.group(2)
    return f"the {gene1} gene and {gene2} gene" if gene2 else f"the {gene1} gene"


def simplify_words_replace(match):
    """Replaces 'the <word_to_replace> <gene-related terms>' with 'the <gene-related terms>'."""
    return f"the {match.group(2)}"

# Function to simplify "the <optional word> <word>ase gene(s)"
def simplify_ase_genes(match):
    """Replaces 'the <optional word> <word>ase gene(s)' with 'the gene(s)'."""
    if "genes" in match.group(0):
        return "the genes"
    else:
        return "the gene"

def get_relevant_sentences(sentences, article_genes):
        relevant_sentences = []
        
        for sentence in sentences:
            paragraph_words = {word.strip(REMOVE_FROM_GENE) for word in sentence.split(' ')} - {''} 
            if  article_genes.intersection(paragraph_words):  
                relevant_sentences.append(sentence)
        return(relevant_sentences)

def preprocess_text(text):
    """Preprocesses the text by cleaning and splitting it into sentences."""
    text = process_raw_data(text, gene=True)
    #text = text.replace('the gene cluster regulator', '').replace('over-', 'over')
    clean_text = re.sub(r'<.*?>', '', text)
    replaced_text = re_pat.sub('', clean_text)
    sentences = big_file_split(replaced_text)
    
    return sentences



# Compile patterns for splitting sentences
split_point = r'(?<=[a-z]\w[A-Z])\.\s(?=\w+)'
split_point_2 = r'(?<=\w[\d\W])\.\s(?=\w+)'
SPLIT_PATTERN_1 = re.compile('\s\.\s\(|\s\.\s|\.\s,|\s{3,}|•\s|\s;\s|(?<=\w[\d\W])\.\s(?=\w+)|(?<=[a-z]\w[A-Z])\.\s(?=\w+)|\.\sthe\s')  # For Step 1
SPLIT_PATTERN_2 = re.compile(r'\sunder\s|\swhich\s|\s\w+ly\s|\sby\s|\svia\s|\sin\s[A-Z].\s|\sresulted\s|\sin\saddition,|\sit\swas\salso\sfound\sthat\s|\sand\shence\s|ha[v|s]e?\sbeen\sreported\s|ha[v|s]e?\sbeen\sexplained\s|ha[v|s]e?\sbeen\sshown\s|ha[v|s]e?\sbeen\sused\s|\bwas\sused\b')     # For Step 2


def clean_up_sentences(sentences):
    """Cleans up sentences by splitting on specific patterns and removes single-word sentences early."""
    clean_sentences = set()  # Use a set to avoid duplicates
    
    # Step 1: Split sentences on specific patterns and filter single-word sentences
    for sentence in sentences:
        sub_sentences = SPLIT_PATTERN_1.split(sentence)  # Use compiled pattern
        for sub_sentence in sub_sentences:
            sub_sentence = sub_sentence.strip(' .,')
            if len(sub_sentence.split()) > 1:  # Filter single-word sentences here
                clean_sentences.add(sub_sentence)
    
    # Step 2: Further split on specific words and filter single-word sentences
    additional_sentences = set()
    for sentence in clean_sentences:
        sub_sentences = SPLIT_PATTERN_2.split(sentence)  # Use compiled pattern
        for sub_sentence in sub_sentences:
            sub_sentence = sub_sentence.strip(' .,')
            if len(sub_sentence.split()) > 1:  # Filter single-word sentences here
                additional_sentences.add(sub_sentence)
    
    # Combine all sentences
    all_sentences = clean_sentences.union(additional_sentences)
    
    return list(additional_sentences)


def trim_process_sub_sentences_start_ending(sub_sentences, stop_words_and=stop_words_and):
    """Process sub-sentences to remove words at the beginning or end based on conditions."""
    trim_sub_senteces_set = set()  # Use a set for faster membership checks
    
    for sub_sentence in sub_sentences:
        words = sub_sentence.strip(',.; ').split(' ')  # Split once and strip once
        if not words:
            continue
        
        # Check the first and last word
        begining = words[0].lower().strip(',.; ')
        end = words[-1].lower().strip(',.; ')
        
        # Determine if the beginning or end should be removed
        remove_begining = begining in stop_words_and or begining.endswith('ly') 
        remove_end = end in stop_words_and or end.endswith('ly')
        
        if remove_begining or remove_end:
            # Remove words from the beginning or end
            if remove_begining:
                words = words[1:]
            if remove_end:
                words = words[:-1]
            
            # Reconstruct the sentence
            change_sentence = ' '.join(words).strip(',.; ')
            
            # Add to the result if not already present
            if change_sentence not in trim_sub_senteces_set:
                trim_sub_senteces_set.add(change_sentence)
                
        elif sub_sentence not in trim_sub_senteces_set:
            # Add the original sentence if not already present
            trim_sub_senteces_set.add(sub_sentence)
    
    return trim_sub_senteces_set


def preprocess_sub_sentence(sub_sentence):
    """Preprocesses a sub-sentence by replacing specific phrases with regex to handle word boundaries."""
    replacements = {
        r'\bthe sigma factor\b': 'the',
        r'\bcoding gene\b': 'gene',
        r'\band another\b': 'and',
        r'\bmutation in\b': 'mutated',
        r'(\bto further\b\s)?\benhance production,': ',',
        r'\bhave met with\b': 'experienced',
        r'\bgenes causing increased ring formation\b': 'genes',
        r'\bthe gene cluster regulator\b':'',
        r'(\bthe )?(relative )?\btranscription(al)? level(s)? of\b':'the expression of',

#        r'\bthe transcription levels of\b':'the expression of',

        r'\bover-':'over',
        r'\bdown-':'down',
        r'\bco-':'co',
        r'\bmutation of the regulator gene(s)?\b': 'mutation of the gene'

        
    }
    
    for old, new in replacements.items():
        sub_sentence = re.sub(old, new, sub_sentence)
    
    return sub_sentence

# Main function to process and simplify a sub-sentence
def simplify_sub_sentence(sub_sentence):
    """Simplifies a sub-sentence using regex patterns."""
    
    # ***ase
    sub_sentence = re.sub(WORDS_REPLACE_PATTERN, simplify_words_replace, sub_sentence)
    sub_sentence = re.sub(ASE_GENE_PATTERN, simplify_ase_genes, sub_sentence)
    
    # Genes
    sub_sentence = re.sub(GENE_PATTERN, simplify_genes, sub_sentence)
    sub_sentence = re.sub(OTHER_GENE_PATTERN, simplify_genes_other, sub_sentence)
    sub_sentence = re.sub(OTHER_GENE_PATTERN_2, simplify_genes_other, sub_sentence)

    sub_sentence = sub_sentence.replace('  ',' ')
    
    return sub_sentence

#def custom_nlp(text, gene_names):
#    """Runs the NLP pipeline and dynamically treats gene names as NOUNs."""
#    doc = nlp(text)
#    entities = []
#    for token in doc:
#        if token.text.strip(REMOVE_FROM_GENE) in gene_names:
#            token.pos_ = "NOUN"
#            entities.append((token.idx, token.idx + len(token.text), "GENE"))
#    if entities:
#        doc.ents = [Span(doc, doc.char_span(start, end).start, doc.char_span(start, end).end, label) for start, end, label in entities]
#    return doc
from spacy.tokens import Token


# Define a custom extension for the original text 
if not Token.has_extension("original_text"):
    Token.set_extension("original_text", default=None, force=True)

@Language.component("normalize_overexpressed")
def normalize_overexpressed(doc):
    
    normalization_rules = {
        "overexpress": "express",
        "coexpress": "express",
        "coregulat": "regulat",
        "downregulat": "regulat",
        "upregulat": "regulat",
        "overproduct":"production"

    }

    modified = False  # Track if modifications are needed
    modified_tokens = []  # Store modified tokens

    # Process tokens in one loop
    for token in doc:
        token._.original_text = token.text  # Store original text
        lower_text = token.text.lower()

        for variant, normalized in normalization_rules.items():
            if lower_text.startswith(variant):
                modified_tokens.append(normalized + token.text[len(variant):])
                modified = True
                break
        else:
            modified_tokens.append(token.text)



    if not modified:
        return doc  # Skip reprocessing if no changes

    # Create a new Doc with the modified tokens
    modified_text = " ".join(modified_tokens)
    with nlp.select_pipes(enable=["tok2vec",'tagger','parser']):
        modified_doc = nlp(modified_text)

    # Add the original text as a custom attribute to the modified_doc
    for i, token in enumerate(modified_doc):
            # Store the original text in the custom attribute
            token._.original_text = doc[i]._.original_text

    return modified_doc


# Register gene_tagger as a custom component
@Language.factory("gene_tagger")
def create_gene_tagger(nlp, name, gene_names=None):
    # Characters to remove from gene names and token text
    remove_from_gene = '.,*-;()'

    # Function to update gene_indices based on gene_names
    def update_gene_indices(gene_names):
        if gene_names:
            cleaned_gene_names = {gene.strip(remove_from_gene) for gene in gene_names}
            return {nlp.vocab.strings[gene]: True for gene in cleaned_gene_names}
        else:
            return {}

    # Define the gene_tagger function
    def gene_tagger(doc):
        entities = []
        for token in doc:
            # Strip unwanted characters from the token text
            cleaned_token_text = token.text.strip(remove_from_gene)
            # Convert cleaned token text to its vocabulary index
            token_index = nlp.vocab.strings[cleaned_token_text]
            # Check if the token index is in the precomputed gene_indices
            if token_index in gene_tagger.gene_indices:
                token.pos_ = "NOUN"
                token.tag_ = "NN"    # Override the fine-grained POS tag

                entities.append(Span(doc, token.i, token.i + 1, label="GENE"))
        # Efficiently merge entities
        doc.ents = (*doc.ents, *entities)
        return doc

    # Initialize gene_names and gene_indices as attributes of the gene_tagger function
    gene_tagger.gene_names = set(gene_names) if gene_names else set()
    gene_tagger.gene_indices = update_gene_indices(gene_names)

    # Add update method to gene_tagger
    def update_gene_names(new_gene_names):
        gene_tagger.gene_names = set(new_gene_names)
        gene_tagger.gene_indices = update_gene_indices(new_gene_names)

    gene_tagger.update_gene_names = update_gene_names

    return gene_tagger


def update_gene_tagger(nlp, gene_names):
    """Updates the gene_names in the existing gene_tagger component."""
    if "gene_tagger" in nlp.pipe_names:
        gene_tagger = nlp.get_pipe("gene_tagger")
        gene_tagger.update_gene_names(gene_names)  # Update both gene_names and gene_indices
    return nlp


def create_custom_nlp(nlp, gene_names):
    """Creates a fresh NLP pipeline based on an existing one and ensures gene_tagger is included after the tagger."""
    custom_nlp = spacy.blank(nlp.lang)  # Create a fresh NLP instance with the same language

    # Copy all components while making space for `gene_tagger`
    added_gene_tagger = False
    for name in nlp.pipe_names:
        if name == "tagger" and not added_gene_tagger:
            custom_nlp.add_pipe(name, source=nlp)  # Add the tagger
            
            custom_nlp.add_pipe("normalize_overexpressed")
            custom_nlp.add_pipe("gene_tagger", config={"gene_names": list(gene_names)})  # Add gene_tagger after tagger
            added_gene_tagger = True  # Ensure it's only added once
        else:
            custom_nlp.add_pipe(name, source=nlp)

    # If gene_tagger wasn't added (e.g., no tagger in the original), add it at the beginning
    if "gene_tagger" not in custom_nlp.pipe_names:
        custom_nlp.add_pipe("gene_tagger", config={"gene_names": list(gene_names)}, first=True)
    
    return custom_nlp


custom_nlp = create_custom_nlp(nlp, gene_names=[]) 
