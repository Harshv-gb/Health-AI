// HealthAI - Client-side enhancements
// Additional JavaScript functionality for enhanced user experience

// Smooth scrolling for navigation links
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips and animations
    initializeAnimations();
    
    // Setup notification system
    initializeNotifications();
    
    // Enhanced form functionality
    enhanceFormExperience();
});

// Initialize page animations
function initializeAnimations() {
    // Intersection Observer for fade-in animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);

    // Observe all feature cards and result sections
    document.querySelectorAll('.feature-card, .analysis-card, .medicine-card, .hospitals-card').forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });
}

// Enhanced notification system
function showNotification(message, type = 'info', duration = 5000) {
    // Remove existing notifications
    const existingNotification = document.querySelector('.notification');
    if (existingNotification) {
        existingNotification.remove();
    }
    
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas ${getNotificationIcon(type)}"></i>
            <span>${message}</span>
            <button class="notification-close" onclick="this.parentElement.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;
    
    // Add styles
    notification.style.cssText = `
        position: fixed;
        top: 90px;
        right: 20px;
        z-index: 10000;
        background: ${getNotificationColor(type)};
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        max-width: 400px;
        animation: slideInRight 0.3s ease;
        font-family: var(--font-family);
    `;
    
    document.body.appendChild(notification);
    
    // Auto remove after duration
    setTimeout(() => {
        if (notification.parentElement) {
            notification.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }
    }, duration);
}

function getNotificationIcon(type) {
    const icons = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle'
    };
    return icons[type] || icons.info;
}

function getNotificationColor(type) {
    const colors = {
        success: '#10b981',
        error: '#ef4444',
        warning: '#f59e0b',
        info: '#3b82f6'
    };
    return colors[type] || colors.info;
}

function initializeNotifications() {
    // Add CSS animations
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideInRight {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        
        @keyframes slideOutRight {
            from { transform: translateX(0); opacity: 1; }
            to { transform: translateX(100%); opacity: 0; }
        }
        
        .notification {
            font-weight: 500;
        }
        
        .notification-content {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }
        
        .notification-close {
            background: none;
            border: none;
            color: inherit;
            cursor: pointer;
            padding: 0.25rem;
            margin-left: auto;
        }
    `;
    document.head.appendChild(style);
}

// Local storage for user preferences
const UserPreferences = {
    save: function(key, value) {
        try {
            localStorage.setItem(`healthai_${key}`, JSON.stringify(value));
        } catch (e) {
            console.warn('Unable to save to localStorage:', e);
        }
    },
    
    load: function(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(`healthai_${key}`);
            return item ? JSON.parse(item) : defaultValue;
        } catch (e) {
            console.warn('Unable to load from localStorage:', e);
            return defaultValue;
        }
    },
    
    remove: function(key) {
        try {
            localStorage.removeItem(`healthai_${key}`);
        } catch (e) {
            console.warn('Unable to remove from localStorage:', e);
        }
    }
};

// Enhanced form experience
function enhanceFormExperience() {
    // Auto-save draft as user types
    const symptomsInput = document.getElementById('text');
    const locationInput = document.getElementById('location');
    
    if (symptomsInput) {
        symptomsInput.addEventListener('input', debounce(() => {
            UserPreferences.save('draftSymptoms', symptomsInput.value);
        }, 1000));
        
        // Load draft on page load
        const draft = UserPreferences.load('draftSymptoms');
        if (draft && !symptomsInput.value) {
            symptomsInput.value = draft;
        }
    }
    
    if (locationInput) {
        locationInput.addEventListener('change', () => {
            UserPreferences.save('lastLocation', locationInput.value);
        });
        
        // Load last location
        const savedLocation = UserPreferences.load('lastLocation');
        if (savedLocation && !locationInput.value) {
            locationInput.value = savedLocation;
        }
    }
    
    // Character counter for symptoms
    if (symptomsInput) {
        const counter = document.createElement('div');
        counter.className = 'character-counter';
        counter.style.cssText = `
            font-size: 0.8rem;
            color: var(--text-light);
            text-align: right;
            margin-top: 0.25rem;
        `;
        
        symptomsInput.addEventListener('input', () => {
            const length = symptomsInput.value.length;
            counter.textContent = `${length}/2000 characters`;
            
            if (length > 2000) {
                counter.style.color = 'var(--danger-color)';
            } else if (length > 1800) {
                counter.style.color = 'var(--warning-color)';
            } else {
                counter.style.color = 'var(--text-light)';
            }
        });
        
        symptomsInput.parentNode.appendChild(counter);
        // Trigger initial count
        symptomsInput.dispatchEvent(new Event('input'));
    }
}

// Utility function for debouncing
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Form validation enhancements
function validateSymptomInput(text) {
    if (!text || text.trim().length < 10) {
        throw new Error('Please provide a more detailed description of your symptoms (at least 10 characters).');
    }
    
    if (text.trim().length > 2000) {
        throw new Error('Symptom description is too long. Please keep it under 2000 characters.');
    }
    
    return true;
}

function validateLocationInput(location) {
    if (!location || location.trim().length < 2) {
        throw new Error('Please provide a valid location.');
    }
    
    return true;
}

// Enhanced error handling
function handleApiError(error, context = 'operation') {
    console.error(`API Error in ${context}:`, error);
    
    let userMessage = 'Something went wrong. Please try again.';
    
    if (error.message.includes('network') || error.message.includes('fetch')) {
        userMessage = 'Network connection issue. Please check your internet connection and try again.';
    } else if (error.message.includes('timeout')) {
        userMessage = 'The request is taking longer than expected. Please try again.';
    } else if (error.message.includes('500')) {
        userMessage = 'Server is temporarily unavailable. Please try again in a few minutes.';
    }
    
    showNotification(userMessage, 'error');
}

// Theme switching functionality (removed duplicate - now handled in main HTML)
// This functionality is now integrated into the main HTML file

// Accessibility enhancements
function enhanceAccessibility() {
    // Add skip to content link
    const skipLink = document.createElement('a');
    skipLink.href = '#main-content';
    skipLink.textContent = 'Skip to main content';
    skipLink.className = 'skip-link';
    skipLink.style.cssText = `
        position: absolute;
        top: -40px;
        left: 6px;
        background: var(--primary-color);
        color: white;
        padding: 8px;
        text-decoration: none;
        z-index: 1000;
        border-radius: 4px;
    `;
    
    skipLink.addEventListener('focus', () => {
        skipLink.style.top = '6px';
    });
    
    skipLink.addEventListener('blur', () => {
        skipLink.style.top = '-40px';
    });
    
    document.body.insertBefore(skipLink, document.body.firstChild);
    
    // Add main content ID
    const heroSection = document.querySelector('.hero');
    if (heroSection) {
        heroSection.id = 'main-content';
    }
}

// Initialize all enhancements
document.addEventListener('DOMContentLoaded', function() {
    // Theme toggle is now handled in main HTML file
    enhanceAccessibility();
    
    // Add keyboard navigation for cards
    document.querySelectorAll('.feature-card, .hospital-item').forEach(card => {
        card.setAttribute('tabindex', '0');
        card.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                card.click();
            }
        });
    });
});

// Export functions for global use
window.HealthAI = {
    showNotification,
    handleApiError,
    UserPreferences,
    validateSymptomInput,
    validateLocationInput
};

// ============================================
// AI Chat Interface Functionality
// ============================================

let chatHistory = [];
let symptomContext = {};
let isRecording = false;
let recognition = null;

// Initialize speech recognition if available
if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';
}

// Initialize chat interface
document.addEventListener('DOMContentLoaded', function() {
    console.log('Chat interface initialized'); // Debug log
    
    // Use event delegation for dynamically shown elements
    document.body.addEventListener('click', function(e) {
        // Ask AI button
        if (e.target.id === 'askAIBtn' || e.target.closest('#askAIBtn')) {
            console.log('Ask AI button clicked!'); // Debug log
            e.preventDefault();
            openChatInterface();
        }
        
        // Close chat button
        if (e.target.id === 'closeChatBtn' || e.target.closest('#closeChatBtn')) {
            console.log('Close chat button clicked!'); // Debug log
            e.preventDefault();
            closeChatInterface();
        }
        
        // Send chat button
        if (e.target.id === 'sendChatBtn' || e.target.closest('#sendChatBtn')) {
            console.log('Send chat button clicked!'); // Debug log
            e.preventDefault();
            sendChatMessage();
        }
        
        // Voice chat button
        if (e.target.id === 'voiceChatBtn' || e.target.closest('#voiceChatBtn')) {
            console.log('Voice chat button clicked!'); // Debug log
            e.preventDefault();
            toggleVoiceInput();
        }
        
        // Suggestion buttons
        if (e.target.classList.contains('suggestion-btn')) {
            const question = e.target.getAttribute('data-question');
            if (question) {
                const chatInput = document.getElementById('chatInput');
                if (chatInput) {
                    chatInput.value = question;
                    sendChatMessage();
                }
            }
        }
    });
    
    // Chat input enter key
    const chatInput = document.getElementById('chatInput');
    if (chatInput) {
        chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendChatMessage();
            }
        });
    }
});

function openChatInterface() {
    console.log('openChatInterface called!'); // Debug log
    const chatInterface = document.getElementById('aiChatInterface');
    console.log('Chat interface element:', chatInterface); // Debug log
    
    if (chatInterface) {
        chatInterface.style.display = 'block';
        
        // Scroll chat into view
        setTimeout(() => {
            chatInterface.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }, 100);
        
        // Focus on input
        const chatInput = document.getElementById('chatInput');
        if (chatInput) {
            chatInput.focus();
        }
        
        // Store symptom context from results
        storeSymptomContext();
        
        // Show notification if available
        if (typeof showNotification === 'function') {
            showNotification('AI Assistant is ready to help!', 'success', 3000);
        }
    } else {
        console.error('Chat interface not found!'); // Debug log
    }
}

function closeChatInterface() {
    const chatInterface = document.getElementById('aiChatInterface');
    if (chatInterface) {
        chatInterface.style.display = 'none';
    }
}

function storeSymptomContext() {
    // Extract symptom context from the displayed results
    const resultsContent = document.querySelector('.results-content');
    if (resultsContent) {
        symptomContext = {
            symptoms: [],
            condition: '',
            department: '',
            urgency: 'non-urgent'
        };
        
        // Try to extract symptoms from the page
        const symptomsText = document.getElementById('text')?.value || '';
        symptomContext.symptoms = symptomsText.split(/[,;\n]/).map(s => s.trim()).filter(s => s);
    }
}

async function sendChatMessage() {
    const chatInput = document.getElementById('chatInput');
    const message = chatInput.value.trim();
    
    if (!message) {
        return;
    }
    
    // Add user message to chat
    addMessageToChat('user', message);
    
    // Clear input
    chatInput.value = '';
    
    // Show typing indicator
    showTypingIndicator();
    
    try {
        // Send to API
        const response = await fetch('http://localhost:5000/api/conversation', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                symptom_context: symptomContext,
                chat_history: chatHistory
            })
        });
        
        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Remove typing indicator
        removeTypingIndicator();
        
        // Add AI response to chat
        addMessageToChat('bot', data.ai_response);
        
        // Update chat history
        chatHistory.push({
            role: 'user',
            content: message
        });
        chatHistory.push({
            role: 'assistant',
            content: data.ai_response
        });
        
        // Update suggestions if provided
        if (data.follow_up_suggestions && data.follow_up_suggestions.length > 0) {
            updateSuggestions(data.follow_up_suggestions);
        }
        
        // Speak response if voice is enabled
        if (window.speechSynthesis && recognition) {
            speakChatMessage(data.ai_response);
        }
        
    } catch (error) {
        console.error('Chat error:', error);
        removeTypingIndicator();
        addMessageToChat('bot', 'I apologize, but I\'m having trouble connecting right now. Please try again in a moment.');
        showNotification('Failed to send message. Please check your connection.', 'error');
    }
}

function addMessageToChat(sender, message) {
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${sender}-message`;
    
    const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    messageDiv.innerHTML = `
        <div class="message-avatar">
            <i class="fas fa-${sender === 'bot' ? 'robot' : 'user'}"></i>
        </div>
        <div class="message-content">
            <p>${escapeHtml(message)}</p>
            <div class="message-timestamp">${timestamp}</div>
        </div>
    `;
    
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function showTypingIndicator() {
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) return;
    
    const typingDiv = document.createElement('div');
    typingDiv.className = 'chat-message bot-message typing-indicator-message';
    typingDiv.id = 'typingIndicator';
    typingDiv.innerHTML = `
        <div class="message-avatar">
            <i class="fas fa-robot"></i>
        </div>
        <div class="message-content">
            <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    `;
    
    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function removeTypingIndicator() {
    const typingIndicator = document.getElementById('typingIndicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

function updateSuggestions(suggestions) {
    const suggestionsContainer = document.getElementById('chatSuggestions');
    if (!suggestionsContainer || suggestions.length === 0) return;
    
    suggestionsContainer.innerHTML = suggestions.map(suggestion => 
        `<button class="suggestion-btn" data-question="${escapeHtml(suggestion)}">${escapeHtml(suggestion)}</button>`
    ).join('');
}

function toggleVoiceInput() {
    const voiceChatBtn = document.getElementById('voiceChatBtn');
    
    if (!recognition) {
        showNotification('Voice input is not supported in your browser', 'error');
        return;
    }
    
    if (isRecording) {
        // Stop recording
        recognition.stop();
        isRecording = false;
        voiceChatBtn.classList.remove('recording');
        voiceChatBtn.innerHTML = '<i class="fas fa-microphone"></i>';
    } else {
        // Start recording
        recognition.start();
        isRecording = true;
        voiceChatBtn.classList.add('recording');
        voiceChatBtn.innerHTML = '<i class="fas fa-microphone-slash"></i>';
        showNotification('Listening... Speak now', 'info', 2000);
    }
    
    recognition.onresult = function(event) {
        const transcript = event.results[0][0].transcript;
        const chatInput = document.getElementById('chatInput');
        if (chatInput) {
            chatInput.value = transcript;
        }
        isRecording = false;
        voiceChatBtn.classList.remove('recording');
        voiceChatBtn.innerHTML = '<i class="fas fa-microphone"></i>';
        
        // Automatically send message
        setTimeout(() => sendChatMessage(), 500);
    };
    
    recognition.onerror = function(event) {
        console.error('Speech recognition error:', event.error);
        isRecording = false;
        voiceChatBtn.classList.remove('recording');
        voiceChatBtn.innerHTML = '<i class="fas fa-microphone"></i>';
        showNotification('Voice input error. Please try again.', 'error');
    };
    
    recognition.onend = function() {
        isRecording = false;
        voiceChatBtn.classList.remove('recording');
        voiceChatBtn.innerHTML = '<i class="fas fa-microphone"></i>';
    };
}

function speakChatMessage(text) {
    if ('speechSynthesis' in window) {
        // Cancel any ongoing speech
        speechSynthesis.cancel();
        
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 0.9;
        utterance.pitch = 1;
        utterance.volume = 0.8;
        
        const voices = speechSynthesis.getVoices();
        const preferredVoice = voices.find(voice => 
            voice.lang.startsWith('en') && voice.name.includes('Female')
        );
        
        if (preferredVoice) {
            utterance.voice = preferredVoice;
        }
        
        speechSynthesis.speak(utterance);
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Export chat functions
window.HealthAI = {
    ...window.HealthAI,
    openChatInterface,
    closeChatInterface,
    sendChatMessage
};
