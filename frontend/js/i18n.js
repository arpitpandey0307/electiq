/**
 * ElectIQ — i18n Module (Internationalization)
 *
 * Provides English ↔ Hindi language switching with automatic
 * HTML lang attribute updates for accessibility.
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

      // Update the HTML lang attribute for screen readers
      document.documentElement.setAttribute('lang', lang);
      document.documentElement.setAttribute('dir', 'ltr');
    } catch (e) {
      console.warn('Translation not found, using defaults');
    }
  },

  /**
   * Translate a key using the current language's translations.
   * @param {string} key - Translation key
   * @returns {string} Translated string or the key itself as fallback
   */
  t(key) {
    return this.translations[key] || key;
  },

  async toggle() {
    const newLang = this.currentLang === 'en' ? 'hi' : 'en';
    await this.loadLanguage(newLang);

    // Update toggle button
    const btn = document.getElementById('langToggle');
    if (btn) {
      btn.textContent = newLang === 'en' ? '🇮🇳' : '🇬🇧';
      btn.setAttribute('aria-label',
        newLang === 'en' ? 'Switch to Hindi' : 'Switch to English'
      );
    }

    App.announce(newLang === 'en' ? 'Language changed to English' : 'भाषा हिंदी में बदली गई');
  }
};
