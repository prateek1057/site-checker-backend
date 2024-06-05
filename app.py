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
from collections import defaultdict
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})

def get_links_from_website(html_code):
    link_list = []
    for link in BeautifulSoup(html_code, 'html.parser', parse_only=SoupStrainer('a')):
        if link.has_attr('href'):
            link_text = link.text.strip()  # Get the text of the link
            if link_text:
                link_list.append((link['href'], link_text))
    return link_list

def check_url_content(link_list):
    No_Content_Links = []
    Invalid_Links = []
    Valid_Links=[]
    for link in link_list:
        try:
            response = requests.get(link[0])
            link_with_status=(link[0],link[1],response.status_code)
            if response.status_code == 200:  
                if not response.text:
                    No_Content_Links.append(link_with_status)
                else:
                    Valid_Links.append(link_with_status)
            else:
                Invalid_Links.append(link_with_status)  
        except requests.exceptions.RequestException as e:
            link_with_status = (link[0], link[1], str(e))
            Invalid_Links.append(link_with_status)
    return Invalid_Links, No_Content_Links,Valid_Links

def get_misspelled_words(html_code):
    soup = BeautifulSoup(html_code, 'html.parser')
    text = soup.get_text()
    skip_words = {'idc', 'webinar', 'microsoft', 'whitepaper'}
    url_pattern = re.compile(r'https?://\S+')
    
    # Initialize the enchant dictionary
    dictionary = enchant.Dict("en_US")
    
    words = re.findall(r'\b\w+\b', text)
    all_words=[]
    correctly_spelled_words=[]
    correctly_spelled_words_count = defaultdict(int)
    misspelled_words_count= defaultdict(int)
    
    for word in words:
        lower_word = word.lower()
        if lower_word in skip_words or url_pattern.match(word):
            continue
        all_words.append(word)

        if dictionary.check(lower_word):
            correctly_spelled_words_count[word] += 1
        else:
            misspelled_words_count[word] += 1
    
    misspelled_words = list(misspelled_words_count.items())
    correctly_spelled_words=list(correctly_spelled_words_count.items())
    return all_words, correctly_spelled_words, misspelled_words
  
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
    def calculate_laplacian_variance(image):
        # Apply the Laplacian operator and return the variance
        return cv2.Laplacian(image, cv2.CV_64F).var()
    
    def resize_image(image, size=(500, 500)):
        # Resize image while maintaining the aspect ratio
        h, w = image.shape[:2]
        if h > w:
            new_h, new_w = size[0], int(size[0] * w / h)
        else:
            new_h, new_w = int(size[1] * h / w), size[1]
        return cv2.resize(image, (new_w, new_h))
    
    # Download the image using requests
    response = requests.get(image_url)
    
    if response.status_code == 200:
        # Convert the downloaded content to a NumPy array
        image_array = np.asarray(bytearray(response.content), dtype=np.uint8)
        
        # Decode the image array using OpenCV
        image = cv2.imdecode(image_array, cv2.IMREAD_GRAYSCALE)
        
        # Resize the image to a standard size for consistency
        image = resize_image(image)
        
        # Calculate the Laplacian variance
        laplacian_var = calculate_laplacian_variance(image)
        
        # Determine if the image is blurry
        is_blurry = laplacian_var < threshold
        return is_blurry
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
    invalid_links, no_content_links,valid_links= check_url_content(links)
    return jsonify({"Invalid_Links": invalid_links, "No_Content_Links": no_content_links,"Valid Links":valid_links,"Count of Valid Links":len(valid_links),
                    "Count of Invalid Links":len(invalid_links),"Count of Links with no content:":len(no_content_links)})

@app.route('/get_misspelledwords_from_website', methods=['POST'])
def get_misspelledwords_from_website_endpoint():
    data = request.get_json()
    html_code = data['code']
    all_words,correct_words_with_feq,misspelled_words_with_feq = get_misspelled_words(html_code)
    return jsonify({"Misspelled_Words": misspelled_words_with_feq, "All Words": all_words, "Correctly Spelled Words":correct_words_with_feq})

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