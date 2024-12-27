import json
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from scipy.spatial.distance import euclidean
from sklearn.preprocessing import OneHotEncoder
import numpy as np

class LorcanaCardFinder:
    def __init__(self, json_path):
        """Initialize the card finder with path to JSON data."""
        self.json_path = json_path
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.important_phrases = ["draw a card", "opposing players", "opposing characters"]
        self.weights = {
            "ink_cost": 0.15,
            "strength": 0.1,
            "willpower": 0.1,
            "lore_points": 0.1,
            "tags": 0.01,
            "ability": 0.24,
            "mechanics": 0.2,
            "ink_color": 0.05,
            "card_type": 0.05
        }
        self.cards = self._load_cards()

    def _load_cards(self):
        """Load card data from JSON file."""
        with open(self.json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data['cards']

    def _normalize(self, value, min_val, max_val):
        """Normalize numerical values to 0-1."""
        return (value - min_val) / (max_val - min_val)

    def _calculate_numeric_similarity(self, val1, val2, min_val, max_val):
        """Calculate similarity between numeric values."""
        norm1 = self._normalize(val1, min_val, max_val)
        norm2 = self._normalize(val2, min_val, max_val)
        return 1 - euclidean([norm1], [norm2])

    def _calculate_categorical_similarity(self, cat1, cat2, categories):
        """Calculate similarity between categorical values."""
        if not cat1 or not cat2 or cat1 not in categories or cat2 not in categories:
            return 0.0
        
        encoder = OneHotEncoder(categories=[categories], sparse_output=False)
        encoded = encoder.fit_transform([[cat1], [cat2]])
        return cosine_similarity([encoded[0]], [encoded[1]])[0][0]

    def _calculate_tag_similarity(self, tags1, tags2):
        """Calculate Jaccard similarity between tag sets."""
        set1, set2 = set(tags1), set(tags2)
        return len(set1 & set2) / len(set1 | set2) if len(set1 | set2) > 0 else 0

    def _calculate_mechanics_similarity(self, mechanics1, mechanics2):
        """Calculate Jaccard similarity between mechanics sets."""
        set1, set2 = set(mechanics1), set(mechanics2)
        return len(set1 & set2) / len(set1 | set2) if len(set1 | set2) > 0 else 0

    def _calculate_ability_similarity(self, ability1, ability2):
        """Calculate similarity between ability texts with phrase boosting."""
        embeddings = self.model.encode([ability1, ability2])
        base_similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
        
        def phrase_match_boost(ability, phrases):
            matches = sum(1 for phrase in phrases if phrase in ability.lower())
            return 1 + 0.1 * matches
        
        boost1 = phrase_match_boost(ability1, self.important_phrases)
        boost2 = phrase_match_boost(ability2, self.important_phrases)
        return base_similarity * (boost1 + boost2) / 2

    def _convert_card_format(self, card):
        """Convert JSON card data to internal format."""
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

    def _calculate_card_similarity(self, card1, card2):
        """Calculate overall similarity between two cards."""
        ink_cost_sim = self._calculate_numeric_similarity(card1["ink_cost"], card2["ink_cost"], 1, 10)
        strength_sim = self._calculate_numeric_similarity(card1["strength"], card2["strength"], 1, 10)
        willpower_sim = self._calculate_numeric_similarity(card1["willpower"], card2["willpower"], 1, 10)
        lore_points_sim = self._calculate_numeric_similarity(card1["lore_points"], card2["lore_points"], 0, 5)
        
        ink_color_sim = self._calculate_categorical_similarity(
            card1["ink_color"], card2["ink_color"], 
            ["Amber", "Amethyst", "Emerald", "Ruby", "Sapphire", "Steel"]
        )
        
        card_type_sim = self._calculate_categorical_similarity(
            card1["card_type"], card2["card_type"],
            ["Character", "Action", "Item", "Location"]
        )
        
        tags_sim = self._calculate_tag_similarity(card1["tags"], card2["tags"])
        ability_sim = self._calculate_ability_similarity(card1["ability"], card2["ability"])
        mechanics_sim = self._calculate_mechanics_similarity(card1["mechanics"], card2["mechanics"])

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

        overall_similarity = sum(self.weights[feature] * similarities[feature] 
                               for feature in similarities)

        return similarities, overall_similarity

    def find_similar_cards(self, card_name, num_results=5):
        """Find similar cards to the given card name."""
        target_card = next((card for card in self.cards 
                           if card.get('simpleName', '').lower() == card_name.lower()), None)
        
        if target_card is None:
            return None, None
        
        converted_target = self._convert_card_format(target_card)
        similar_cards_details = []
        
        for card in self.cards:
            converted_card = self._convert_card_format(card)
            similarities, overall_similarity = self._calculate_card_similarity(converted_target, converted_card)
            similar_cards_details.append((card, similarities, overall_similarity))
        
        similar_cards_details.sort(key=lambda x: x[2], reverse=True)
        return target_card, similar_cards_details[1:num_results+1]

def format_card_details(card):
    """Format card details for display."""
    return {
        "fullName": card.get('fullName', ''),
        "color": card.get('color', ''),
        "cost": card.get('cost', ''),
        "strength": card.get('strength', ''),
        "willpower": card.get('willpower', ''),
        "lore": card.get('lore', ''),
        "rarity": card.get('rarity', ''),
        "set": card.get('setCode', ''),
        "fullText": card.get('fullText', '')
    }

def print_card_comparison(target_card, similar_cards):
    """
    Print a formatted comparison between a target card and its similar cards.
    
    Args:
        target_card (dict): The original card to compare against
        similar_cards (list): List of tuples containing (card, similarities, overall_similarity)
    """
    if not target_card:
        print("No target card provided")
        return

    target_details = format_card_details(target_card)
    
    print("\n" + "="*100)
    print(f"Comparing cards similar to: {target_details['fullName']}")
    print("="*100)
    
    # Print header
    print(f"{'Attribute':<15} {'Original':<25} {'Similar Card':<25} {'Difference':<15}")
    print("-"*80)
    
    for card, similarities, overall_similarity in similar_cards:
        card_details = format_card_details(card)
        print(f"\nSimilar Card: {card_details['fullName']} (Similarity: {overall_similarity:.4f})")
        print("-"*80)
        
        # Compare numerical values
        for attr in ['color', 'cost', 'strength', 'willpower', 'lore', 'rarity', 'set']:
            original = str(target_details[attr])
            similar = str(card_details[attr])
            diff = ""
            
            # For numerical values, calculate the difference
            if attr in ['cost', 'strength', 'willpower', 'lore'] and original and similar:
                try:
                    num_diff = int(similar) - int(original)
                    diff = f"({'+' if num_diff > 0 else ''}{num_diff})"
                except ValueError:
                    diff = "N/A"
            
            print(f"{attr.capitalize():<15} {original:<25} {similar:<25} {diff:<15}")
        
        # Print abilities separately as they might be longer
        print("\nAbilities:")
        print(f"Original: {target_details['fullText']}")
        print(f"Similar:  {card_details['fullText']}")
        
        print("\nSimilarity Breakdown:")
        for feature, score in similarities.items():
            print(f"  {feature.capitalize():<15}: {score:.4f}")
        print("="*100)

# Example usage:
if __name__ == "__main__":
    finder = LorcanaCardFinder('database/allCards.json')
    
    card_name = "lilo escape artist"
    target_card, similar_cards = finder.find_similar_cards(card_name)
    
    if target_card:
        print_card_comparison(target_card, similar_cards)
    else:
        print(f"Card: {card_name} - wasn't found")