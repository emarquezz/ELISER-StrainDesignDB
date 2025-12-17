import sys
sys.path.append('../Classify_articles/')


import pandas as pd
import numpy as np

from extract_NCBI import *

# scrape webpage
import scrapy
from scrapy.crawler import CrawlerRunner
# text cleaning
import re
# Reactor restart
from crochet import setup, wait_for
setup()


import collections
import re


class FormatOutput(object):
    def process_item(self, item, spider):
        """text processing"""
        for section in item.keys():
            for subsection in item[section].keys():
                raw_text = item[section][subsection]
                joined_raw_text = raw_text[0]+' '+''.join(raw_text[1:])
                processed_line = self.__remove_things__(joined_raw_text)
                item[section][subsection] = processed_line
        return item

    def __remove_things__(self, raw_text):
        pattern_references= re.compile("\s\[(\d+,?\s?)+\]")
        pattern_fig_tables = re.compile("biorxiv;[a-zA-Z0-9\/]*\s\w?\d:")
        result = re.sub(pattern_references, '', raw_text)
        result2 = re.sub(pattern_fig_tables, '', result)
        final_text = re.sub('\s+',' ', result2)

        return(final_text)
    
# ############################ #
#              PMC             #
# ############################ #
from lxml import etree
import logging
import pandas as pd

class PMC_Spider(scrapy.Spider):
    """scrape PMC files"""
    name = "PMC_Spider"
    start_urls = [
        'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&webenv=MCID_6478a0bbcf3e2544e246ab08&query_key=1&rettype=xml&retmode=text&tool=biopython&email=elisa.m.zavala%40ntnu.no',
    ]
    custom_settings = {
        'ITEM_PIPELINES': {
            '__main__.FormatOutput': 1
        },
        'FEEDS': {
            'quotes_2.csv': {
                'format': 'csv',
                'overwrite': True
            }
        }
    }
    logging.info(f"Article path: {start_urls}")


    def parse(self, response):

        # Parse with lxml
        tree = etree.fromstring(response.body)

        # Namespace-agnostic article path
        articles = tree.xpath('//*[local-name()="pmc-articleset"]/*[local-name()="article"]')
        articulos = {}
        logging.info(f"Found {len(articles)} articles")

        for n, article_body in enumerate(articles):
            # More precise PMID extraction targeting exactly the element we want
            pmid = article_body.xpath('.//*[local-name()="article-id"][@pub-id-type="pmid"]/text()')

            if not pmid:
                logging.warning(f"No PMID found for article {n}")
                continue  # Skip if no PMID found

            pmid = str(pmid[0])

            articulos[pmid] = {}
            articulos[pmid]['Text'] = {}
            articulos[pmid]['Org_Gene'] = {}

            # Process sections
            sections = article_body.xpath('.//*[local-name()="body"]/*[local-name()="sec"]')
            for m, section in enumerate(sections):
                all_info = section.xpath('.//text()')
                p_org_gene = section.xpath('.//*[local-name()="italic"]/text()')

                articulos[pmid]['Text']['Section_'+str(m)] = all_info
                articulos[pmid]['Org_Gene']['Section_'+str(m)] = p_org_gene

            # Process paragraphs directly under body
            missing_data = article_body.xpath('.//*[local-name()="body"]/*[local-name()="p"]')
            if len(articulos[pmid]['Text'].keys()) == 2:
                for m, section in enumerate(missing_data):
                    all_info = section.xpath('.//text()')
                    p_org_gene = section.xpath('.//*[local-name()="italic"]/text()')

                    articulos[pmid]['Text']['Section_e_'+str(m)] = all_info
                    articulos[pmid]['Org_Gene']['Section_e_'+str(m)] = p_org_gene

        # Save to JSON
        pd.DataFrame(articulos).to_json('scraping_info.json')
        yield articulos
            
        



@wait_for(100)
def run_PMC_Spider(url):
    """run spider with PMC_Spider"""
    PMC_Spider.start_urls = [ url ]
    crawler = CrawlerRunner()
    d = crawler.crawl(PMC_Spider)
    return d

def unroll_sections(dictionary):
    full_text = []
    for sections in dictionary.values():
                        #print(section_dict.values())
                        full_text.extend(sections)
    full_text = ' '.join(full_text)
    return(full_text)

def get_PMC_full_text_url(url, sections=False, prob_organism=False):
    run_PMC_Spider(url)
    text_obtained = pd.read_json('scraping_info.json',convert_axes=False)
    text_obtained = text_obtained.applymap(lambda x: np.nan if isinstance(x, dict) and not x else x)
    text_obtained = text_obtained.T 
    
    if not sections:
        text_obtained.Text = text_obtained.Text.dropna().apply(unroll_sections)
        
    if not prob_organism:
        return (text_obtained.Text)
    
    return(text_obtained)

import logging

# ----------------------------
# Setup logging
# ----------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s - %(message)s",
    force=True
)

def get_PMC_scrappy_url(articles_ids, batches_len=500, scrapy_url=False):
    urls_to_search = {}
    batched_art_ids = [
        articles_ids[i * batches_len:(i + 1) * batches_len]
        for i in range((len(articles_ids) + batches_len - 1) // batches_len)
    ]

    for n, pmc_ids in enumerate(batched_art_ids):
        attempt = 1
        while attempt <= 3:
            try:
                logging.info(f"Fetching batch {n+1}/{len(batched_art_ids)} (Attempt {attempt})")
                info = fetch_PMC_record(pmc_ids, scrapy_url)
                urls_to_search[n] = info
                break
            except Exception as e:
                logging.warning(f"Attempt {attempt} failed for batch {n+1}: {e}")
                attempt += 1
                time.sleep(1)  # Optional: wait before retrying
        else:
            logging.error(f"All attempts failed for batch {n+1}")
    return urls_to_search


def get_PMC_full_text(pmc_ids, sections=False, prob_organism=False):
    
    multiple_urls = get_PMC_scrappy_url(pmc_ids,scrapy_url=True)
    
    text_batches = []
    for url in multiple_urls.values():
        text_obtained = get_PMC_full_text_url(url, sections, prob_organism)
        text_obtained.index = text_obtained.index.astype(int)
        text_batches.append(text_obtained)
       
    full_text = pd.concat(text_batches).dropna()
    return(full_text)


    
# ############################ #
#          Biorxiv             #
# ############################ #

#Biorxiv_url = 'https://www.biorxiv.org/content/biorxiv/early/2018/12/13/496497.full.pdf'
#run_BiorxivSpider([Biorxiv_url])
#pd.read_json('./Biorxiv.json')

def remake_Biorxiv_urls(urls):
    new_urls = []
    for url in urls:
        url = url.split('.full')[0]
        new_url = f'{url}.source.xml'
        new_urls.append(new_url)

    return(new_urls)

class BiorxivSpider(scrapy.Spider):
    name = "BiorxivSpider"
    start_urls = [
        'https://www.biorxiv.org/content/biorxiv/early/2017/11/06/215012.source.xml',
        # Add more Biorxiv
    ]
    custom_settings = {
        'ITEM_PIPELINES': {
            '__main__.FormatOutput': 1
        },
        'FEEDS': {
            'Biorxiv.json': {
                'format': 'json',
                'overwrite': True
            }
        }
    }

    def parse(self, response):
        article = {}
        body_sections = response.xpath('/article/body//sec')
        abstract = response.xpath('/article//abstract//text()').extract()
        article['Abstract'] = {'main_text':abstract}
        for section in body_sections:
            parent = section.xpath('..')
            parent_name = parent.xpath('name()').get()
            sub_name = section.xpath('.//text()').get()
            #print(f"{parent_name}: {sub_name}")
            raw_text = section.xpath('.//text()').extract()
            #print([texto_nuevo_lindo])
            if parent_name =='body':
                article[sub_name] = {'main_text':raw_text}
                parent_sub_name = sub_name
            else:
                article[parent_sub_name][sub_name] = raw_text
        yield(article)

@wait_for(100)
def run_BiorxivSpider(urls):
    """run spider with MJKQuotesToCsv"""
    new_urls = remake_Biorxiv_urls(urls)
    BiorxivSpider.start_urls = new_urls
    crawler = CrawlerRunner()
    d = crawler.crawl(BiorxivSpider)
    return d

# ############################ #
#          Frontiers           #
# ############################ #

#Frontiers_url = 'https://www.frontiersin.org/articles/10.3389/fbioe.2013.00007/pdf'
#run_FrontiersSpider([Frontiers_url])

def remake_Frontiers_urls(urls):
    new_urls = []
    for url in urls:
        url = url.split('/pdf')[0]
        new_url = f'{url}/xml/nlm'
        new_urls.append(new_url)

    return(new_urls)

class FrontiersSpider(scrapy.Spider):
    name = "FrontiersSpider"
    start_urls = [
        'https://www.frontiersin.org/articles/10.3389/fbioe.2013.00007/xml/nlm',
        # Add more Springer Link article URLs here
    ]
    custom_settings = {
        'ITEM_PIPELINES': {
            '__main__.FormatOutput': 1
        },
        'FEEDS': {
            'Frontiers.json': {
                'format': 'json',
                'overwrite': True
            }
        }
    }

    def parse(self, response):
        article = {}
        body_sections = response.xpath('/article/body//sec')
        abstract = response.xpath('/article//abstract//text()').extract()
        article['Abstract'] = {'main_text':abstract}
        for section in body_sections:
            parent = section.xpath('..')
            parent_name = parent.xpath('name()').get()
            #print(parent_name)
            sub_name = section.xpath('./title//text()').getall()
            sub_name = ' '.join(sub_name)
            raw_text = section.xpath('.//text()').extract()
            #print([texto_nuevo_lindo])
            #print(f"{parent_name}: {sub_name}")
            if parent_name =='body':
                article[sub_name] = {'main_text':raw_text}
                parent_sub_name = sub_name
            else:
                article[parent_sub_name][sub_name] = raw_text
        yield(article)

        


@wait_for(100)
def run_FrontiersSpider(urls):
    """run spider with MJKQuotesToCsv"""
    new_urls = remake_Frontiers_urls(urls)
    FrontiersSpider.start_urls = new_urls
    crawler = CrawlerRunner()
    d = crawler.crawl(FrontiersSpider)
    return d


# ############################ #
#            PlosOne           #
# ############################ #

#PlosOne_url = 'https://journals.plos.org/ploscompbiol/article/file?id=10.1371/journal.pcbi.1002460&type=printable'
#run_PlosOneSpider([PlosOne_url])

def remake_PlosOne_urls(urls):
    new_urls = []
    for url in urls:
        url = url.split('=printable')[0]
        new_url = f'{url}=manuscript'
        new_urls.append(new_url)

    return(new_urls)

class PlosOneSpider(FrontiersSpider):
    name = "PlosOneSpider"
    start_urls = [
        'https://journals.plos.org/ploscompbiol/article/file?id=10.1371/journal.pcbi.1002460&type=manuscript',
        # Add more Springer Link article URLs here
    ]
    custom_settings = {
        'ITEM_PIPELINES': {
            '__main__.FormatOutput': 1
        },
        'FEEDS': {
            'PlosOne.json': {
                'format': 'json',
                'overwrite': True
            }
        }
    }
    

@wait_for(100)
def run_PlosOneSpider(urls):
    # change ending of url to manuscript
    """run spider with MJKQuotesToCsv"""
    new_urls = remake_PlosOne_urls(urls)
    PlosOneSpider.start_urls = new_urls
    crawler = CrawlerRunner()
    d = crawler.crawl(PlosOneSpider)
    return d

# ############################ #
#              MDPI            #
# ############################ #

#MDPI_url = 'https://www.mdpi.com/1420-3049/25/23/5611/pdf'
#run_MDPISpider([MDPI_url])
#pd.read_json('./MDPI.json')

def remake_MDPI_urls(urls):
    new_urls = []
    for url in urls:
        url = url.rsplit('/',1)[0]
        #print(url)
        response = requests.get(url)
        #print(response.text)
        data = response.text
        
        patterns = {'ijms':r'ijms-\d+-\d+',
                    'molecules':r'molecules-\d+-\d+',
                    'metabolites':r'metabolites-\d+-\d+',
                    'microorganisms':r'microorganisms-\d+-\d+'}
        
        for idx,pattern in patterns.items():
            match = re.search(pattern, data)
            if match:
                result = match.group()

                new_url = f'https://mdpi-res.com/d_attachment/{idx}/{result}/article_deploy/{result}.xml'
                new_urls.append(new_url)
                break

            
    return(new_urls)

class MDPISpider(FrontiersSpider):
    name = "MDPISpider"
    start_urls = [
        'https://mdpi-res.com/d_attachment/molecules/molecules-25-05611/article_deploy/molecules-25-05611.xml',
        'https://mdpi-res.com/d_attachment/ijms/ijms-20-01683/article_deploy/ijms-20-01683.xml',
        # Add more MDPI Link article URLs here
    ]
    custom_settings = {
        'ITEM_PIPELINES': {
            '__main__.FormatOutput': 1
        },
        'FEEDS': {
            'MDPI.json': {
                'format': 'json',
                'overwrite': True
            }
        }
    }
        
@wait_for(100)
def run_MDPISpider(urls):
    """run spider with MJKQuotesToCsv"""
    new_urls = remake_MDPI_urls(urls)
    MDPISpider.start_urls = new_urls
    crawler = CrawlerRunner()
    d = crawler.crawl(MDPISpider)
    return d



# ############################ #
#           Non-xml            #
# ############################ #


from io import BytesIO
import requests
from pdfminer.high_level import extract_text_to_fp
from pdfminer.layout import LAParams


def cut_unrelevant_info(text):
    # Define a list of keywords to split the text on
    keywords = ['References', 'REFERENCES', 'Acknowledgements', 'ACKNOWLEDGEMENTS']
    
    # Iterate over the keywords and split the text on the first occurrence of each keyword
    for keyword in keywords:
        text = text.split(keyword)[0]
    
    return text


def extract_pdf_data(url):
    response = requests.get(url)

    with BytesIO(response.content) as data:
        # Read PDF content using pdfminer.six
        output = BytesIO()
        laparams = LAParams(word_margin=0.2)
        extract_text_to_fp(data, output, laparams=laparams)
        text = output.getvalue().decode()
        # Split the text at the "References" section
        text = cut_unrelevant_info(text)
    
    return(text)


def retrieve_full_text(full_links_list):
    full_text = None
    json = False
    spider = None
    try:
        for link in full_links_list:
            # Choose spider
            if 'www.frontiersin.org' in link:
                run_FrontiersSpider([link])
                json = True
                spider = 'Frontiers'
                
            elif 'journals.plos.org' in link:
                run_PlosOneSpider([link])
                json = True
                spider = 'PlosOne'

            elif 'www.biorxiv.org' in link:
                run_BiorxivSpider([link])
                json = True
                spider = 'Biorxiv'
                
            elif 'www.mdpi.com' in link:
                run_MDPISpider([link])
                json = True
                spider = 'MDPI'
                
            else:
                try:
                    full_text = extract_pdf_data(link)
                    return(full_text)
                except:
                    print(full_links_list,'\n',link)
                    continue

            # If spider
            if json:
                json_text = pd.read_json(f'./{spider}.json')
                full_text = []
                for sections in json_text.values:
                    for section_dict in sections:
                        #print(section_dict.values())
                        full_text.extend(section_dict.values())
                full_text = ' '.join(full_text)##
#                full_text = '\n\n'.join(full_text)##

                
                return(full_text)
            return(full_text)
    except:
        print(link)
        return('Fail')