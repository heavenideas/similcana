import json

def process_lorcana_data(filepath):
    """
    Processes Lorcana JSON data to extract key information for deckbuilding.

    Args:
        filepath (str): The path to the JSON file.

    Returns:
        list: A list of dictionaries, each representing a processed card.
    """

    processed_cards = []

    with open(filepath, 'r', encoding='utf-8') as f:
      data = json.load(f)

    for card in data.get('cards', []):
        processed_card = {
            "ink_cost": card.get("cost"),
            "card_type": card.get("type"),
            "tags": card.get("subtypes", []),
            "mechanics": [],
            "ability": card.get("fullText", ""),  # keep full ability text
            "strength": card.get("strength"),
            "willpower": card.get("willpower"),
            "lore_points": card.get("lore"),
            "ink_color": card.get("color"),
             "inkwell": card.get("inkwell", False)

        }

        # Extract keywords from abilities and add to mechanics list
        for ability in card.get("abilities", []):
          if ability.get("type") == "keyword":
            keyword_name = ability.get("keyword")
            if ability.get("keywordValue"):
              keyword_name = f"{keyword_name} {ability.get('keywordValue')}"

            processed_card["mechanics"].append(keyword_name)



        processed_cards.append(processed_card)

    return processed_cards



if __name__ == '__main__':
    filepath = '/Users/inesdemenaurrutia/PycharmProjects/Similicana/LorcanaJSON/output/generated/allCards.json'  # Replace with your actual file path
    processed_data = process_lorcana_data(filepath)

    processed_data_filepath = '/Users/inesdemenaurrutia/PycharmProjects/Similicana/LorcanaJSON/output/generated/processed_lorcana_data.json'

    # Optional: Print the processed data (or save it to another file)
    # for card in processed_data:
    #     print(card)
    #     print("---")
    with open(processed_data_filepath, 'w', encoding='utf-8') as outfile:
      json.dump(processed_data, outfile, indent=2)
    print(f"Processed data saved to {processed_data_filepath}")
