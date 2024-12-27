let isSystemReady = false;

function checkSystemStatus() {
    fetch('/status')
        .then(response => response.json())
        .then(data => {
            if (data.ready) {
                isSystemReady = true;
                document.getElementById('searchButton').disabled = false;
                document.getElementById('cardSearch').disabled = false;
            } else {
                setTimeout(checkSystemStatus, 1000);
            }
        });
}

let searchTimeout = null;
const SEARCH_DELAY = 300; // milliseconds

function setLoading(isLoading) {
    const spinner = document.getElementById('loadingSpinner');
    const searchButton = document.getElementById('searchButton');
    const searchInput = document.getElementById('cardSearch');
    const resultsSection = document.querySelector('.results-section');

    if (isLoading) {
        spinner.classList.remove('hidden');
        searchButton.classList.add('disabled');
        searchInput.classList.add('disabled');
        searchButton.disabled = true;
        searchInput.disabled = true;
        resultsSection.style.opacity = '0.5';
    } else {
        spinner.classList.add('hidden');
        searchButton.classList.remove('disabled');
        searchInput.classList.remove('disabled');
        searchButton.disabled = false;
        searchInput.disabled = false;
        resultsSection.style.opacity = '1';
    }
}

function findSimilarCards() {
    if (!isSystemReady) {
        alert('System is still initializing, please wait...');
        return;
    }
    const cardName = document.getElementById('cardSearch').value;
    const resultCount = document.getElementById('resultCount').value;
    
    // Show loading state
    setLoading(true);
    
    fetch('/find_similar', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `card_name=${encodeURIComponent(cardName)}&result_count=${encodeURIComponent(resultCount)}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
            return;
        }
        displayResults(data);
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while fetching results');
    })
    .finally(() => {
        // Hide loading state
        setLoading(false);
    });
}

function displayResults(data) {
    // Store original card details for comparison
    window.originalCardDetails = data.target_card.details;
    
    // Display target card
    const targetCard = data.target_card;
    document.getElementById('targetCardDisplay').innerHTML = createCardHTML(targetCard, null);

    // Display similar cards
    const similarCardsHTML = data.similar_cards
        .map(card => createCardHTML(card, card.overall_similarity))
        .join('');
    document.getElementById('similarCardsDisplay').innerHTML = similarCardsHTML;
}

function createSimilarityHTML(similarities) {
    if (!similarities) return '';
    
    const similarityDetails = [
        { key: 'ink_cost', label: 'Ink Cost' },
        { key: 'strength', label: 'Strength' },
        { key: 'willpower', label: 'Willpower' },
        { key: 'lore_points', label: 'Lore Points' },
        { key: 'tags', label: 'Tags' },
        { key: 'ability', label: 'Ability' },
        { key: 'mechanics', label: 'Mechanics' },
        { key: 'ink_color', label: 'Ink Color' },
        { key: 'card_type', label: 'Card Type' },
        { key: 'inkwell', label: 'Inkwell' }
    ];

    return `
        <div class="similarity-details">
            <h3>Similarity Breakdown:</h3>
            <div class="similarity-grid">
                ${similarityDetails.map(({ key, label }) => `
                    <div class="similarity-item">
                        <span class="similarity-label">${label}:</span>
                        <span class="similarity-value">${(similarities[key] * 100).toFixed(1)}%</span>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
}

function createCardHTML(card, similarity) {
    const similarityHTML = similarity !== null 
        ? `<div class="similarity-score">Overall Similarity: ${(similarity * 100).toFixed(1)}%</div>`
        : '';

    // Helper function to calculate and format the difference
    const getDifference = (originalValue, currentValue) => {
        if (originalValue === undefined || currentValue === undefined) return '';
        const diff = currentValue - originalValue;
        if (diff === 0) return '';
        return `<span class="value-difference ${diff > 0 ? 'positive' : 'negative'}">(${diff > 0 ? '+' : ''}${diff})</span>`;
    };

    // Helper function to create attribute HTML with similarity tooltip and difference
    const createAttributeHTML = (label, value, similarityKey, originalValue) => {
        const similarityValue = card.similarities && card.similarities[similarityKey]
            ? `${(card.similarities[similarityKey] * 100).toFixed(1)}% similar`
            : null;
        
        const tooltipAttr = similarityValue 
            ? `data-tooltip="${similarityValue}"` 
            : '';

        const difference = similarity !== null ? getDifference(originalValue, value) : '';

        return `
            <div class="attribute" ${tooltipAttr}>
                <span class="attribute-label">${label}:</span>
                <span>${value} ${difference}</span>
            </div>
        `;
    };

    // Use the cardTraderUrl directly from the response instead of constructing it
    const cardTraderUrl = card.cardTraderUrl;

    // Get original card values if this is a similar card
    const originalCard = window.originalCardDetails;

    // Fix: Get the correct simpleName from the card object structure
    const cardSimpleName = card.details?.simpleName || card.simpleName || '';
    
    // Debug log to verify the card name
    console.log('Card being rendered:', cardSimpleName);

    // Fix: Update the click handler to use a data attribute instead of inline onclick
    const imageClickHandler = similarity !== null ? 
        `data-card-name="${cardSimpleName.replace(/"/g, '&quot;')}" class="clickable-card-image"` : '';

    return `
        <div class="card-display">
            <div class="card-image-container">
                <img class="card-image" src="${card.image_url}" 
                     alt="${card.details.fullName}"
                     ${imageClickHandler}>
                ${similarity !== null ? '<div class="click-hint">Click to find similar cards</div>' : ''}
                <div class="card-market-info">
                    <a href="${cardTraderUrl}" 
                       target="_blank" 
                       rel="noopener noreferrer" 
                       class="cardtrader-link">
                        Check price on CardTrader
                    </a>
                </div>
            </div>
            <div class="card-details">
                ${similarityHTML}
                ${createAttributeHTML('Name', card.details.fullName)}
                ${createAttributeHTML('Color', card.details.color, 'ink_color', originalCard?.color)}
                ${createAttributeHTML('Cost', card.details.cost, 'ink_cost', originalCard?.cost)}
                ${createAttributeHTML('Strength', card.details.strength, 'strength', originalCard?.strength)}
                ${createAttributeHTML('Willpower', card.details.willpower, 'willpower', originalCard?.willpower)}
                ${createAttributeHTML('Lore', card.details.lore, 'lore_points', originalCard?.lore)}
                ${createAttributeHTML('Text', card.details.fullText, 'ability')}
                ${similarity !== null ? createSimilarityHTML(card.similarities) : ''}
            </div>
        </div>
    `;
}

function initializeSearch() {
    const searchInput = document.getElementById('cardSearch');
    const searchResults = document.getElementById('searchResults');

    // Add input event listener for search
    searchInput.addEventListener('input', function(e) {
        const searchTerm = e.target.value.trim();
        
        // Clear previous timeout
        if (searchTimeout) {
            clearTimeout(searchTimeout);
        }

        // Hide results if search term is too short
        if (searchTerm.length < 2) {
            searchResults.classList.add('hidden');
            return;
        }

        // Set new timeout for search
        searchTimeout = setTimeout(() => {
            performSearch(searchTerm);
        }, SEARCH_DELAY);
    });

    // Close search results when clicking outside
    document.addEventListener('click', function(e) {
        if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
            searchResults.classList.add('hidden');
        }
    });
}

function performSearch(searchTerm) {
    fetch('/search_cards', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `search_term=${encodeURIComponent(searchTerm)}`
    })
    .then(response => response.json())
    .then(results => {
        displaySearchResults(results);
    })
    .catch(error => {
        console.error('Error searching cards:', error);
    });
}

function displaySearchResults(results) {
    const searchResults = document.getElementById('searchResults');
    
    if (results.length === 0) {
        searchResults.classList.add('hidden');
        return;
    }

    searchResults.innerHTML = results.map(card => `
        <div class="search-result-item" onclick="selectCard('${card.simpleName}')">
            <img src="${card.image_url}" alt="${card.name}" onerror="this.src='placeholder.jpg'">
            <span class="search-result-name">${card.name}</span>
        </div>
    `).join('');

    searchResults.classList.remove('hidden');
}

function selectCard(cardName) {
    const searchInput = document.getElementById('cardSearch');
    searchInput.value = cardName;
    document.getElementById('searchResults').classList.add('hidden');
    findSimilarCards();
}

const defaultWeights = {
    ink_cost: 0.15,
    strength: 0.10,
    willpower: 0.10,
    lore_points: 0.10,
    tags: 0.01,
    ability: 0.24,
    mechanics: 0.15,
    ink_color: 0.05,
    card_type: 0.05,
    inkwell: 0.05
};

let currentWeights = { ...defaultWeights };

function initializeWeightsPanel() {
    const toggleButton = document.getElementById('toggleWeights');
    const weightsControls = document.getElementById('weightsControls');
    const resetButton = document.getElementById('resetWeights');
    const applyButton = document.getElementById('applyWeights');
    
    // Toggle weights panel
    toggleButton.addEventListener('click', () => {
        weightsControls.classList.toggle('hidden');
        toggleButton.querySelector('.toggle-icon').textContent = 
            weightsControls.classList.contains('hidden') ? '▼' : '▲';
    });
    
    // Initialize all sliders
    document.querySelectorAll('.weight-slider').forEach(slider => {
        slider.addEventListener('input', updateWeights);
    });
    
    // Reset weights
    resetButton.addEventListener('click', resetWeights);
    
    // Apply weights
    applyButton.addEventListener('click', applyWeights);
}

function updateWeights() {
    let total = 0;
    const sliders = document.querySelectorAll('.weight-slider');
    
    // Calculate new values
    sliders.forEach(slider => {
        const value = parseInt(slider.value) / 100;
        total += value;
        slider.nextElementSibling.textContent = value.toFixed(2);
        currentWeights[slider.dataset.weightName] = value;
    });
    
    // Update total display
    const totalElement = document.getElementById('weightsTotal');
    const warningElement = document.getElementById('weightsTotalWarning');
    const applyButton = document.getElementById('applyWeights');
    
    totalElement.textContent = total.toFixed(2);
    
    if (Math.abs(total - 1.0) > 0.001) {
        totalElement.classList.add('invalid');
        warningElement.classList.remove('hidden');
        applyButton.disabled = true;
    } else {
        totalElement.classList.remove('invalid');
        warningElement.classList.add('hidden');
        applyButton.disabled = false;
    }
}

function resetWeights() {
    currentWeights = { ...defaultWeights };
    
    document.querySelectorAll('.weight-slider').forEach(slider => {
        const defaultValue = defaultWeights[slider.dataset.weightName] * 100;
        slider.value = defaultValue;
        slider.nextElementSibling.textContent = (defaultValue / 100).toFixed(2);
    });
    
    updateWeights();
}

function applyWeights() {
    // Send weights to backend
    fetch('/update_weights', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(currentWeights)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // If there's an active search, refresh results
            const currentSearch = document.getElementById('cardSearch').value;
            if (currentSearch) {
                findSimilarCards();
            }
        }
    });
}

function initializeStickyHeader() {
    const targetCard = document.querySelector('.target-card');
    if (!targetCard) return;

    window.addEventListener('scroll', () => {
        if (window.scrollY > 0) {
            targetCard.classList.add('scrolled');
        } else {
            targetCard.classList.remove('scrolled');
        }
    });
}

// Add this new function to initialize click handlers
function initializeCardClickHandlers() {
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('clickable-card-image')) {
            const cardName = e.target.getAttribute('data-card-name');
            console.log('Clicked card name:', cardName);
            if (cardName) {
                searchForCard(cardName);
            }
        }
    });
}

// Add this new function to handle card image clicks
function searchForCard(cardName) {
    if (!cardName) {
        console.error('No card name provided');
        return;
    }
    
    console.log('Searching for card:', cardName);
    const searchInput = document.getElementById('cardSearch');
    searchInput.value = cardName;
    findSimilarCards();
    
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}

// Add this to your existing window.onload or at the bottom of your script
document.addEventListener('DOMContentLoaded', function() {
    initializeSearch();
    initializeWeightsPanel();
    initializeStickyHeader();
    initializeCardClickHandlers();
    document.getElementById('searchButton').disabled = true;
    document.getElementById('cardSearch').disabled = true;
    checkSystemStatus();
});

// Add event listener for Enter key in search box
document.getElementById('cardSearch').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        findSimilarCards();
    }
});

// Add this new function to handle card image clicks
function searchForCard(cardName) {
    if (!cardName) {
        console.error('No card name provided');
        return;
    }
    
    const searchInput = document.getElementById('cardSearch');
    searchInput.value = cardName;
    findSimilarCards();
    
    // Scroll to top of page
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
} 