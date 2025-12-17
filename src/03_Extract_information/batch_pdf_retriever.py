import logging     

import subprocess
import time

import pandas as pd

from io import BytesIO
from pdfminer.high_level import extract_text_to_fp
from pdfminer.layout import LAParams
import concurrent.futures

import json



DOI_FILE = './temp_pdfs/dois.txt'
RESULTS_FILE = './temp_pdfs/result.csv'
PDF_DIR = './temp_pdfs'
BATCH_SAVE_INTERVAL = 5
BATCH_TIMEOUT = 1800  # seconds
PDF_TIMEOUT = 1200   # seconds

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s',
    )
    
    
setup_logging()


def write_dois_to_file(doi_list, file_path=DOI_FILE):
    with open(file_path, 'w') as f:
        for doi in doi_list:
            f.write(f"{doi}\n")
            

def run_pypaperbot(doi_file=DOI_FILE, output_dir=PDF_DIR, timeout=BATCH_TIMEOUT):
    logging.info("Waiting 10 seconds before running PyPaperBot...")
    time.sleep(10)
    cmd = f'python -m PyPaperBot --doi-file={doi_file} --dwn-di="{output_dir}" --restrict="1"'
    subprocess.run(cmd, shell=True, timeout=timeout)
    
    

def load_results(results_file=RESULTS_FILE):
    try:
        df = pd.read_csv(results_file)
        return df.dropna(subset=['PDF Name'])
    except Exception as e:
        logging.error(f"Failed to read {results_file}: {e}")
        return None
    
    


def extract_text_safe(file_path):
    with open(file_path, 'rb') as data:
        output = BytesIO()
        laparams = LAParams(word_margin=0.2)
        extract_text_to_fp(data, output, laparams=laparams)
        return output.getvalue().decode()

def extract_text_with_timeout(file_path, timeout=PDF_TIMEOUT):
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(extract_text_safe, file_path)
        return future.result(timeout=timeout)
    
def cleanup_pdfs(pdf_dir=PDF_DIR):
    subprocess.run(f'rm -f {pdf_dir}/*.pdf', shell=True)
    
    
def save_json(data, file_path):
    with open(file_path, 'w') as f:
        json.dump(data, f)
    

def cut_unrelevant_info(text):
    # Define a list of keywords to split the text on
    keywords = ['References', 'REFERENCES', 'Acknowledgements', 'ACKNOWLEDGEMENTS']
    
    # Iterate over the keywords and split the text on the first occurrence of each keyword
    for keyword in keywords:
        text = text.split(keyword)[0]
    
    return text

