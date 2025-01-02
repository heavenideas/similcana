import os
from flask import Flask, render_template, request, jsonify
from find_similar_cards import LorcanaCardFinder, format_card_details
import threading
import time
import logging
from deck_generation_from_collection import parse_decklist, generate_final_deck, display_final_deck_comparison, load_collection

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize the finder in a background thread
finder = None
def initialize_finder():
    global finder
    logger.debug("Initializing Finder")
    finder = LorcanaCardFinder('database/allCards.json')
    logger.debug("DONE - Initializing Finder")

init_thread = threading.Thread(target=initialize_finder)
init_thread.start()

def convert_similarity_values(similarities, overall_similarity):
    """Helper function to convert tensor values to Python floats"""
    # Convert individual similarities
    converted_similarities = {}
    for key, value in similarities.items():
        try:
            if hasattr(value, 'item'):
                converted_similarities[key] = float(value.item())
            elif hasattr(value, 'tolist'):
                converted_similarities[key] = float(value.tolist())
            else:
                converted_similarities[key] = float(value)
        except Exception as e:
            logger.error(f"Error converting similarity for key {key}: {e}")
            converted_similarities[key] = 0.0
    
    # Convert overall similarity
    try:
        if hasattr(overall_similarity, 'item'):
            overall_similarity = float(overall_similarity.item())
        elif hasattr(overall_similarity, 'tolist'):
            overall_similarity = float(overall_similarity.tolist())
        else:
            overall_similarity = float(overall_similarity)
    except Exception as e:
        logger.error(f"Error converting overall similarity: {e}")
        overall_similarity = 0.0
    
    return converted_similarities, overall_similarity

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/status')
def status():
    return jsonify({'ready': finder is not None})

@app.route('/find_similar', methods=['POST'])
def find_similar():
    logger.debug("find_similar route called")
    if finder is None:
        return jsonify({'error': 'System is still initializing, please wait...'})
    
    try:
        card_name = request.form.get('card_name', '').lower()
        result_count = int(request.form.get('result_count', 5))
        
        logger.debug(f"Searching for card: {card_name} with {result_count} results")
        
        target_card, similar_cards = finder.find_similar_cards(card_name, num_results=result_count)
        
        if not target_card:
            return jsonify({'error': f"Card '{card_name}' not found"})
        
        response = {
            'target_card': {
                'details': format_card_details(target_card),
                'image_url': target_card.get('images', {}).get('full', ''),
                'cardTraderUrl': target_card.get('externalLinks', {}).get('cardTraderUrl', '#')
            },
            'similar_cards': []
        }
        
        logger.debug(f"Found target card: {target_card.get('name')}")
        
        for card, similarities, overall_similarity in similar_cards:
            logger.debug(f"Processing similar card: {card.get('name')}")
            
            converted_similarities, overall_similarity = convert_similarity_values(similarities, overall_similarity)
            
            response['similar_cards'].append({
                'details': format_card_details(card),
                'image_url': card.get('images', {}).get('full', ''),
                'similarities': converted_similarities,
                'overall_similarity': overall_similarity,
                'cardTraderUrl': card.get('externalLinks', {}).get('cardTraderUrl', '#')
            })
        
        logger.debug("Successfully prepared response")
        return jsonify(response)
        
    except Exception as e:
        logger.exception("Error in find_similar route")
        return jsonify({'error': str(e)})

@app.route('/search_cards', methods=['POST'])
def search_cards():
    logger.debug("search_cards route called")
    search_term = request.form.get('search_term', '').lower()
    if len(search_term) < 2:  # Only search if we have at least 2 characters
        return jsonify([])
    
    # Search through cards and find matches
    matches = []
    for card in finder.cards:
        card_name = card.get('simpleName', '').lower()
        if search_term in card_name:
            matches.append({
                'name': card.get('fullName', ''),
                'simpleName': card.get('simpleName', ''),
                'image_url': card.get('images', {}).get('thumbnail', '')
            })
    
    # Sort matches so that names starting with the search term come first
    matches.sort(key=lambda x: (
        not x['simpleName'].lower().startswith(search_term),
        x['simpleName']
    ))
    
    # Limit results to top 10
    return jsonify(matches[:10])

@app.route('/update_weights', methods=['POST'])
def update_weights():
    new_weights = request.json
    
    # Validate weights sum to 1.0
    if abs(sum(new_weights.values()) - 1.0) > 0.001:
        return jsonify({'success': False, 'error': 'Weights must sum to 1.0'})
    
    # Update weights in the finder
    finder.weights = new_weights
    return jsonify({'success': True})

@app.route('/batch')
def batch():
    return render_template('batch.html')

@app.route('/find_similar_batch', methods=['POST'])
def find_similar_batch():
    logger.debug("find_similar_batch route called")
    if finder is None:
        return jsonify({'error': 'System is still initializing, please wait...'})
    
    try:
        data = request.get_json()
        cards = data.get('cards', [])
        result_count = int(data.get('result_count', 5))
        
        logger.debug(f"Processing batch of {len(cards)} cards")
        
        results = []
        for card_name in cards:
            logger.debug(f"Processing card: {card_name}")
            
            target_card, similar_cards = finder.find_similar_cards(card_name, num_results=result_count)
            if target_card:
                result = {
                    'target_card': {
                        'details': format_card_details(target_card),
                        'image_url': target_card.get('images', {}).get('full', ''),
                        'cardTraderUrl': target_card.get('externalLinks', {}).get('cardTraderUrl', '#')
                    },
                    'similar_cards': []
                }
                
                for card, similarities, overall_similarity in similar_cards:
                    converted_similarities, overall_similarity = convert_similarity_values(similarities, overall_similarity)
                    
                    result['similar_cards'].append({
                        'details': format_card_details(card),
                        'image_url': card.get('images', {}).get('full', ''),
                        'similarities': converted_similarities,
                        'overall_similarity': overall_similarity,
                        'cardTraderUrl': card.get('externalLinks', {}).get('cardTraderUrl', '#')
                    })
                results.append(result)
        
        logger.debug("Successfully prepared batch response")
        return jsonify(results)
        
    except Exception as e:
        logger.exception("Error in find_similar_batch route")
        return jsonify({'error': str(e)})

@app.route('/deck-comparison')
def deck_comparison():
    return render_template('deck_comparison.html')

@app.route('/analyze_deck', methods=['POST'])
def analyze_deck():
    if finder is None:
        return jsonify({'error': 'System is still initializing, please wait...'})
    
    data = request.get_json()
    decklist_text = data.get('decklist', '')

    # Load collection and parse decklist
    collection = load_collection('database/export.csv')
    decklist = parse_decklist(decklist_text)

    # Generate final decklist and log replacements
    final_deck, replacement_log = generate_final_deck(decklist, collection, finder)

    # Prepare HTML for the results
    html_output = generate_deck_comparison_html(decklist, final_deck, replacement_log)

    # Combine final deck and replacement log for the final deck results
    combined_final_deck = {}
    for card_name, quantity in final_deck.items():
        # Check if there are replacements in the log
        if card_name in replacement_log:
            # If there are replacements, we can log the final count from the replacement log
            for replacement_card, reason in replacement_log[card_name]:
                full_name = get_full_name(replacement_card)  # Get full name for the replacement card
                if replacement_card in combined_final_deck:
                    combined_final_deck[replacement_card]['final_count'] = quantity
                else:
                    combined_final_deck[replacement_card] = {
                        'name': full_name,
                        'final_count': quantity,
                        'image_url': get_image_url(replacement_card)  # Use the helper function to get the image URL
                    }
        else:
            full_name = get_full_name(card_name)  # Get full name for the original card
            if card_name in combined_final_deck:
                combined_final_deck[card_name]['final_count'] = quantity
            else:
                combined_final_deck[card_name] = {
                    'name': full_name,
                    'final_count': quantity,
                    'image_url': get_image_url(card_name)  # Use the helper function to get the image URL
                }

    # Convert the combined_final_deck dictionary to a list for the final output
    return jsonify({
        'html': html_output,
        'final_deck': list(combined_final_deck.values())  # Ensure this is included
    })

def generate_deck_comparison_html(original_decklist, final_deck, replacement_log):
    output = []
    headers = ["Original Card", "Original Count", "Replaced With", "Replacement Reason", "Final Count"]
    output.append(f"<h2>Deck Comparison</h2>")
    output.append("<table>")
    output.append("<tr>" + "".join(f"<th>{header}</th>" for header in headers) + "</tr>")

    for original_card, original_count in original_decklist.items():
        replacements = replacement_log.get(original_card, [])
        if not replacements:
            final_count = final_deck.get(original_card, 0)
            output.append(f"<tr><td>{original_card}</td><td>{original_count}</td><td>{original_card}</td><td>Card available</td><td>{final_count}</td></tr>")
        else:
            for i, (replacement_card, reason) in enumerate(replacements):
                final_count = final_deck.get(replacement_card, 0)
                if i == 0:
                    output.append(f"<tr><td>{original_card}</td><td>{original_count}</td><td>{replacement_card}</td><td>{reason}</td><td>{final_count}</td></tr>")
                else:
                    output.append(f"<tr><td></td><td></td><td>{replacement_card}</td><td>{reason}</td><td>{final_count}</td></tr>")
    
    output.append("</table>")
    return "".join(output)

def get_image_url(card_name):
    """Helper function to retrieve the image URL for a given card name."""
    for card in finder.cards:
        if card.get('simpleName', '').lower() == card_name.lower():
            return card.get('images', {}).get('full', '')  # Adjust the key as necessary
    return ''  # Return an empty string if the card is not found

def get_full_name(card_name):
    """Helper function to retrieve the full name for a given card name."""
    for card in finder.cards:
        if card.get('simpleName', '').lower() == card_name.lower():
            return card.get('fullName', '')  # Adjust the key as necessary
    return card_name  # Return the simple name if the full name is not found

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))  # Render uses PORT env variable
    app.run(host='0.0.0.0', port=port) 