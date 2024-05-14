from flask import Flask, jsonify, request
from spellchecker import SpellChecker
import requests
import re
from bs4 import BeautifulSoup, SoupStrainer
from flask_cors import CORS
import urllib.request
from time import time

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})

def get_links_from_website(url):
    response = requests.get(url)
    link_list = []

    for link in BeautifulSoup(response.content, 'html.parser', parse_only=SoupStrainer('a')):
        if link.has_attr('href'):
            link_list.append(link['href'])
    return link_list

def check_url_content(link_list):
    No_Content_Links = []
    Invalid_Links = []
    for link in link_list:
        try:
            response = requests.get(link)
            if response.status_code == 200:  
                if not response.text:
                    No_Content_Links.append(link)  
            else:
                Invalid_Links.append(link)  
        except requests.exceptions.RequestException as e:
            Invalid_Links.append(link)
    return Invalid_Links, No_Content_Links

def get_misspelled_words(text):
    spell = SpellChecker()
    skip_words = {'IDC', 'Webinar', 'Microsoft','whitepaper'}
    url_pattern = r'https?://\S+'    
    words = re.findall(r'\b\w+\b', text)
    misspelled_words = []
    for word in words:
        if word in skip_words:
            continue
        if re.match(url_pattern, word):
            continue
        if word.lower() not in spell and word.lower() not in skip_words:
            misspelled_words.append(word)
    return misspelled_words

def get_misspelledwords_from_website(url):
    misspelled_words = []
    try:
        response = requests.get(url)
        if response.status_code == 200: 
            soup = BeautifulSoup(response.text, 'html.parser')
            all_text = soup.get_text()
            misspelled_words = get_misspelled_words(all_text)
        else:
            return f"Error: {response.status_code} - Unable to fetch content from {url}"
    except requests.exceptions.RequestException as e:
        return f"Error: {e}"
    if len(misspelled_words):
        return misspelled_words
    else:
        return "No Misspelled word Found"

@app.route('/check_website_links', methods=['POST'])
def check_website_links():
    data = request.get_json()
    url_to_check = data['url']
    links = get_links_from_website(url_to_check)
    invalid_links, no_content_links = check_url_content(links)
    return jsonify({"Invalid_Links": invalid_links, "No_Content_Links": no_content_links})

@app.route('/get_misspelledwords_from_website', methods=['POST'])
def get_misspelledwords_from_website_endpoint():
    data = request.get_json()
    url_to_check = data['url']
    misspelled_words = get_misspelledwords_from_website(url_to_check)
    return jsonify({"Misspelled_Words": misspelled_words})

@app.route('/check_load_time', methods=['POST'])
def check_load_time():
    data = request.get_json()
    url = data['url']
    stream = urllib.request.urlopen(url)
    start_time = time()
    output = stream.read()
    end_time = time()
    stream.close()
    load_time = end_time - start_time
    return f"Page load time of Website is: {load_time:.3f}"

if __name__ == '__main__':
    app.run(debug=True)