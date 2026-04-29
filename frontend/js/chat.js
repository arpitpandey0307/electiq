/**
 * ElectIQ — Chat Module: SSE streaming + typewriter effect
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
    // Show welcome + fetch suggestions
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
      <div class="welcome-container">
        <span class="welcome-icon">🗳️</span>
        <h2 class="welcome-title">Welcome to ElectIQ!</h2>
        <p class="welcome-subtitle">${roleGreetings[role] || roleGreetings.voter}</p>
        <div class="suggestions" id="chatSuggestions"></div>
      </div>
    `;
  },

  async fetchSuggestions(role) {
    try {
      const res = await fetch(`/api/chat/suggestions?role=${role}`);
      const data = await res.json();
      this.suggestions = data.suggestions || [];
      this.renderSuggestions();
    } catch (e) {
      // Fallback suggestions
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
    
    container.innerHTML = this.suggestions.map(q =>
      `<button class="suggestion-chip" onclick="Chat.useSuggestion('${q.replace(/'/g, "\\'")}')">${q}</button>`
    ).join('');
  },

  useSuggestion(text) {
    this.inputEl.value = text;
    this.sendMessage();
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

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          role: App.state.role || 'voter',
          message: text,
          history: this.history.slice(-10) // Last 10 messages for context
        })
      });

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
            } catch (e) { /* skip malformed */ }
          }
        }
      }

      this.history.push({ role: 'assistant', content: fullResponse });
      
      // Check for quiz trigger
      this.checkQuizTrigger(fullResponse, text);

    } catch (err) {
      this.hideTyping();
      this.addMessage('ai', 'Sorry, I had trouble connecting. Please try again.');
    }

    this.isStreaming = false;
    this.sendBtn.disabled = false;
    this.inputEl.focus();
  },

  addMessage(type, content, streaming = false) {
    const div = document.createElement('div');
    div.className = `message ${type}`;
    
    const avatar = type === 'ai' ? '🗳️' : '👤';
    const sender = type === 'ai' ? 'ElectIQ' : 'You';
    
    div.innerHTML = `
      <div class="message-avatar">${avatar}</div>
      <div class="message-body">
        <span class="message-sender">${sender}</span>
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
    div.innerHTML = `
      <div class="message-avatar" style="background: linear-gradient(135deg, var(--primary), var(--primary-light)); color: white; border-radius: 50%; width: 36px; height: 36px; display: flex; align-items: center; justify-content: center;">🗳️</div>
      <div class="typing-dots"><span></span><span></span><span></span></div>
    `;
    this.messagesEl.appendChild(div);
    this.scrollToBottom();
  },

  hideTyping() {
    document.getElementById('typingIndicator')?.remove();
  },

  formatMarkdown(text) {
    // Simple markdown → HTML
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
      cta.onclick = () => { App.switchTab('quiz'); };
      cta.innerHTML = `
        <span>🏆</span>
        <span class="quiz-cta-text">Test your knowledge on this topic! →</span>
        <span class="quiz-cta-arrow">→</span>
      `;
      this.messagesEl.appendChild(cta);
      this.scrollToBottom();
    }
  },

  scrollToBottom() {
    this.messagesEl.scrollTop = this.messagesEl.scrollHeight;
  },

  // Called from timeline/scenarios to pre-fill a question
  askAbout(text) {
    App.switchTab('chat');
    this.inputEl.value = text;
    setTimeout(() => this.sendMessage(), 300);
  }
};
