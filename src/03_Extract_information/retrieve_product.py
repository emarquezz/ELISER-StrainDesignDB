#maybe just remove stop words in the cleanup of fake products or filter_non_relevant
# CHECK PRINT MINI SENTENCES
import os
import sys
sys.path.append('../')

# Data manipulation and analysis
import pandas as pd
import re

# Natural language processing
import spacy
from spacy import displacy
from spacy.tokenizer import Tokenizer
from spacy.util import compile_prefix_regex, compile_infix_regex, compile_suffix_regex

import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize

from text_analysis import get_variations_nlp_tagger, classify_variations, get_wordnet_lemmas, stop_words

## Generate inflected forms of words
import pyinflect

# Module with organisms of interest
from retrieve_organism import *


GENERAL_STRIP = r' .‘]”[‐,:)-’;(\\'
# Create a new set of stopwords that excludes the words 'and' and 'of'

# Define a set of stopwords to exclude
STOPWORDS_TO_EXCLUDE = {'and', 'of'}

# Create a new set of stopwords that excludes the specified words
stop_words_and = stop_words.difference(STOPWORDS_TO_EXCLUDE)

# Define a set of additional words and punctuation marks to split sentences on
EXTRA_SPLIT_SENTENCE = {'changes', 'enable', 'fates', 'towards', 'using', ':', '.', 'via', 'the',
                        'moreover', 'furthermore', 'therefore', 'however', 'often','but','also', 'by'}

# Update the stop_words_and set with the extra_split_sentence set
stop_words_and.update(EXTRA_SPLIT_SENTENCE)


# Load the large English language model from spacy
nlp = spacy.load('en_core_web_sm')

# Define a list of custom infixes for tokenization
custom_infixes = [r"[-]~", r"[(]~", r"[0-9]~", r"[,]~"]

# Compile the custom infixes into a regular expression object
infix_re = spacy.util.compile_infix_regex(custom_infixes)

# Define a regular expression pattern to match certain words and word variations
#periplasmic and cytosolic?

# Define a list of word roots and variations to match
word_roots = [
    'abound', 'abundan', 'accelerat', 'accomplishment', 'accumulat', 'achievement', 
    'acidification', 'activ', 'actualiz', 'advanc', 'aerob', 'amplitude', 'analys', 
    'anoxic', 'antimicrobial', 'arguabl', 'asymmetr', 'augmentative', 'autogenic', 
    'bacterial', 'base','basic', 'beauteous', 'best', 'better', 'biter', 'boost', 'boot', 
    'boundless','capsul', 'cellular', 'celluloid', 'centraliz', 'certain','chemical', 'chewable', 
    'cytosolic', 'codependent', 'cofactor','colorless', 'combinatorial', 'commercial', 'compatib', 
    'comple', 'comprehen','common', 'conserv', 'consider', 'consolidat', 'const', 'contaminat', 
    'contin', 'corrod', 'coupl', 'covariance','criterion','critical', 'crucial', 'customiz', 'cytogenetic', 
    'cytotoxicit', 'decarbonis', 'defined', 'degrad', 'deification', 'demonstrative', 
    'denazification', 'design', 'determinative', 'detoxification', 'development', 
    'diagonal', 'differ','difficult', 'diminish', 'direct', 'disincorporat', 'dispel', 'divers', 'enantiop',
    'dramati', 'driven', 'eatable', 'econom', 'edge', 'effect', 'efficien', 'emulat', 
    'encompass', 'energ', 'engineer', 'enhanc', 'entrop', 'enzymatic', 'equable', 
    'essenti', 'esterification', 'karyotic', 'excellent', 'exclusiv', 'exploitation', 
    'export','exotic', 'express','extend','extract', 'extricat', 'ferment', 'ferromagnetism', 'fertile', 'fifth', 
    'final', 'first', 'flexib', 'flux', 'foreseeabilit', 'formaliz', 'fourth', 'free', 
    'freshwater', 'friendly', 'function', 'futile', 'generat', 'goiter', 'gradable', 
    'gram', 'great', 'green', 'hard', 'high(level| titer)?','heterotroph', 'increas', 'import', 
    'improv', 'increment', 'independe', 'individua', 'industr', 'infus', 'innovation', 'institut',
    'integrat', 'interm', 'isogonal', 'isotrop', 'kilo','kinetic', 'large', 'latest', 'laxative', 
    'lessen', 'linear', 'liquidat', 'logic', 'logous', 'loiter', 'low', 'macrophage', 
    'magneto', 'magnetopause', 'maintain', 'manufactur', 'masticat', 'maxim', 'medicinal',
    'metaboli', 'microb', 'millilit', 'minimiz', 'miter', 'most', 'mycobacteri', 'myriad',
    'natur','nativ', 'niter', 'nitrification', 'nondurable', 'novel', 'objectivit', 'one-pot', 
    'opportunit', 'optical', 'optim', 'orange', 'orthogonalit', 'ounce', 'overall',# 'organ',
    'pair', 'paralleliz', 'pasteurization', 'penultimate', 'perfectness', 'periplasmic', 
    'personal', 'petrification', 'pharmaceutic','photosensitizer', 'phytotoxicit', 'plenteous', 'plicat', 
    'polysaccharide', 'possibilit', 'potentia', 'prepar', 'preserv', 'previous', 
    'process', 'products', 'proficient', 'profit', 'progress', 'promising','promot', 'prospe', 
    'quadratic', 'quanti', 'quick', 'rapid', 'rare', 'ratable', 'ratio', 'reabsorption', 
    'recalibrat', 'recen', 'recombin', 'reconstruct', 'recycl', 'reduc', 'regrad', 
    'relevant', 'reliable', 'renewab', 'replic', 'represent', 'research', 'restructur', 
    'reusab', 'robust', 'rough', 'scarification', 'second', 'secretory', 'select', 
    'seventh','several', 'significa', 'simultane', 'sixth', 'sock', 'specializ', 'specif', 'stabiliz', 
    'stabl', 'stage', 'stainable', 'step', 'stimulation', 'straightforward', 
    'strapless', 'strengthen', 'strong', 'stud', 'sublim', 'subsequent', 'substantial', 
    'success', 'supersymmetr', 'surround', 'sustain', 'symmetric', 'synchroni', 
    'synthetic', 'system', 'technolog', 'term', 'therap', 'third', 'titer', 'toxic', 
    'transmogrification', 'trilog', 'trophic', 'tropism', 'tune','ubiquitou', 'uptake', 'useful', 
    'utilization', 'valua', 'varia', 'varie','variety','vario', 'velocit', 'versatil', 'vital', 
    'vitrification', 'vivo', 'volatili','volume', 'weldable', 'well', 'whole', 'yield'
] + ['many']

# Join word roots into a single regex pattern
word_pattern = '|'.join(word_roots)

# Define the full regex pattern with word boundaries
pattern = fr'\b(\w*-?)({word_pattern})(\w*-?\w*)\b'

# Compile the regex pattern
re_pat = re.compile(pattern)


# Define a string containing a list of verbs
verbs = "increases improve higher better enhance efficient produce yield titer"
verbs +=  " overexpress biosynthesis synthesis greater boost optimize maximize exclusive"
verbs +=  " overproduction production success successfully improvement most stable function"

# Get variations of the words
variations = get_variations_nlp_tagger(verbs, nlp)
verbs, adjectives, nouns, adverbs,ad_verb, adj_noun = classify_variations(variations)


# Create a list of words and word variations to include in analysis
words = ['produces','production','overproduction','biosythesis','bioprocessing',
         'conversion','synthesizes','converting',]
words += variations['NN'] + variations['VBD']
words = set(words)

# Remove certain words from the list of words to include in analysis
# Create a set of words to remove from the words set
words_to_remove = {'well','welled','stable','stabled','efficient','most',
                   'great','exclusive','function','functioned','success'}

# Remove the words from the words set
words.difference_update(words_to_remove)

# Create a list of all verb,adverb and adjective lemmas in WordNet
complete_verbs, adjectives, adverbs = get_wordnet_lemmas()
irrelevant_words = complete_verbs+adverbs #adjectives is weird...

# Get variations of the words
variations_2 = get_variations_nlp_tagger(' '.join(irrelevant_words), nlp)



variations_list = variations.values()
variations_list = [item for sublist in variations_list for item in sublist]
variations_list_2 = variations_2.values()
variations_list_2 = [item for sublist in variations_list_2 for item in sublist]
# Maybe not remove analogue? and precursor? enzyme?

before_list = ['enzyme', 'growth', 'analog', 'analogue', 'precursor', 'the', 'a', 'an', 'chemical', 'that', 'process',
               'processes', 'array', '', 'production', 'of', '.', 'coli', 'titrating', 'phenotype', 'level', 'obstacles', 
               'strategy', 'original', 'host', 'cell', 'is', 'vehicle', 'commerically', 'evolution', 'could', 'fig', 'etc', 
               '', 'tolerance', 'compound', 'rangge', 'scale', 'transformation', 'algorithm', 'novo', 'strain', 'target',
               'product', 'gene', 'require', 'further', 'new', 'old', 'reaction', 'model', 'report', 'result', 'value-added', 'fine',
               'mechanism', 'bottleneck', 'de-novo', 'necessary', 'approach', 'use', 'dictate', 'valorize', 
               'investigate', 'performance', 'underlying', 'optimization', 'initial', 'broad', 'range', 'sequential', 
               'storage', 'plant', 'variety', 'respectively', 'recent', 'year', 'pathway', 'inexpensive', 'biology', 'future', 
               'molecule','metabolite', 'reprogramming', 'utilization', 'platform', 'provide', 'make', 'connection', 
               'biomolecule', 'vitro', 'rate', 'direct', 'synthetic', 'system', 'comparison', 'economic', 'approach', 'many', 
               'crude', 'indicate', 'demontrate', 'common', 'today', 'extract', 'several', 'specific', 'show', 'currently', 
               'module', 'technique', 'late', 'cost', 'exist', 'serve', 'replace', 'condition', 'play', 'fast', 'chassis', 
               'genetic', 'method', 'genomic', 'unit', 'secretion', 'unit-1', 'dependency', 'ref',
               'growth-rate','discovery','industry-scale', 'transcriptomic', 'dysbiotic', 'optogenetic', 'stereospecific', 
               'prokaryote-specific', 'transgenic', 'thermophilic', 'obstacle', 'distribution', 'pathway-specific', 
               'periplasmic', 'microfluidic', 'bicistronic', 'non-pathogenic', 'consumption', 'strategie', 'republic', 
               'institute', 'polytechnic','fig','role', 'goal', 'titre', 'new', 'usage', 'genome', 'genetic', 'kinetic', 
               'neurogenic' ,'dynamic', 'static', 'pleiotropic', 'regulation', 'rather', 'been', 'frequency', 'difficulty',
               'induction', 'introduction', 'maintenance', 'overview', 'architecture', 'environment', 'specialty',
               'repertoire', 'prediction', 'implementation', 'example', 'jounraldoi', 'endpoint', 'tradeoff', 'since',
               'failed', 'manner', 'mode', 'period', 'formation','eukaryotic', 'toward', 'wealth', 'via', 'al', 'et',
              'despite', 'european', 'elsevier', 'disruption', 'genome-scale', 'library', 'spectrum', 'bioproduct',
               'resource', 'bioresource', 'primary product', 'error', 'trial-and-error', 'errors','anti-diabetic']
other_nouns = ['extender','antitumor','enantiopure','chiral', 'self-sufficiency','mitochondrial',
               'solute','strategy','performance', 'resource','method' ]

before_list = set(before_list)
before_list = words | set(stop_words_and) | set(variations_list) | set(variations_list_2) | set(irrelevant_words)

before_list = before_list | set(other_nouns)
# Add plural forms (avoiding duplicates automatically)
before_list.update(n + 's' for n in list(before_list))

# Add species and genus names (assuming .values is a list-like)
before_list.update(species_list.values)
before_list.update(genus_list.values)
before_list.update(genus_list.str.lower().values)

# Remove unwanted terms in one operation
before_list.difference_update({
    'acid', 'acids', 'lactate', 'citrate',
    'carboxylate', 'Glycine', 'glycine', 'calcine'
})

before_list = frozenset(before_list)
words = frozenset(words)

def custom_tokenizer(nlp):
    """
        Creates a custom tokenizer using the specified vocabulary and infix finder.

        Parameters:
        - nlp (spacy.lang.en.English): A pre-initialized English language model from the spacy library.

        Returns:
        - Tokenizer: A custom tokenizer object for the specified vocabulary and infix finder.
    """
    return Tokenizer(nlp.vocab, infix_finditer=infix_re.finditer)

nlp.tokenizer = custom_tokenizer(nlp)


def remove_adjectives(text, word='production'):  
    """
    Remove adjectives from a given text.

    This function searches for occurrences of the following patterns in the text:

    '(and )' + pattern: a word preceded by the word 'and'
    '(word) of (an|the|a|any|some)?' + pattern: a word preceded by the preposition "of"
    pattern + ' (word)': a word followed by another word
    pattern + ' \S* (word)': a word followed by another word and possibly more characters
    The pattern parameter is a regular expression that matches an adjective. By default, this is set to '\S*adjective\b'.

    The word parameter specifies the word that should be checked for in the text. By default, this is set to "production".
    
    So we are searching to change  "and -adjective- acetate production" to "and acetate production"

    Parameters:
    text (str): The text to modify.
    word (str, optional): The word to be checked for in the text. Default is "production".

    Returns:
    str: The modified text.
    """
    # Define the patterns for replacement
    f_patterns = [
        r'\b(and\s+)?{}\b'.format(pattern),                        # and_ad_x_production
        r'\b({}\s+of)\s+(an|the|a|any|some)?\s+{}\b'.format(word, pattern),  # production_of_ad_x
        r'\b{}\s+{}\b'.format(pattern, word),                     # ad_production
        r'\b{}\s+\S*\s+{}\b'.format(pattern, word)                # ad_x_production
    ]
    
    # Compile all patterns into a single regex for efficiency
    combined_pattern = '|'.join(f_patterns)
    regex = re.compile(combined_pattern)
    
    # Replace matching patterns in the text
    def replace_match(match):
        # Determine which group matched and return appropriate replacement
        if match.group(1):
            return match.group(1).strip()  # For 'and ad_x_production'
        else:
            return ''  # For other patterns, remove the adjective part
    
    modified_text = regex.sub(replace_match, text)
    modified_text = re.sub(r'\s+', ' ', modified_text)

    return modified_text.strip()


# Precompiled regex patterns for replace_production_words
_RP_PROD_MOBPSI = re.compile(r'Multi-omic based production strain improvement \(MOBpsi\)', re.IGNORECASE)
_RP_PROD_TITER = re.compile(r"\btiter of [0-9]+\.?[0-9]?")
_RP_LOWERCASE_WORDS = re.compile(r"\b(\w{2,})\b[\$\@()+.\s]?")
_RP_REMOVE_PHRASES_1 = re.compile(r'( and characterization\b)|(\bconjugate\b)|(\bbioconjugate\b)|(\bstability\b)')
_RP_REMOVE_PHRASES_2 = re.compile(r'\ba variety of\b')

_RP_ASSIMILATION = re.compile(r'\b[Aa]ssimilation of\b')
_RP_TITER_IMPROVEMENT = re.compile('titer improvement')
_RP_SPECIFIC_COMPOUND = re.compile(r'specific compound(s)?')
_RP_STORAGE_COMPOUND = re.compile(r'storage compound(s)?')
# Use named groups to match and remove <i> and </i> tags.
_RP_HTML_TAGS = re.compile(r'<[^>]*>')
_RP_EXTRA_SPACES = re.compile(r'\s+')
_RP_MEDIUM_CHAIN = re.compile(r'\b(medium|short)?-chain(-length)?\b')
_RP_THAT_IS = re.compile(r'(,a (\w+ )that is)')
_RP_RIBOSOMAL = re.compile(r'\b(non)?(-)?ribosomal\b')

# Handles phrases like "bioprocessing of ... into/to synthesize"
_RP_BIOPROCESSING = re.compile(r'(\b[Bb]ioprocessing|(\b[Bb]io)?conversion)\s+of.*\s+(in)?to\s+(synthesize)?')
_RP_BIOMANUFACTURING = re.compile(r'\b[Bb]io(-)?manufacturing\s+of.*\s+(in)?to\s+(synthesize)?')
_RP_PRODUCED = re.compile(r'\b(is|are|can be|was|were)\b(?!\.)\b(?:[^.]*\bproduced\b)')
_RP_IMPROVEMENT_INTO = re.compile(r'(\b[Ii]mprovement)\s+of\s+.*\s+into\s+')
_RP_IMPROVEMENT_FOR = re.compile(r'(\b[Ii]mprovement)\s+of\s+.*\s+for\s+')
_RP_PRODUCES = re.compile(r'([Pp]roduces|([Bb]io)?synthesizes)\s+')
_RP_PRODUCED_BY = re.compile(r'([Pp]roduced|([Bb]io)[Ss]ynthesized)\s+by\s+')
_RP_BIOSYNTHESIS_PROD = re.compile(r'\b[Bb]iosynthesis\s+and\s+production\s+of\s+')
_RP_CONVERTING = re.compile(r'([Cc]onverting)\s+.*\s+(in)?to\s+')
_RP_TO_PRODUCE = re.compile(r'\s+to\s+([Pp]roduce|([Bb]io)?[Ss]ynthesize)\s+')
_RP_TO_BIOMANUFACTURING = re.compile(r'\s+to\s+[Bb]io(-)[Mm]anufacturing\s+of\s+')
_RP_PROD_UNITS = re.compile(r'\bproduction\s+of\s(pure\s)?+units\b')

# Production of enantiomeric precursors of
_RP_PROD_ENANTIOMERIC = re.compile(r'\b([Pp]roduction\s+of\s+)(enantiomeric\s)?precursors\s+of\b')
_RP_CATALYTIC_PROD = re.compile(r'\b([Bb]io)?catalyt?ic\s+production\s+of\b')
_RP_CATALYTIC_OF = re.compile(r'\b([Bb]io)?catalyt?ic\s+of\b')
_RP_PRIMARY_PRODUCT = re.compile(r'[Pp]rimary product')
_RP_STARFISH = re.compile(r'neurogenic starfish')
_RP_PLANT_SPECIFIC = re.compile(r'plant-specific', re.IGNORECASE)

# et al
_RP_ET_AL = re.compile(r'et al([,.])?([.,])', re.IGNORECASE)

# Misc phrase cleanup
_RP_REMOVE_TERMS = re.compile(
    r'(active form of|its analogues|its analogs|important molecules:|first- and second-generation|one stone two birds: |pharmaceutical applications:)'
)
_RP_ADV_PROD = re.compile(r'significal production|advanced production')
_RP_REMOVE_FILLERS = re.compile(r' an |de novo | both catalytic and stability')

_RP_PROD_TERMS = re.compile('(' + '|'.join(f'{w} of' for w in words) + ')')


_RP_PROPERTIES_OF_PRODUCED = re.compile(
    r'\bproperties of\s+([\w\-]+)\s+produced\b', re.IGNORECASE
)

_RP_PATHWAY_TO_ROUTE = re.compile(r'\bpathway(s?)\b', re.IGNORECASE)
_RP_ERROR_TO_MISTAKE = re.compile(r'\bproduction error(s?)\b', re.IGNORECASE)
_RP_PLATFORM_TO_SYSTEM = re.compile(r'\bplatform(s?)\b', re.IGNORECASE)
_PROD_WORDS_CLEANUP = re.compile(
    r'\b(?:product|production)\s+(%s)\b' % '|'.join(words),
    flags=re.IGNORECASE
)
_PROD_WORDS_CLEANUP_2 = re.compile(
    r'\b(%s)\s+of\s+(?:the\s+)?product\b' % '|'.join(words),
    flags=re.IGNORECASE
)


# Main function with preserved comments
def replace_production_words(full_text, word='production'):
    """
    Replaces certain words in the given text to make its analysis easier.

    Parameters:
    full_text (str): The text to modify.
    word (str, optional): The word to be replaced in certain cases. Default is 'production'.

    Returns:
    str: The modified text.
    """
    #full_text = full_text.lower()
    
    full_text = _RP_PROD_MOBPSI.sub('MOBpsi', full_text)
    full_text = _RP_PROD_TITER.sub("production.", full_text)
    full_text = _RP_LOWERCASE_WORDS.sub(lambda m: m.group(0).lower(), full_text)
    
    full_text = _RP_REMOVE_PHRASES_1.sub('', full_text)
    full_text = _RP_REMOVE_PHRASES_2.sub('', full_text)

    full_text = _RP_ASSIMILATION.sub('conversion of', full_text)
    
    full_text = _RP_TITER_IMPROVEMENT.sub('production', full_text)
    full_text = _RP_SPECIFIC_COMPOUND.sub('compound', full_text)
    full_text = _RP_STORAGE_COMPOUND.sub('compound', full_text)
    
    full_text = _RP_PATHWAY_TO_ROUTE.sub(lambda m: 'route' + m.group(1), full_text)

    # Use named groups to match and remove <i> and </i> tags.
    full_text = _RP_HTML_TAGS.sub('', full_text)
    full_text = _RP_EXTRA_SPACES.sub(' ', full_text)
    full_text = full_text.replace(' and of ', ' of ')
    full_text = full_text.replace(' of and ', ' of ')

    full_text = full_text.replace(' gentamicin A ', ' gentamicin-A ')
    full_text = full_text.replace(' gentamicin B ', ' gentamicin-B ')
    full_text = full_text.replace(' gentamicin c1a ', ' gentamicin-c1a ')
    full_text = _RP_MEDIUM_CHAIN.sub('', full_text)
    full_text = _RP_THAT_IS.sub('. It is', full_text)
    
    full_text = _RP_RIBOSOMAL.sub('', full_text)

    full_text = remove_adjectives(full_text, word)

    full_text = _RP_BIOPROCESSING.sub('production of ', full_text)
    full_text = _RP_BIOMANUFACTURING.sub('production of ', full_text)
    full_text = _RP_PRODUCED.sub('production', full_text)
    full_text = _RP_IMPROVEMENT_INTO.sub('production of ', full_text)
    full_text = _RP_IMPROVEMENT_FOR.sub('for ', full_text)
    full_text = _RP_PRODUCES.sub('allows the production of ', full_text)
    full_text = _RP_PRODUCED_BY.sub('production by ', full_text)
    full_text = _RP_BIOSYNTHESIS_PROD.sub('production of', full_text)
    full_text = _RP_CONVERTING.sub('production of ', full_text)
    full_text = _RP_TO_PRODUCE.sub(' for the production of ', full_text)
    full_text = _RP_TO_BIOMANUFACTURING.sub(' for the production of ', full_text)
    full_text = _RP_PROD_UNITS.sub('production of', full_text)

    # Production of enantiomeric precursors of
    full_text = _RP_PROD_ENANTIOMERIC.sub(r'\1', full_text)
    full_text = _RP_CATALYTIC_PROD.sub('production of', full_text)
    full_text = _RP_CATALYTIC_OF.sub('production of ', full_text)
    full_text = _RP_PRIMARY_PRODUCT.sub('', full_text)
    full_text = _RP_STARFISH.sub('', full_text)
    full_text = _RP_PLANT_SPECIFIC.sub('', full_text)
    
    # et al
    full_text = _RP_ET_AL.sub('and others,', full_text)

    prod_terms = _RP_PROD_TERMS
    # Use a single pattern to match and replace multiple phrases.
    full_text = prod_terms.sub('production of', full_text)

    # Remove miscellaneous phrases
    full_text = _RP_REMOVE_TERMS.sub('', full_text)
    full_text = remove_adjectives(full_text)
    
    # Use a named group to match and remove numbers followed by a "fold" or "mg" suffix.
    #pattern = r'(?P<number>[0-9]+) (?P<suffix>fold|[mμ]g[/]?l?)'
    #full_text = re.sub(pattern, '', full_text)
    
    # Replace remaining phrases with the word "production".
    full_text = _RP_ADV_PROD.sub('production', full_text)
    full_text = _RP_REMOVE_FILLERS.sub(' ', full_text)

    full_text = full_text.replace(' and of ', ' of ')
    full_text = full_text.replace(' of and ', ' of ')
    full_text = full_text.replace('molecule', 'product')
    full_text = full_text.replace('production performance', 'production')
    full_text = full_text.replace('production performance', 'production')

    full_text = re.sub(r'\banti-?parasitic agent\b', 'antiparasitic', full_text, flags=re.IGNORECASE)

    full_text = _RP_PROPERTIES_OF_PRODUCED.sub(r'\1 produced', full_text)
    full_text = _RP_PATHWAY_TO_ROUTE.sub(lambda m: 'route' + m.group(1), full_text)    
    full_text = _RP_ERROR_TO_MISTAKE.sub(lambda m: 'mistake' + m.group(1), full_text)
    full_text = _RP_PLATFORM_TO_SYSTEM.sub(lambda m: 'system' + m.group(1), full_text)
    full_text = _PROD_WORDS_CLEANUP.sub(r'\1', full_text)
    full_text = _PROD_WORDS_CLEANUP_2.sub(r'\1', full_text)
    
    return full_text


# Make a function to merge the mol and g versions. Also to merge the number without space and with spae

# Precompiled regex patterns for remove_units
_REMOVE_UNITS_PATTERNS = [
    # mg l(-1) or mg g(-1) and variants
    (re.compile(r'\b[mμµ]?[gLl] [mμµ]?[lLg]\b(\(?-1\)?)?'), 'units'),
    # number without space
    (re.compile(r'(\d+)[mμµ]?[gLl] [mμµ]?[lLg]\b(\(?-1\)?)?'), r'\1 units'),
    # (123123%)
    (re.compile(r'\(\d+%\)'), 'units'),

    
    # mmol l(-1)
    (re.compile(r'\b[mμµ]?mol [mμµ]?[lLg]\b(\(?-1\)?)?'), 'units'),
    # number without space
    (re.compile(r'(\d+)[mμµ]?mol [mμµ]?[lLg]\b(\(?-1\)?)?'), r'\1 units'),

    # 34 mg or mg/L
    (re.compile(r'\b[mμµ]?[glL](\/[mμµ]?[lL])?\b(\(-1\))?'), 'units'),
    # number without space
    (re.compile(r'(\d+)[mμµ]?[glL](\/[mμµ]?[lL])?\b(\(-1\))?'), r'\1 units'),

    # 34 mmol or mmol/L
    (re.compile(r'\b[mμµ]?mol(\/[mμµ]?[lL])?\b(\(-1\))?'), 'units'),
    # number without space
    (re.compile(r'(\d+)[mμµ]?mol(\/[mμµ]?[lL])?\b(\(-1\))?'), r'\1 units'),

    # cell/h
    (re.compile(r'\bcell\/?h(-1)?\b'), 'units'),

    # lone "mol"
    (re.compile(r'\b[mμµ]?mol\b'), 'units'),

    # unitsl
    (re.compile(r'\bunits\/?[lL]\b'), 'units'),
    (re.compile(r'\bunits\/?liter\b'), 'units'),

    # units-1
    (re.compile(r'units-\d+'), 'units'),
    (re.compile(r'units-(\w+)'), r'units \1'),

    (re.compile(r'units\/units'), 'units'),

    # join the number with the units
    (re.compile(r'(\d+\.?\d*)\s(units)'), r'\1-\2'),

    (re.compile(r'units-\(\+\)-(\w+)'), r'units \1')
]

def remove_units(text):
    
    # mg l(-1) or mg g(-1) and variants
    # number without space
    
    #mmol l(-1)
    # number without space

    # 34 mg o mg/L
    #number without space    

    # 34 mmol o mmol/L
    #number without space    

    #cell/h

    #unitsl
    #    units-1

    # join the number with the units

    for pattern, repl in _REMOVE_UNITS_PATTERNS:
        text = pattern.sub(repl, text)

    return(text)

# Precompiled regex patterns for remove_journals
_JOURNAL_PATTERN = re.compile(r'(\w{1,7}\s+){1,2}(\w{1,13}\s+){1,2}\(?\d+\)?\s*(\d+[:–;.])+(\s+)?\d+')
_JOURNAL_FILTER = re.compile(r'^(over)?(expression|production)\b', re.IGNORECASE)
_JOURNAL_PATTERN_2 = re.compile(
    r'(\w{1,7}[\.,]{1,2}?\s+){1,2}(\w{1,13}[\.,]{1,2}?\s+){1,2}\(?\d+\)?\s*(\(?\d+\)[:–;.,]?)+(\s+)?\d+.\d+[:–;.,]?\s+\w{4}',
    re.IGNORECASE
)
_DOI_PATTERN = re.compile(r'DOI:?\s+(\w+[-.\/])+\d+', re.IGNORECASE)
_DATE_PATTERN_1 = re.compile(r'\w+(\s+)?\w+:\s+\d{1,2}\s+\w+\s+\d{4}', re.IGNORECASE)
_DATE_PATTERN_2 = re.compile(r'\w+(\s+)?\w+:\s+\w+\s+\d{1,2},?\s+\d{4}', re.IGNORECASE)
_URL_PATTERN = re.compile(r'\w+[\.:].+\w+\.(org|com)\/.+', re.IGNORECASE)

def remove_journals(text):
    # Match candidate journal strings
    matches = _JOURNAL_PATTERN.findall(text)

    # Filter out those that start with 'expression' or 'production'
    valid_matches = [match for match in matches if not _JOURNAL_FILTER.match(match[0])]

    # Remove valid matches from text
    for match in valid_matches:
        text = text.replace(match[0], '')

    full_text = text
    full_text = _JOURNAL_PATTERN_2.sub('', full_text)
    full_text = _DOI_PATTERN.sub('', full_text)
    full_text = _DATE_PATTERN_1.sub('', full_text)
    full_text = _DATE_PATTERN_2.sub('', full_text)
    full_text = _URL_PATTERN.sub('', full_text)

    return full_text

# Precompile regex patterns globally
# remove DOIs
DOI_REGEX = re.compile(r'10.\d{4,9}/[-._;()/:A-Z0-9]+', re.IGNORECASE)

# remove URLs
URL_REGEX = re.compile(r"(https?):((//)|(\\\\\\\\))+[\w\d:#@%/;$()~_?\\+-=\\\\\\.&]*")

# eMPTY []
EMPTY_BRACKETS_REGEX = re.compile(r'\[\s\]\.')

# Make numbers just numbers without dots
NUMBER_DOTS_REGEX = re.compile(r'(?<=\d)\.(?=\d)')

# Just one space
ONE_SPACE_REGEX = re.compile(r"\s+")

# Join some chemicals with these words - gene specific
GENE_UPPERCASE_REGEX = re.compile(r"\b(?![A-Z]{2,}\d*\b)(\w{2,})(?<![A-Z])\b[\$\@()+.\s]?")

# Join some chemicals with these words - general
LOWERCASE_REGEX = re.compile(r"\b(\w{2,})\b[\$\@()+.\s]?")

def process_raw_data(raw_text, gene=False):
    '''Replace some special characters and chemical names'''
    #print(raw_text)
    # DO NOT REPLACE THE DOT IF THERE ARE NUMBERS AROUND
    #remove_dot = re.sub(r"(?<!\d)\.(?!\d)", " .", raw_text)
    #replaced_units = remove_units(remove_dot)
    
    # remove DOIs
    raw_text = re.sub(DOI_REGEX, '', raw_text)

    #remove URLs
    raw_text = re.sub(URL_REGEX, '', raw_text)

    #eMPTY []
    raw_text = re.sub(EMPTY_BRACKETS_REGEX, '', raw_text)

    # journal problems pdf
    raw_text = remove_journals(raw_text)

    replaced_units = remove_units(raw_text)

    # Make numbers just numbers without dots
    replaced_units = re.sub(NUMBER_DOTS_REGEX, '', replaced_units)

    # Just one space
    one_space = re.sub(ONE_SPACE_REGEX, " ", replaced_units)

    # Replace special characters
    text = one_space.replace('"', '').replace('\xa0', ' ').replace('±', ' ').replace('\u2009', ' ').replace('\u202f', ' ')

    # Join some words to avoid missing them
    match = re.search(r'\([^\)]*\)', text)
    if match:
        new_word = match.group(0).replace(' ', '-')
        text = text.replace(match.group(0), new_word)

    # Join some chemicals with these words
    if gene:
        # Some genes end with uppercase
        #text = re.sub(r"\b(\w{2,})(?<![A-Z])\b[\$\@()+.\s]?", lambda match: match.group(0).lower(), text)
        # Some genes are all uppercase and finish wiht digits
        text = re.sub(GENE_UPPERCASE_REGEX, lambda match: match.group(0).lower(), text)
        #print('10',text)
    else:
        text = re.sub(LOWERCASE_REGEX, lambda match: match.group(0).lower(), text)

    return(text)

                
SP_CLEAN_RE = re.compile(r"[^a-zA-Z\s]")                
def search_production_word(sentence):
    clean_text = SP_CLEAN_RE.sub("", sentence)
    split_text = set(clean_text.lower().split())
    return bool(words.intersection(split_text))

def split_sentence(sentence):
#    EXTRA_SPLIT_SENTENCE = EXTRA_SPLIT_SENTENCE|{''}
    doc = nlp(sentence)
    result = []
    seen = set()
    for sent in doc.sents:
        for token in sent:
            if token.pos_ == "VERB" or token.text.lower() in stop_words_and:
                idx = token.i - sent.start
                if idx <= 0:
                    continue
                    
                sub_sent_1_tokens = sent[idx:]
                sub_sent_2_tokens = sent[:idx]
                
                sub_sentence_1 = sub_sent_1_tokens.text
                sub_sentence_2 = sub_sent_2_tokens.text
                
                test_1 = sent[idx-1:].text
                test_2 = sent[:idx-1].text
                
                bool_1 = (test_1 not in seen) and (sub_sentence_1 not in seen)
                bool_2 = (test_2 not in seen) and (sub_sentence_2 not in seen)

                # Check for length and EXTRA_SPLIT_SENTENCE words before appending
            
                
                # Conditions for sub_sentence_1
                if (bool_1 and search_production_word(sub_sentence_1) and 
                    not (
                        (len(sub_sent_1_tokens) == 2 and 
                         any(t.text.lower() in EXTRA_SPLIT_SENTENCE for t in sub_sent_1_tokens)) or
                        (len(sub_sent_1_tokens) == 3 and 
                         sum(t.text.lower() in EXTRA_SPLIT_SENTENCE for t in sub_sent_1_tokens) >= 2)
                    )):
                    seen.add(sub_sentence_1)
                    result.append(sub_sentence_1)

                # Conditions for sub_sentence_2
                if (bool_2 and search_production_word(sub_sentence_2) and 
                    not (
                        (len(sub_sent_2_tokens) == 2 and 
                         any(t.text.lower() in EXTRA_SPLIT_SENTENCE for t in sub_sent_2_tokens)) or
                        (len(sub_sent_2_tokens) == 3 and 
                         sum(t.text.lower() in EXTRA_SPLIT_SENTENCE for t in sub_sent_2_tokens) >= 2)
                    )):
                    seen.add(sub_sentence_2)
                    result.append(sub_sentence_2)
                    
    result.reverse()
    result.sort(key=lambda l: len(l))
    result = order_relevant(result, text=True)
    return result


def split_sentence_nlp(sentence):
    doc = nlp(sentence)
    result = []

    noun_list = [
        chunk for chunk in doc.noun_chunks
        if len(chunk) > 1
        and search_production_word(chunk.text)
        and not (
            (len(chunk) == 2 and 
             any(token.text.lower() in EXTRA_SPLIT_SENTENCE for token in chunk)) or
            (len(chunk) == 3 and 
             sum(token.text.lower() in EXTRA_SPLIT_SENTENCE for token in chunk) >= 2)
        )
    ]

    if (noun_list and doc.text not in [chunk.text for chunk in noun_list]) or (not noun_list):
        noun_list.append(doc)

    noun_list.reverse()
    noun_list.sort(key=lambda l: len(l))

    nc_list = []
    nc_raw_text = set()

    for nc in noun_list:
        try:
            if nc.text not in nc_raw_text:
                nc_list.append(nc)
                nc_raw_text.add(nc.text)

            np = doc[nc.root.left_edge.i : nc.root.right_edge.i + 1]
            if (len(np) > 1 
                and np.text not in nc_raw_text 
                and search_production_word(np.text) 
                and not (
                    (len(np) == 2 and 
                     any(token.text.lower() in EXTRA_SPLIT_SENTENCE for token in np)) or
                    (len(np) == 3 and 
                     sum(token.text.lower() in EXTRA_SPLIT_SENTENCE for token in np) >= 2)
                )):
                nc_list.append(np)
                nc_raw_text.add(np.text)

        except:
            continue

    nc_list.reverse()
    nc_list.sort(key=lambda l: len(l))

    return order_relevant(nc_list)
        
def order_relevant(list_sentences, text=False):
    relevant_nc = [filter_non_relevant(sentence,text) for sentence in list_sentences if filter_non_relevant(sentence,text)]
    priority = []
    non_priority = []
    for nc in relevant_nc:
        if 'production of' in nc and nc not in priority:#.text:
                priority.append(nc)
        elif nc not in non_priority:
                non_priority.append(nc)
        #print(nc_list,'deberia filtrar')
    return priority+non_priority


def filter_non_relevant(sentence,text=False):
    if text:
        sentence_list = sentence.split(' ')
    else:
        sentence_list = sentence.text.split(' ')
    clean_list = list(filter(lambda x: x != '', sentence_list))
    clean_sentence = ' '.join(clean_list)
    len_words = re.split(r',?\s+',clean_sentence)
    
    fake_product_pattern = r'^([Tt]he|[Aa]nd|[Aa])$'
    fake_product_bool = (len(len_words)==2 and (re.search(fake_product_pattern, len_words[0]) or '' in len_words or '.' in len_words or len_words[0] in stop_words_and))
    just_acid_bool = (len(len_words)==2 and clean_sentence.strip().rstrip()=='acid production')
    
    if len(len_words)!=1 and not fake_product_bool and not clean_sentence.strip(r':\s,.').endswith('production of'):
        if not just_acid_bool:
            #print('clean',clean_sentence)
            return(clean_sentence)
        
    else:
        return(None)
    
# Precompute frozen sets specific to clean_products
_CLEAN_PRODUCTS_SUFFIXES = ('ic', 'amino', 'ethyl', 'amil', 'tetramate',
                            'farnesyl', 'fatty','acid','human')
_CLEAN_PRODUCTS_ENDINGS = (
    'ing', 'ed', 'ity', 'ities', 'ible', '-fold', '%', 'ation', 
    'ive', 'ives', 'ively', 'able', 'omic', '-specific', 'units', '*', '†', '†,1',
    'tion', 'ment', 'ness', 'ary','ence','ent','bly','ade','wide','ant','metric',
    'ries', 'ties', 'ble', 'ity', 'ous', 'lar', 'cial', 'rial', 'tral', 'chiral',
    'tural','ical','ple','ory','tor','product')
_CLEAN_PRODUCTS_EXCEPTIONS = ('plastic', 'non-specific')
_CLEAN_PRODUCTS_BEFORE_LIST = frozenset({'and', 'cys'})  # Add other words you want to exclude


FAKE_PRODUCTS = [
    "towards","difficult","mixture","role","method","standpoint","certain",
    "several","future","overall","degree","suite","procedure","repertoire",
    "recovery","maincatalyst","strategy","discovery","performance",
    "superiorperformance","mechanism","response","interplay","spectrum",
    "candidate","technique","could","proxy","entire","academic","widespread",
    "healthy","costly","despite","dual","myriad","mainobstacle","bilevel",
    "heterotroph","organic","toolbox","wildtype","choice","data","toward",
    "length","survival","criterion","biology","immensevariety","latter",
    "shortcut","frontier","scaleup","bulkscale","grand","common","universal",
    "global","addedvalue","recalcitrance","storage","palette","mode",
    "productivity","machinery","attenuation","redox","phenotypic","fossil",
    "variety","vast","sensor","authentic","revision","scenario","dropin",
    "since","delivery","barrier","portfolio","disease","workhorse","result",
    "phenotype","biotic","mimicry","efficacy","unknown","covert",
    "gatekeeper","native","area","anthropogenic","formula","basic",
    "enantiomeric","problem","cheap","may","chapter","acidic","superior",
    "wealth","scope","benign","ton","juice","proven","meaningful","concise",
    "performer","rand","kind","division","resource","wastewater", "main","membrane"
] + ['cellulosic','pure','synthesis',
     'cell','food','raw','threat','trait','usage',
     'substrate','substance','virus','vitro']

def clean_products(product):
    unicos = set()
    new_products = list(filter(None, product))
    product = list(set(product))
    
    # Early exit for single-token cases
    if len(product) == 1:
        token_text = product[0].text.strip(GENERAL_STRIP)
        if token_text in _CLEAN_PRODUCTS_BEFORE_LIST or len(token_text) == 1 or token_text.isdigit() or token_text.endswith(('cellulosic', 'cellulolytic', 'ethyl','sis')) or token_text =='product' or token_text in(FAKE_PRODUCTS):
            return None

    #print(product)
    # Handle special suffix cases
    for n in product:
        text = n.text.strip(GENERAL_STRIP)
        #print(n)
        if n.text.endswith(_CLEAN_PRODUCTS_SUFFIXES) and not n.text.endswith(_CLEAN_PRODUCTS_EXCEPTIONS):
            #print(n)
            extra = ic_ending(n)
            if extra[0] and extra[1] not in new_products:
                new_products.append(extra[1])
            elif not extra[0] and extra[2] in new_products:
                new_products.remove(extra[2])
                if extra[1] in new_products:
                    new_products.remove(extra[1])
                    
    more_products = list(new_products)                     
    for n in new_products:
        text = n.text.strip(GENERAL_STRIP)
        #print(n)
        if n.text.endswith(_CLEAN_PRODUCTS_SUFFIXES) and not n.text.endswith(_CLEAN_PRODUCTS_EXCEPTIONS):
            #print(n)
            extra = ic_ending(n)
            if extra[0] and extra[1] not in more_products:
                more_products.append(extra[1])
            elif not extra[0] and extra[2] in more_products:
                more_products.remove(extra[2])
                if extra[1] in more_products:
                    more_products.remove(extra[1])
                    
                    
                    
    for n in more_products:
        text = n.text.strip(GENERAL_STRIP)
        if len(product) ==1 and not text.isnumeric() and text not in before_list:
            unicos.add(n)
        elif len(text) > 1 and text not in before_list:
            unicos.add(n)

    unicos = [n for n in unicos if not n.text.endswith(_CLEAN_PRODUCTS_ENDINGS)]
    unicos = [n for n in unicos if not n.text in FAKE_PRODUCTS]

    unicos.sort( key=lambda l: l.i)
    #print('unico',unicos)
    return [p for p in unicos if p.text != ''] if unicos else None

    
    
    
import logging

# Configure logging (you can set this up once at the start of your script)
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[
        logging.FileHandler('ic_ending_checks.log'),  # Log to file
        logging.StreamHandler()  # Also log to console
    ]
)

# Core word lists (add new words here)
_BASE_BEFORE = {
    'cellulosic', 'lignocellulosic', 'oleic', 'lignocellulolytic', 'polycyclic',
    'aromatic', 'amino', 'semialdehyde', 'tetramate', 'non-proteinogenic',
    'cellulolytic', 'aliphatic', 'phenolic', 'proteinogenic', 'farnesyl',
    'tetramate', 'ethyl', 'methyl', 'polyhydric', 'byciclic', 'fatty',
    'cyclic', 'macrocyclic','monocyclic','human','monocylic',
}

_BASE_AFTER = {
    'acid', 'alcohol', 'aldehyde', 'enzyme', 'glucoside', 'hydrolytic',
    'isoprenoid', 'steroid', 'macrolactams', 'isothiocyanate', 'ketone',
    'ester', 'peptide', 'itaconate', 'anthranilate', 'coumarin', 'acetate',
    'ivermectin', 'propionate', 'cinnamate', 'plipastatin', 'biofuel','fatty',
    'cellulose', 'valeric', 'and', 'aketide', 'hsaf','secol','naphthoic','biomass',
    'tripsin','saccharide'
}

_BASE_FAKE_BEFORE = {
    'kinetic', 'technoeconomic', 'proteomic', 'dynamic', 'transcriptomic',
    'genetic', 'synergistic', 'thermodynamic', 'specific', 'static', 'genomic',
    'economyc', 'optogenetic', 'economic', 'mesophilic', 'racemic', 'macroscopic',
    'acetogenic', 'problematic', 'probabilistic', 'microfluidic','catabolic','genic',
    'academic', 'meiotic','phylogenetic',
    
}

_BASE_FAKE_AFTER = {
    'model', 'modeling', 'of', 'response', 'control', 'tools', 'limitations',
    'and', 'with', 'approaches', 'framework', 'for', 'end', 'regulation',
    'solid', 'to', 'on', 'strategies', 'locus', 'viability', 'circuit',
    'network', 'basis', 'viability', 'modification', 'compunds', 'approach',
    'pathway', 'modules', 'mixture', 'manipulation', 'instability', 'phenotype',
    'bacteria', 'algorithm', 'superhost','production', 'modulation', 'synthesis',
    'production', 'biosynthesis','transformation','combined'
}

# Auto-generated plurals (don't edit these)
def _make_plurals(words):
    return {f"{word}s" for word in words if not word.endswith('s')}

# Final frozen sets for lookup
_BEFORE_TEXT = frozenset(_BASE_BEFORE)
_AFTER_TEXT = frozenset(_BASE_AFTER | _make_plurals(_BASE_AFTER))
_FAKE_BEFORE = frozenset(_BASE_FAKE_BEFORE)
_FAKE_AFTER = frozenset(_BASE_FAKE_AFTER | _make_plurals(_BASE_FAKE_AFTER))
_ANTIBIOTICS = ('icin', 'ycin', 'odin', 'idin', 'pentin', 'perlin', 'acin', 'atin',
                          'yxin','etin','aphen','peptin','tilin')


def ic_ending(result):
    try:
        doc = result.doc
        # BACKWARD CHECK: if "acid" and previous word ends in "ic"
        if result.text.lower() == 'acid' and result.i > 0:
            prev = doc[result.i - 1]
            if prev.text.lower().endswith(('ic','fatty','amino')):
                return (True, prev)  # backward match

        # FORWARD CHECK: existing logic
        if result.i + 1 < len(doc):
            extra = doc[result.i + 1]
            extra_text = extra.text.strip(GENERAL_STRIP)

            if extra_text in _AFTER_TEXT or result.text in _BEFORE_TEXT or result.text.endswith('oxy'):
                return (True, extra)
            if extra_text.endswith(tuple(_AFTER_TEXT)) or result.text.endswith(tuple(_BEFORE_TEXT)):
                return (True, extra)
            elif (result.text.endswith(('antibiotic','antiparasitic')) or result.text == 'anti-diabetic') and extra_text.endswith(_ANTIBIOTICS):
                return (True, extra)
            elif result.text.endswith('cyclic') and extra_text.endswith(('ene','ate','ide','lactams')):
                return (True, extra)
            elif extra_text in _FAKE_AFTER and result.text in _FAKE_BEFORE:
                return (False, extra, result)
            elif extra_text not in _FAKE_AFTER and result.text not in _FAKE_BEFORE:
                logging.info('--------CHECK REQUIRED--------')
                logging.info(f'Result: {result}, Extra: {extra}')
                logging.info(f'Full context: {doc}')
    except Exception as e:
        logging.error(f'Error processing result: {result}', exc_info=True)

    return (True, result)

                    
def detect_collocations(doc, parent_lemma,dep):
    """
    Create a generator of all occurrences of collocation in a document.
    
    Parameters:
    doc (spacy.tokens.doc.Doc): A spacy document.
    parent_lemma (str): The lemma of the parent token.
    dep (str): The dependency between the parent and child tokens.
    
    Returns:
    list[str]: A list of strings representing the collocations found in the document.
    """
    #print('entre a detect')
    for token in doc:
        #print(token.lemma_)
        if token.text == parent_lemma:
            #print(token.doc.text)
            product =  production_of([], token, dep, doc) #remove doc
            #print('producto collocations', product, len(product))
            # If there is product, check if there is more than one
            if len(product) and 'and' in doc.text:
                #print('More than one')
                more_product = x_and_y_production(set(product), doc, token)
                product += more_product
                return(clean_products(product))
                
            
            elif len(product):
                return(clean_products(product))

            
            else:
                product = x_production([], token, doc)
                #print(product,'mauau')
                if len(product) and 'and' in doc.text:
                    #print('More than one')
                    more_product = x_and_y_production(set(product), doc, token)
                    product += more_product
                    return(clean_products(product))

                #continue
                elif len(product):
                    return(clean_products(product))


    # Return an empty set if no collocations were found.
    return set()


def check_noun(np):
    """
    Filters out any noun phrases that do not contain the desired word.
    
    Parameters:
    np (spacy.tokens.span.Span): A noun phrase to check.
    
    Returns:
    tuple: A tuple containing the modified noun phrase as a string, and a list of present words. Returns (None, None) if the noun phrase is invalid.
    """
        
    if len(np)!=1:
            texto = np#.text#.lower()
            split_texto = set(texto.split(' '))
            present = words.intersection(split_texto) 
            #print('Primer filtro',texto,present)
            #print('Contiene:',present)
            if present:
                texto = texto.replace("'",'').replace(" )",")").replace(" its "," ").replace("poly (","poly(").replace('(or ','(or')
                for pres in present:
                    texto = replace_production_words(texto,pres)
                #texto = replace_words(texto)
                texto = texto.replace('a novel', '').split(' ')
                set_texto = set(texto)
                present = words.intersection(set_texto)
                #print(texto)
                # Use the `filter()` function to remove empty items from the list.
                texto = ' '.join(filter(None, texto))
                #print('Nuevo texto',texto,present)
                
                if present and len(set_texto)!=1:
                    #print('Elegi',texto,present,)
                    return(texto,list(present))

    return(None,None)


def compund_waterfall(product, n_children):
    """
    Finds the compound words in the children of the given node.
    
    Parameters:
    product (list): The list where the compound words will be stored.
    n_children (spacy.tokens.span.Span): The node whose children will be searched for compound words.
    
    Returns:
    list: The list with the compound words found in the children of the given node.
    """
    list_amod = ['amod', 'nummod', 'npadvmod', 'compound', 'nmod']
    size = len(list(n_children.children))
    while size > 0:
        for n_child in n_children.children:
            find = False
            if n_child.dep_ in list_amod:
                product.append(n_child)
                n_children = n_child
                size = len(list(n_children.children))
                find = True
                for sec_child in n_children.children:
                    if sec_child.dep_ in list_amod and sec_child.text.strip(',') not in before_list:
                        product.append(sec_child)
                break
        if not find:
            size = 0
    product.reverse()
    return product

def production_of(product, token, dep, doc):
    """
    Collect dependencies of a specified type that are children of the 'of' preposition.
    
    Parameters:
    product (list): A list of dependencies that have already been collected.
    token (spacy.tokens.token.Token): The token to search for 'of' preposition children.
    dep (str): The dependency type to collect.
    doc (spacy.tokens.doc.Doc): The document that contains the token.
    
    Returns:
    list: A list of dependencies of the specified type.
    """
    # Look for the "of" preposition in the children of the token.
    for child in token.children:
        if child.dep_ == 'prep' and child.lemma_ == 'of':
            #print('AAAH')
            # Collect the dependencies of the specified types.
            product = product_production_of(product, child, dep,token)
        #print(child)
    # If no dependencies were found, try looking for the "of" preposition in the
    # next token in the document.
    production_idx = list(doc).index(token)
    if not product and production_idx < len(doc) - 1:
        #print('Jemlou')
        test_of = doc[production_idx+1]
        if test_of.dep_ == 'prep' and test_of.lemma_ == 'of':
            # Collect the dependencies of the specified types.
            product = product_production_of(product, test_of, dep, token)
    return product


def product_production_of(product, child, dep, token):
    """
    Collects dependencies of the specified types from a given child node in a dependency tree.
    
    Parameters:
    product (list): A list of dependencies to be collected.
    child (spacy.tokens.token.Token): The child node to collect dependencies from.
    dep (str): The type of dependencies to collect.
    token (spacy.tokens.token.Token): The parent node of the child node.
    
    Returns:
    list: The updated list of dependencies.
    """
    #print('AJUA',child)
    # Collect dependencies of the specified types.
    production_of_types = ['pobj', 'punct', 'pcomp', 'propn', 'dep']
    for sec_child in child.children:
        #print(sec_child.text,sec_child.dep_)
        if str(sec_child.dep_) in production_of_types:
            # Add the dependency to the product list.
            product.append(sec_child)
            # Check for additional dependencies.
            product += check_amod(sec_child)
            for th_child in sec_child.children:
                # Check for additional dependencies.
                product += check_amod(th_child)
                if th_child.dep_ == dep:
                    # Add the dependency to the product list.
                    lastprod = product.pop(-1)
                    product.append(th_child)
                    product.append(lastprod)
                    # Check for additional dependencies.
                    product += check_amod(lastprod)
    more_types = ['appos','dep','nsubj']                
    for other_child in token.children:
        if str(other_child.dep_) in more_types:
            product.append(other_child)
            product += check_amod(other_child)
    return product



def check_amod(child):
    """
    Check for additional dependencies of certain types in the children of a given token.
    
    Parameters:
    child (spacy token): The token to check for dependencies.
    
    Returns:
    List[spacy token]: A list of dependencies found in the children of the given token.
    """
    # List of dependency types to check for.
    amod_types = ['amod','nummod','npadvmod','compound','nmod']
    # List of words to exclude.
    excluded_words = []
    product = []
    for sec_child in child.children:
        if sec_child.dep_ in amod_types and sec_child.text.strip(',') not in excluded_words:
            # Add the dependency to the product list.
            product.append(sec_child)
        # Check for additional dependencies.
            product = compund_waterfall(product, sec_child)
            
    return(product)



def x_and_y_production( tokens, doc, p_token):
    """
    Finds additional tokens that are linked to the given tokens using conjunctions (e.g., 'and').
    
    Parameters:
    tokens (list): A list of spaCy tokens.
    doc (spaCy doc): A spaCy document containing the tokens.
    p_token (spaCy token): A spaCy token that serves as a starting point for the search.
    
    Returns:
    list: A list of additional spaCy tokens that are linked to the given tokens using conjunctions.
    """
    x_and_y_words = ['conj', 'cc']
    product = []
    prev_products = [token.text for token in tokens]
    for token in tokens:
        #print(token,'tokensito')
        for child in token.children:
            #print(child.text, child.dep_)
            if str(child.dep_) in x_and_y_words and child.text not in before_list:
                product.append(child)
                #print(product)
                product += check_amod(child)
                #print('primer and',product)

        if len(product) and product[-1].text == 'and':
                #print(token.text,product,'JEMLOU')
                #print('texto',token.doc.text.split(' '))
                and_idx = token.doc.text.split(' ').index(token.text)
                try:
                    poss_prod = token.doc.text.split(' ')[and_idx+2]
                    #print(poss_prod)
                    if poss_prod not in prev_products:
                        #print('sigoo')
                        for token_2 in doc:
                            #print(token_2.text, token_2.tag_)
                            if token_2.text == poss_prod and (token_2.tag_ == 'CD' or token_2.text.endswith('in') or token_2.text.endswith('ol')):
                                product.append(token_2)
                                #print('esste and')
                                
                except:
                    continue
    if not product:
        for child in p_token.children:
            if str(child.dep_) in x_and_y_words and child.idx>p_token.idx:
                product.append(child)
    return(product)



def x_production(product, token, doc):
    """
    Collect dependencies of certain types that are related to the given token.
    This function searches for dependencies of certain types in the children and ancestors
    of the given token, and adds them to the `product` list. It also calls the `check_amod`
    function to collect additional dependencies of certain types.
    
    Args:
        product: A list of dependencies that have been collected so far.
        token: A token from a spacy document.
        doc: The spacy document that the token belongs to.
        
    Returns:
        A list of dependencies that have been collected.
    """
    dep_list = ['amod', 'nummod', 'det', 'dobj','punct','ROOT','nsubj','compound']

    for child in token.children:
        #enhanced riboflavin production 
        #print(child.text,'MAUAU',token,child.dep_)
        compound = ['succinate', 'enduracidin', 'mevalonate']
        #print(str(child.dep_) in dep_list)
        #print(str(child.dep_))
        #print(child.tag_ !='VBN' or child.text in compound)
        #print(str(child.text.strip(',') )not in before_list+after_list+['microbial'])
        if (str(child.dep_) in dep_list) and (child.tag_ !='VBN' or child.text in compound) and (str(child.text.strip(',')) not in before_list): #+after_list+['microbial']):
            product.append(child)
            #print('uno',product)
            product+= check_amod(child)
        elif child.dep_ == 'nmod' :
            product.append(child)
            #print('dos')
            product+= check_amod(child)
                    
        if str(child.dep_) == 'det'  and child.text == 'A':
            product.append(doc[child.i-1])
            #product+= check_amod(doc[child.i-1])

        else:
            continue
    #print(token,'TOKEN')   

    for child in token.ancestors:
        #print(child.dep_,child.text, 'jemlou ')#npadvmod
        if str(child.dep_) == 'prep'  and child.text == 'in':
            for sec_child in child.children:
                #print('ME ')
                if str(sec_child.dep_) in dep_list:
                    product.append(sec_child)
                    product+= check_amod(sec_child)
             #       product+= check_amod(sec_child)
            
        if str(child.dep_) == 'ROOT':
            product.append(child)
            product+= check_amod(child)
    return(product)


def process_sentences(text):
    text = process_raw_data(test_1)
    replaced_text = replace_production_words(text)
    replaced_text = re_pat.sub('', replaced_text)
    sub_sentences = split_sentence(replaced_text)
    trim_sub_senteces = []
    for sub_sentence in sub_sentences:
        if sub_sentence.split(' ')[0] in stop_words_and:
            new_sub = ' '.join(sub_sentence.split(' ')[1:])
            if new_sub not in trim_sub_senteces:
                               trim_sub_senteces.append(new_sub)
    relevant_info = []
    
    for sub_sentence in sub_sentences:
        new_sub_sentence = split_sentence_nlp(sub_sentence)
        if new_sub_sentence:
            for result in new_sub_sentence:
                texto, present = check_noun(result)
                if texto:
                    relevant_info.append(texto)
                    
def extract_product(texto, nlp=nlp):
    split_texto = set(texto.lower().split(' ')) 
    production_words = words.intersection(split_texto) 
    if production_words:
        texto = replace_production_words(texto)
        texto = re_pat.sub('', texto)

        production_word = list(production_words)[0]
        #print(production_word, production_words)
        product = detect_collocations(nlp(texto),production_word, "compound")
        #print('PRODUCT IS', product)
        return(product)
    
# === Precompiled regex patterns for big_file_split ===

# Sentence boundaries based on punctuation and word casing:
# 1. Sentences that end with a word, ')' or ']', and start with uppercase (to avoid splitting organism names like "E. coli")
# 2. Colons followed by a space (used in label-style sentences like "Methods: Example")
# 3. Sentences that end with lowercase and start with lowercase (to avoid splitting gene/protein names like "abc. def")
# 4. General case: if ending with ')' or ']' followed by any word character (safe fallback)
_RP_SPLIT_SENTENCES_PATTERN = re.compile(
    r'(?<=[\w\)\]])\.(?=\s+[A-Z]|\s?$)'     # Sentences that end with word and start with upper (to avoid organisms)
    r'|:\s'                                 # Colons followed by space (label-value)
    r'|(?<=[a-z])\.(?=\s+[a-z]|\s?$)'       # Sentences that end with lowercase and start with lowercase
    r'|(?<=[\)\]])\.(?=\s+\w|\s?$)'         # General: ). or ]. followed by word char
)

# Extra cleanup: handles malformed separators like " . " or ". ," in middle of sentence
_RP_EXTRA_SPLIT_PATTERN = re.compile(r'\s\.\s|\.\s,')


def big_file_split(sentence, limit_search=400):
    """
    Splits a large string into cleaner, approximate sentence segments.
    
    Parameters:
    sentence (str): Full input text to segment.
    limit_search (int): Optional search bound (currently unused).

    Returns:
    list: A list of cleaned sentence-like segments.
    """

    result = []

    if sentence:
        # Apply sentence splitting regex
        sentences = _RP_SPLIT_SENTENCES_PATTERN.split(sentence)

        # Remove empty trailing segment if split ends with dot
        if sentences and sentences[-1] == '':
            sentences = sentences[:-1]

        # Extra pass for edge punctuation cases
        clean_up = []
        for sent in sentences:
            clean_up.extend(_RP_EXTRA_SPLIT_PATTERN.split(sent))

        return clean_up

    return result



                        
def _get_product_mlp(raw_text):
    limit_search = 400
    text = process_raw_data(raw_text)
    #print(len(raw_text))
    #replaced_text = replace_production_words(text)
    replaced_text = text
    replaced_text = re_pat.sub('', replaced_text)

    #split sentences
    sentences = big_file_split(replaced_text)
    relevant_info = []
    
    for paragraph in sentences:
        production_words = search_production_word(paragraph)
        if production_words and len(relevant_info) < limit_search:
            seen_check_noun = set()
            seen_check_noun.add('organic synthesis')
            seen_check_noun.add('the production performance')
            seen_check_noun.add('production performance')


            
            paragraph =  replace_production_words(paragraph)
            sub_sentences = split_sentence(paragraph)
            
            
            if not sub_sentences:
                sub_sentences = [paragraph]
                
                
                
            for sub_sentence in sub_sentences:
                if sub_sentence not in relevant_info:
                    relevant_info.append(sub_sentence)
                    
                    
                    new_sub_sentence = split_sentence_nlp(sub_sentence)
                    
                    if new_sub_sentence:
                        for result in new_sub_sentence:
                            if result in seen_check_noun:
                                continue
                            #print('result',result)

                            seen_check_noun.add(result)
                            
                            texto, present = check_noun(result)
                            if texto:
                                search_text = texto.strip().strip('.') 
                                product =extract_product(search_text)
                                if product:
                                    #if 'cellulosic' in [p.text for p in product]:
                                        #print(product)
                                        #return product
                                    return(product)

                        
                elif len(relevant_info)>limit_search:
                    print('mauauu')
                    return(result)
                
                
# KEEP effective caches (proven structure)
product_cache = {}         # maps: noun phrase -> product
check_noun_cache = {}      # maps: result -> (texto, present)

# Initialize global hit/miss counters
cache_hits = {
    'check_noun_cache': 0,
    'product_cache': 0
}

cache_misses = {
    'check_noun_cache': 0,
    'product_cache': 0
}

def get_product_mlp_cache_track(raw_text):
    limit_search = 400
    text = process_raw_data(raw_text)
    replaced_text = re_pat.sub('', text)
    sentences = big_file_split(replaced_text)
    relevant_info = []
    
    for paragraph in sentences:
        production_words = search_production_word(paragraph)
        if production_words and len(relevant_info) < limit_search:
            seen_check_noun = {
                'organic synthesis', 
                'the production performance', 
                'production performance'
            }
            
            paragraph = replace_production_words(paragraph)
            sub_sentences = split_sentence(paragraph) or [paragraph]
            
            for sub_sentence in sub_sentences:
                if sub_sentence not in relevant_info:
                    relevant_info.append(sub_sentence)
                    
                    new_sub_sentence = split_sentence_nlp(sub_sentence)
                    if not new_sub_sentence:
                        continue
                    
                    product_found = None
                    for result in new_sub_sentence:
                        if result in seen_check_noun:
                            continue
                        seen_check_noun.add(result)
                        
                        # --- 1. Check/update noun cache ---
                        if result in check_noun_cache:
                            cache_hits['check_noun_cache'] += 1
                            texto, present = check_noun_cache[result]
                            
                            # EARLY SKIP: If we know it's invalid from previous processing
                            if not present or not texto:
                                continue
                                
                            search_text = texto.strip().strip('.')
                            
                            # --- 2. Check product cache ---
                            if search_text in product_cache:
                                cache_hits['product_cache'] += 1
                                product = product_cache[search_text]
                                if product:
                                    product_found = product
                                    break  # Found product!
                                else:
                                    continue  # Known to not yield product
                            else:
                                # Need to extract product
                                cache_misses['product_cache'] += 1
                                product = extract_product(search_text)
                                product_cache[search_text] = product
                                if product:
                                    product_found = product
                                    break
                                else:
                                    continue
                                
                        else:
                            cache_misses['check_noun_cache'] += 1
                            texto, present = check_noun(result)
                            check_noun_cache[result] = (texto, present)
                            
                            if not present or not texto:
                                continue
                                
                            search_text = texto.strip().strip('.')
                            
                            # --- 2. Check/update product cache ---
                            if search_text in product_cache:
                                cache_hits['product_cache'] += 1
                                product = product_cache[search_text]
                                if product:
                                    product_found = product
                                    break
                                else:
                                    continue
                            else:
                                cache_misses['product_cache'] += 1
                                product = extract_product(search_text)
                                product_cache[search_text] = product
                                if product:
                                    product_found = product
                                    break
                                else:
                                    continue
                    
                    if product_found:
                        return product_found
                
                elif len(relevant_info) > limit_search:
                    return None
    
    return None

def print_cache_stats():
    total_hits = sum(cache_hits.values())
    total_misses = sum(cache_misses.values())
    total = total_hits + total_misses
    hit_rate = (total_hits / total) * 100 if total > 0 else 0
    
    print(f"Overall cache hit rate: {hit_rate:.1f}%")
    for cache_name in cache_hits:
        hits = cache_hits[cache_name]
        misses = cache_misses[cache_name]
        total_ops = hits + misses
        rate = (hits / total_ops) * 100 if total_ops > 0 else 0
        print(f"{cache_name}: {hits}/{total_ops} ({rate:.1f}% hit rate)")