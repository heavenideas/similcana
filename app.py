import os
from flask import Flask, render_template, request, jsonify
from find_similar_cards import LorcanaCardFinder, format_card_details
import threading
import time
import logging

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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
            # Log the types of values we're dealing with
            logger.debug(f"Processing similar card: {card.get('name')}")
            logger.debug(f"Similarities type: {type(similarities)}")
            logger.debug(f"Overall similarity type: {type(overall_similarity)}")
            
            # Convert tensor values to Python float
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
                    logger.error(f"Value type: {type(value)}")
                    converted_similarities[key] = 0.0
            
            # Convert overall_similarity
            try:
                if hasattr(overall_similarity, 'item'):
                    overall_similarity = float(overall_similarity.item())
                elif hasattr(overall_similarity, 'tolist'):
                    overall_similarity = float(overall_similarity.tolist())
                else:
                    overall_similarity = float(overall_similarity)
            except Exception as e:
                logger.error(f"Error converting overall similarity: {e}")
                logger.error(f"Overall similarity type: {type(overall_similarity)}")
                overall_similarity = 0.0
            
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

@app.route('/get_similar_cards', methods=['POST'])
def get_similar_cards():
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

@app.route('/batch')
def batch():
    return render_template('batch.html')

@app.route('/find_similar_batch', methods=['POST'])
def find_similar_batch():
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
                    # Convert tensor values to Python float
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
                    
                    # Convert overall_similarity
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))  # Render uses PORT env variable
    app.run(host='0.0.0.0', port=port) 