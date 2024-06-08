from flask import Flask, jsonify, request
import requests
import re
from bs4 import BeautifulSoup, SoupStrainer
# from flask_cors import CORS
# import urllib.request
from time import time
import cv2
import numpy as np
from collections import defaultdict
from textblob import TextBlob
from urllib.parse import urlparse, urlunparse
import re
from bs4 import BeautifulSoup
from textblob import TextBlob
from spellchecker import SpellChecker
from collections import defaultdict
from flask import Flask, jsonify, request
from collections import defaultdict
from spellchecker import SpellChecker
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

def get_misspelled_words(html_code):
    # Parse HTML and extract text
    soup = BeautifulSoup(html_code, 'html.parser')
    text = soup.get_text()
    
    # Set of words to skip
    skip_words = {'idc', 'webinar', 'microsoft', 'whitepaper'}
    # Regex pattern to match URLs
    url_pattern = re.compile(r'https?://\S+')
    
    # Initialize the spell checker
    spell = SpellChecker()
    
    # Find all words in the text
    words = re.findall(r'\b\w+\b', text)
    all_words = []
    correctly_spelled_words_count = defaultdict(int)
    misspelled_words_count = defaultdict(int)
    
    for word in words:
        lower_word = word.lower()
        # Skip the word if it is in the skip list or if it matches the URL pattern
        if lower_word in skip_words or url_pattern.search(word):
            continue
        all_words.append(word)
        
        # Check if the word is misspelled
        if lower_word not in spell:
            misspelled_words_count[word] += 1
        else:
            correctly_spelled_words_count[word] += 1
    
    correctly_spelled_words = list(correctly_spelled_words_count.items())
    misspelled_words = list(misspelled_words_count.items())
    
    return all_words, correctly_spelled_words, misspelled_words

def get_correct_words(misspelled_words):
    spell = SpellChecker()
    corrected_words_list = [
        (word, freq, spell.correction(word))
        for word, freq in misspelled_words
    ]
    return corrected_words_list

@app.route('/validate', methods=['POST'])
def validate_html():
    data = request.get_json()
    html_code = data.get('html_code')
    if not html_code:
        return jsonify({"error": "No HTML code provided"}), 400
    
    all_words, correctly_spelled_words, misspelled_words = get_misspelled_words(html_code)
    corrected_words = get_correct_words(misspelled_words)
    
    return jsonify({
        "all_words": all_words,
        "correctly_spelled_words": correctly_spelled_words,
        "misspelled_words": misspelled_words,
        "corrected_words": corrected_words
    })

if __name__ == '__main__':
    app.run(debug=True)
