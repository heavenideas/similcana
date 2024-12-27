from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Initialize model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Example abilities
card_1_ability = "Whenever you play a character, you may draw a card."
card_2_ability = "Whenever you play this card, you may draw a card."
# card_2_ability = "Exert chosen opposing character when this character is played."

# Define important phrases
important_phrases = ["draw a card", "damage", "heal"]

def calculate_weighted_similarity(ability1, ability2, important_phrases):
    # Generate embeddings
    embeddings = model.encode([ability1, ability2])

    # Calculate base similarity
    base_similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]

    # Add weight for important phrases
    def phrase_match_boost(ability, phrases):
        matches = sum(1 for phrase in phrases if phrase in ability.lower())
        return 1 + 0.1 * matches  # Boost by 10% per match

    boost_1 = phrase_match_boost(ability1, important_phrases)
    boost_2 = phrase_match_boost(ability2, important_phrases)

    # Calculate final similarity with boosts
    weighted_similarity = base_similarity * (boost_1 + boost_2) / 2
    return weighted_similarity

# Calculate weighted similarity
weighted_similarity = calculate_weighted_similarity(card_1_ability, card_2_ability, important_phrases)

print(f"Weighted Similarity: {weighted_similarity:.4f}")
