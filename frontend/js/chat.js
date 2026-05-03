/**
 * ElectIQ — Chat Module
 *
 * SSE streaming chat with typewriter effect, accessible message log,
 * quiz topic detection with cross-tab navigation, and timestamps
 * for screen reader users.
 */

const Chat = {
  history: [],
  isStreaming: false,
  suggestions: [],

  init() {
    this.messagesEl = document.getElementById('chatMessages');
    this.inputEl = document.getElementById('chatInput');
    this.sendBtn = document.getElementById('chatSendBtn');

    // Send button
    this.sendBtn.addEventListener('click', () => this.sendMessage());

    // Enter key (shift+enter for newline)
    this.inputEl.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.sendMessage();
      }
    });

    // Auto-resize textarea
    this.inputEl.addEventListener('input', () => {
      this.inputEl.style.height = 'auto';
      this.inputEl.style.height = Math.min(this.inputEl.scrollHeight, 120) + 'px';
    });
  },

  onRoleSelected(role) {
    this.showWelcome(role);
    this.fetchSuggestions(role);
  },

  showWelcome(role) {
    const roleGreetings = {
      voter: "I'll help you understand everything about voting — from registration to election day!",
      candidate: "I'll guide you through the nomination process, campaign rules, and election procedures.",
      journalist: "I'll help you understand electoral regulations, media guidelines, and campaign finance rules.",
      student: "I'll make elections fun and easy to understand with simple explanations and examples!"
    };

    this.messagesEl.innerHTML = `
      <div class="welcome-container" role="status">
        <span class="welcome-icon" aria-hidden="true">🗳️</span>
        <h2 class="welcome-title">Welcome to ElectIQ!</h2>
        <p class="welcome-subtitle">${roleGreetings[role] || roleGreetings.voter}</p>
        <div class="suggestions" id="chatSuggestions" role="group" aria-label="Suggested questions"></div>
      </div>
    `;
  },

  async fetchSuggestions(role) {
    try {
      const res = await fetch(`/api/chat/suggestions?role=${encodeURIComponent(role)}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      this.suggestions = data.suggestions || [];
      this.renderSuggestions();
    } catch (e) {
      this.suggestions = [
        "How does voting work?",
        "What ID do I need?",
        "Explain the election process",
        "What is EVM?"
      ];
      this.renderSuggestions();
    }
  },

  renderSuggestions() {
    const container = document.getElementById('chatSuggestions');
    if (!container) return;

    container.innerHTML = this.suggestions.map(q => {
      const escaped = q.replace(/'/g, "\\'").replace(/"/g, '&quot;');
      return `<button class="suggestion-chip" type="button" aria-label="Ask: ${q}" data-question="${escaped}">${q}</button>`;
    }).join('');

    // Attach event listeners (no inline onclick)
    container.querySelectorAll('.suggestion-chip').forEach(chip => {
      chip.addEventListener('click', () => {
        this.useSuggestion(chip.dataset.question);
      });
    });
  },

  useSuggestion(text) {
    this.inputEl.value = text;
    this.sendMessage();
  },

  /**
   * Format a timestamp for screen reader accessibility.
   * @returns {string} Formatted time string
   */
  _formatTimestamp() {
    return new Date().toLocaleTimeString('en-IN', {
      hour: '2-digit',
      minute: '2-digit'
    });
  },

  async sendMessage() {
    const text = this.inputEl.value.trim();
    if (!text || this.isStreaming) return;

    // Clear welcome if first message
    const welcome = this.messagesEl.querySelector('.welcome-container');
    if (welcome) welcome.remove();

    // Add user message
    this.addMessage('user', text);
    this.history.push({ role: 'user', content: text });

    // Clear input
    this.inputEl.value = '';
    this.inputEl.style.height = 'auto';

    // Show typing indicator
    this.showTyping();

    // Stream AI response
    this.isStreaming = true;
    this.sendBtn.disabled = true;
    this.sendBtn.setAttribute('aria-busy', 'true');

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          role: App.state.role || 'voter',
          message: text,
          history: this.history.slice(-10)
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      this.hideTyping();

      // Create AI message bubble
      const msgEl = this.addMessage('ai', '', true);
      const contentEl = msgEl.querySelector('.message-text');
      let fullResponse = '';

      // Read SSE stream
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.done) break;
              if (data.token) {
                fullResponse += data.token;
                contentEl.innerHTML = this.formatMarkdown(fullResponse);
                this.scrollToBottom();
              }
            } catch (e) { /* skip malformed SSE data */ }
          }
        }
      }

      this.history.push({ role: 'assistant', content: fullResponse });
      App.announce('ElectIQ has responded');

      // Check for quiz trigger
      this.checkQuizTrigger(fullResponse, text);

    } catch (err) {
      this.hideTyping();
      this.addMessage('ai', 'Sorry, I had trouble connecting. Please try again.');
      App.announce('Error: Could not get a response');
    }

    this.isStreaming = false;
    this.sendBtn.disabled = false;
    this.sendBtn.setAttribute('aria-busy', 'false');
    this.inputEl.focus();
  },

  addMessage(type, content, streaming = false) {
    const div = document.createElement('div');
    div.className = `message ${type}`;
    div.setAttribute('role', 'article');

    const avatar = type === 'ai' ? '🗳️' : '👤';
    const sender = type === 'ai' ? 'ElectIQ' : 'You';
    const timestamp = this._formatTimestamp();

    div.innerHTML = `
      <div class="message-avatar" aria-hidden="true">${avatar}</div>
      <div class="message-body">
        <div class="message-header">
          <span class="message-sender">${sender}</span>
          <time class="message-time" datetime="${new Date().toISOString()}">${timestamp}</time>
        </div>
        <div class="message-content">
          <span class="message-text">${streaming ? '' : this.formatMarkdown(content)}</span>
        </div>
      </div>
    `;

    this.messagesEl.appendChild(div);
    this.scrollToBottom();
    return div;
  },

  showTyping() {
    const div = document.createElement('div');
    div.className = 'typing-indicator';
    div.id = 'typingIndicator';
    div.setAttribute('role', 'status');
    div.setAttribute('aria-label', 'ElectIQ is typing');
    div.innerHTML = `
      <div class="message-avatar typing-avatar" aria-hidden="true">🗳️</div>
      <div class="typing-dots"><span></span><span></span><span></span></div>
    `;
    this.messagesEl.appendChild(div);
    this.scrollToBottom();
  },

  hideTyping() {
    document.getElementById('typingIndicator')?.remove();
  },

  /**
   * Convert basic markdown formatting to HTML.
   * @param {string} text - Raw text with markdown formatting
   * @returns {string} HTML-formatted string
   */
  formatMarkdown(text) {
    return text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/^[•●]\s?/gm, '• ')
      .replace(/\n/g, '<br>')
      .replace(/📎\s*(Source:.*)/g, '<span class="message-source">📎 $1</span>');
  },

  checkQuizTrigger(response, question) {
    const quizTopics = ['registration', 'voting', 'candidate', 'nomination', 'counting', 'result', 'evm', 'ballot'];
    const lowerQ = question.toLowerCase();
    const matchedTopic = quizTopics.find(t => lowerQ.includes(t));

    if (matchedTopic) {
      const cta = document.createElement('div');
      cta.className = 'quiz-cta';
      cta.setAttribute('role', 'button');
      cta.setAttribute('tabindex', '0');
      cta.setAttribute('aria-label', 'Test your knowledge on this topic with a quiz');
      cta.addEventListener('click', () => App.switchTab('quiz'));
      cta.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          App.switchTab('quiz');
        }
      });
      cta.innerHTML = `
        <span aria-hidden="true">🏆</span>
        <span class="quiz-cta-text">Test your knowledge on this topic! →</span>
      `;
      this.messagesEl.appendChild(cta);
      this.scrollToBottom();
    }
  },

  scrollToBottom() {
    this.messagesEl.scrollTop = this.messagesEl.scrollHeight;
  },

  askAbout(text) {
    App.switchTab('chat');
    this.inputEl.value = text;
    setTimeout(() => this.sendMessage(), 300);
  }
};
