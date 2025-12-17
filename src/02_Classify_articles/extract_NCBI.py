from Bio import Entrez
from pandas import DataFrame, read_json
from math import ceil
from urllib.error import HTTPError
from file_management import get_files_dir

Entrez.email = 'elisa.m.zavala@ntnu.no'
def term_OR_ncbi(terms, term_sp = '[TIAB]', operator='OR'):
    '''This function takes a list of terms and a boolean operator as input and returns a string in the format required by the NCBI Entrez API to search for articles with any of the terms in the fields specified in term_sp. The term_sp parameter specifies which fields to search in and can be set to '[TIAB]' to search in the title or abstract. The operator parameter specifies how to join the terms, with 'OR' as the default.'''
    half_term = ['('+string+term_sp+')' for string in terms]
    operator = ' '+operator+' '
    term = operator.join(half_term)
    
    return(term)

def join_term(terms, operator = 'AND'):
    '''This function is similar to term_OR_ncbi() but the operator parameter is set to 'AND' by default, so the terms are joined with 'AND' rather than 'OR'.'''
    term = term_OR_ncbi(terms,'', operator)
    
    return(term)


def search_entrez(query, retmax=12000):
    ''' This function performs a search using the NCBI Entrez API and returns the search results. The query parameter is the search term and the retmax parameter specifies the maximum number of results to return. The default value for retmax is 9999. If more results are found, a warning message is printed. If no results are found, a message is printed indicating that no findings were found for the query.'''
    #print(retmax)
    handle = Entrez.esearch(db='pubmed', 
                            sort='relevance', 
                            retmax = retmax,
                            retmode='xml', 
                            term=query)
    results = Entrez.read(handle)
    if int(results['Count']) > int(retmax):
        print('Warning! \nTake into account that retmax set to 9999 and you found ', results['Count'],'articles')
        
    elif int(results['Count']) == 0:
        print('No findings for the term:',query[0:100],'...')
    return results
    
    
def fetch_record(pm_ids):
    '''This function retrieves the records for a list of PubMed IDs using the NCBI Entrez API. The pm_ids parameter is a list of PubMed IDs. The function returns the records.'''
    
    record = None
    post_results = Entrez.read(Entrez.epost("pubmed", id=",".join(pm_ids)))
    webenv = post_results["WebEnv"]
    query_key = post_results["QueryKey"]
    try:
        fetch_handle = Entrez.efetch(db='pubmed', webenv=webenv, query_key=query_key,
                                 rettype='xml', retmode='text')
        
        try:
            record = Entrez.read(fetch_handle)
            fetch_handle.close()
        except:
            print("failed read()")
            
    except:
        print("Failed batch")
    
    return record
        
    
def fetch_PMC_record(pm_ids, scrapy_url=False):
    '''Gets the record related to a list of pubmed IDs through the efetch tool from ENTREZ. It returns the read record.'''
    attempt = 1
    record = None
    post_results = Entrez.read(Entrez.epost("pmc", id=",".join(pm_ids)))
    webenv = post_results["WebEnv"]
    query_key = post_results["QueryKey"]
    
    while attempt <= 3:
        try:
            fetch_handle = Entrez.efetch(db='pmc', webenv=webenv, query_key=query_key,
                                     rettype='xml', retmode='text')
            if scrapy_url:
                return(fetch_handle.url)
            
            record = fetch_handle.read()
            fetch_handle.close()
            return record   
            #try:
             #   record = Entrez.read(fetch_handle)
              #  fetch_handle.close()
            #except:
             #   print("failed read()")


        except:
            print("Failed batch")
            attempt +=1


file='list_journals_avoid.json'
base, input_dir, output_dir = get_files_dir()
input_dir = input_dir /"Journals"/"Avoid"
avoid_journals = read_json(input_dir / file)

def build_journal_query(avoid_journals, positive_set=True):
    operator = 'NOT' if positive_set else 'AND'

    journal_expressions = []
    for column in avoid_journals:
        avoid_journ = avoid_journals[column].dropna()
        if not avoid_journ.empty:
            neg_exp = ' OR '.join([f'({journal}[JOUR])' for journal in avoid_journ])
            neg_exp = f' {operator} ({neg_exp})'
            journal_expressions.append(neg_exp)

    return journal_expressions


def remove_journals(full_term, journal_ids, positive_set=True):
    articles_ids = []
    for list_journals in journal_ids:
        art_ids = search_entrez(full_term + list_journals)
        art_ids = art_ids['IdList']
        articles_ids.append(set(art_ids))

    if positive_set and articles_ids:
        id_list = set.intersection(*articles_ids)
    elif articles_ids:
        id_list = set.union(*articles_ids)
    else:
        id_list = set()

    return list(id_list)

    

def extract_ids(subsection):
    '''This function extracts the PubMed ID, PubMed Central ID, and DOI for an article from a subsection of the NCBI Entrez API results. The subsection parameter is a subsection of the results containing information about a single article. The function returns a tuple with the PubMed ID, PubMed Central ID, and DOI.
    '''
    pubmed_id = 'None'
    pmc_id = 'None'
    DOI = 'None'
    for articleid in subsection['PubmedData']['ArticleIdList']:
        idtype = articleid.attributes['IdType'].lower()
        if idtype == 'pmc':
            pmc_id = articleid.lstrip('PMC')
        elif idtype == 'pubmed':
            pubmed_id = articleid
        elif idtype == 'doi':
            DOI = articleid
            
    return(pubmed_id, pmc_id, DOI)





import csv
import time
import logging
from collections import defaultdict

# ----------------------------
# Setup logging
# ----------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s - %(message)s",
    force=True
)

# ----------------------------
# Helper: Write articles to CSV
# ----------------------------
def write_articles_to_csv(year, article_ids):
    filename = f"article_ids_{year}.csv"
    logging.info(f"Writing {len(article_ids)} IDs to {filename}")
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["ArticleID"])
        for aid in article_ids:
            writer.writerow([aid])

# ----------------------------
# Helper: Extract year from search term
# ----------------------------
def extract_year_from_term(term):
    try:
        date = term.split('AND (')[-1].split('[dp]')[0].strip()
        year = int(date[:4])
        return year, date
    except Exception as e:
        logging.error(f"Failed to extract year from term: {term} — {e}")
        return None, None

# ----------------------------
# Main: Process all search terms
# ----------------------------
def process_terms(full_term_w_dates, journal_ids, start_year=2000):
    articles_by_year = defaultdict(list)
    current_year = start_year
    years_processed = 0
    year_start_time = time.time()


    for i, full_term in enumerate(full_term_w_dates):
        year, date = extract_year_from_term(full_term)
        if year is None:
            continue

        logging.info(date)

        if year > current_year:
            elapsed = time.time() - year_start_time
            logging.info(f"Time taken to fetch data for {current_year}: {elapsed:.2f} seconds")

            if articles_by_year[current_year]:
                write_articles_to_csv(current_year, articles_by_year[current_year])
                articles_by_year[current_year].clear()

            years_processed += 1
            current_year = year
            logging.info(f"Processing year {year}")
            year_start_time = time.time()

            if years_processed % 5 == 0:
                logging.info("Throttling to avoid server block — sleeping for 60 seconds...")
                time.sleep(60)

        article_ids = remove_journals(full_term, journal_ids)
        articles_by_year[year].extend(article_ids)
        logging.info(f"  -> Retrieved {len(article_ids)} IDs for period {date}")

    # Final flush
    elapsed = time.time() - year_start_time
    logging.info(f"Time taken to fetch data for {current_year}: {elapsed:.2f} seconds")

    if articles_by_year[current_year]:
        write_articles_to_csv(current_year, articles_by_year[current_year])
        articles_by_year[current_year].clear()
        

def extract_year(subsection):
    '''This function extracts the year of publication for an article from a subsection of the NCBI Entrez API results. The subsection parameter is a subsection of the results containing information about a single article. The function returns the year of publication as a string. If the year cannot be extracted, the function returns 'None'.
    '''
    try:
        year = subsection['Journal']['JournalIssue']['PubDate']
        if 'Year' in year.keys():
                year = year['Year']
        elif 'MedlineDate' in year.keys():
                year = year['MedlineDate'].split(' ')[0]
        else:                
            try:
                year = subsection['ArticleDate'][0]['Year']
            except:
                prin('fail :(')
        return(year)
    except:
        try:
            year = subsection['ELocationID'][0].split('.')[2]
            if int(year) < 1910 or int(year)>2100:
                year = None
            return(year)
        except:
                print('failed extract_year()')

def extract_relevant_info(info, pm_id, file, title, abstract, journal, year, art_type ):
    '''This function extracts the title, abstract, journal, year of publication, PubMed ID, PubMed Central ID, and DOI for an article from a subsection of the NCBI Entrez API results. The info parameter is a subsection of the results containing information about a single article, pm_id is the PubMed ID for the article, file is the file to write the extracted information to, title, abstract, journal, and year are variables to store the extracted information, and art_type is a string to store the type of publication (e.g. "Journal Article"). The function writes the extracted information to the specified file with '\t' as the separator.
'''
    
    subsection = info['MedlineCitation']['Article']
    
    file_object = open(file, 'a')
    
    if info:
        try:
            title = subsection['ArticleTitle']
            if not abstract:
                abstract = subsection['Abstract']['AbstractText'][0]
            else:
                try:
                    abstract = subsection['Abstract']['AbstractText'][0]
                except:
                    abstract = 'NOT AVAILABLE'
                    print('no abstract',pm_id)
            journal = subsection['Journal']['Title']
            year = extract_year(subsection)
            pubmed, pmc, doi = extract_ids(info)
            try:
                for publicationtype in subsection['PublicationTypeList']:
                    art_type += publicationtype+','
            except:
                print('Publication Type not found')
                art_type = 'Not found'
                
            author_list = []
            for author in subsection['AuthorList']:
                author_list.append('[ForeName:'+author['ForeName']+',LastName:'+author['LastName']+']')
            if title and abstract and journal and year:

                relevant_info = '\t'.join([pm_id, title, abstract,
                                           journal, year, pmc,
                                           doi, art_type,' '.join(author_list)])+'\n'
                file_object.write(relevant_info)

        except:
            print("Failed to extract relevant info: ", pm_id)


def collect_relevant_info(articles_ids, file, batches_len=499, title=None, abstract=None, journal=None, year=None, art_type=''):
    ''' This function collects the title, abstract, journal, year of publication, PubMed ID, PubMed Central ID, and DOI for a list of PubMed IDs using the NCBI Entrez API. The articles_ids parameter is a list of PubMed IDs, file is the file to write the collected information to, batches_len is the number of IDs to include in each batch when making requests to the NCBI Entrez API (default is 499), and title, abstract, journal, year, and art_type are variables to store the collected information. The function writes the collected information to the specified file with '\t' as the separator.
    '''
    
    batched_art_ids = [articles_ids[i * batches_len:(i + 1) * batches_len] 
                   for i in range((len(articles_ids) + batches_len- 1) // batches_len )]
    
    out_handle = open(file, "w") 
    out_handle.write('PM_ID\tTitle\tAbstract\tJournal\tYear\tPMC_ID\tDOI\tType\tAuthor\n')
    out_handle.close()
    n=0
    for pm_ids in batched_art_ids:
        
        attempt = 1
        while attempt <= 3:
            try:
                info = fetch_record(pm_ids)
                for record in info['PubmedArticle']:
                    pm_id = record['MedlineCitation']['PMID']
                    retrieved_info = extract_relevant_info(record, pm_id, file, title, abstract, journal, year, art_type)
                break
                
                
            except HTTPError as err:
                if 500 <= err.code <= 599:
                    print("Received error from server %s" % err)
                    print("Attempt %i of 3" % attempt)
                    attempt += 1
                    time.sleep(15)
                else:
                    raise

            except:
                attempt += 1
                print('Error not from server, attempt #: ', attempt)
            
        n+=1
    print('Information saved in', file)
    
