import os
from flask import Flask, render_template, request, jsonify
from find_similar_cards import LorcanaCardFinder, format_card_details
import threading
import time

app = Flask(__name__)

# Initialize the finder in a background thread
finder = None
def initialize_finder():
    global finder
    finder = LorcanaCardFinder('database/allCards.json')

init_thread = threading.Thread(target=initialize_finder)
init_thread.start()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/status')
def status():
    return jsonify({'ready': finder is not None})

@app.route('/find_similar', methods=['POST'])
def find_similar():
    if finder is None:
        return jsonify({'error': 'System is still initializing, please wait...'})
        
    card_name = request.form.get('card_name', '').lower()
    result_count = int(request.form.get('result_count', 5))
    
    target_card, similar_cards = finder.find_similar_cards(card_name, num_results=result_count)
    
    if not target_card:
        return jsonify({'error': f"Card '{card_name}' not found"})
    
    response = {
        'target_card': {
            'details': format_card_details(target_card),
            'image_url': target_card.get('images', {}).get('full', ''),
        },
        'similar_cards': []
    }
    
    for card, similarities, overall_similarity in similar_cards:
        converted_similarities = {
            k: float(v) for k, v in similarities.items()
        }
        
        response['similar_cards'].append({
            'details': format_card_details(card),
            'image_url': card.get('images', {}).get('full', ''),
            'similarities': converted_similarities,
            'overall_similarity': float(overall_similarity)
        })
    
    return jsonify(response)

@app.route('/search_cards', methods=['POST'])
def search_cards():
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))  # Render uses PORT env variable
    app.run(host='0.0.0.0', port=port) 