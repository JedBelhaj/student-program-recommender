// API Configuration
const API_BASE_URL = 'http://127.0.0.1:8000';

// DOM Elements
const form = document.getElementById('recommendation-form');
const inputSection = document.getElementById('input-section');
const resultsSection = document.getElementById('results-section');
const loading = document.getElementById('loading');
const errorMessage = document.getElementById('error-message');
const errorText = document.getElementById('error-text');
const recommendationsContainer = document.getElementById('recommendations-container');
const resetBtn = document.getElementById('reset-btn');
const submitBtn = document.getElementById('submit-btn');

// Grade inputs - update display on change
const gradeInputs = document.querySelectorAll('input[type="number"]');
gradeInputs.forEach(input => {
    input.addEventListener('input', (e) => {
        const display = e.target.nextElementSibling;
        if (display && display.classList.contains('grade-display')) {
            display.textContent = `${e.target.value}%`;
        }
    });
});

// Form submission
form.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    // Get form data
    const formData = new FormData(form);
    const interests = formData.get('interests');
    const mathGrade = parseFloat(formData.get('math_grade'));
    const scienceGrade = parseFloat(formData.get('science_grade'));
    const languageGrade = parseFloat(formData.get('language_grade'));
    const k = parseInt(formData.get('k'));
    
    // Validate
    if (!interests.trim()) {
        showError('Please enter your interests');
        return;
    }
    
    // Prepare request
    const requestBody = {
        interests: interests,
        math_grade: mathGrade,
        science_grade: scienceGrade,
        language_grade: languageGrade
    };
    
    // Show loading
    inputSection.classList.add('hidden');
    resultsSection.classList.add('hidden');
    errorMessage.classList.add('hidden');
    loading.classList.remove('hidden');
    
    try {
        // Call API
        const response = await fetch(`${API_BASE_URL}/recommend?k=${k}&approach=hybrid`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestBody)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to get recommendations');
        }
        
        const data = await response.json();
        
        // Display results
        displayRecommendations(data.recommendations);
        
        // Hide loading, show results
        loading.classList.add('hidden');
        resultsSection.classList.remove('hidden');
        
    } catch (error) {
        console.error('Error:', error);
        loading.classList.add('hidden');
        showError(error.message);
    }
});

// Display recommendations
function displayRecommendations(recommendations) {
    recommendationsContainer.innerHTML = '';
    
    recommendations.forEach((rec, index) => {
        const card = createRecommendationCard(rec, index + 1);
        recommendationsContainer.appendChild(card);
    });
}

// Create recommendation card
function createRecommendationCard(rec, rank) {
    const card = document.createElement('div');
    card.className = 'recommendation-card';
    
    // Parse skills into tags
    const skills = rec.skills.split(' ').filter(s => s.trim());
    
    card.innerHTML = `
        <div class="recommendation-header">
            <div>
                <div style="font-size: 0.875rem; color: var(--text-secondary); font-weight: 600;">
                    #${rank} RECOMMENDATION
                </div>
                <h3 class="program-title">${rec.program_name}</h3>
                <p class="program-description">${rec.description}</p>
            </div>
            <div class="score-badge">
                ${(rec.score * 100).toFixed(0)}% Match
            </div>
        </div>
        
        <div class="skills-tags">
            ${skills.map(skill => `<span class="skill-tag">${skill}</span>`).join('')}
        </div>
        
        <div class="explanation">
            💡 ${rec.explanation}
        </div>
        
        <div class="feedback-buttons">
            <button class="feedback-btn" onclick="submitFeedback('${rec.program_id}', 'clicked', this)">
                👍 Interested
            </button>
            <button class="feedback-btn" onclick="submitFeedback('${rec.program_id}', 'rejected', this)">
                👎 Not for me
            </button>
        </div>
    `;
    
    return card;
}

// Submit feedback
async function submitFeedback(programId, feedbackType, button) {
    try {
        const response = await fetch(`${API_BASE_URL}/feedback`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                program_id: programId,
                feedback_type: feedbackType
            })
        });
        
        if (response.ok) {
            // Update button state
            const buttons = button.parentElement.querySelectorAll('.feedback-btn');
            buttons.forEach(btn => {
                btn.classList.remove('clicked', 'rejected');
            });
            button.classList.add(feedbackType);
            
            // Show confirmation
            const originalText = button.textContent;
            button.textContent = '✓ Recorded';
            setTimeout(() => {
                button.textContent = originalText;
            }, 2000);
        }
    } catch (error) {
        console.error('Feedback error:', error);
    }
}

// Reset form
resetBtn.addEventListener('click', () => {
    resultsSection.classList.add('hidden');
    inputSection.classList.remove('hidden');
    form.reset();
    
    // Reset grade displays
    gradeInputs.forEach(input => {
        const display = input.nextElementSibling;
        if (display && display.classList.contains('grade-display')) {
            display.textContent = `${input.value}%`;
        }
    });
});

// Show error
function showError(message) {
    errorText.textContent = message;
    errorMessage.classList.remove('hidden');
    inputSection.classList.add('hidden');
    resultsSection.classList.add('hidden');
}

// Test cases
const testCases = {
    cs: {
        interests: "technology, artificial intelligence, programming, software development, algorithms",
        math_grade: 92,
        science_grade: 88,
        language_grade: 75
    },
    bio: {
        interests: "biology, chemistry, medicine, healthcare, genetics, research",
        math_grade: 78,
        science_grade: 95,
        language_grade: 82
    },
    business: {
        interests: "economics, finance, management, marketing, entrepreneurship",
        math_grade: 85,
        science_grade: 72,
        language_grade: 88
    },
    arts: {
        interests: "design, creativity, visual arts, media, communication, storytelling",
        math_grade: 70,
        science_grade: 68,
        language_grade: 94
    },
    engineering: {
        interests: "mechanics, robotics, electronics, physics, problem solving, innovation",
        math_grade: 93,
        science_grade: 90,
        language_grade: 72
    }
};

// Fill test case
function fillTestCase(testName) {
    const test = testCases[testName];
    if (!test) return;
    
    // Fill form
    document.getElementById('interests').value = test.interests;
    document.getElementById('math_grade').value = test.math_grade;
    document.getElementById('science_grade').value = test.science_grade;
    document.getElementById('language_grade').value = test.language_grade;
    
    // Update displays
    document.querySelector('#math_grade + .grade-display').textContent = `${test.math_grade}%`;
    document.querySelector('#science_grade + .grade-display').textContent = `${test.science_grade}%`;
    document.querySelector('#language_grade + .grade-display').textContent = `${test.language_grade}%`;
    
    // Scroll to form
    document.getElementById('input-section').scrollIntoView({ behavior: 'smooth', block: 'center' });
    
    // Highlight form briefly
    const form = document.getElementById('recommendation-form');
    form.style.border = '2px solid var(--primary)';
    setTimeout(() => {
        form.style.border = '';
    }, 1500);
}

// Hide error
function hideError() {
    errorMessage.classList.add('hidden');
    inputSection.classList.remove('hidden');
}

// Check API health on load
window.addEventListener('load', async () => {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        if (!response.ok) {
            showError('API server is not responding. Please make sure the server is running.');
        }
    } catch (error) {
        showError('Cannot connect to API server. Please start the server with: python -m uvicorn app.main:app --reload');
    }
});
