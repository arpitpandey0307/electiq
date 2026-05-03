/**
 * ElectIQ — Timeline Module
 *
 * Renders the interactive election process timeline with accessible
 * milestone nodes, a slide-in detail panel with focus trapping,
 * and integration with the glossary endpoint.
 */

const Timeline = {
  data: null,
  loaded: false,

  init() {
    // Panel close handlers
    document.getElementById('panelClose')?.addEventListener('click', () => this.closePanel());
    document.getElementById('panelBackdrop')?.addEventListener('click', () => this.closePanel());

    // Focus trapping in timeline panel
    const panel = document.getElementById('timelinePanel');
    if (panel) {
      panel.addEventListener('keydown', (e) => {
        if (panel.classList.contains('open')) {
          App.trapFocus(panel, e);
        }
      });
    }
  },

  async load() {
    if (this.loaded) return;

    try {
      const res = await fetch('/api/timeline');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      this.data = await res.json();
      this.render();
      this.loaded = true;
      // Clear aria-busy
      const container = document.getElementById('timelineContent');
      if (container) container.removeAttribute('aria-busy');
    } catch (e) {
      const container = document.getElementById('timelineContent');
      container.removeAttribute('aria-busy');
      container.innerHTML =
        '<div class="empty-state" role="alert"><span class="empty-icon" aria-hidden="true">⚠️</span><p class="empty-text">Unable to load timeline. Please try again.</p></div>';
    }
  },

  render() {
    const container = document.getElementById('timelineContent');
    const milestones = this.data.milestones;

    let html = `
      <h2 class="section-title">Election Process Timeline</h2>
      <p class="section-subtitle">Click any milestone to learn more about that stage</p>
      <div class="timeline-scroll" role="region" aria-label="Election timeline">
        <div class="timeline" role="list">
    `;

    milestones.forEach((m) => {
      html += `
        <div class="timeline-node ${m.status}" data-milestone-id="${m.id}"
             role="listitem" tabindex="0" aria-label="${m.label} — ${m.status}">
          <div class="timeline-dot" aria-hidden="true">${m.icon}</div>
          <span class="timeline-label">${m.label}</span>
          <span class="timeline-date">${this.formatDate(m.date)}</span>
        </div>
      `;
    });

    html += `</div></div>`;

    // Glossary section
    html += `
      <h2 class="section-title" id="glossaryTitle">📊 Key Election Terms</h2>
      <p class="section-subtitle">Click a term to expand its definition</p>
      <div class="glossary-grid" id="glossaryGrid" role="list" aria-labelledby="glossaryTitle"></div>
    `;

    container.innerHTML = html;

    // Attach event listeners (no inline onclick)
    container.querySelectorAll('.timeline-node').forEach(node => {
      const milestoneId = node.dataset.milestoneId;
      node.addEventListener('click', () => this.openPanel(milestoneId));
      node.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          this.openPanel(milestoneId);
        }
      });
    });

    this.loadGlossary();
  },

  async loadGlossary() {
    try {
      const res = await fetch('/api/glossary');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const grid = document.getElementById('glossaryGrid');

      grid.innerHTML = data.terms.map(t => `
        <div class="glossary-card" role="listitem" tabindex="0" aria-expanded="false"
             aria-label="${t.term}: ${t.short}">
          <div class="card-header">
            <span class="card-icon" aria-hidden="true">${t.icon}</span>
            <span class="card-term">${t.term}</span>
          </div>
          <p class="card-short">${t.short}</p>
          <div class="card-detail">${t.detailed}</div>
          <button class="dig-deeper" type="button" aria-label="Show detailed definition of ${t.term}">Dig Deeper ↓</button>
        </div>
      `).join('');

      // Attach event listeners for expand/collapse
      grid.querySelectorAll('.glossary-card').forEach(card => {
        const toggleExpand = () => {
          card.classList.toggle('expanded');
          const isExpanded = card.classList.contains('expanded');
          card.setAttribute('aria-expanded', isExpanded ? 'true' : 'false');
        };
        card.addEventListener('click', toggleExpand);
        card.addEventListener('keydown', (e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            toggleExpand();
          }
        });
      });
    } catch (e) { /* skip glossary on error */ }
  },

  openPanel(milestoneId) {
    const m = this.data.milestones.find(x => x.id === milestoneId);
    if (!m) return;

    // Store previous focus for restoration
    this._previousFocus = document.activeElement;

    document.getElementById('panelIcon').textContent = m.icon;
    document.getElementById('panelTitle').textContent = m.label;
    document.getElementById('panelDate').textContent = this.formatDate(m.date);
    document.getElementById('panelDescription').textContent = m.details;

    // Key facts
    const factsEl = document.getElementById('panelFacts');
    factsEl.innerHTML = m.key_facts.map(f => `<li>${f}</li>`).join('');

    // Who's involved
    const whoEl = document.getElementById('panelWho');
    whoEl.innerHTML = m.who_involved.map(w =>
      `<span class="panel-who-tag" role="listitem">${w}</span>`
    ).join('');

    // FAQ — use event listeners instead of inline onclick
    const faqEl = document.getElementById('panelFaq');
    faqEl.innerHTML = m.faq.map((q, i) =>
      `<li tabindex="0" role="button" data-faq-index="${i}" aria-label="Ask ElectIQ: ${q}">${q}</li>`
    ).join('');

    faqEl.querySelectorAll('li[role="button"]').forEach(li => {
      const question = m.faq[parseInt(li.dataset.faqIndex, 10)];
      li.addEventListener('click', () => Chat.askAbout(question));
      li.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          Chat.askAbout(question);
        }
      });
    });

    // Ask button
    const askBtn = document.getElementById('panelAskBtn');
    askBtn.onclick = () => {
      Chat.askAbout(`Tell me more about ${m.label} in the election process`);
      this.closePanel();
    };

    // Open panel with accessibility
    const panel = document.getElementById('timelinePanel');
    panel.classList.add('open');
    panel.setAttribute('aria-hidden', 'false');
    document.getElementById('panelBackdrop').classList.add('visible');
    document.body.style.overflow = 'hidden';

    // Move focus to close button for keyboard users
    requestAnimationFrame(() => {
      document.getElementById('panelClose').focus();
    });

    App.announce(`Opened details for ${m.label}`);
  },

  closePanel() {
    const panel = document.getElementById('timelinePanel');
    panel.classList.remove('open');
    panel.setAttribute('aria-hidden', 'true');
    document.getElementById('panelBackdrop').classList.remove('visible');
    document.body.style.overflow = '';

    // Restore focus to the element that opened the panel
    if (this._previousFocus && this._previousFocus.focus) {
      this._previousFocus.focus();
    }

    App.announce('Detail panel closed');
  },

  /**
   * Format a date string into a human-readable format.
   * @param {string} dateStr - ISO date string
   * @returns {string} Formatted date
   */
  formatDate(dateStr) {
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-IN', {
      day: 'numeric', month: 'short', year: 'numeric'
    });
  }
};
