/**
 * ElectIQ — Scenarios Module
 *
 * Interactive decision tree renderer for "What If?" election scenarios.
 * Provides keyboard navigation and screen reader support.
 */

const Scenarios = {
  data: null,
  loaded: false,

  init() {},

  async load() {
    if (this.loaded) return;

    try {
      const res = await fetch('/api/scenarios');
      this.data = await res.json();
      this.loaded = true;
      this.showGrid();
    } catch (e) {
      document.getElementById('scenarioContent').innerHTML =
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
        <div class="scenario-card" onclick="Scenarios.openScenario('${s.id}')"
             tabindex="0" role="listitem" aria-label="${s.title}: ${s.description}"
             onkeydown="if(event.key==='Enter')Scenarios.openScenario('${s.id}')">
          <span class="scenario-icon" aria-hidden="true">${s.icon}</span>
          <span class="scenario-title">${s.title}</span>
          <span class="scenario-desc">${s.description}</span>
        </div>
      `;
    });

    html += '</div>';
    container.innerHTML = html;
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
        <button class="btn btn-secondary btn-sm scenario-back-btn" onclick="Scenarios.showGrid()" aria-label="Back to all scenarios">← Back to Scenarios</button>
        <div class="scenario-step">
    `;

    if (node.result) {
      html += `
        <div class="scenario-result" role="alert">
          <div class="result-text">${node.question ? `<p class="scenario-question">${node.question}</p>` : ''}${node.result}</div>
          ${node.source ? `<div class="result-source">📎 ${node.source}</div>` : ''}
        </div>
        <button class="btn btn-primary btn-sm scenario-ask-btn" onclick="Chat.askAbout('${title.replace(/'/g, "\\'")}')" aria-label="Ask ElectIQ for more details about ${title}">
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
          <button class="scenario-choice" onclick='Scenarios.renderStep(JSON.parse(this.dataset.next), "${title.replace(/"/g, '&quot;')}")' data-next="${nextData}"
                  aria-label="Choice: ${opt.label}">
            ${opt.label}
          </button>
        `;
      });

      html += '</div>';
    }

    html += '</div></div>';
    container.innerHTML = html;
  }
};
