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

    async delete(path) {
        console.log('API DELETE to:', `${this.baseUrl}${path}`);
        const response = await fetch(`${this.baseUrl}${path}`, {
            method: 'DELETE'
        });
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
    status: document.getElementById('status'),
    sessionsList: document.getElementById('sessionsList'),
    newChatBtn: document.getElementById('newChatBtn')
};

// Application state
let currentFeedbackMessageId = null;
let currentSessionId = null;

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
            const response = await api.post('/chat', {
                message,
                session_id: currentSessionId
            });

            // Update current session if new session created
            if (response.session_id && !currentSessionId) {
                currentSessionId = response.session_id;
                await loadSessions();
                highlightSession(currentSessionId);
            }

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
            body: JSON.stringify({
                message,
                stream: true,
                session_id: currentSessionId
            })
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

                        // Update current session if new session created
                        if (data.session_id && !currentSessionId) {
                            currentSessionId = data.session_id;
                            await loadSessions();
                            highlightSession(currentSessionId);
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

// =============================
// Session Management Functions
// =============================

async function loadSessions() {
    try {
        const sessions = await api.get('/sessions?limit=20');

        elements.sessionsList.innerHTML = '';

        if (sessions.length === 0) {
            elements.sessionsList.innerHTML = '<div style="padding: 20px; text-align: center; color: #666; font-size: 14px;">No sessions yet.<br>Start a new chat!</div>';
            return;
        }

        sessions.forEach(session => {
            const sessionElement = createSessionElement(session);
            elements.sessionsList.appendChild(sessionElement);
        });

        // Highlight current session if any
        if (currentSessionId) {
            highlightSession(currentSessionId);
        }
    } catch (error) {
        console.error('Failed to load sessions:', error);
        showStatus(`Failed to load sessions: ${error.message}`, 'error');
    }
}

function createSessionElement(session) {
    const div = document.createElement('div');
    div.className = 'session-item';
    div.dataset.sessionId = session.session_id;

    // Format the session ID (first 8 chars)
    const shortId = session.session_id.substring(0, 8);

    // Format the time
    const timeAgo = formatTimeAgo(new Date(session.last_at));

    div.innerHTML = `
        <div class="session-info">
            <div class="session-id-short">${shortId}...</div>
            <div class="session-time">${timeAgo}</div>
        </div>
        <button class="session-delete" title="Delete session">×</button>
    `;

    // Click to switch session
    div.addEventListener('click', (e) => {
        if (!e.target.classList.contains('session-delete')) {
            switchToSession(session.session_id);
        }
    });

    // Delete button
    const deleteBtn = div.querySelector('.session-delete');
    deleteBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        deleteSession(session.session_id);
    });

    return div;
}

function formatTimeAgo(date) {
    const seconds = Math.floor((new Date() - date) / 1000);

    if (seconds < 60) return 'Just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;

    return date.toLocaleDateString();
}

function highlightSession(sessionId) {
    // Remove active class from all sessions
    document.querySelectorAll('.session-item').forEach(item => {
        item.classList.remove('active');
    });

    // Add active class to current session
    const sessionElement = document.querySelector(`[data-session-id="${sessionId}"]`);
    if (sessionElement) {
        sessionElement.classList.add('active');
    }
}

async function switchToSession(sessionId) {
    setLoading(true);

    try {
        // Load session messages
        const history = await api.get(`/chat-history?limit=100`);

        // Filter messages for this session
        const sessionMessages = history.filter(msg => msg.session_id === sessionId);

        if (sessionMessages.length === 0) {
            showStatus('No messages found in this session', 'error');
            return;
        }

        // Clear current messages
        elements.messages.innerHTML = '';

        // Add messages in chronological order
        sessionMessages.reverse().forEach(entry => {
            addMessage(entry.content, entry.role, entry.created_at);
        });

        // Update current session
        currentSessionId = sessionId;
        highlightSession(sessionId);

        showStatus('Session loaded', 'success');

    } catch (error) {
        showStatus(`Failed to load session: ${error.message}`, 'error');
    } finally {
        setLoading(false);
    }
}

async function deleteSession(sessionId) {
    if (!confirm('Are you sure you want to delete this session? This cannot be undone.')) {
        return;
    }

    setLoading(true);

    try {
        await api.delete(`/sessions/${sessionId}`);

        // If deleting current session, start new chat
        if (sessionId === currentSessionId) {
            startNewChat();
        }

        // Reload sessions list
        await loadSessions();

        showStatus('Session deleted', 'success');
    } catch (error) {
        showStatus(`Failed to delete session: ${error.message}`, 'error');
    } finally {
        setLoading(false);
    }
}

function startNewChat() {
    // Clear current session
    currentSessionId = null;

    // Clear messages
    elements.messages.innerHTML = `
        <div class="message assistant">
            <div class="message-content">
                Hello! I'm your AI assistant. You can upload knowledge files and ask me questions about them.
            </div>
        </div>
    `;

    // Clear input
    elements.messageInput.value = '';

    // Remove active highlight
    document.querySelectorAll('.session-item').forEach(item => {
        item.classList.remove('active');
    });

    // Focus input
    elements.messageInput.focus();

    showStatus('Started new chat', 'success');
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
elements.newChatBtn.addEventListener('click', startNewChat);

// Initialize
console.log('Data Flywheel Chatbot initialized');
loadSessions(); // Load sessions on startup
elements.messageInput.focus();
