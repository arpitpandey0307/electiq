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
  },

  async load() {
    if (this.loaded) return;

    try {
      const res = await fetch('/api/timeline');
      this.data = await res.json();
      this.render();
      this.loaded = true;
    } catch (e) {
      document.getElementById('timelineContent').innerHTML =
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

    milestones.forEach((m, i) => {
      html += `
        <div class="timeline-node ${m.status}" onclick="Timeline.openPanel('${m.id}')"
             role="listitem" tabindex="0" aria-label="${m.label} — ${m.status}"
             onkeydown="if(event.key==='Enter')Timeline.openPanel('${m.id}')">
          <div class="timeline-dot" aria-hidden="true">${m.icon}</div>
          <span class="timeline-label">${m.label}</span>
          <span class="timeline-date">${this.formatDate(m.date)}</span>
        </div>
      `;
    });

    html += `</div></div>`;

    // Glossary section
    html += `
      <h2 class="section-title" style="margin-top:32px">📊 Key Election Terms</h2>
      <p class="section-subtitle">Click a term to expand its definition</p>
      <div class="glossary-grid" id="glossaryGrid" role="list"></div>
    `;

    container.innerHTML = html;
    this.loadGlossary();
  },

  async loadGlossary() {
    try {
      const res = await fetch('/api/glossary');
      const data = await res.json();
      const grid = document.getElementById('glossaryGrid');

      grid.innerHTML = data.terms.map(t => `
        <div class="glossary-card" onclick="this.classList.toggle('expanded')"
             role="listitem" tabindex="0" aria-expanded="false"
             onkeydown="if(event.key==='Enter'){this.classList.toggle('expanded');this.setAttribute('aria-expanded',this.classList.contains('expanded'))}">
          <div class="card-header">
            <span class="card-icon" aria-hidden="true">${t.icon}</span>
            <span class="card-term">${t.term}</span>
          </div>
          <p class="card-short">${t.short}</p>
          <div class="card-detail">${t.detailed}</div>
          <button class="dig-deeper" aria-label="Show detailed definition of ${t.term}">Dig Deeper ↓</button>
        </div>
      `).join('');
    } catch (e) { /* skip glossary on error */ }
  },

  openPanel(milestoneId) {
    const m = this.data.milestones.find(x => x.id === milestoneId);
    if (!m) return;

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

    // FAQ
    const faqEl = document.getElementById('panelFaq');
    faqEl.innerHTML = m.faq.map(q =>
      `<li onclick="Chat.askAbout('${q.replace(/'/g, "\\'")}')"
           tabindex="0" role="button"
           onkeydown="if(event.key==='Enter')Chat.askAbout('${q.replace(/'/g, "\\'")}')">${q}</li>`
    ).join('');

    // Ask button
    document.getElementById('panelAskBtn').onclick = () => {
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
    document.getElementById('panelClose').focus();

    App.announce(`Opened details for ${m.label}`);
  },

  closePanel() {
    const panel = document.getElementById('timelinePanel');
    panel.classList.remove('open');
    panel.setAttribute('aria-hidden', 'true');
    document.getElementById('panelBackdrop').classList.remove('visible');
    document.body.style.overflow = '';

    App.announce('Detail panel closed');
  },

  formatDate(dateStr) {
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-IN', {
      day: 'numeric', month: 'short', year: 'numeric'
    });
  }
};
