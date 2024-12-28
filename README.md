# Similcana

A web application for finding similar Lorcana cards based on various attributes and characteristics.

![Similicana Main View](img/similicana_main_screenshot.png)


## Disclaimer

>This project is not affiliated with or endorsed by the creators of Lorcana. It is a personal project created for fun and to experiment with finding an easier way to find similar cards for deck building. 
>I'm not claiming this is good code, and it's provided as is. Feel free to use it for your own purposes, but I'm not responsible for any issues it may cause. 

## Background

I wanted to find a way to easily find similar cards for deck building. One of the most common issues is not having access to specific cards that are common in competitive decks, because they are either too expensive or not available on the secondary market. 

Also I felt that there are a lot of cards that are similar in some way, but not exactly the same, and it would be helpful to have a way to find them to better utilize your collection. 

Think of it as a poor man's deckbuilder helper.

I did try to find a similar tool, but I couldn't find anything that was exactly what I wanted, so I decided to build my own. 

## Features

- Find similar cards based on multiple attributes
- Adjustable similarity weights
- Interactive web interface
- Real-time card comparison
- Price checking integration with CardTrader

### Attributes Breakdown

Here is a breakdown of the attributes that are used to compare cards. 

- Ink Cost: Ink cost of the card.
- Strength: Strength of the card.
- Willpower: Willpower of the card.
- Lore Points: Lore points of the card.
- Tags: List of tags that are on the card.
- Ability: The ability text of the card. *This is one of the key features of this project.* I use a sentence transformer model to embed the ability text and then compare the embeddings to find similar cards. The idea being that through the embedding process, the ability text is converted into a vector space where the similarity can be calculated. This might lead to interesting results that might not be obvious otherwise.
- Mechanics: This is a list of mechanics that are on the cards abilities section. The list is not exhaustive, but it is a start.
- Ink Color: Amber, Amethyst, Emerald, Ruby, Sapphire, Steel
- Card Type: Character, Action, Item, Location
- Inkwell: is this card inkable or not?


# Technical Details

## Requirements

- Python 3.9+
- Dependencies listed in requirements.txt

## Installation

1. Clone the repository: 

```bash
git clone https://github.com/heavenideas/similcana.git
cd similcana
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```
4. Ensure the database file is present:
- Place `allCards.json` in the `database/` directory

## Usage

1. Start the Flask application:

```bash
python app.py
```

2. Access the application in your web browser at `http://127.0.0.1:5000/`


## Project Structure

- `app.py`: Main Flask application
- `database/`: Database files
- `static/`: Static files (CSS, JavaScript)
- `templates/`: HTML templates
- `requirements.txt`: Project dependencies


## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- LorcanaJSON: The LorcanaJSON project is a great resource for Lorcana card data. I used the data from this project to create my database.
