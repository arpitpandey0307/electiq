/**
 * ElectIQ — Quiz Module
 *
 * Interactive quiz engine with topic selection, progressive scoring,
 * badge awards, and full keyboard accessibility.
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
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      this.topics = data.topics;
      this.showTopicSelector();
      container.removeAttribute('aria-busy');
    } catch (e) {
      container.removeAttribute('aria-busy');
      container.innerHTML = '<div class="empty-state" role="alert"><span class="empty-icon" aria-hidden="true">⚠️</span><p class="empty-text">Unable to load quizzes.</p></div>';
    }
  },

  showTopicSelector() {
    const container = document.getElementById('quizContent');

    // Badges bar
    let badgesHtml = '<div class="badges-bar" role="list" aria-label="Badge progress">';
    const allBadges = [
      { id: 'civic-novice', name: 'Civic Novice', icon: '🥉' },
      { id: 'informed-citizen', name: 'Informed Citizen', icon: '🥈' },
      { id: 'democracy-champion', name: 'Democracy Champion', icon: '🥇' },
      { id: 'electiq-master', name: 'ElectIQ Master', icon: '🏆' }
    ];
    allBadges.forEach(b => {
      const earned = App.hasBadge(b.id);
      badgesHtml += `<span class="badge ${earned ? 'earned' : ''}" role="listitem" aria-label="${b.name}: ${earned ? 'Earned' : 'Not yet earned'}">${b.icon} ${b.name}</span>`;
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
      <div class="quiz-progress-summary" aria-live="polite">${completed}/${total} topics completed</div>
      <div class="progress-bar-container" role="progressbar" aria-valuenow="${Math.round(pct)}" aria-valuemin="0" aria-valuemax="100" aria-label="Quiz progress: ${completed} of ${total} topics completed">
        <div class="progress-bar-fill" style="width:${pct}%"></div>
      </div>
      <div class="quiz-topics" role="list" aria-label="Quiz topics">
    `;

    this.topics.forEach(t => {
      const score = App.state.quizScores[t.id];
      const scoreLabel = score ? `✅ ${score.score}/${score.total}` : `${t.question_count} questions`;
      html += `
        <div class="quiz-topic-card" data-topic-id="${t.id}" tabindex="0" role="listitem"
             aria-label="${t.title}: ${scoreLabel}">
          <span class="topic-icon" aria-hidden="true">${t.icon}</span>
          <span class="topic-name">${t.title}</span>
          <span class="topic-count">${scoreLabel}</span>
        </div>
      `;
    });

    html += '</div>';
    container.innerHTML = html;

    // Attach event listeners (no inline onclick)
    container.querySelectorAll('.quiz-topic-card').forEach(card => {
      const topicId = card.dataset.topicId;
      card.addEventListener('click', () => this.startQuiz(topicId));
      card.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          this.startQuiz(topicId);
        }
      });
    });

    App.announce(`Quiz loaded. ${total} topics available, ${completed} completed.`);
  },

  async startQuiz(topicId) {
    this.currentTopic = topicId;
    this.currentQ = 0;
    this.score = 0;
    this.answered = false;

    try {
      const res = await fetch(`/api/quiz/${encodeURIComponent(topicId)}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      this.questions = data.questions;
      this.showQuestion();
      App.announce(`Quiz started: ${data.title || topicId}. Question 1 of ${this.questions.length}.`);
    } catch (e) {
      App.announce('Failed to load quiz. Please try again.');
    }
  },

  showQuestion() {
    const container = document.getElementById('quizContent');
    const q = this.questions[this.currentQ];
    const letters = ['A', 'B', 'C', 'D'];
    const qNum = this.currentQ + 1;
    const qTotal = this.questions.length;

    container.innerHTML = `
      <div class="quiz-game" role="region" aria-label="Quiz question ${qNum} of ${qTotal}">
        <button class="btn btn-secondary btn-sm quiz-back-btn" id="quizBackBtn" type="button" aria-label="Go back to topic selection">← Back to Topics</button>
        <div class="quiz-progress">
          <span class="quiz-progress-text" aria-live="polite">Question ${qNum} of ${qTotal}</span>
          <div class="progress-bar-container" role="progressbar" aria-valuenow="${Math.round(((this.currentQ) / qTotal) * 100)}" aria-valuemin="0" aria-valuemax="100">
            <div class="progress-bar-fill" style="width:${((this.currentQ) / qTotal) * 100}%"></div>
          </div>
        </div>
        <div class="quiz-question-card">
          <p class="quiz-question-text" id="quizQuestionText">${q.q}</p>
          <div class="quiz-options" role="group" aria-labelledby="quizQuestionText" id="quizOptionsGroup">
            ${q.options.map((opt, i) => `
              <button class="quiz-option" id="quizOpt${i}" type="button"
                      aria-label="Option ${letters[i]}: ${opt}" aria-describedby="quizQuestionText">
                <span class="option-letter" aria-hidden="true">${letters[i]}</span>
                <span>${opt}</span>
              </button>
            `).join('')}
          </div>
          <div class="quiz-explanation" id="quizExplanation" role="region" aria-label="Explanation">
            <span class="explanation-label">💡 Explanation</span>
            ${q.explanation}
          </div>
          <button class="btn btn-primary quiz-next-btn" id="quizNextBtn" type="button">
            ${this.currentQ < qTotal - 1 ? 'Next Question →' : 'See Results →'}
          </button>
        </div>
      </div>
    `;

    // Attach event listeners
    document.getElementById('quizBackBtn')?.addEventListener('click', () => this.showTopicSelector());
    document.getElementById('quizNextBtn')?.addEventListener('click', () => this.nextQuestion());

    container.querySelectorAll('.quiz-option').forEach((btn, i) => {
      btn.addEventListener('click', () => this.answer(i));
    });

    this.answered = false;
  },

  answer(idx) {
    if (this.answered) return;
    this.answered = true;

    const q = this.questions[this.currentQ];
    const correct = q.answer;

    document.getElementById(`quizOpt${idx}`).classList.add('selected');

    if (idx === correct) {
      document.getElementById(`quizOpt${idx}`).classList.add('correct');
      this.score++;
      App.announce('Correct!');
    } else {
      document.getElementById(`quizOpt${idx}`).classList.add('wrong');
      document.getElementById(`quizOpt${correct}`).classList.add('correct');
      App.announce(`Incorrect. The correct answer was option ${['A','B','C','D'][correct]}.`);
    }

    // Show explanation and next button
    document.getElementById('quizExplanation').classList.add('visible');
    const nextBtn = document.getElementById('quizNextBtn');
    nextBtn.classList.add('visible');
    requestAnimationFrame(() => nextBtn.focus());

    // Disable all options properly
    document.querySelectorAll('.quiz-option').forEach(el => {
      el.classList.add('selected');
      el.disabled = true;
      el.setAttribute('aria-disabled', 'true');
    });
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

    App.saveQuizScore(this.currentTopic, this.score, this.questions.length);

    container.innerHTML = `
      <div class="quiz-results" role="region" aria-label="Quiz results">
        <div class="quiz-score-circle ${scoreClass}" aria-label="Score: ${this.score} out of ${this.questions.length}">${this.score}/${this.questions.length}</div>
        <h2 class="quiz-results-title">${pct}% Correct!</h2>
        <p class="quiz-results-subtitle">${message}</p>
        <div class="quiz-results-actions">
          <button class="btn btn-primary" id="quizRetryBtn" type="button" aria-label="Retry this quiz">🔄 Retry</button>
          <button class="btn btn-secondary" id="quizAllTopicsBtn" type="button" aria-label="Back to all quiz topics">📋 All Topics</button>
          <button class="btn btn-gold" id="quizShareBtn" type="button" aria-label="Share your score">📤 Share Score</button>
        </div>
      </div>
    `;

    // Attach event listeners
    document.getElementById('quizRetryBtn')?.addEventListener('click', () => this.startQuiz(this.currentTopic));
    document.getElementById('quizAllTopicsBtn')?.addEventListener('click', () => this.showTopicSelector());
    document.getElementById('quizShareBtn')?.addEventListener('click', () => this.shareScore());

    App.announce(`Quiz complete! You scored ${this.score} out of ${this.questions.length}. ${pct} percent correct.`);
  },

  shareScore() {
    const pct = Math.round((this.score / this.questions.length) * 100);
    const text = `🗳️ I scored ${pct}% on ElectIQ's Election Quiz! Test your knowledge too! #ElectIQ #CivicEducation`;

    if (navigator.share) {
      navigator.share({ title: 'My ElectIQ Score', text }).catch(() => {});
    } else if (navigator.clipboard) {
      navigator.clipboard.writeText(text).then(() => {
        App.announce('Score copied to clipboard');
      }).catch(() => {
        App.announce('Unable to copy score');
      });
    }
  }
};
