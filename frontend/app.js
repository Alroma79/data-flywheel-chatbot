/**
 * Data Flywheel Chatbot Frontend
 * Simple vanilla JavaScript application for chatbot interaction
 */

// API helper functions - UPDATED FOR BACKEND
const api = {
    baseUrl: (() => {
        const configured = window.API_BASE_URL;
        if (configured && typeof configured === 'string') {
            return `${configured.replace(/\/$/, '')}/api/v1`;
        }

        const { protocol, origin } = window.location;
        if (protocol === 'file:') {
            return 'http://localhost:8000/api/v1';
        }

        return `${origin}/api/v1`;
    })(),

    getToken() {
        return window.sessionStorage.getItem('flywheelAppToken') || '';
    },

    buildHeaders(includeJson = false) {
        const headers = {};
        if (includeJson) {
            headers['Content-Type'] = 'application/json';
        }
        const token = this.getToken();
        if (token) {
            headers.Authorization = `Bearer ${token}`;
        }
        return headers;
    },

    async post(path, body) {
        console.log('API POST to:', `${this.baseUrl}${path}`);
        const response = await fetch(`${this.baseUrl}${path}`, {
            method: 'POST',
            headers: this.buildHeaders(true),
            body: JSON.stringify(body)
        });
        return this.handleResponse(response);
    },
    
    async postFile(path, formData) {
        console.log('API POST FILE to:', `${this.baseUrl}${path}`);
        const response = await fetch(`${this.baseUrl}${path}`, {
            method: 'POST',
            headers: this.buildHeaders(),
            body: formData
        });
        return this.handleResponse(response);
    },
    
    async get(path) {
        const response = await fetch(`${this.baseUrl}${path}`, {
            headers: this.buildHeaders()
        });
        return this.handleResponse(response);
    },

    async delete(path) {
        console.log('API DELETE to:', `${this.baseUrl}${path}`);
        const response = await fetch(`${this.baseUrl}${path}`, {
            method: 'DELETE',
            headers: this.buildHeaders()
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
    newChatBtn: document.getElementById('newChatBtn'),
    chatView: document.getElementById('chatView'),
    analyticsView: document.getElementById('analyticsView'),
    chatViewBtn: document.getElementById('chatViewBtn'),
    analyticsViewBtn: document.getElementById('analyticsViewBtn'),
    analyticsToken: document.getElementById('analyticsToken'),
    saveTokenBtn: document.getElementById('saveTokenBtn'),
    refreshAnalyticsBtn: document.getElementById('refreshAnalyticsBtn'),
    analyticsStatus: document.getElementById('analyticsStatus'),
    configurationAnalytics: document.getElementById('configurationAnalytics'),
    negativeFeedbackList: document.getElementById('negativeFeedbackList'),
    totalResponsesMetric: document.getElementById('totalResponsesMetric'),
    ratedResponsesMetric: document.getElementById('ratedResponsesMetric'),
    approvalRateMetric: document.getElementById('approvalRateMetric'),
    feedbackCoverageMetric: document.getElementById('feedbackCoverageMetric')
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

function escapeHtml(value) {
    return String(value ?? '')
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#039;');
}

function formatPercent(value) {
    if (value === null || value === undefined) {
        return '—';
    }
    return `${Math.round(value * 100)}%`;
}

// Message rendering functions
function createMessageElement(content, type, timestamp = null, sources = null, messageId = null) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    if (messageId !== null && messageId !== undefined) {
        messageDiv.dataset.messageId = String(messageId);
    }
    
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
                        const messageText = (contentDiv.textContent || '').trim();
                        if (!messageText) {
                            showStatus('Message not ready for feedback yet', 'error');
                            return;
                        }
                        submitMessageFeedback(
                            messageText,
                            feedback,
                            commentInput.value,
                            messageDiv.dataset.messageId
                        );
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
                response.knowledge_sources,
                response.assistant_message_id
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
                ...api.buildHeaders(true)
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

                        if (data.assistant_message_id) {
                            assistantMessageElement.dataset.messageId =
                                String(data.assistant_message_id);
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
            addMessage(
                entry.content,
                entry.role,
                entry.created_at,
                null,
                entry.id
            );
        });
        
        showStatus(`Loaded ${history.length} recent conversations`, 'success');
        
    } catch (error) {
        showStatus(`History error: ${error.message}`, 'error');
    } finally {
        setLoading(false);
    }
}

async function submitMessageFeedback(message, feedback, comment = '', responseId = null) {
    try {
        const sanitizedMessage = (message || '').trim();
        if (!sanitizedMessage) {
            showStatus('Cannot submit feedback for an empty message', 'error');
            return;
        }

        const payload = {
            message: sanitizedMessage,
            user_feedback: feedback,
            comment: (comment || '').trim() || null
        };
        const parsedResponseId = Number(responseId);
        if (Number.isInteger(parsedResponseId) && parsedResponseId > 0) {
            payload.response_id = parsedResponseId;
        }

        await api.post('/feedback', payload);

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
            addMessage(entry.content, entry.role, entry.created_at, null, entry.id);
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
    setActiveView('chat');

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

// =============================
// Flywheel Analytics
// =============================

function showAnalyticsStatus(message, type = 'success') {
    elements.analyticsStatus.innerHTML =
        `<div class="status ${type}">${escapeHtml(message)}</div>`;
}

function setActiveView(viewName) {
    const showingAnalytics = viewName === 'analytics';
    elements.chatView.classList.toggle('hidden', showingAnalytics);
    elements.analyticsView.classList.toggle('hidden', !showingAnalytics);
    elements.chatViewBtn.classList.toggle('active', !showingAnalytics);
    elements.analyticsViewBtn.classList.toggle('active', showingAnalytics);

    if (showingAnalytics) {
        loadAnalytics();
    } else {
        elements.messageInput.focus();
    }
}

function renderConfigurationAnalytics(configurations) {
    if (!configurations.length) {
        elements.configurationAnalytics.innerHTML =
            '<div class="dashboard-empty">No attributed responses yet. Send a chat message and rate the response.</div>';
        return;
    }

    const rows = configurations.map(config => {
        const approvalWidth = config.approval_rate === null
            ? 0
            : Math.round(config.approval_rate * 100);
        return `
            <tr>
                <td>
                    <strong>${escapeHtml(config.config_name)}</strong><br>
                    <span>${escapeHtml(config.model || 'Unknown model')}</span>
                </td>
                <td>${config.total_responses}</td>
                <td>${config.rated_responses}</td>
                <td>
                    ${formatPercent(config.approval_rate)}
                    <div class="rate-bar" aria-hidden="true">
                        <span style="width: ${approvalWidth}%"></span>
                    </div>
                </td>
                <td>${formatPercent(config.feedback_coverage)}</td>
                <td>${config.average_latency_ms === null ? '—' : `${config.average_latency_ms} ms`}</td>
            </tr>
        `;
    }).join('');

    elements.configurationAnalytics.innerHTML = `
        <table class="analytics-table">
            <thead>
                <tr>
                    <th>Configuration</th>
                    <th>Responses</th>
                    <th>Rated</th>
                    <th>Approval</th>
                    <th>Coverage</th>
                    <th>Avg. latency</th>
                </tr>
            </thead>
            <tbody>${rows}</tbody>
        </table>
    `;
}

function renderNegativeFeedback(examples) {
    if (!examples.length) {
        elements.negativeFeedbackList.innerHTML =
            '<div class="dashboard-empty">No negative feedback has been attributed yet.</div>';
        return;
    }

    elements.negativeFeedbackList.innerHTML = examples.map(example => `
        <article class="negative-item">
            <div class="negative-meta">
                <span>Config: ${escapeHtml(example.config_name)}</span>
                <span>Model: ${escapeHtml(example.model || 'Unknown')}</span>
                <span>${escapeHtml(new Date(example.timestamp).toLocaleString())}</span>
            </div>
            <div class="negative-prompt">
                <strong>Prompt:</strong> ${escapeHtml(example.prompt || 'Unavailable')}
            </div>
            <div class="negative-response">
                <strong>Response:</strong> ${escapeHtml(example.response)}
            </div>
            <div class="negative-comment">
                <strong>User comment:</strong> ${escapeHtml(example.comment || 'No comment supplied')}
            </div>
        </article>
    `).join('');
}

function renderSummaryMetrics(configurations) {
    const totals = configurations.reduce((summary, config) => {
        summary.responses += config.total_responses;
        summary.rated += config.rated_responses;
        summary.positive += config.positive_feedback;
        return summary;
    }, { responses: 0, rated: 0, positive: 0 });

    elements.totalResponsesMetric.textContent = String(totals.responses);
    elements.ratedResponsesMetric.textContent = String(totals.rated);
    elements.approvalRateMetric.textContent = totals.rated
        ? formatPercent(totals.positive / totals.rated)
        : '—';
    elements.feedbackCoverageMetric.textContent = totals.responses
        ? formatPercent(totals.rated / totals.responses)
        : '0%';
}

async function loadAnalytics() {
    elements.refreshAnalyticsBtn.disabled = true;
    showAnalyticsStatus('Loading analytics...');

    try {
        const [configurations, negativeFeedback] = await Promise.all([
            api.get('/analytics/configurations'),
            api.get('/analytics/negative-feedback?limit=20')
        ]);

        renderSummaryMetrics(configurations);
        renderConfigurationAnalytics(configurations);
        renderNegativeFeedback(negativeFeedback);
        showAnalyticsStatus(`Loaded ${configurations.length} configuration result(s).`);
    } catch (error) {
        const needsToken = /403|token|credentials/i.test(error.message);
        showAnalyticsStatus(
            needsToken
                ? 'Analytics access requires the APP_TOKEN configured on the server.'
                : `Analytics error: ${error.message}`,
            'error'
        );
    } finally {
        elements.refreshAnalyticsBtn.disabled = false;
    }
}

function saveAnalyticsToken() {
    const token = elements.analyticsToken.value.trim();
    if (token) {
        window.sessionStorage.setItem('flywheelAppToken', token);
        showAnalyticsStatus('Token saved for this browser session.');
    } else {
        window.sessionStorage.removeItem('flywheelAppToken');
        showAnalyticsStatus('Stored token cleared.');
    }
    loadAnalytics();
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
elements.chatViewBtn.addEventListener('click', () => setActiveView('chat'));
elements.analyticsViewBtn.addEventListener('click', () => setActiveView('analytics'));
elements.refreshAnalyticsBtn.addEventListener('click', loadAnalytics);
elements.saveTokenBtn.addEventListener('click', saveAnalyticsToken);

// Initialize
console.log('Data Flywheel Chatbot initialized');
elements.analyticsToken.value = api.getToken();
loadSessions(); // Load sessions on startup
elements.messageInput.focus();
