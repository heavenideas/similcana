let isSystemReady = false;

function checkSystemStatus() {
    fetch('/status')
        .then(response => response.json())
        .then(data => {
            if (data.ready) {
                isSystemReady = true;
                const currentPath = window.location.pathname;
                if (currentPath === '/') {
                    const searchInput = document.getElementById('cardSearch');
                    const searchButton = document.getElementById('searchButton');
                    if (searchInput && searchButton) {
                        searchInput.disabled = false;
                        searchButton.disabled = false;
                    }
                } else if (currentPath === '/batch') {
                    const batchInput = document.getElementById('batchCardInput');
                    const analyzeButton = document.querySelector('button[onclick="findSimilarCardsForBatch()"]');
                    if (batchInput && analyzeButton) {
                        batchInput.disabled = false;
                        analyzeButton.disabled = false;
                    }
                }
            } else {
                setTimeout(checkSystemStatus, 1000);
            }
        });
}

let searchTimeout = null;
const SEARCH_DELAY = 300; // milliseconds

function setLoading(isLoading) {
    const spinner = document.getElementById('loadingSpinner');
    const resultsSection = document.querySelector('.results-section');
    
    // Get the current page path to determine which elements to manipulate
    const currentPath = window.location.pathname;
    
    if (currentPath === '/') {
        // Single card view
        const searchButton = document.getElementById('searchButton');
        const searchInput = document.getElementById('cardSearch');
        
        if (isLoading) {
            spinner.classList.remove('hidden');
            searchButton.classList.add('disabled');
            searchInput.classList.add('disabled');
            searchButton.disabled = true;
            searchInput.disabled = true;
            if (resultsSection) {
                resultsSection.style.opacity = '0.5';
            }
        } else {
            spinner.classList.add('hidden');
            searchButton.classList.remove('disabled');
            searchInput.classList.remove('disabled');
            searchButton.disabled = false;
            searchInput.disabled = false;
            if (resultsSection) {
                resultsSection.style.opacity = '1';
            }
        }
    } else if (currentPath === '/batch') {
        // Batch view
        const analyzeButton = document.querySelector('button[onclick="findSimilarCardsForBatch()"]');
        const batchInput = document.getElementById('batchCardInput');
        const batchResults = document.getElementById('batchResults');
        
        if (isLoading) {
            spinner.classList.remove('hidden');
            analyzeButton.disabled = true;
            batchInput.disabled = true;
            if (batchResults) {
                batchResults.style.opacity = '0.5';
            }
        } else {
            spinner.classList.add('hidden');
            analyzeButton.disabled = false;
            batchInput.disabled = false;
            if (batchResults) {
                batchResults.style.opacity = '1';
            }
        }
    }
}

function findSimilarCards() {
    if (!isSystemReady) {
        alert('Find Similar Cards: error message:System is still initializing, please wait...');
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
    const getDifference = (originalValue, currentValue, skipDiff = false) => {
        if (skipDiff || originalValue === undefined || currentValue === undefined) return '';
        const diff = currentValue - originalValue;
        if (diff === 0) return '';
        return `<span class="value-difference ${diff > 0 ? 'positive' : 'negative'}">(${diff > 0 ? '+' : ''}${diff})</span>`;
    };

    // Helper function to create attribute HTML with similarity tooltip and difference
    const createAttributeHTML = (label, value, similarityKey, originalValue, skipDiff = false) => {
        const similarityValue = card.similarities && card.similarities[similarityKey]
            ? `${(card.similarities[similarityKey] * 100).toFixed(1)}% similar`
            : null;
        
        const tooltipAttr = similarityValue 
            ? `data-tooltip="${similarityValue}"` 
            : '';

        const difference = similarity !== null ? getDifference(originalValue, value, skipDiff) : '';

        return `
            <div class="attribute" ${tooltipAttr}>
                <span class="attribute-label">${label}:</span>
                <span>${value} ${difference}</span>
            </div>
        `;
    };

    // Helper function to format color display
    const formatColor = (color) => {
        if (!color) return '';
        // For dual colors, add a special class and formatting
        if (color.includes('-')) {
            const colors = color.split('-');
            return `<span class="dual-color">${colors.join(' / ')}</span>`;
        }
        return color;
    };

    const cardTraderUrl = card.cardTraderUrl;
    const originalCard = window.originalCardDetails;
    const cardSimpleName = card.details?.simpleName || card.simpleName || '';

    const imageClickHandler = similarity !== null ? 
        `data-card-name="${cardSimpleName.replace(/"/g, '&quot;')}" class="clickable-card-image"` : '';

    const mechanics = card.details?.mechanics || [];
    
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
                ${createAttributeHTML('Color', formatColor(card.details.color), 'ink_color', originalCard?.color, true)}
                ${createAttributeHTML('Cost', card.details.cost, 'ink_cost', originalCard?.cost)}
                ${createAttributeHTML('Strength', card.details.strength, 'strength', originalCard?.strength)}
                ${createAttributeHTML('Willpower', card.details.willpower, 'willpower', originalCard?.willpower)}
                ${createAttributeHTML('Lore', card.details.lore, 'lore_points', originalCard?.lore)}
                ${createAttributeHTML('Text', card.details.fullText, 'ability')}
                ${createAttributeHTML('Mechanics', mechanics.length > 0 ? mechanics.join(', ') : 'None', 'mechanics', originalCard?.mechanics, true)}
                ${similarity !== null ? createSimilarityHTML(card.similarities) : ''}
            </div>
        </div>
    `;
}

// New function for batch card results
function createBatchCardHTML(card) {
    // This function handles the display of a card in batch results
    return `
        <div class="compact-card">
            <div class="card-image-container">
                <img src="${card.image_url}" alt="${card.details.fullName}" data-card-image>
                <div class="card-zoom">
                    <img src="${card.image_url}" alt="${card.details.fullName}">
                </div>
            </div>
            <div class="compact-card-info">
                <div class="compact-card-name">${card.details.fullName}</div>
                <div class="compact-card-similarity">${(card.overall_similarity * 100).toFixed(1)}%</div>
                <div class="compact-card-details">
                    ${createCompactSimilarityBreakdown(card.similarities)}
                </div>
            </div>
        </div>
    `;
}

// Function to create a compact similarity breakdown for batch results
function createCompactSimilarityBreakdown(similarities) {
    const keyMetrics = [
        { key: 'ability', label: 'Ability' },
        { key: 'mechanics', label: 'Mechanics' },
        { key: 'ink_cost', label: 'Cost' }
    ];

    return keyMetrics.map(({ key, label }) => `
        <div class="compact-similarity-item">
            <span class="compact-similarity-label">${label}:</span>
            <span class="compact-similarity-value">${(similarities[key] * 100).toFixed(0)}%</span>
        </div>
    `).join('');
}

function initializeSearch() {
    const searchInput = document.getElementById('cardSearch');
    const searchResults = document.getElementById('searchResults');
    
    if (!searchInput || !searchResults) return;

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

// Remove duplicate searchForCard functions and keep one version
function searchForCard(cardName) {
    if (!cardName) {
        console.error('No card name provided');
        return;
    }
    
    // Check if we're on the single card analysis page
    if (window.location.pathname !== '/') {
        window.location.href = `/?card=${encodeURIComponent(cardName)}`;
        return;
    }
    
    const searchInput = document.getElementById('cardSearch');
    if (searchInput) {
        searchInput.value = cardName;
        findSimilarCards();
        
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    }
}

function processBatchCardList(text) {
    // Split by newlines and process each line
    return text.split('\n')
        .map(line => line.trim())
        // Remove empty lines
        .filter(line => line)
        // Remove quantity numbers and trim
        .map(line => line.replace(/^\d+\s+/, ''))
        // Remove duplicate cards
        .filter((card, index, self) => self.indexOf(card) === index);
}

function findSimilarCardsForBatch() {
    const cardList = document.getElementById('batchCardInput').value;
    const resultCount = document.getElementById('resultCount').value;
    const processedCards = processBatchCardList(cardList);
    const loadingSpinner = document.getElementById('loadingSpinner');
    const progressContainer = document.getElementById('progressContainer');
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    
    // Reset and show progress elements
    progressBar.style.width = '0%';
    progressText.textContent = 'Processing cards: 0/0';
    progressContainer.classList.remove('hidden');
    loadingSpinner.classList.add('hidden');
    
    // Set up progress event source
    if (progressEventSource) {
        progressEventSource.close();
    }
    progressEventSource = new EventSource('/batch_progress');
    progressEventSource.onmessage = function(event) {
        const progress = JSON.parse(event.data);
        const percentage = (progress.current / progress.total * 100) || 0;
        progressBar.style.width = `${percentage}%`;
        progressText.textContent = `Processing cards: ${progress.current}/${progress.total}`;
        
        if (progress.current >= progress.total && progress.total > 0) {
            progressEventSource.close();
        }
    };
    
    fetch('/find_similar_batch', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            cards: processedCards,
            result_count: resultCount
        })
    })
    .then(response => response.json())
    .then(data => {
        progressContainer.classList.add('hidden');
        if (data.error) {
            alert(data.error);
            return;
        }
        displayBatchResults(data);
    })
    .catch(error => {
        progressContainer.classList.add('hidden');
        console.error('Error:', error);
        alert('An error occurred while fetching results');
    });
}

function displayBatchResults(data) {
    const resultsContainer = document.getElementById('batchResults');
    resultsContainer.innerHTML = '';

    // Create a container for each source card and its similar cards
    data.forEach(result => {
        const cardSection = document.createElement('div');
        cardSection.className = 'batch-card-section';
        
        // Update header to include card-image-container for zoom functionality
        cardSection.innerHTML = `
            <div class="batch-card-header" onclick="toggleSection(this)">
                <div class="card-image-container">
                    <img src="${result.target_card.image_url}" 
                         class="batch-card-thumbnail" 
                         data-card-image>
                    <div class="card-zoom">
                        <img src="${result.target_card.image_url}" 
                             alt="${result.target_card.details.fullName}">
                    </div>
                </div>
                <h3>${result.target_card.details.fullName}</h3>
                <span class="expand-icon">▼</span>
            </div>
            <div class="batch-card-content">
                <div class="similar-cards-grid">
                    ${result.similar_cards
                        .map(card => createCompactCardHTML(card))
                        .join('')}
                </div>
            </div>
        `;
        
        resultsContainer.appendChild(cardSection);
    });
}

function createCompactCardHTML(card) {
    const similarity = card.overall_similarity;
    return `
        <div class="compact-card">
            <div class="card-image-container">
                <img src="${card.image_url}" alt="${card.details.fullName}" data-card-image>
                <div class="card-zoom">
                    <img src="${card.image_url}" alt="${card.details.fullName}">
                </div>
            </div>
            <div class="compact-card-info">
                <div class="compact-card-name">${card.details.fullName}</div>
                <div class="compact-card-similarity">${(similarity * 100).toFixed(1)}%</div>
                <div class="compact-card-details">
                    ${createCompactSimilarityBreakdown(card.similarities)}
                </div>
            </div>
        </div>
    `;
}

function createCompactSimilarityBreakdown(similarities) {
    const keyMetrics = [
        { key: 'ability', label: 'Ability' },
        { key: 'mechanics', label: 'Mechanics' },
        { key: 'ink_cost', label: 'Cost' }
    ];

    return keyMetrics.map(({ key, label }) => `
        <div class="compact-similarity-item">
            <span class="compact-similarity-label">${label}:</span>
            <span class="compact-similarity-value">${(similarities[key] * 100).toFixed(0)}%</span>
        </div>
    `).join('');
}

function toggleSection(header) {
    const content = header.nextElementSibling;
    const icon = header.querySelector('.expand-icon');
    
    content.style.display = content.style.display === 'none' ? 'block' : 'none';
    icon.textContent = content.style.display === 'none' ? '▼' : '▲';
}

function initializeImageZoom() {
    document.addEventListener('mouseover', function(e) {
        const cardImage = e.target.closest('[data-card-image]');
        if (cardImage) {
            const zoomContainer = cardImage.nextElementSibling; // Get the zoom container
            if (zoomContainer && zoomContainer.classList.contains('card-zoom')) {
                zoomContainer.style.display = 'block'; // Show the zoom container
                // Add small delay before adding visible class for transition
                setTimeout(() => zoomContainer.classList.add('visible'), 10);
                
                // Position the zoom container
                document.addEventListener('mousemove', updateZoomPosition);
                
                function updateZoomPosition(e) {
                    const x = e.clientX + 20;
                    const y = e.clientY + 20;
                    
                    // Check if the zoom container would go off screen
                    const rect = zoomContainer.getBoundingClientRect();
                    const maxX = window.innerWidth - rect.width - 20; // Add padding
                    const maxY = window.innerHeight - rect.height - 20; // Add padding
                    
                    // Adjust position to keep zoom in viewport
                    let finalX = x;
                    let finalY = y;
                    
                    if (x > maxX) {
                        finalX = e.clientX - rect.width - 20; // Show on left side of cursor
                    }
                    if (y > maxY) {
                        finalY = Math.max(20, maxY); // Stick to top if needed
                    }
                    
                    zoomContainer.style.left = finalX + 'px';
                    zoomContainer.style.top = finalY + 'px';
                }
                
                // Clean up when mouse leaves
                cardImage.addEventListener('mouseleave', function cleanup() {
                    zoomContainer.classList.remove('visible');
                    setTimeout(() => {
                        zoomContainer.style.display = 'none';
                    }, 200); // Match transition duration
                    document.removeEventListener('mousemove', updateZoomPosition);
                    cardImage.removeEventListener('mouseleave', cleanup);
                }, { once: true });
            }
        }
    });
}

// Update the DOMContentLoaded event listener
document.addEventListener('DOMContentLoaded', function() {
    // Get the current page path
    const currentPath = window.location.pathname;
    
    // Initialize weights panel for both views
    if (document.getElementById('weightsControls')) {
        initializeWeightsPanel();
    }
    
    if (currentPath === '/') {
        // Initialize single card analysis page
        const searchInput = document.getElementById('cardSearch');
        if (searchInput) {
            initializeSearch();
            initializeStickyHeader();
            initializeCardClickHandlers();
            initializeImageZoom();
            
            // Add event listener for Enter key in search box
            searchInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    findSimilarCards();
                }
            });
            
            // Check for card parameter in URL
            const urlParams = new URLSearchParams(window.location.search);
            const cardParam = urlParams.get('card');
            if (cardParam) {
                searchInput.value = decodeURIComponent(cardParam);
                findSimilarCards();
            }
            
            searchInput.disabled = true;
            document.getElementById('searchButton').disabled = true;
        }
    } else if (currentPath === '/batch') {
        // Initialize batch analysis page
        const batchInput = document.getElementById('batchCardInput');
        const analyzeButton = document.querySelector('button[onclick="findSimilarCardsForBatch()"]');
        if (batchInput && analyzeButton) {
            batchInput.disabled = true;
            analyzeButton.disabled = true;
            initializeImageZoom();
        }
    }
    
    // Common initialization for both pages
    checkSystemStatus();
});

let progressEventSource = null;

function analyzeDeck() {
    const deckInput = document.getElementById('deckInput').value;
    const ignoreCollection = document.getElementById('ignoreCollection').checked;
    const loadingSpinner = document.getElementById('loadingSpinner');
    const deckResults = document.getElementById('deckResults');
    const finalDeckResults = document.getElementById('finalDeckResults');
    const finalDeckTableBody = document.getElementById('finalDeckTableBody');
    const progressContainer = document.getElementById('progressContainer');
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');

    // Reset and show progress elements
    progressBar.style.width = '0%';
    progressText.textContent = 'Processing cards: 0/0';
    progressContainer.classList.remove('hidden');
    loadingSpinner.classList.add('hidden');
    deckResults.innerHTML = '';
    finalDeckTableBody.innerHTML = '';
    finalDeckResults.classList.add('hidden');

    // Set up progress event source
    if (progressEventSource) {
        progressEventSource.close();
    }
    progressEventSource = new EventSource('/deck_progress');
    progressEventSource.onmessage = function(event) {
        const progress = JSON.parse(event.data);
        const percentage = (progress.current / progress.total * 100) || 0;
        progressBar.style.width = `${percentage}%`;
        progressText.textContent = `Processing cards: ${progress.current}/${progress.total}`;
        
        if (progress.current >= progress.total && progress.total > 0) {
            progressEventSource.close();
        }
    };

    fetch('/analyze_deck', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
            decklist: deckInput,
            ignoreCollection: ignoreCollection
        })
    })
    .then(response => response.json())
    .then(data => {
        progressContainer.classList.add('hidden');
        if (data.error) {
            deckResults.innerHTML = `<p>Error: ${data.error}</p>`;
        } else {
            deckResults.innerHTML = data.html;

            const finalDeck = data.final_deck;
            if (Array.isArray(finalDeck)) {
                finalDeck.forEach(card => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>
                            <img src="${card.image_url}" alt="${card.name}" style="width: 50px; height: auto;" data-card-image>
                            <div class="card-zoom">
                                <img src="${card.image_url}" alt="${card.name}">
                            </div>
                        </td>
                        <td>${card.final_count}</td>
                        <td>${card.name}</td>
                    `;
                    finalDeckTableBody.appendChild(row);
                });
                finalDeckResults.classList.remove('hidden');
                initializeImageZoom();
            } else {
                deckResults.innerHTML = `<p>Error: Final deck data is not in the expected format.</p>`;
            }
        }
    })
    .catch(error => {
        progressContainer.classList.add('hidden');
        deckResults.innerHTML = `<p>Error: ${error.message}</p>`;
    });
}

function showFormattedDeck() {
    // Create modal container
    const modal = document.createElement('div');
    modal.className = 'deck-modal';
    
    // Create modal content
    const modalContent = document.createElement('div');
    modalContent.className = 'deck-modal-content';
    
    // Create close button
    const closeButton = document.createElement('span');
    closeButton.className = 'deck-modal-close';
    closeButton.innerHTML = '&times;';
    closeButton.onclick = () => modal.remove();
    
    // Create text content
    const textContent = document.createElement('pre');
    textContent.className = 'deck-list-text';
    
    // Get deck list from table
    const deckList = [];
    const rows = document.getElementById('finalDeckTableBody').getElementsByTagName('tr');
    for (const row of rows) {
        const cells = row.getElementsByTagName('td');
        const count = cells[1].textContent;
        const name = cells[2].textContent;
        deckList.push(`${count} ${name}`);
    }
    
    textContent.textContent = deckList.join('\n');
    
    // Assemble modal
    modalContent.appendChild(closeButton);
    modalContent.appendChild(textContent);
    modal.appendChild(modalContent);
    document.body.appendChild(modal);
    
    // Close modal when clicking outside
    modal.onclick = (e) => {
        if (e.target === modal) {
            modal.remove();
        }
    };
}