import json
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from scipy.spatial.distance import euclidean
from sklearn.preprocessing import OneHotEncoder
import numpy as np

# Initialize Sentence-BERT model
model = SentenceTransformer('all-MiniLM-L6-v2')

# # Define card attributes with mechanics
# card_1 = {
#     "name": "Stitch, Rock Star",
#     "ink_cost": 6,
#     "card_type": "Character",
#     "tags": ["Dreamborn", "Hero"],
#     "mechanics": ["Evasive", "Support"],
#     "ability": "Whenever you play a character, you may draw a card.",
#     "strength": 4,
#     "willpower": 6,
#     "lore_points": 2,
#     "ink_color": "Sapphire"
# }

# card_2 = {
#     "name": "Elsa, Snow Queen",
#     "ink_cost": 5,
#     "card_type": "Character",
#     "tags": ["Storyborn", "Hero"],
#     "mechanics": ["Rush", "Challenger"],
#     "ability": "Exert chosen opposing character when this character is played.",
#     "strength": 3,
#     "willpower": 4,
#     "lore_points": 1,
#     "ink_color": "Sapphire"
# }

# Define important phrases for ability weighting
important_phrases = ["draw a card", "opposing players", "opposing characters"]

# Feature weights (adjusted to include mechanics)
weights = {
    "ink_cost": 0.15,
    "strength": 0.1,
    "willpower": 0.1,
    "lore_points": 0.1,
    "tags": 0.01,
    "ability": 0.24,  # Reduced by 0.01
    "mechanics": 0.2,
    "ink_color": 0.05,
    "card_type": 0.05
}

# Validate weights sum to 1
total_weight = sum(weights.values())
if abs(total_weight - 1.0) > 1e-10:  # Using small epsilon for floating point comparison
    raise ValueError(f"Weights must sum to 1.0, but they sum to {total_weight}")
else:
    print("Weights sum to 1.0")


# Normalize numerical values to 0-1
def normalize(value, min_val, max_val):
    return (value - min_val) / (max_val - min_val)

# Calculate numeric similarity
def calculate_numeric_similarity(val1, val2, min_val, max_val):
    norm1 = normalize(val1, min_val, max_val)
    norm2 = normalize(val2, min_val, max_val)
    return 1 - euclidean([norm1], [norm2])

# Calculate categorical similarity (one-hot encoding)
def calculate_categorical_similarity(cat1, cat2, categories):
    # Handle empty or invalid categories
    if not cat1 or not cat2 or cat1 not in categories or cat2 not in categories:
        return 0.0
    
    encoder = OneHotEncoder(categories=[categories], sparse_output=False)
    encoded = encoder.fit_transform([[cat1], [cat2]])
    return cosine_similarity([encoded[0]], [encoded[1]])[0][0]

# Calculate tag similarity (Jaccard index)
def calculate_tag_similarity(tags1, tags2):
    set1, set2 = set(tags1), set(tags2)
    return len(set1 & set2) / len(set1 | set2) if len(set1 | set2) > 0 else 0

# Calculate mechanics similarity (Jaccard Index)
def calculate_mechanics_similarity(mechanics1, mechanics2):
    set1, set2 = set(mechanics1), set(mechanics2)
    return len(set1 & set2) / len(set1 | set2) if len(set1 | set2) > 0 else 0

# Calculate ability similarity with phrase boosting
def calculate_ability_similarity(ability1, ability2, important_phrases):
    embeddings = model.encode([ability1, ability2])
    base_similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
    
    def phrase_match_boost(ability, phrases):
        matches = sum(1 for phrase in phrases if phrase in ability.lower())
        return 1 + 0.1 * matches
    
    boost1 = phrase_match_boost(ability1, important_phrases)
    boost2 = phrase_match_boost(ability2, important_phrases)
    return base_similarity * (boost1 + boost2) / 2

# Combine all similarities
def calculate_card_similarity(card1, card2, weights):
    # Numeric features
    ink_cost_sim = calculate_numeric_similarity(card1["ink_cost"], card2["ink_cost"], 1, 10)
    strength_sim = calculate_numeric_similarity(card1["strength"], card2["strength"], 1, 10)
    willpower_sim = calculate_numeric_similarity(card1["willpower"], card2["willpower"], 1, 10)
    lore_points_sim = calculate_numeric_similarity(card1["lore_points"], card2["lore_points"], 0, 5)

    # Categorical features
    ink_color_sim = calculate_categorical_similarity(card1["ink_color"], card2["ink_color"], ["Amber", "Amethyst", "Emerald", "Ruby", "Sapphire", "Steel"])
    card_type_sim = calculate_categorical_similarity(card1["card_type"], card2["card_type"], 
        ["Character", "Action", "Item", "Location"])

    # Tags
    tags_sim = calculate_tag_similarity(card1["tags"], card2["tags"])

    # Abilities
    ability_sim = calculate_ability_similarity(card1["ability"], card2["ability"], important_phrases)

    # Mechanics
    mechanics_sim = calculate_mechanics_similarity(card1["mechanics"], card2["mechanics"])

    # Weighted similarity
    similarities = {
        "ink_cost": ink_cost_sim,
        "strength": strength_sim,
        "willpower": willpower_sim,
        "lore_points": lore_points_sim,
        "tags": tags_sim,
        "ability": ability_sim,
        "mechanics": mechanics_sim,
        "ink_color": ink_color_sim,
        "card_type": card_type_sim
    }

    overall_similarity = sum(weights[feature] * similarities[feature] for feature in similarities)

    return similarities, overall_similarity

# # Run similarity calculation
# similarities, overall_similarity = calculate_card_similarity(card_1, card_2, weights)

# # Print results
# print("Similarity Breakdown:")
# for feature, score in similarities.items():
#     print(f"  {feature.capitalize()}: {score:.4f}")
# print(f"\nOverall Similarity: {overall_similarity:.4f}")

# Load Lorcana card data
def load_lorcana_cards():
    with open('/Users/inesdemenaurrutia/PycharmProjects/Similicana/LorcanaJSON/output/generated/allCards.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data['cards']

# Convert JSON card to our format
def convert_card_format(card):
    return {
        "name": card.get('name', ''),
        "ink_cost": card.get('cost', 0),
        "card_type": card.get('type', ''),
        "tags": card.get('subtypes', []),
        "mechanics": [ability.get('keyword', '') for ability in card.get('abilities', []) 
                     if ability.get('type') == 'keyword'],
        "ability": ' '.join([ability.get('fullText', '') for ability in card.get('abilities', [])]),
        "strength": card.get('strength', 0),
        "willpower": card.get('willpower', 0),
        "lore_points": card.get('lore', 0),
        "ink_color": card.get('color', '')
    }

# Find card by name
def find_card_by_name(cards, name):
    # Convert input name to lowercase and remove extra spaces
    search_name = ' '.join(name.lower().split())
    
    for card in cards:
        # Compare with simpleName from JSON
        if card.get('simpleName', '').lower() == search_name:
            return card
            
    # If no exact match found
    print(f"No exact match found for '{name}'")
    
    # Optionally: Show partial matches
    partial_matches = [card for card in cards 
                      if search_name in card.get('simpleName', '').lower()]
    
    if partial_matches:
        print("\nDid you mean one of these?")
        for card in partial_matches[:5]:  # Show up to 5 suggestions
            print(f"- {card['fullName']}")
    
    return None

# Find similar cards
def find_similar_cards(target_card, all_cards, n=5):
    similarities = []
    converted_target = convert_card_format(target_card)
    
    for card in all_cards:
        converted_card = convert_card_format(card)
        _, similarity = calculate_card_similarity(converted_target, converted_card, weights)
        similarities.append((card['name'], similarity))
    
    # Sort by similarity score in descending order
    similarities.sort(key=lambda x: x[1], reverse=True)
    return similarities[:n]

# Main function to search for similar cards
def search_similar_cards(card_name, num_results=5):
    cards = load_lorcana_cards()
    target_card = find_card_by_name(cards, card_name)
    
    if target_card is None:
        print(f"Card '{card_name}' not found.")
        return
    
    print("\nTarget Card Details:")
    print(f"Full Name: {target_card.get('fullName', '')}")
    print(f"Color: {target_card.get('color', '')}")
    print(f"Cost: {target_card.get('cost', '')}")
    print(f"Strength: {target_card.get('strength', '')}")
    print(f"Willpower: {target_card.get('willpower', '')}")
    print(f"Lore: {target_card.get('lore', '')}")
    print(f"Rarity: {target_card.get('rarity', '')}")
    print(f"Set: {target_card.get('setCode', '')}")
    print(f"Full Text: {target_card.get('fullText', '')}\n")
    
    print("Finding similar cards...")
    converted_target = convert_card_format(target_card)
    
    similar_cards_details = []
    for card in cards:
        converted_card = convert_card_format(card)
        similarities, overall_similarity = calculate_card_similarity(converted_target, converted_card, weights)
        similar_cards_details.append((card, similarities, overall_similarity))
    
    # Sort by overall similarity
    similar_cards_details.sort(key=lambda x: x[2], reverse=True)
    # Skip the first one as it's the same card
    similar_cards_details = similar_cards_details[1:num_results+1]
    
    print("\nMost similar cards:")
    for card, similarities, overall_similarity in similar_cards_details:
        print(f"\nSimilarity Score: {overall_similarity:.4f}")
        print(f"Full Name: {card.get('fullName', '')}")
        print(f"Color: {card.get('color', '')}")
        print(f"Cost: {card.get('cost', '')}")
        print(f"Strength: {card.get('strength', '')}")
        print(f"Willpower: {card.get('willpower', '')}")
        print(f"Lore: {card.get('lore', '')}")
        print(f"Rarity: {card.get('rarity', '')}")
        print(f"Set: {card.get('setCode', '')}")
        print(f"Full Text: {card.get('fullText', '')}")
        
        print("\nSimilarity Breakdown:")
        for feature, score in similarities.items():
            print(f"  {feature.capitalize()}: {score:.4f}")
        print("-" * 80)

# Example usage
if __name__ == "__main__":
    card_name = input("Enter card name to find similar cards: ")
    search_similar_cards(card_name)
