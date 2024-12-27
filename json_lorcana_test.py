import json
import os

# Load Lorcana card data
def load_lorcana_cards():
    cards_path = "/Users/inesdemenaurrutia/PycharmProjects/Similicana/LorcanaJSON/output/generated/allCards.json"
    with open(cards_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# Add this near the top of your smilicana_prototype.py
lorcana_cards = load_lorcana_cards()

