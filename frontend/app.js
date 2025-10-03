/**
 * Data Flywheel Chatbot Frontend
 * Simple vanilla JavaScript application for chatbot interaction
 */

// API helper functions - UPDATED FOR BACKEND
const api = {
    baseUrl: 'http://localhost:8000/api/v1',
    
    async post(path, body) {
        console.log('API POST to:', `${this.baseUrl}${path}`);
        const response = await fetch(`${this.baseUrl}${path}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(body)
        });
        return this.handleResponse(response);
    },
    
    async postFile(path, formData) {
        console.log('API POST FILE to:', `${this.baseUrl}${path}`);
        const response = await fetch(`${this.baseUrl}${path}`, {
            method: 'POST',
            body: formData
        });
        return this.handleResponse(response);
    },
    
    async get(path) {
        const response = await fetch(`${this.baseUrl}${path}`);
        return this.handleResponse(response);
    },
    
    async handleResponse(response) {
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || `HTTP ${response.status}`);
        }
        return data;
    }
};

// DOM elements
const elements = {
    messages: document.getElementById('messages'),
    messageInput: document.getElementById('messageInput'),
    sendBtn: document.getElementById('sendBtn'),
    fileInput: document.getElementById('fileInput'),
    uploadBtn: document.getElementById('uploadBtn'),
    historyBtn: document.getElementById('historyBtn'),
    status: document.getElementById('status')
};

// Application state
let currentFeedbackMessageId = null;

// Utility functions
function showStatus(message, type = 'success') {
    elements.status.innerHTML = `<div class="status ${type}">${message}</div>`;
    setTimeout(() => {
        elements.status.innerHTML = '';
    }, 5000);
}

function setLoading(isLoading) {
    const container = document.querySelector('.chat-container');
    if (isLoading) {
        container.classList.add('loading');
    } else {
        container.classList.remove('loading');
    }
}

function scrollToBottom() {
    elements.messages.scrollTop = elements.messages.scrollHeight;
}

function formatTimestamp(timestamp) {
    return new Date(timestamp).toLocaleTimeString();
}

// Message rendering functions
function createMessageElement(content, type, timestamp = null, sources = null, messageId = null) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    messageDiv.dataset.messageId = messageId;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = content;
    messageDiv.appendChild(contentDiv);
    
    if (sources && sources.length > 0) {
        const sourcesDiv = document.createElement('div');
        sourcesDiv.className = 'knowledge-sources';
        sourcesDiv.innerHTML = '<strong>Sources:</strong> ' + 
            sources.map(s => `<span class="knowledge-source">${s.filename} (${s.relevance_score})</span>`).join('');
        messageDiv.appendChild(sourcesDiv);
    }
    
    if (timestamp) {
        const metaDiv = document.createElement('div');
        metaDiv.className = 'message-meta';
        metaDiv.textContent = formatTimestamp(timestamp);
        messageDiv.appendChild(metaDiv);
    }
    
    // Add feedback buttons for assistant messages
    if (type === 'assistant') {
        const feedbackDiv = document.createElement('div');
        feedbackDiv.className = 'feedback-buttons';
        feedbackDiv.innerHTML = `
            <button class="feedback-btn" data-feedback="thumbs_up" title="Good response">👍</button>
            <button class="feedback-btn" data-feedback="thumbs_down" title="Poor response">👎</button>
            <input type="text" class="feedback-comment" placeholder="Optional comment..." style="display:none;">
        `;
        messageDiv.appendChild(feedbackDiv);
        
        // Add feedback event listeners
        const feedbackBtns = feedbackDiv.querySelectorAll('.feedback-btn');
        const commentInput = feedbackDiv.querySelector('.feedback-comment');
        
        feedbackBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const feedback = btn.dataset.feedback;
                const wasActive = btn.classList.contains('active');
                
                // Reset all buttons
                feedbackBtns.forEach(b => b.classList.remove('active'));
                commentInput.style.display = 'none';
                
                if (!wasActive) {
                    btn.classList.add('active');
                    commentInput.style.display = 'block';
                    commentInput.focus();
                    
                    // Submit feedback when comment is entered or after a delay
                    const submitFeedback = () => {
                        submitMessageFeedback(content, feedback, commentInput.value);
                        commentInput.removeEventListener('blur', submitFeedback);
                        commentInput.removeEventListener('keypress', handleEnter);
                    };
                    
                    const handleEnter = (e) => {
                        if (e.key === 'Enter') {
                            submitFeedback();
                        }
                    };
                    
                    commentInput.addEventListener('blur', submitFeedback);
                    commentInput.addEventListener('keypress', handleEnter);
                    
                    // Auto-submit after 3 seconds if no comment
                    setTimeout(() => {
                        if (btn.classList.contains('active') && !commentInput.value) {
                            submitFeedback();
                        }
                    }, 3000);
                }
            });
        });
    }
    
    return messageDiv;
}

function addMessage(content, type, timestamp = null, sources = null, messageId = null) {
    const messageElement = createMessageElement(content, type, timestamp, sources, messageId);
    elements.messages.appendChild(messageElement);
    scrollToBottom();
    return messageElement;
}

// Chat functions
async function sendMessage(useStreaming = true) {
    const message = elements.messageInput.value.trim();
    if (!message) {
        showStatus('Please enter a message', 'error');
        return;
    }

    // Add user message to chat
    const userMessageElement = addMessage(message, 'user', new Date().toISOString());
    elements.messageInput.value = '';

    setLoading(true);

    // Non-streaming request
    if (!useStreaming) {
        try {
            const response = await api.post('/chat', { message });

            // Add assistant response
            addMessage(
                response.reply,
                'assistant',
                new Date().toISOString(),
                response.knowledge_sources
            );

        } catch (error) {
            showStatus(`Chat error: ${error.message}`, 'error');
            addMessage('Sorry, I encountered an error processing your message.', 'assistant');
        } finally {
            setLoading(false);
        }
        return;
    }

    // Streaming request
    try {
        // Create placeholder for assistant response
        const responseTimestamp = new Date().toISOString();
        const assistantMessageElement = addMessage('', 'assistant', responseTimestamp);
        const contentDiv = assistantMessageElement.querySelector('.message-content');
        const knowledgeSourcesDiv = document.createElement('div');
        knowledgeSourcesDiv.className = 'knowledge-sources';
        assistantMessageElement.appendChild(knowledgeSourcesDiv);

        // Stream setup
        const response = await fetch(`${api.baseUrl}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message, stream: true })
        });

        // Check if response is okay
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        // Stream processing
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let fullResponse = '';

        while (true) {
            const { done, value } = await reader.read();

            if (done) break;

            const chunk = decoder.decode(value);
            const lines = chunk.split('\n\n');

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));

                        // Update response text
                        if (data.reply !== undefined) {
                            contentDiv.textContent = data.reply;
                            scrollToBottom();
                        }

                        // Update knowledge sources
                        if (data.knowledge_sources) {
                            knowledgeSourcesDiv.innerHTML = '<strong>Sources:</strong> ' +
                                data.knowledge_sources.map(s =>
                                    `<span class="knowledge-source">${s.filename} (${s.relevance_score})</span>`
                                ).join('');
                        }

                        // Handle potential error response
                        if (data.error) {
                            throw new Error(data.error);
                        }
                    } catch (parseError) {
                        console.error('Error parsing stream data:', parseError);
                    }
                }
            }
        }

    } catch (error) {
        showStatus(`Chat error: ${error.message}`, 'error');
        addMessage('Sorry, I encountered an error processing your message.', 'assistant');
    } finally {
        setLoading(false);
    }
}

async function uploadFile() {
    const file = elements.fileInput.files[0];
    if (!file) {
        showStatus('Please select a file', 'error');
        return;
    }
    
    // Validate file type
    const allowedTypes = ['.txt', '.pdf'];
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
    if (!allowedTypes.includes(fileExtension)) {
        showStatus('Only TXT and PDF files are allowed', 'error');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    setLoading(true);
    
    try {
        const response = await api.postFile('/knowledge/files', formData);
        showStatus(`File uploaded successfully: ${response.filename}`, 'success');
        elements.fileInput.value = '';
    } catch (error) {
        showStatus(`Upload error: ${error.message}`, 'error');
    } finally {
        setLoading(false);
    }
}

async function loadChatHistory() {
    setLoading(true);
    
    try {
        const history = await api.get('/chat-history?limit=10');
        
        // Clear existing messages except welcome message
        const welcomeMessage = elements.messages.querySelector('.message.assistant');
        elements.messages.innerHTML = '';
        if (welcomeMessage) {
            elements.messages.appendChild(welcomeMessage);
        }
        
        // Add history messages in chronological order
        history.reverse().forEach(entry => {
            addMessage(entry.user_message, 'user', entry.timestamp, null, entry.id);
            addMessage(entry.bot_reply, 'assistant', entry.timestamp, null, entry.id);
        });
        
        showStatus(`Loaded ${history.length} recent conversations`, 'success');
        
    } catch (error) {
        showStatus(`History error: ${error.message}`, 'error');
    } finally {
        setLoading(false);
    }
}

async function submitMessageFeedback(message, feedback, comment = '') {
    try {
        await api.post('/feedback', {
            message: message,
            user_feedback: feedback,
            comment: comment || null
        });
        
        showStatus('Feedback submitted successfully', 'success');
    } catch (error) {
        showStatus(`Feedback error: ${error.message}`, 'error');
    }
}

// Event listeners
elements.sendBtn.addEventListener('click', sendMessage);
elements.messageInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

elements.uploadBtn.addEventListener('click', uploadFile);
elements.historyBtn.addEventListener('click', loadChatHistory);

// Initialize
console.log('Data Flywheel Chatbot initialized');
elements.messageInput.focus();
