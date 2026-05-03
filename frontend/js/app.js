/**
 * ElectIQ — App Core: State Management, Router, and Accessibility
 *
 * Manages application state, tab navigation with full keyboard support
 * (WAI-ARIA Tabs pattern), dark mode with system preference detection,
 * role selection with focus trapping, and the progressive badge system.
 *
 * Accessibility Features:
 *   - WAI-ARIA Tabs pattern with arrow key navigation
 *   - Focus trapping in modals (role selection, badge overlay)
 *   - Screen reader announcements via aria-live region
 *   - Escape key support for dismissing overlays
 *   - prefers-color-scheme and prefers-reduced-motion support
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

  /**
   * Initialize the application — called on DOMContentLoaded.
   */
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

    // Initialize subsystems
    this.initTabs();
    this.initHeaderActions();
    this.initKeyboardNav();
    this.initModalEvents();

    // Initialize feature modules
    Chat.init();
    Timeline.init();
    Quiz.init();
    Scenarios.init();
  },

  // ── Accessibility: Screen Reader Announcements ──

  /**
   * Announce a message to screen readers via the aria-live region.
   * @param {string} message - Text to announce
   */
  announce(message) {
    const el = document.getElementById('liveAnnouncements');
    if (el) {
      el.textContent = '';
      // Brief delay ensures the live region triggers re-announcement
      requestAnimationFrame(() => {
        setTimeout(() => { el.textContent = message; }, 100);
      });
    }
  },

  // ── Focus Trapping Utility ──

  /**
   * Trap keyboard focus within a container element.
   * @param {HTMLElement} container - The container to trap focus within
   * @param {KeyboardEvent} event - The keyboard event
   */
  trapFocus(container, event) {
    if (event.key !== 'Tab') return;

    const focusable = container.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );

    if (focusable.length === 0) return;

    const first = focusable[0];
    const last = focusable[focusable.length - 1];

    if (event.shiftKey) {
      if (document.activeElement === first) {
        event.preventDefault();
        last.focus();
      }
    } else {
      if (document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }
  },

  // ── Role Modal ──

  showRoleModal() {
    const modal = document.getElementById('roleModal');
    modal.classList.remove('hidden');
    modal.removeAttribute('aria-hidden');

    // Store the element that opened the modal for focus restoration
    this._previousFocus = document.activeElement;

    // Focus first interactive element
    const firstFocusable = modal.querySelector('.role-card');
    if (firstFocusable) {
      requestAnimationFrame(() => firstFocusable.focus());
    }
  },

  hideRoleModal() {
    const modal = document.getElementById('roleModal');
    modal.classList.add('hidden');
    modal.setAttribute('aria-hidden', 'true');

    // Restore focus to the element that opened the modal
    if (this._previousFocus && this._previousFocus.focus) {
      this._previousFocus.focus();
    }
  },

  initModalEvents() {
    // Role card click handlers (moved from inline onclick)
    document.querySelectorAll('.role-card').forEach(card => {
      card.addEventListener('click', () => {
        this.selectRole(card.dataset.role);
      });
    });

    // Confirm button
    const confirmBtn = document.getElementById('roleConfirmBtn');
    if (confirmBtn) {
      confirmBtn.addEventListener('click', () => this.confirmRole());
    }

    // Badge dismiss button
    const badgeDismissBtn = document.getElementById('badgeDismissBtn');
    if (badgeDismissBtn) {
      badgeDismissBtn.addEventListener('click', () => {
        document.getElementById('badgeOverlay').classList.add('hidden');
      });
    }

    // Focus trapping in role modal
    const roleModal = document.getElementById('roleModal');
    if (roleModal) {
      roleModal.addEventListener('keydown', (e) => {
        this.trapFocus(roleModal, e);
      });
    }

    // Focus trapping in badge overlay
    const badgeOverlay = document.getElementById('badgeOverlay');
    if (badgeOverlay) {
      badgeOverlay.addEventListener('keydown', (e) => {
        this.trapFocus(badgeOverlay, e);
        if (e.key === 'Escape') {
          badgeOverlay.classList.add('hidden');
        }
      });
    }

    // Language toggle
    const langToggle = document.getElementById('langToggle');
    if (langToggle) {
      langToggle.addEventListener('click', () => I18n.toggle());
    }
  },

  selectRole(role) {
    this.state.role = role;
    localStorage.setItem('electiq_role', role);

    // Update visual selection and ARIA state
    document.querySelectorAll('.role-card').forEach(c => {
      const isSelected = c.dataset.role === role;
      c.classList.toggle('selected', isSelected);
      c.setAttribute('aria-checked', isSelected ? 'true' : 'false');
    });

    this.announce(`Selected role: ${role}`);
  },

  confirmRole() {
    if (!this.state.role) return;
    this.hideRoleModal();
    this.updateRoleBadge();
    Chat.onRoleSelected(this.state.role);
    this.announce(`Role confirmed: ${this.state.role}. Welcome to ElectIQ!`);
  },

  updateRoleBadge() {
    const roleNames = {
      voter: '🗳️ Voter',
      candidate: '🏛️ Candidate',
      journalist: '📰 Journalist',
      student: '🎓 Student'
    };
    const badge = document.getElementById('roleBadge');
    if (badge) {
      badge.textContent = roleNames[this.state.role] || '🗳️ Voter';
      badge.setAttribute('aria-label',
        `Change role. Current role: ${this.state.role || 'Voter'}`
      );
    }
  },

  // ── Tab Navigation with Keyboard Support ──

  initTabs() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const tab = btn.dataset.tab;
        this.switchTab(tab);
      });
    });
    this.switchTab(this.state.activeTab);
  },

  /**
   * Initialize keyboard navigation for tabs (Arrow keys, Home, End).
   * Follows WAI-ARIA Tabs pattern for full accessibility.
   */
  initKeyboardNav() {
    const tabList = document.querySelector('[role="tablist"]');
    if (!tabList) return;

    tabList.addEventListener('keydown', (e) => {
      const tabs = Array.from(tabList.querySelectorAll('[role="tab"]'));
      const currentIndex = tabs.indexOf(document.activeElement);
      let newIndex = currentIndex;

      switch (e.key) {
        case 'ArrowRight':
        case 'ArrowDown':
          e.preventDefault();
          newIndex = (currentIndex + 1) % tabs.length;
          break;
        case 'ArrowLeft':
        case 'ArrowUp':
          e.preventDefault();
          newIndex = (currentIndex - 1 + tabs.length) % tabs.length;
          break;
        case 'Home':
          e.preventDefault();
          newIndex = 0;
          break;
        case 'End':
          e.preventDefault();
          newIndex = tabs.length - 1;
          break;
        default:
          return;
      }

      tabs[newIndex].focus();
      this.switchTab(tabs[newIndex].dataset.tab);
    });

    // Handle Enter/Space on role cards in modal
    document.querySelectorAll('.role-card').forEach(card => {
      card.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          this.selectRole(card.dataset.role);
        }
      });
    });

    // Handle Escape to close overlays
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        // Close role modal (only if a role is already selected)
        const modal = document.getElementById('roleModal');
        if (!modal.classList.contains('hidden') && this.state.role) {
          this.hideRoleModal();
        }
        // Close timeline panel
        const panel = document.getElementById('timelinePanel');
        if (panel && panel.classList.contains('open')) {
          Timeline.closePanel();
        }
        // Close badge overlay
        const badge = document.getElementById('badgeOverlay');
        if (badge && !badge.classList.contains('hidden')) {
          badge.classList.add('hidden');
        }
      }
    });
  },

  switchTab(tabId) {
    this.state.activeTab = tabId;

    // Update tab button states (ARIA + visual)
    document.querySelectorAll('.tab-btn').forEach(btn => {
      const isActive = btn.dataset.tab === tabId;
      btn.classList.toggle('active', isActive);
      btn.setAttribute('aria-selected', isActive ? 'true' : 'false');
      btn.setAttribute('tabindex', isActive ? '0' : '-1');
    });

    // Update tab panel visibility
    document.querySelectorAll('.tab-content').forEach(content => {
      content.classList.toggle('active', content.id === `tab-${tabId}`);
    });

    // Lazy-load data for the active tab
    if (tabId === 'timeline') Timeline.load();
    if (tabId === 'quiz') Quiz.loadTopics();
    if (tabId === 'scenarios') Scenarios.load();

    this.announce(`Switched to ${tabId} tab`);
  },

  // ── Header Actions ──

  initHeaderActions() {
    // Dark mode toggle
    document.getElementById('darkToggle')?.addEventListener('click', () => {
      this.state.darkMode = !this.state.darkMode;
      localStorage.setItem('electiq_dark', this.state.darkMode);
      document.documentElement.setAttribute(
        'data-theme', this.state.darkMode ? 'dark' : 'light'
      );
      const btn = document.getElementById('darkToggle');
      btn.textContent = this.state.darkMode ? '☀️' : '🌙';
      btn.setAttribute('aria-label',
        this.state.darkMode ? 'Switch to light mode' : 'Switch to dark mode'
      );
      this.announce(this.state.darkMode ? 'Dark mode enabled' : 'Light mode enabled');
    });

    // Role badge click → reopen modal
    document.getElementById('roleBadge')?.addEventListener('click', () => {
      this.showRoleModal();
    });

    // Set initial dark mode icon and label
    const darkBtn = document.getElementById('darkToggle');
    if (darkBtn) {
      darkBtn.textContent = this.state.darkMode ? '☀️' : '🌙';
      darkBtn.setAttribute('aria-label',
        this.state.darkMode ? 'Switch to light mode' : 'Switch to dark mode'
      );
    }
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

    this.announce(`Congratulations! You earned the ${name} badge!`);

    // Focus the dismiss button for keyboard users
    const dismissBtn = document.getElementById('badgeDismissBtn');
    if (dismissBtn) {
      requestAnimationFrame(() => dismissBtn.focus());
    }

    setTimeout(() => overlay.classList.add('hidden'), 5000);
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

    // Perfect scores across all topics
    const allPerfect = Object.values(this.state.quizScores).every(s => s.score === s.total);
    if (completedTopics >= 5 && allPerfect) {
      this.earnBadge('electiq-master', 'ElectIQ Master', '🏆');
    }
  }
};

// Start the app
document.addEventListener('DOMContentLoaded', () => App.init());
