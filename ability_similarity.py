from find_similar_cards import LorcanaCardFinder
import sys
import numpy as np

def progress_bar(current, total, width=50):
    """Display a simple progress bar."""
    progress = float(current) / total
    filled = int(width * progress)
    bar = '█' * filled + '░' * (width - filled)
    percent = int(100 * progress)
    return f'\r[{bar}] {percent}% ({current}/{total})'

def print_table(headers, rows, column_widths=None):
    """Print a simple text table with dynamic column widths."""
    if not column_widths:
        column_widths = []
        for i in range(len(headers)):
            width = max(
                len(str(headers[i])),
                max(len(str(row[i])) for row in rows)
            )
            column_widths.append(width + 2)
    
    header_line = "│"
    for header, width in zip(headers, column_widths):
        header_line += f" {header:<{width}} │"
    
    separator = "├" + "┼".join("─" * width for width in column_widths) + "┤"
    top_border = "┌" + "┬".join("─" * width for width in column_widths) + "┐"
    bottom_border = "└" + "┴".join("─" * width for width in column_widths) + "┘"
    
    print(top_border)
    print(header_line)
    print(separator)
    
    for row in rows:
        row_line = "│"
        for item, width in zip(row, column_widths):
            row_line += f" {str(item):<{width}} │"
        print(row_line)
    
    print(bottom_border)

def get_processed_ability_text(card):
    """Use the same ability text processing as in LorcanaCardFinder._convert_card_format."""
    if card.get('type') == 'Action':
        return ' '.join(card.get('effects', []))
    
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
    
    return ' '.join(processed_abilities)

def precompute_embeddings(finder):
    """Precompute embeddings for all cards with abilities."""
    print("\n📊 Precomputing embeddings for all cards...")
    
    # Store card data and embeddings
    valid_cards = []
    ability_texts = []
    processed_abilities = []
    
    for card in finder.cards:
        processed_text = get_processed_ability_text(card)
        if processed_text.strip():  # Only include cards with non-empty processed abilities
            valid_cards.append(card)
            ability_texts.append(processed_text)
            processed_abilities.append(processed_text)
    
    # Batch compute embeddings
    total = len(ability_texts)
    print(f"Found {total} cards with abilities")
    
    # Compute all embeddings at once
    embeddings = finder.model.encode(ability_texts, batch_size=32, show_progress_bar=True)
    
    return valid_cards, embeddings, processed_abilities

def find_similar_abilities(finder, card_name, valid_cards, all_embeddings, processed_abilities):
    print("\n🔍 Searching for card...")
    target_card = next((card for card in valid_cards 
                       if card.get('simpleName', '').lower() == card_name.lower()), None)
    
    if not target_card:
        print(f"❌ Card '{card_name}' not found.")
        return

    target_processed_ability = get_processed_ability_text(target_card)
    if not target_processed_ability:
        print(f"❌ Card '{card_name}' has no abilities.")
        return

    print(f"✅ Found card: {target_card['name']}")
    print(f"Processed ability text: {target_processed_ability}")
    
    # Get target card's embedding
    target_idx = valid_cards.index(target_card)
    target_embedding = all_embeddings[target_idx]
    
    similarity_functions = ['cosine', 'dot', 'euclidean', 'manhattan']
    results = []

    print("\n📊 Computing similarities...")
    for sim_idx, sim_function in enumerate(similarity_functions):
        print(f"\n⚙️  Using {sim_function} similarity ({sim_idx + 1}/{len(similarity_functions)})")
        finder.set_similarity_function(sim_function)
        
        # Compute similarities for all cards at once
        similarities = []
        for idx, (card, embedding) in enumerate(zip(valid_cards, all_embeddings)):
            if card['fullName'] == target_card['fullName']:
                continue
            
            # Calculate similarity based on the metric
            if sim_function == 'cosine':
                sim = np.dot(target_embedding, embedding) / (np.linalg.norm(target_embedding) * np.linalg.norm(embedding))
            elif sim_function == 'dot':
                sim = np.dot(target_embedding, embedding)
            elif sim_function == 'euclidean':
                distance = np.linalg.norm(target_embedding - embedding)
                sim = max(0, 1 - distance / 20.0)  # Convert distance to similarity
            else:  # manhattan
                distance = np.sum(np.abs(target_embedding - embedding))
                sim = max(0, 1 - distance / 20.0)  # Convert distance to similarity
            
            similarities.append((sim, card['name'], processed_abilities[idx]))

        # Sort and get top 5
        similarities.sort(reverse=True)
        for sim, name, ability in similarities[:5]:
            results.append([sim_function, f"{sim:.3f}", name, ability])

    print("\n🎯 Results for similar abilities:\n")
    print(f"Target card: {target_card['name']}")
    print(f"Processed ability: {target_processed_ability}\n")
    
    headers = ["Metric", "Score", "Card Name", "Processed Ability Text"]
    print_table(headers, results)
    print("\n✨ Analysis complete!")

if __name__ == "__main__":
    print("🔧 Initializing card finder...")
    finder = LorcanaCardFinder('database/allCards.json')
    
    # Precompute all embeddings once
    valid_cards, all_embeddings, processed_abilities = precompute_embeddings(finder)
    print("✅ Initialization complete!")
    
    while True:
        card_name = input("\n📝 Enter card name (or 'quit' to exit): ")
        if card_name.lower() == 'quit':
            break
        find_similar_abilities(finder, card_name, valid_cards, all_embeddings, processed_abilities) 