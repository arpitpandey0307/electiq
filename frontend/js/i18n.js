/**
 * ElectIQ — i18n Module (Language Switching)
 */

const I18n = {
  currentLang: 'en',
  translations: {},

  async init() {
    this.currentLang = App.state.lang;
    await this.loadLanguage(this.currentLang);
  },

  async loadLanguage(lang) {
    try {
      const res = await fetch(`/assets/translations/${lang}.json`);
      this.translations = await res.json();
      this.currentLang = lang;
      App.state.lang = lang;
      localStorage.setItem('electiq_lang', lang);
    } catch (e) {
      console.log('Translation not found, using defaults');
    }
  },

  t(key) {
    return this.translations[key] || key;
  },

  async toggle() {
    const newLang = this.currentLang === 'en' ? 'hi' : 'en';
    await this.loadLanguage(newLang);
    // Update lang toggle button
    const btn = document.getElementById('langToggle');
    if (btn) btn.textContent = newLang === 'en' ? '🇮🇳' : '🇬🇧';
  }
};
