# TODO Improve the removal of adjectives, verbs, etc. 
import spacy
import numpy as np
from nltk import PorterStemmer, WordNetLemmatizer, tokenize
from nltk.corpus import stopwords,verbnet
from nltk.corpus import wordnet




stop_words = set(stopwords.words('english'))

adjective_synsets = list(wordnet.all_synsets('a'))
adjectives_adverbs = set()
for synset in adjective_synsets:
    for lemma in synset.lemmas():
        adjectives_adverbs.add(lemma.name().replace('_',' '))

adverb_synsets = list(wordnet.all_synsets('r'))
for synset in adverb_synsets:
    for lemma in synset.lemmas():
        adjectives_adverbs.add(lemma.name().replace('_',' '))
numeric_tokens = {n for n in adjectives_adverbs if n.isnumeric()}
adjectives_adverbs -= numeric_tokens

        
nouns_list = set()
noun_synsets = list(wordnet.all_synsets('n'))
for synset in noun_synsets:
    for lemma in synset.lemmas():
        nouns_list.add(lemma.name().replace('_', ' '))
        
        
verb_classes = verbnet.classids()

# Get a list of all the verbs in the verbnet corpus
verbs = []
for verb_class in verb_classes:
    for lemma in verbnet.lemmas(verb_class):
        verbs.append(lemma)

    # Create a set of the unique verbs
verb_set = set(verbs)
        
def get_variations_nlp_tagger(text, nlp=spacy.load('en_core_web_sm')):

    excluded_labels = ['$']

    # Parse the "text" string to identify the individual words and their part-of-speech labels
    doc = nlp(text)
    
    # Create a dictionary to store variations of the words 
    variations = {label: [] for label in nlp.get_pipe("tagger").labels if label not in excluded_labels}
    
    # Iterate over the words in the parsed "text" string
    for token in doc:
        # Iterate over the labels in the part-of-speech tagger
        for label in nlp.get_pipe("tagger").labels:
            # If the word has a variation with the current label, add it to the variations dictionary
            if token._.inflect(label) and label not in excluded_labels:
                variations[label].append(token._.inflect(label))

    # Remove empty entries from the variations dictionary
    variations = {k: v for k, v in variations.items() if len(v)}
    return(variations)

def classify_variations(variations):
    
    # Collect verb variations from the variations dictionary
    verbs = []
    for label in ['VBD', 'VBG', 'VBN', 'VB', 'VBP', 'VBZ']:
        verbs.extend(variations[label])

    # Collect adjective variations from the variations dictionary
    adjectives = []
    for label in ['JJ', 'JJS', 'JJR']:
        adjectives.extend(variations[label])

    # Collect noun variations from the variations dictionary
    nouns = []
    for label in ['NN', 'NNS']:
        nouns.extend(variations[label])

    # Collect adverb variations from the variations dictionary
    adverbs = []
    for label in ['RB', 'RBS', 'RBR']:
        adverbs.extend(variations[label])

    # Create a list of phrases combining an adverb with a verb
    adv_verb = [f'{start} {end}' for start in adverbs for end in verbs]

    # Create a list of phrases combining an adjective with a noun
    adj_noun = [f'{start} {end}' for start in adjectives for end in nouns]
    
    return(verbs, adjectives, nouns, adverbs,adv_verb, adj_noun)

def get_wordnet_lemmas():
    # Create a list of all verb,adverb and adjective lemmas in WordNet
    complete_verbs = []
    for synset in wordnet.all_synsets(wordnet.VERB):
        for lemma in synset.lemmas():
            complete_verbs.append(lemma.name())
    complete_verbs = list(set(complete_verbs))

    # Create a list of all adjective lemmas in WordNet
    adjectives = []
    for synset in wordnet.all_synsets(wordnet.ADJ):
        for lemma in synset.lemmas():
            adjectives.append(lemma.name())
    adjectives = list(set(adjectives))

    # Create a list of all adverb lemmas in WordNet
    adverbs = []
    for synset in wordnet.all_synsets(wordnet.ADV):
        for lemma in synset.lemmas():
            adverbs.append(lemma.name())
    adverbs = list(set(adverbs))
    
    return(complete_verbs,adjectives,adverbs)

def similar_words(your_word, number_syn=20):
    nlp = spacy.load('en_core_web_lg')

    '''https://stackoverflow.com/questions/54717449/mapping-word-vector-to-the-most-similar-closest-word-using-spacy'''
    ms = nlp.vocab.vectors.most_similar(
        np.asarray([nlp.vocab.vectors[nlp.vocab.strings[your_word]]]), n=number_syn)
    s_words = [nlp.vocab.strings[w] for w in ms[0][0]]
    distances = ms[2]
    return(s_words)

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

def remove_stopwords(text):
    words = text.split()
    filtered_words = [word for word in words if word.lower() not in stop_words]
    return ' '.join(filtered_words)

def remove_verbs(text, case_relevant = False):

    
    words = text.split()
    if not case_relevant:
        filtered_words = [word for word in words if word.lower() not in verb_set]
    else:
        filtered_words = [word for word in words if word not in stop_words]

    return ' '.join(filtered_words)

def remove_adj_adv(text):

    words = text.split()
    filtered_words = [word for word in words if word not in adjectives_adverbs]
    
    return ' '.join(filtered_words)

def remove_noun(text):

    words = text.split()
    filtered_words = [word for word in words if word not in nouns_list]
    
    return ' '.join(filtered_words)

def normalizar(x):
    porter = PorterStemmer()
    lemm = WordNetLemmatizer()
    
    """Make words like Enhanced or Enhancing the same"""
    words = tokenize.word_tokenize(x)
    new = [porter.stem(t) for t in words]
    new = ' '.join(new)
    return(new)


def normalize_org(x):
    """Avoid letting organisms mess with the pondering"""
    organisms = ['escherichia', 'coli', 'cerevisiae', 'saccharomyces',
                 'pseudomonas', 'halomona', 'yeast', 'bacillus',
                'subtilis', 'clostridium', 'thermocellum','cyanobacteria',
                'meningoseptica','plant','human','thermophillus','spp',
                'synechococcus','consortia','streptomyces',
                 'consortium']

    x = x.lower()
    for organism in organisms:
        x = x.replace(organism, '')


    return(x)

def normalize_other(x):
    """Avoid letting organisms mess with the pondering"""
    organisms = ['not', 'available','saccharoperbutylacetonicum',
                'asexual','reproduction','estrogen',
                'sulfur','biohydrogen',
                'lactic','biogas','straw','thermophillic',]
    x = x.lower()
    for organism in organisms:
        x = x.replace(organism, '')

    return(x)


def normalize_chemical(text):
    import re

    # Define the pattern to match words ending with specified suffixes
    pattern = r'\b\w*(ene|ide|ane|ine|ite|enol|olic|aryl|ose|diol|oxyl|syl|nosid|lactone|anol|cyanin|anin|celulos|anin)\b'
    
    # Define the replacement function
    def replace_func(match):
        # Get the matched word
        word = match.group(0)
        # Find the ending part matched by the pattern
        ending = match.group(1)
        # Replace the ending with 'pretty'
        return word[:-len(ending)] + 'chemical'
    
    # Perform the replacement using re.sub
    result = re.sub(pattern, replace_func, text)
    return result
