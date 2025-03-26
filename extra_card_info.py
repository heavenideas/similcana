import requests
from bs4 import BeautifulSoup

def scrape_webpage(url, card):
    # Send a GET request to the URL
    response = requests.get(url)
    
    # Parse the HTML content
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Extract specific information
    
    # Assuming you have already created the soup object
    h2_element = soup.find('h2', id='set_about_section')

    longword_paragraphs = []
    current_element = h2_element.find_next('p', class_='longword')

    while current_element and current_element.name == 'p' and 'longword' in current_element.get('class', []):
        longword_paragraphs.append(current_element.text)
        current_element = current_element.find_next('p', class_='longword')

    for paragraph in longword_paragraphs:
        if '$' not in paragraph and '*' not in paragraph:
            print(card)
            print(paragraph)

    # Add more extraction logic here based on your needs

cards = ["Hades - Lord of the Underworld",
"HeiHei - Boat Snack",
"LeFou - Bumbler",
"Lilo - Making a Wish",
"Simba - Scrappy Cub"]

for card in cards:
    cardText = card.replace(" - ", " ").replace(" ", "-").lower()
    target_url = f'https://lorcana.cardsrealm.com/en-us/card/{cardText}'
    print(target_url)
    scrape_webpage(target_url, card)
    print("--------------------------------\n\n")
