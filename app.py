from flask import Flask, jsonify, request
import enchant
import requests
import re
from bs4 import BeautifulSoup, SoupStrainer
from flask_cors import CORS
import urllib.request
from time import time
import cv2
import numpy as np

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})

def get_links_from_website(html_code):
    link_list = []
    for link in BeautifulSoup(html_code, 'html.parser', parse_only=SoupStrainer('a')):
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

def get_misspelled_words(html_code):
    soup = BeautifulSoup(html_code, 'html.parser')
    text = soup.get_text()
    skip_words = {'idc', 'webinar', 'microsoft', 'whitepaper'}
    url_pattern = re.compile(r'https?://\S+')
    
    # Initialize the enchant dictionary
    dictionary = enchant.Dict("en_US")
    
    words = re.findall(r'\b\w+\b', text)
    misspelled_words = set()
    
    for word in words:
        lower_word = word.lower()
        if lower_word in skip_words or url_pattern.match(word):
            continue
        if not dictionary.check(lower_word):
            misspelled_words.add(word)
    
    return list(misspelled_words)

    
def get_image_src_links(html_code):
    src_links = []

    soup = BeautifulSoup(html_code, 'html.parser')
    img_tags = soup.find_all('img')

    for img in img_tags:
        if img.has_attr('src'):
            if(img['src']=='/MS logo.png'):
                src_links.append('https://smt.microsoft.com/MS%20logo.png')
            else:
                src_links.append(img['src'])

    return src_links

def is_blurry(image_url, threshold=100):
    # Download the image using requests
    response = requests.get(image_url)
    
    if response.status_code == 200:
        # Convert the downloaded content to a NumPy array
        image_array = np.asarray(bytearray(response.content), dtype=np.uint8)
        
        # Decode the image array using OpenCV
        image = cv2.imdecode(image_array, cv2.IMREAD_GRAYSCALE)
        
        # Apply the Laplacian operator
        laplacian_var = cv2.Laplacian(image, cv2.CV_64F).var()
        # print(laplacian_var)
        # If the variance is less than the threshold, the image is considered blurry
        return laplacian_var < threshold
    else:
        print("Failed to download the image from the URL")
        return False

@app.route('/check_blurry_images', methods=['POST'])   
def check_web_images():
    data = request.get_json()
    html_code = data['code']
    blurry_images=[]
    image_urls=get_image_src_links(html_code)
    for image_url in image_urls:
        if(is_blurry(image_url,100)):
            blurry_images.append(image_url)
        else:
            print("Image is not blurry")

    if len(blurry_images)==0:
        return jsonify({"Message":"No Blurry Image Found"})
    else:
        return jsonify({"Blurry Images Links:" :blurry_images})

@app.route('/check_website_links', methods=['POST'])
def check_website_links():
    data = request.get_json()
    html_code = data['code']
    links = get_links_from_website(html_code)
    invalid_links, no_content_links = check_url_content(links)
    return jsonify({"Invalid_Links": invalid_links, "No_Content_Links": no_content_links})

@app.route('/get_misspelledwords_from_website', methods=['POST'])
def get_misspelledwords_from_website_endpoint():
    data = request.get_json()
    html_code = data['code']
    misspelled_words = get_misspelled_words(html_code)
    if(len(get_misspelled_words)==0):
        return jsonify({"Message": "No Misspelled Words Found"})
    else:
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
    return jsonify({"Page Load Time is:":load_time})