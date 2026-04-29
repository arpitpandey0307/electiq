/**
 * ElectIQ — Quiz Module: Engine + Badge logic
 */

const Quiz = {
  topics: [],
  currentTopic: null,
  questions: [],
  currentQ: 0,
  score: 0,
  answered: false,

  init() {},

  async loadTopics() {
    const container = document.getElementById('quizContent');
    
    try {
      const res = await fetch('/api/quiz');
      const data = await res.json();
      this.topics = data.topics;
      this.showTopicSelector();
    } catch (e) {
      container.innerHTML = '<div class="empty-state"><span class="empty-icon">⚠️</span><p class="empty-text">Unable to load quizzes.</p></div>';
    }
  },

  showTopicSelector() {
    const container = document.getElementById('quizContent');
    
    // Show badges
    let badgesHtml = '<div class="badges-bar">';
    const allBadges = [
      { id: 'civic-novice', name: 'Civic Novice', icon: '🥉' },
      { id: 'informed-citizen', name: 'Informed Citizen', icon: '🥈' },
      { id: 'democracy-champion', name: 'Democracy Champion', icon: '🥇' },
      { id: 'electiq-master', name: 'ElectIQ Master', icon: '🏆' }
    ];
    allBadges.forEach(b => {
      const earned = App.hasBadge(b.id);
      badgesHtml += `<span class="badge ${earned ? 'earned' : ''}">${b.icon} ${b.name}</span>`;
    });
    badgesHtml += '</div>';

    // Progress
    const completed = Object.keys(App.state.quizScores).length;
    const total = this.topics.length;
    const pct = total > 0 ? (completed / total * 100) : 0;

    let html = `
      <h2 class="section-title">🏆 Election IQ Quiz</h2>
      <p class="section-subtitle">Test your knowledge and earn badges!</p>
      ${badgesHtml}
      <div style="margin-bottom:8px;font-size:13px;color:var(--text-muted)">${completed}/${total} topics completed</div>
      <div class="progress-bar-container">
        <div class="progress-bar-fill" style="width:${pct}%"></div>
      </div>
      <div class="quiz-topics">
    `;

    this.topics.forEach(t => {
      const score = App.state.quizScores[t.id];
      const scoreLabel = score ? `✅ ${score.score}/${score.total}` : `${t.question_count} questions`;
      html += `
        <div class="quiz-topic-card" onclick="Quiz.startQuiz('${t.id}')">
          <span class="topic-icon">${t.icon}</span>
          <span class="topic-name">${t.title}</span>
          <span class="topic-count">${scoreLabel}</span>
        </div>
      `;
    });

    html += '</div>';
    container.innerHTML = html;
  },

  async startQuiz(topicId) {
    this.currentTopic = topicId;
    this.currentQ = 0;
    this.score = 0;
    this.answered = false;

    try {
      const res = await fetch(`/api/quiz/${topicId}`);
      const data = await res.json();
      this.questions = data.questions;
      this.showQuestion();
    } catch (e) {
      alert('Failed to load quiz. Please try again.');
    }
  },

  showQuestion() {
    const container = document.getElementById('quizContent');
    const q = this.questions[this.currentQ];
    const letters = ['A', 'B', 'C', 'D'];

    container.innerHTML = `
      <div class="quiz-game">
        <button class="btn btn-secondary btn-sm" onclick="Quiz.showTopicSelector()" style="margin-bottom:16px">← Back to Topics</button>
        <div class="quiz-progress">
          <span class="quiz-progress-text">Question ${this.currentQ + 1} of ${this.questions.length}</span>
          <div class="progress-bar-container" style="flex:1">
            <div class="progress-bar-fill" style="width:${((this.currentQ) / this.questions.length) * 100}%"></div>
          </div>
        </div>
        <div class="quiz-question-card">
          <p class="quiz-question-text">${q.q}</p>
          <div class="quiz-options">
            ${q.options.map((opt, i) => `
              <button class="quiz-option" onclick="Quiz.answer(${i})" id="quizOpt${i}">
                <span class="option-letter">${letters[i]}</span>
                <span>${opt}</span>
              </button>
            `).join('')}
          </div>
          <div class="quiz-explanation" id="quizExplanation">
            <span class="explanation-label">💡 Explanation</span>
            ${q.explanation}
          </div>
          <button class="btn btn-primary quiz-next-btn" id="quizNextBtn" onclick="Quiz.nextQuestion()">
            ${this.currentQ < this.questions.length - 1 ? 'Next Question →' : 'See Results →'}
          </button>
        </div>
      </div>
    `;
    this.answered = false;
  },

  answer(idx) {
    if (this.answered) return;
    this.answered = true;

    const q = this.questions[this.currentQ];
    const correct = q.answer;

    // Mark selected
    document.getElementById(`quizOpt${idx}`).classList.add('selected');
    
    if (idx === correct) {
      document.getElementById(`quizOpt${idx}`).classList.add('correct');
      this.score++;
    } else {
      document.getElementById(`quizOpt${idx}`).classList.add('wrong');
      document.getElementById(`quizOpt${correct}`).classList.add('correct');
    }

    // Show explanation
    document.getElementById('quizExplanation').classList.add('visible');
    document.getElementById('quizNextBtn').classList.add('visible');

    // Disable all options
    document.querySelectorAll('.quiz-option').forEach(el => el.classList.add('selected'));
  },

  nextQuestion() {
    this.currentQ++;
    if (this.currentQ < this.questions.length) {
      this.showQuestion();
    } else {
      this.showResults();
    }
  },

  showResults() {
    const container = document.getElementById('quizContent');
    const pct = Math.round((this.score / this.questions.length) * 100);
    let scoreClass = 'low';
    let message = 'Keep learning! Every question is a step toward informed citizenship.';
    
    if (pct === 100) { scoreClass = 'perfect'; message = '🎉 Perfect score! You\'re an election expert!'; }
    else if (pct >= 80) { scoreClass = 'great'; message = '🌟 Excellent! You really know your elections!'; }
    else if (pct >= 60) { scoreClass = 'okay'; message = '👍 Good job! A few more topics and you\'ll be a pro!'; }

    // Save score
    App.saveQuizScore(this.currentTopic, this.score, this.questions.length);

    container.innerHTML = `
      <div class="quiz-results">
        <div class="quiz-score-circle ${scoreClass}">${this.score}/${this.questions.length}</div>
        <h2 class="quiz-results-title">${pct}% Correct!</h2>
        <p class="quiz-results-subtitle">${message}</p>
        <div class="quiz-results-actions">
          <button class="btn btn-primary" onclick="Quiz.startQuiz('${this.currentTopic}')">🔄 Retry</button>
          <button class="btn btn-secondary" onclick="Quiz.showTopicSelector()">📋 All Topics</button>
          <button class="btn btn-gold" onclick="Quiz.shareScore()">📤 Share Score</button>
        </div>
      </div>
    `;
  },

  shareScore() {
    const pct = Math.round((this.score / this.questions.length) * 100);
    const text = `🗳️ I scored ${pct}% on ElectIQ's Election Quiz! Test your knowledge too! #ElectIQ #CivicEducation`;
    
    if (navigator.share) {
      navigator.share({ title: 'My ElectIQ Score', text });
    } else {
      navigator.clipboard.writeText(text).then(() => {
        alert('Score copied to clipboard! Share it on social media! 🎉');
      });
    }
  }
};
