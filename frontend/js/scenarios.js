/**
 * ElectIQ — Scenarios Module: Decision tree renderer
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
        '<div class="empty-state"><span class="empty-icon">⚠️</span><p class="empty-text">Unable to load scenarios.</p></div>';
    }
  },

  showGrid() {
    const container = document.getElementById('scenarioContent');
    const scenarios = this.data.scenarios;

    let html = `
      <h2 class="section-title">🧩 What If? Scenario Simulator</h2>
      <p class="section-subtitle">Explore common election scenarios and learn what happens step-by-step</p>
      <div class="scenario-grid">
    `;

    scenarios.forEach(s => {
      html += `
        <div class="scenario-card" onclick="Scenarios.openScenario('${s.id}')">
          <span class="scenario-icon">${s.icon}</span>
          <span class="scenario-title">${s.title}</span>
          <span class="scenario-desc">${s.description}</span>
        </div>
      `;
    });

    html += '</div>';
    container.innerHTML = html;
  },

  openScenario(id) {
    const scenario = this.data.scenarios.find(s => s.id === id);
    if (!scenario) return;
    this.renderStep(scenario.tree, scenario.title);
  },

  renderStep(node, title) {
    const container = document.getElementById('scenarioContent');

    let html = `
      <div class="scenario-viewer">
        <button class="btn btn-secondary btn-sm scenario-back-btn" onclick="Scenarios.showGrid()">← Back to Scenarios</button>
        <div class="scenario-step">
    `;

    if (node.result) {
      // Leaf node — show result
      html += `
        <div class="scenario-result">
          <div class="result-text">${node.question ? `<p class="scenario-question">${node.question}</p>` : ''}${node.result}</div>
          ${node.source ? `<div class="result-source">📎 ${node.source}</div>` : ''}
        </div>
        <button class="btn btn-primary btn-sm scenario-ask-btn" onclick="Chat.askAbout('${title.replace(/'/g, "\\'")}')">
          💬 Ask ElectIQ to explain more
        </button>
      `;
    } else {
      // Choice node
      html += `<p class="scenario-question">${node.question}</p>`;
      html += '<div class="scenario-choices">';
      
      node.options.forEach((opt, i) => {
        const nextData = JSON.stringify(opt.next || { result: opt.result, source: opt.source }).replace(/"/g, '&quot;');
        html += `
          <button class="scenario-choice" onclick='Scenarios.renderStep(JSON.parse(this.dataset.next), "${title.replace(/"/g, '&quot;')}")' data-next="${nextData}">
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
