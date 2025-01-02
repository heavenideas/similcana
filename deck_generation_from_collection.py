import pandas as pd
from find_similar_cards import LorcanaCardFinder, sanitize_string
import re  # Add this import at the top of your file
from pprint import *


def load_collection(csv_path):
    df = pd.read_csv(csv_path)
    df['total_copies'] = df['Normal'] + df['Foil']
    # Filter out entries with total_copies = 0
    df = df[df['total_copies'] > 0]  # Only keep entries with copies greater than 0
    # Use sanitize_string instead of lambda for name processing
    return df.set_index(df['Name'].apply(sanitize_string))['total_copies'].to_dict()  # Pre-process names

def parse_decklist(decklist_text):
    decklist = {}
    for line in decklist_text.strip().split("\n"):
        parts = line.split(" ", 1)
        quantity = int(parts[0])
        # Preprocess the card name
        name = sanitize_string(parts[1])  # Remove special characters, convert to lowercase, and ensure single spaces
        
        decklist[name] = quantity
    return decklist

def generate_final_deck(decklist, collection, finder):

    '''
    '''
    #pprint(collection)

    final_deck = {}
    replacement_log = {}  # Log replacements for display
    max_copies = 4  # Maximum copies allowed for each card

    # Track colors of the original decklist
    original_colors = set()
    for card_name in decklist.keys():
        #print(finder.find_card_by_name(card_name))
        card_color = finder.find_card_by_name(card_name).get('color')  # Assuming color is stored in the collection
        if card_color:
            original_colors.add(card_color)

    original_colors = list(original_colors)[:2]  # Keep only 2 colors
    
    
    # iterate through the original decklist
    # Extract Card name and quanity of cards in the decklist
    for card_name, quantity in decklist.items():
        #initialize with specific value to be able to cache results
        similar_cards = "Intial Empty Similar Card Results"

        #itrate through each copy of the card
        for _ in range(quantity):
            #if we have that card in our collection AND the card isn't already 4 times in the final deck
            if collection.get(card_name, 0) > 0 and final_deck.get(card_name, 0) < max_copies:  # Check if we can add more copies:
                # Add this available card to our final deck
                final_deck[card_name] = final_deck.get(card_name, 0) + 1
                # reduce the number of copies in our collection
                collection[card_name] -= 1

                if card_name not in replacement_log:
                    replacement_log[card_name] = []
                replacement_log[card_name].append((card_name, f"Added from your collection"))

            else:

                if similar_cards == "Intial Empty Similar Card Results":
                    # Find similar replacements if this is the first time
                    target_card, similar_cards = finder.find_similar_cards(card_name, num_results=25)

                if similar_cards is None:
                    if card_name not in replacement_log:
                        replacement_log[card_name] = []
                    replacement_log[card_name].append(("Error", f"Error finding similar cards to: {card_name}"))
                    break    

                found_valid_card = False

                # iterate through each found similar card 
                for similar_card, _, similarity_score in similar_cards:
                    similar_card_name = similar_card['simpleName']
                    similar_card_color = similar_card.get('color')  # Assuming color is stored in the similar card

                     # Check if the similar card matches one of the original colors
                    if similar_card_color in original_colors:
                        # Check if not in original decklist and if we have a copy of this card
                        if collection.get(similar_card_name, 0) > 0 and similar_card_name not in decklist:
                            # Check max copies for similar card in the final deck list  
                            if final_deck.get(similar_card_name, 0) < max_copies:  
                                    # add card copy to final deck
                                    final_deck[similar_card_name] = final_deck.get(similar_card_name, 0) + 1
                                    # reduce the number of copies in our collection
                                    collection[similar_card_name] -= 1
                                    
                                    # Log replacement
                                    if card_name not in replacement_log:
                                        replacement_log[card_name] = []
                                    replacement_log[card_name].append((similar_card_name, f"Similarity Score: {similarity_score:.2f}"))
                                    found_valid_card = True
                                    break

                # If no valid card found, try again with more results
                if not found_valid_card:
                     # Log replacement
                    if card_name not in replacement_log:
                        replacement_log[card_name] = []
                    replacement_log[card_name].append((card_name, f"No Cards in your collection found to substitute this card"))
                                    
                    # target_card, similar_cards = finder.find_similar_cards(card_name, num_results=20)
                    # for similar_card, _, similarity_score in similar_cards:
                    #     similar_card_name = similar_card['simpleName']
                    #     similar_card_color = similar_card.get('color')  # Assuming color is stored in the similar card

                    #     if collection.get(similar_card_name, 0) > 0 and similar_card_name not in decklist:  # Check if not in original decklist
                    #         if final_deck.get(similar_card_name, 0) < max_copies:  # Check max copies for similar card
                    #             # Check if the similar card matches one of the original colors
                    #             if similar_card_color in original_colors:
                    #                 final_deck[similar_card_name] = final_deck.get(similar_card_name, 0) + 1
                    #                 collection[similar_card_name] -= 1
                                    
                    #                 # Log replacement
                    #                 if card_name not in replacement_log:
                    #                     replacement_log[card_name] = []
                    #                 replacement_log[card_name].append((similar_card_name, f"Similarity Score: {similarity_score:.2f}"))
                    #                 break

    return final_deck, replacement_log


def display_final_deck_comparison(original_decklist, final_deck, replacement_log):
    """
    Display a detailed comparison of the original decklist and the final deck.
    
    Args:
        original_decklist (dict): Original decklist mapping card names to quantities.
        final_deck (dict): Final deck mapping card names to quantities.
        replacement_log (dict): Log of replacements {original_card: [(replacement_card, reason), ...]}.
    """
    # Define headers
    headers = ["Original Card", "Original Count", "Replaced With", "Replacement Reason", "Final Count"]
    header_line = f"{headers[0]:<25} | {headers[1]:<15} | {headers[2]:<25} | {headers[3]:<40} | {headers[4]:<12}"
    separator = "-" * len(header_line)

    # Print headers
    print(header_line)
    print(separator)

    # Fill rows
    for original_card, original_count in original_decklist.items():
        replacements = replacement_log.get(original_card, [])
        if not replacements:
            # No replacements, card directly included in the final deck
            final_count = final_deck.get(original_card, 0)
            print(f"{original_card:<25} | {original_count:<15} | {original_card:<25} | {'Card available':<40} | {final_count:<12}")
        else:
            for i, (replacement_card, reason) in enumerate(replacements):
                final_count = final_deck.get(replacement_card, 0)
                if i == 0:
                    # First replacement row includes the original card info
                    print(f"{original_card:<25} | {original_count:<15} | {replacement_card:<25} | {reason:<40} | {final_count:<12}")
                else:
                    # Subsequent rows don't repeat the original card info
                    print(f"{'':<25} | {'':<15} | {replacement_card:<25} | {reason:<40} | {final_count:<12}")


if __name__ == "__main__":
    # Initialize LorcanaCardFinder
    finder = LorcanaCardFinder('database/allCards.json')

    # Load collection and parse decklist
    collection = load_collection('database/export.csv')
    decklist_text = """
4 Vision of the Future
4 Tamatoa - So Shiny!
4 Brawl
4 Pawpsicle
4 Hiram Flaversham - Toymaker
1 Hide Away
3 Maui - Half-Shark
2 Be Prepared
4 Sail The Azurite Sea
4 Tipo - Growing Son
3 How Far I'll Go
1 Let it Go
1 A Pirate's Life
3 Maui - Hero to All
1 Lucky Dime
3 Maleficent - Monstrous Dragon
3 Ice Block
3 Sisu - Daring Visitor
4 Sisu - Empowered Sibling
3 Gramma Tala - Keeper of Ancient Stories
1 Raya - Kumandran Rider
    """

    decklist = parse_decklist(decklist_text)

    # Generate final decklist
    # final_deck = generate_final_deck(decklist, collection, finder)

    # Generate final decklist and log replacements
    final_deck, replacement_log = generate_final_deck(decklist, collection, finder)

    # Print or save the final deck
    for card_name, quantity in final_deck.items():
        print(f"{quantity} {card_name}")

    # Display comparison
    display_final_deck_comparison(decklist, final_deck, replacement_log)
