import os
import json
from sentence_transformers import SentenceTransformer, SimilarityFunction
from sklearn.metrics.pairwise import cosine_similarity
from scipy.spatial.distance import euclidean
from sklearn.preprocessing import OneHotEncoder
import numpy as np

class LorcanaCardFinder:
    def __init__(self, json_path, embeddings_cache_path='embeddings_cache.json', recache_embeddings=False):
        """Initialize the card finder with path to JSON data and embeddings cache."""
        self.json_path = json_path
        self.embeddings_cache_path = embeddings_cache_path
        self.recache_embeddings = recache_embeddings
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.similarity_function = SimilarityFunction.COSINE  # Default
        self.model.similarity_fn_name = self.similarity_function
        self.important_phrases = ["draw a card", "opposing players", "opposing characters"]
        self.weights = {
            "ink_cost": 0.15,
            "strength": 0.1,
            "willpower": 0.1,
            "lore_points": 0.1,
            "tags": 0.01,
            "ability": 0.24,
            "mechanics": 0.15,
            "ink_color": 0.05,
            "card_type": 0.05,
            "inkwell": 0.05
        }
        self.cards = self._load_cards()
        self._filter_cards()
        
        # Load or precompute embeddings
        self.card_formats = {}
        self.ability_embeddings = {}
        self._load_embeddings()  # Load embeddings from cache or initialize
        if self.recache_embeddings:
            self._precompute_card_data()
            self._save_embeddings()

    def _load_embeddings(self):
        """Load embeddings from a cache file if it exists."""
        if os.path.exists(self.embeddings_cache_path):
            with open(self.embeddings_cache_path, 'r', encoding='utf-8') as f:
                self.ability_embeddings = json.load(f)
            print("Loaded embeddings from cache.")
        else:
            print("No cached embeddings found. Precomputing embeddings...")

    def _save_embeddings(self):
        """Save embeddings to a cache file."""
        with open(self.embeddings_cache_path, 'w', encoding='utf-8') as f:
            json.dump(self.ability_embeddings, f)
        print("Embeddings saved to cache.")

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

    def _precompute_card_data(self):
        """Pre-compute card formats and embeddings."""
        print("Pre-computing card data...")
        all_abilities = []
        ability_map = {}
        
        # First pass: convert formats and collect abilities
        for card in self.cards:
            card_format = self._convert_card_format(card)
            self.card_formats[card['simpleName']] = card_format
            
            if card_format['ability'].strip():
                all_abilities.append(card_format['ability'])
                ability_map[len(all_abilities) - 1] = card['simpleName']
        
        # Batch compute all embeddings at once
        if all_abilities:
            print("Computing ability embeddings...")
            all_embeddings = self.model.encode(all_abilities, batch_size=32, show_progress_bar=True)
            
            # Map embeddings back to cards
            for idx, embedding in enumerate(all_embeddings):
                card_name = ability_map[idx]
                self.ability_embeddings[card_name] = embedding.tolist()  # Convert to list for JSON serialization
        
        print("Pre-computation complete!")

    def _calculate_ability_similarity(self, ability1, ability2, card1_name, card2_name):
        """Calculate similarity between ability texts using configured similarity function."""
        if not ability1.strip() or not ability2.strip():
            return 0.0
            
        embedding1 = self.ability_embeddings.get(card1_name)
        embedding2 = self.ability_embeddings.get(card2_name)
        
        if embedding1 is None or embedding2 is None:
            return 0.0
        
        # Convert embeddings to NumPy arrays
        embedding1 = np.array(embedding1)
        embedding2 = np.array(embedding2)

        # Calculate similarity using the configured similarity function
        base_similarity = cosine_similarity(
            embedding1.reshape(1, -1), 
            embedding2.reshape(1, -1)
        )[0][0]
        
        # Normalize similarity score for non-cosine metrics
        if self.similarity_function in [SimilarityFunction.EUCLIDEAN, SimilarityFunction.MANHATTAN]:
            # Convert negative distance to similarity score between 0 and 1
            max_distance = 20.0  # Approximate max distance based on empirical observation
            base_similarity = max(0, 1 - abs(base_similarity) / max_distance)
        
        # Apply phrase boosting
        def phrase_match_boost(ability, phrases):
            matches = sum(1 for phrase in phrases if phrase in ability.lower())
            return min(1 + 0.1 * matches, 1.5)
        
        boost1 = phrase_match_boost(ability1, self.important_phrases)
        boost2 = phrase_match_boost(ability2, self.important_phrases)
        boosted_similarity = base_similarity * (boost1 + boost2) / 2
        
        return min(boosted_similarity, 1.0)

    def _find_mechanics(self, card):
        """Find mechanics based on predefined keywords in card text."""
        MECHANIC_KEYWORDS = {
            'bodyguard',
            'challenger',
            'evasive',
            'reckless',
            'resist',
            'rush',
            'shift',
            'singer',
            'support',
            'ward',
            'banish',
            'your hand',
            'their hand',
            'opposing players',
            'opposing characters',
            'draw',
            'shuffle',
            'damage',
            'heal',
            'remove',
            'chosen character',
            'location',
            'chosen item',
            'your inkwell'
        }
        
        mechanics = set()  # Using set to avoid duplicates
        
        # For Action cards, check effects text
        if card.get('type') == 'Action':
            for effect in card.get('effects', []):
                effect_lower = effect.lower()
                # Check for each mechanic keyword in the full text
                mechanics.update(keyword for keyword in MECHANIC_KEYWORDS 
                               if keyword in effect_lower)
        else:
            # For other cards, check abilities
            for ability in card.get('abilities', []):
                # Check keyword field first (case-insensitive)
                if ability.get('keyword', '').lower() in MECHANIC_KEYWORDS:
                    mechanics.add(ability.get('keyword', '').lower())
                
                # Also check fullText for mechanics
                if ability.get('fullText'):
                    text_lower = ability.get('fullText').lower()
                    mechanics.update(keyword for keyword in MECHANIC_KEYWORDS 
                                   if keyword in text_lower)
        
        return list(mechanics)  # Convert set back to list

    def _convert_card_format(self, card):
        """Convert JSON card data to internal format."""
        # For Action cards, use effects instead of abilities
        if card.get('type') == 'Action':
            processed_abilities = card.get('effects', [])
        else:
            # Process abilities to remove ability names and ignore keyword abilities
            processed_abilities = []
            for ability in card.get('abilities', []):
                # Skip keyword abilities
                if ability.get('type') == 'keyword':
                    continue
                
                full_text = ability.get('fullText', '')
                ability_name = ability.get('name', '')
                
                # Remove ability name from the start of fullText if present
                if ability_name and full_text.startswith(ability_name):
                    # Remove name and any following dash/hyphen with surrounding whitespace
                    full_text = full_text[len(ability_name):].strip()
                    full_text = full_text.lstrip('—').strip()
                
                processed_abilities.append(full_text)
        
        return {
            "name": card.get('name', ''),
            "ink_cost": card.get('cost', 0),
            "card_type": card.get('type', ''),
            "tags": card.get('subtypes', []),
            "mechanics": self._find_mechanics(card),
            "ability": ' '.join(processed_abilities),
            "strength": card.get('strength', 0),
            "willpower": card.get('willpower', 0),
            "lore_points": card.get('lore', 0),
            "ink_color": card.get('color', ''),
            "inkwell": card.get('inkwell', False)
        }

    def _calculate_inkwell_similarity(self, inkwell1, inkwell2):
        """Calculate similarity based on inkwell capability."""
        if inkwell1 and inkwell2:
            return 1.0
        elif inkwell1 != inkwell2:
            return 0.0
        else:
            return 0.5

    def _calculate_card_similarity(self, card1, card2, card1_name, card2_name):
        """Calculate overall similarity between two cards using cached data."""
        similarities = {
            "ink_cost": self._calculate_numeric_similarity(card1["ink_cost"], card2["ink_cost"], 1, 10),
            "strength": self._calculate_numeric_similarity(card1["strength"], card2["strength"], 1, 10),
            "willpower": self._calculate_numeric_similarity(card1["willpower"], card2["willpower"], 1, 10),
            "lore_points": self._calculate_numeric_similarity(card1["lore_points"], card2["lore_points"], 0, 5),
            "tags": self._calculate_tag_similarity(card1["tags"], card2["tags"]),
            "ability": self._calculate_ability_similarity(card1["ability"], card2["ability"], card1_name, card2_name),
            "mechanics": self._calculate_mechanics_similarity(card1["mechanics"], card2["mechanics"]),
            "ink_color": self._calculate_categorical_similarity(
                card1["ink_color"], card2["ink_color"],
                ["Amber", "Amethyst", "Emerald", "Ruby", "Sapphire", "Steel"]
            ),
            "card_type": self._calculate_categorical_similarity(
                card1["card_type"], card2["card_type"],
                ["Character", "Action", "Item", "Location"]
            ),
            "inkwell": self._calculate_inkwell_similarity(card1["inkwell"], card2["inkwell"])
        }

        overall_similarity = sum(self.weights[feature] * similarities[feature] 
                               for feature in similarities)

        return similarities, overall_similarity

    def _filter_cards(self):
        """Filter out enchanted and promotional cards, and deduplicate by fullName."""
        filtered_cards = {}
        
        for card in self.cards:
            # Skip enchanted cards
            if 'enchantedId' in card:
                continue
                
            # Skip promotional versions
            if card.get('rarity', '').lower() == 'promotional':
                continue
                
            # Use fullName as key to avoid duplicates
            full_name = card.get('fullName', '')
            
            # If we haven't seen this card name before, or this is a better version
            # (prefer non-variant cards)
            if (full_name not in filtered_cards or 
                ('variant' in filtered_cards[full_name] and 'variant' not in card)):
                filtered_cards[full_name] = card
        
        # Update self.cards with filtered list
        self.cards = list(filtered_cards.values())
    
    def find_card_by_name(self, card_name):

        target_card = None

        #search by simple name
        target_card = next((card for card in self.cards 
                        if card.get('simpleName', '') == sanitize_string(card_name)), None)
    
        if target_card == None: #try full name
            target_card = next((card for card in self.cards 
                          if card.get('fullName', '') == sanitize_string(card_name)), None)
        
        return target_card

    def find_similar_cards(self, card_name, num_results=5):
        """Find similar cards to the given card name using cached data."""
        target_card = next((card for card in self.cards 
                          if card.get('simpleName', '') == sanitize_string(card_name)), None)
        
        if target_card is None:
            return None, None
        
        converted_target = self.card_formats.get(target_card['simpleName'])
        if not converted_target:
            converted_target = self._convert_card_format(target_card)
        
        similar_cards_details = []
        seen_names = {target_card['fullName']}  # Track seen card names
        
        for card in self.cards:
            # Skip if we've seen this card name already
            if card['fullName'] in seen_names:
                continue
                
            converted_card = self.card_formats.get(card['simpleName'])
            if not converted_card:
                converted_card = self._convert_card_format(card)
            
            similarities, overall_similarity = self._calculate_card_similarity(
                converted_target, 
                converted_card,
                target_card['simpleName'],
                card['simpleName']
            )
            similar_cards_details.append((card, similarities, overall_similarity))
            seen_names.add(card['fullName'])
        
        similar_cards_details.sort(key=lambda x: x[2], reverse=True)
        return target_card, similar_cards_details[:num_results]

    def set_similarity_function(self, function_name):
        """Set the similarity function to use for ability comparison."""
        valid_functions = {
            'cosine': SimilarityFunction.COSINE,
            'dot': SimilarityFunction.DOT_PRODUCT,
            'euclidean': SimilarityFunction.EUCLIDEAN,
            'manhattan': SimilarityFunction.MANHATTAN
        }
        if function_name.lower() not in valid_functions:
            raise ValueError(f"Invalid similarity function. Choose from: {', '.join(valid_functions.keys())}")
        
        self.similarity_function = valid_functions[function_name.lower()]
        self.model.similarity_fn_name = self.similarity_function

def sanitize_string(input_string):
    # Remove all special characters except hyphens in words
    sanitized = input_string.replace('!', '').replace(' - ', ' ').replace('.','')
    sanitized = " ".join(sanitized.lower().strip().split())

    return sanitized

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
        "fullText": card.get('fullText', ''),
        "inkwell": card.get('inkwell', False),
        "mechanics": LorcanaCardFinder._find_mechanics(None, card)
    }

def print_card_comparison(target_card, similar_cards, finder):
    """
    Print a formatted comparison between a target card and its similar cards.
    
    Args:
        target_card (dict): The original card to compare against
        similar_cards (list): List of tuples containing (card, similarities, overall_similarity)
        finder (LorcanaCardFinder): Instance of the card finder class
    """
    if not target_card:
        print("No target card provided")
        return

    target_details = format_card_details(target_card)
    
    print("\n" + "="*110)
    print(f"Comparing cards similar to: {target_details['fullName']}")
    print("="*110)
    
    # Print header
    print(f"{'Attribute':<15} {'Original':<25} {'Similar Card':<25} {'Difference':<15}")
    print("-"*110)
    
    for card, similarities, overall_similarity in similar_cards:
        card_details = format_card_details(card)
        print(f"\nSimilar Card: {card_details['fullName']} (Overall Similarity: {overall_similarity:.4f})")
        print("-"*110)
        
        # Compare numerical and categorical values with their similarities
        for attr in ['color','inkwell', 'cost', 'strength', 'willpower', 'lore', 'rarity', 'set']:
            original = str(target_details[attr])
            similar = str(card_details[attr])
            diff = ""
            
            # Get the corresponding similarity score
            sim_key = None
            if attr == 'color': sim_key = 'ink_color'
            elif attr == 'cost': sim_key = 'ink_cost'
            elif attr in ['strength', 'willpower']: sim_key = attr
            elif attr == 'lore': sim_key = 'lore_points'
            elif attr == 'inkwell': sim_key = 'inkwell'
            
            sim_score = f"(Similarity: {similarities.get(sim_key, 'N/A'):.4f})" if sim_key else ""
            
            # Calculate numerical difference if applicable
            if attr in ['cost', 'strength', 'willpower', 'lore'] and original and similar:
                try:
                    num_diff = int(similar) - int(original)
                    diff = f"({'+' if num_diff > 0 else ''}{num_diff})"
                except ValueError:
                    diff = "N/A"
            
            # Special formatting for inkwell
            if attr == 'inkwell':
                original = "✓" if original.lower() == 'true' else "✗"
                similar = "✓" if similar.lower() == 'true' else "✗"
            
            print(f"{attr.capitalize():<15} {original:<25} {similar:<25} {diff:<15} {sim_score}")
        
        # Print abilities with similarity score
        print(f"\nAbilities (Similarity: {similarities['ability']:.4f}):")
        print(f"Original: {target_details['fullText']}")
        print('\n')
        print(f"Similar:  {card_details['fullText']}")
        
        # Add mechanics comparison with similarity score
        print(f"\nMechanics (Similarity: {similarities['mechanics']:.4f}):")
        target_mechanics = set(finder._find_mechanics(target_card))
        similar_mechanics = set(finder._find_mechanics(card))
        shared_mechanics = target_mechanics & similar_mechanics
        unique_to_target = target_mechanics - similar_mechanics
        unique_to_similar = similar_mechanics - target_mechanics
        
        if shared_mechanics:
            print("Shared mechanics:", ", ".join(shared_mechanics))
        if unique_to_target:
            print("Unique to original:", ", ".join(unique_to_target))
        if unique_to_similar:
            print("Unique to similar:", ", ".join(unique_to_similar))
        
        # Print tags with similarity score
        print(f"\nTags (Similarity: {similarities['tags']:.4f}):")
        target_tags = set(target_card.get('subtypes', []))
        similar_tags = set(card.get('subtypes', []))
        shared_tags = target_tags & similar_tags
        unique_to_target_tags = target_tags - similar_tags
        unique_to_similar_tags = similar_tags - target_tags
        
        if shared_tags:
            print("Shared tags:", ", ".join(shared_tags))
        if unique_to_target_tags:
            print("Unique to original:", ", ".join(unique_to_target_tags))
        if unique_to_similar_tags:
            print("Unique to similar:", ", ".join(unique_to_similar_tags))
        
        print("\nSimilarity Breakdown:")
        for feature, score in similarities.items():
            print(f"  {feature.capitalize():<15}: {score:.4f}")
        print("="*110)




# Example usage:
if __name__ == "__main__":
    finder = LorcanaCardFinder('database/allCards.json')
    
    #finder.set_similarity_function('cosine')

    # Try different similarity functions
    similarity_functions = ['cosine', 'dot', 'euclidean', 'manhattan']
    card_name = "a whole new world"
    
    for sim_function in similarity_functions:
        print(f"\nUsing {sim_function} similarity:")
        finder.set_similarity_function(sim_function)
        target_card, similar_cards = finder.find_similar_cards(card_name)
        if target_card:
            print_card_comparison(target_card, similar_cards, finder)
        else:
            print(f"Card: {card_name} - wasn't found")