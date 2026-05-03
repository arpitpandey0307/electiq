/**
 * ElectIQ — Scenarios Module
 *
 * Interactive decision tree renderer for "What If?" election scenarios.
 * Provides keyboard navigation, screen reader support, and proper
 * event handling without inline handlers.
 */

const Scenarios = {
  data: null,
  loaded: false,

  init() {},

  async load() {
    if (this.loaded) return;

    try {
      const res = await fetch('/api/scenarios');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      this.data = await res.json();
      this.loaded = true;
      this.showGrid();
      const container = document.getElementById('scenarioContent');
      if (container) container.removeAttribute('aria-busy');
    } catch (e) {
      const container = document.getElementById('scenarioContent');
      container.removeAttribute('aria-busy');
      container.innerHTML =
        '<div class="empty-state" role="alert"><span class="empty-icon" aria-hidden="true">⚠️</span><p class="empty-text">Unable to load scenarios.</p></div>';
    }
  },

  showGrid() {
    const container = document.getElementById('scenarioContent');
    const scenarios = this.data.scenarios;

    let html = `
      <h2 class="section-title">🧩 What If? Scenario Simulator</h2>
      <p class="section-subtitle">Explore common election scenarios and learn what happens step-by-step</p>
      <div class="scenario-grid" role="list" aria-label="Election scenarios">
    `;

    scenarios.forEach(s => {
      html += `
        <div class="scenario-card" data-scenario-id="${s.id}"
             tabindex="0" role="listitem" aria-label="${s.title}: ${s.description}">
          <span class="scenario-icon" aria-hidden="true">${s.icon}</span>
          <span class="scenario-title">${s.title}</span>
          <span class="scenario-desc">${s.description}</span>
        </div>
      `;
    });

    html += '</div>';
    container.innerHTML = html;

    // Attach event listeners (no inline onclick)
    container.querySelectorAll('.scenario-card').forEach(card => {
      const id = card.dataset.scenarioId;
      card.addEventListener('click', () => this.openScenario(id));
      card.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          this.openScenario(id);
        }
      });
    });

    App.announce(`${scenarios.length} scenarios loaded. Choose one to explore.`);
  },

  openScenario(id) {
    const scenario = this.data.scenarios.find(s => s.id === id);
    if (!scenario) return;
    App.announce(`Opening scenario: ${scenario.title}`);
    this.renderStep(scenario.tree, scenario.title);
  },

  renderStep(node, title) {
    const container = document.getElementById('scenarioContent');

    let html = `
      <div class="scenario-viewer" role="region" aria-label="Scenario: ${title}">
        <button class="btn btn-secondary btn-sm scenario-back-btn" id="scenarioBackBtn" type="button" aria-label="Back to all scenarios">← Back to Scenarios</button>
        <div class="scenario-step">
    `;

    if (node.result) {
      html += `
        <div class="scenario-result" role="alert">
          <div class="result-text">${node.question ? `<p class="scenario-question">${node.question}</p>` : ''}${node.result}</div>
          ${node.source ? `<div class="result-source">📎 ${node.source}</div>` : ''}
        </div>
        <button class="btn btn-primary btn-sm scenario-ask-btn" id="scenarioAskBtn" type="button" aria-label="Ask ElectIQ for more details about ${title}">
          💬 Ask ElectIQ to explain more
        </button>
      `;
      App.announce('Scenario complete. Result displayed.');
    } else {
      html += `<p class="scenario-question" id="scenarioQuestion">${node.question}</p>`;
      html += '<div class="scenario-choices" role="group" aria-labelledby="scenarioQuestion">';

      node.options.forEach((opt, i) => {
        const nextData = JSON.stringify(opt.next || { result: opt.result, source: opt.source }).replace(/"/g, '&quot;');
        html += `
          <button class="scenario-choice" type="button" data-next="${nextData}" data-title="${title.replace(/"/g, '&quot;')}"
                  aria-label="Choice: ${opt.label}">
            ${opt.label}
          </button>
        `;
      });

      html += '</div>';
    }

    html += '</div></div>';
    container.innerHTML = html;

    // Attach event listeners
    document.getElementById('scenarioBackBtn')?.addEventListener('click', () => this.showGrid());
    document.getElementById('scenarioAskBtn')?.addEventListener('click', () => Chat.askAbout(title));

    container.querySelectorAll('.scenario-choice').forEach(btn => {
      btn.addEventListener('click', () => {
        const nextData = JSON.parse(btn.dataset.next);
        const stepTitle = btn.dataset.title;
        this.renderStep(nextData, stepTitle);
      });
    });
  }
};
