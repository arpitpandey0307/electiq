/**
 * ElectIQ — App Core: State Management + Router
 */

const App = {
  state: {
    role: localStorage.getItem('electiq_role') || null,
    activeTab: 'chat',
    darkMode: localStorage.getItem('electiq_dark') === 'true' ||
              window.matchMedia('(prefers-color-scheme: dark)').matches,
    badges: JSON.parse(localStorage.getItem('electiq_badges') || '[]'),
    quizScores: JSON.parse(localStorage.getItem('electiq_scores') || '{}'),
    lang: localStorage.getItem('electiq_lang') || 'en'
  },

  init() {
    // Apply dark mode
    if (this.state.darkMode) {
      document.documentElement.setAttribute('data-theme', 'dark');
    }
    
    // Show role modal if no role set
    if (!this.state.role) {
      this.showRoleModal();
    } else {
      this.hideRoleModal();
      this.updateRoleBadge();
    }

    // Init tab navigation
    this.initTabs();
    
    // Init header actions
    this.initHeaderActions();

    // Init modules
    Chat.init();
    Timeline.init();
    Quiz.init();
    Scenarios.init();
  },

  // ── Role Modal ──
  showRoleModal() {
    document.getElementById('roleModal').classList.remove('hidden');
  },

  hideRoleModal() {
    document.getElementById('roleModal').classList.add('hidden');
  },

  selectRole(role) {
    this.state.role = role;
    localStorage.setItem('electiq_role', role);
    
    // Highlight selected card
    document.querySelectorAll('.role-card').forEach(c => c.classList.remove('selected'));
    document.querySelector(`[data-role="${role}"]`).classList.add('selected');
  },

  confirmRole() {
    if (!this.state.role) return;
    this.hideRoleModal();
    this.updateRoleBadge();
    Chat.onRoleSelected(this.state.role);
  },

  updateRoleBadge() {
    const roleNames = { voter: '🗳️ Voter', candidate: '🏛️ Candidate', journalist: '📰 Journalist', student: '🎓 Student' };
    const badge = document.getElementById('roleBadge');
    if (badge) badge.textContent = roleNames[this.state.role] || '🗳️ Voter';
  },

  // ── Tab Navigation ──
  initTabs() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const tab = btn.dataset.tab;
        this.switchTab(tab);
      });
    });
    this.switchTab(this.state.activeTab);
  },

  switchTab(tabId) {
    this.state.activeTab = tabId;
    
    // Update buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.tab === tabId);
    });
    
    // Update content
    document.querySelectorAll('.tab-content').forEach(content => {
      content.classList.toggle('active', content.id === `tab-${tabId}`);
    });

    // Lazy-load data
    if (tabId === 'timeline') Timeline.load();
    if (tabId === 'quiz') Quiz.loadTopics();
    if (tabId === 'scenarios') Scenarios.load();
  },

  // ── Header Actions ──
  initHeaderActions() {
    // Dark mode toggle
    document.getElementById('darkToggle')?.addEventListener('click', () => {
      this.state.darkMode = !this.state.darkMode;
      localStorage.setItem('electiq_dark', this.state.darkMode);
      document.documentElement.setAttribute('data-theme', this.state.darkMode ? 'dark' : 'light');
      const btn = document.getElementById('darkToggle');
      btn.textContent = this.state.darkMode ? '☀️' : '🌙';
    });

    // Role badge click → reopen modal
    document.getElementById('roleBadge')?.addEventListener('click', () => {
      this.showRoleModal();
    });

    // Set initial dark mode icon
    const darkBtn = document.getElementById('darkToggle');
    if (darkBtn) darkBtn.textContent = this.state.darkMode ? '☀️' : '🌙';
  },

  // ── Badge System ──
  earnBadge(badgeId, name, icon) {
    if (this.state.badges.includes(badgeId)) return false;
    this.state.badges.push(badgeId);
    localStorage.setItem('electiq_badges', JSON.stringify(this.state.badges));
    this.showBadgeCelebration(name, icon);
    return true;
  },

  showBadgeCelebration(name, icon) {
    const overlay = document.getElementById('badgeOverlay');
    document.getElementById('badgeBigIcon').textContent = icon;
    document.getElementById('badgeName').textContent = name;
    overlay.classList.remove('hidden');
    
    setTimeout(() => overlay.classList.add('hidden'), 3000);
    overlay.addEventListener('click', () => overlay.classList.add('hidden'), { once: true });
  },

  hasBadge(id) {
    return this.state.badges.includes(id);
  },

  saveQuizScore(topic, score, total) {
    this.state.quizScores[topic] = { score, total, date: Date.now() };
    localStorage.setItem('electiq_scores', JSON.stringify(this.state.quizScores));
    
    // Check badge milestones
    const completedTopics = Object.keys(this.state.quizScores).length;
    if (completedTopics >= 1) this.earnBadge('civic-novice', 'Civic Novice', '🥉');
    if (completedTopics >= 3) this.earnBadge('informed-citizen', 'Informed Citizen', '🥈');
    if (completedTopics >= 5) this.earnBadge('democracy-champion', 'Democracy Champion', '🥇');
    
    // Perfect scores
    const allPerfect = Object.values(this.state.quizScores).every(s => s.score === s.total);
    if (completedTopics >= 5 && allPerfect) this.earnBadge('electiq-master', 'ElectIQ Master', '🏆');
  }
};

// Start the app
document.addEventListener('DOMContentLoaded', () => App.init());
