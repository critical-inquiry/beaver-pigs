
###beaver-pigs24 -- free palestine###

import os
import requests
from bs4 import BeautifulSoup
import git
import hashlib
import logging

### constants IMPORTANT!! -- find the appropriate .pem cert CHAIN file from the police website and download it. specify path under CERT_PATH (must be cert chain) ###

URL = "https://police.mit.edu/police-logs"
CERT_PATH = "X:\\yourrepo\\cert.pem"
REPO_PATH = "X:\\yourrepo\\beaver-pigs"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36',
    'Referer': 'https://police.mit.edu/police-logs',
}

### logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def initialize_repo(repo_path):
    """initialize and return git repo."""
    os.chdir(repo_path)
    repo = git.Repo(repo_path)
    assert not repo.bare, "Repository is bare!"
    return repo

def fetch_pdf_links(url, cert_path, headers):
    """fetch and return list of pdf links from the url."""
    response = requests.get(url, verify=cert_path, headers=headers)
    if response.status_code != 200:
        logging.error(f"Failed to retrieve the page. Status code: {response.status_code}")
        return []
    
    soup = BeautifulSoup(response.content, 'html.parser')
    pdf_links = [
        a['href'] for a in soup.find_all('a', href=True)
        if a['href'].endswith('.pdf') and '/MIT-Police-Files/' in a['href']
    ]
    return pdf_links

def download_pdf(pdf_url, pdf_name, cert_path, headers):
    """download a pdf and return the content if successful, else none."""
    response = requests.get(pdf_url, verify=cert_path, headers=headers)
    if response.headers.get('Content-Type') == 'application/pdf':
        logging.info(f"Downloaded {pdf_name}")
        return response.content
    logging.warning(f"Downloaded content is not a pdf for {pdf_name}, skipping this file.")
    return None

def is_pdf_updated(local_file, remote_content):
    """check if remote pdf is different from local."""
    local_file_hash = hashlib.md5(local_file).hexdigest()
    remote_file_hash = hashlib.md5(remote_content).hexdigest()
    return local_file_hash == remote_file_hash

def push_to_github(repo, pdf_name):
    """commit and push updated pdf to github."""
    try:
        repo.git.add(pdf_name)
        repo.index.commit(f"Add/update {pdf_name}")
        origin = repo.remote(name='origin')
        origin.push()
        logging.info(f"Pushed {pdf_name} to GitHub.")
    except git.exc.GitCommandError as e:
        logging.error(f"Failed to push {pdf_name} to GitHub: {e}")

def main():
    repo = initialize_repo(REPO_PATH)
    pdf_links = fetch_pdf_links(URL, CERT_PATH, HEADERS)

    for link in pdf_links:
        pdf_url = f"https://police.mit.edu{link}"
        pdf_name = os.path.basename(link)

        ### check for pdf duplicates
        if os.path.exists(pdf_name):
            with open(pdf_name, 'rb') as f:
                local_content = f.read()

            remote_content = download_pdf(pdf_url, pdf_name, CERT_PATH, HEADERS)
            if remote_content and not is_pdf_updated(local_content, remote_content):
                with open(pdf_name, 'wb') as pdf_file:
                    pdf_file.write(remote_content)
                push_to_github(repo, pdf_name)
        else:
            # download and save pdf
            remote_content = download_pdf(pdf_url, pdf_name, CERT_PATH, HEADERS)
            if remote_content:
                with open(pdf_name, 'wb') as pdf_file:
                    pdf_file.write(remote_content)
                push_to_github(repo, pdf_name)

    logging.info("Script completed successfully.")

if __name__ == "__main__":
    main()
