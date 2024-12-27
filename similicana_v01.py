from find_similar_cards import LorcanaCardFinder, print_card_comparison

# Initialize the finder with the new path to JSON file
finder = LorcanaCardFinder('database/allCards.json')

card_name = input(f"Enter the card name: \n")

# Process the card name to remove any capitalization, special characters, and normalize spaces
card_name = " ".join(card_name.lower().replace("-", " ").strip().split())

print(f"Processing card name: {card_name}")
# Find similar cards
target_card, similar_cards = finder.find_similar_cards(card_name)

print_card_comparison(target_card, similar_cards, finder)