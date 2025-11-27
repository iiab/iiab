// static/js/main.js

// Default language
const DEFAULT_LANG = "en";

// Available languages (adjust if you add more)
const SUPPORTED_LANGS = ["en", "es"];

// Load markdown file for a given language, with fallback to DEFAULT_LANG
async function loadMarkdown(lang) {
  let targetLang = SUPPORTED_LANGS.includes(lang) ? lang : DEFAULT_LANG;
  let path = `static/content/${targetLang}.md`;

  try {
    const res = await fetch(path);
    if (res.ok) {
      return await res.text();
    }
    console.warn(`Markdown not found for '${targetLang}', falling back to default.`);
  } catch (err) {
    console.error(`Error loading markdown for '${targetLang}':`, err);
  }

  // Fallback to default language file
  if (targetLang !== DEFAULT_LANG) {
    try {
      const fallbackRes = await fetch(`static/content/${DEFAULT_LANG}.md`);
      if (fallbackRes.ok) {
        return await fallbackRes.text();
      }
    } catch (fallbackErr) {
      console.error("Error loading fallback markdown:", fallbackErr);
    }
  }

  // Last resort content if everything fails
  return "# Content not available\n\nPlease try again later.";
}

// Render markdown for a given language into #content
async function renderContent(lang) {
  const md = await loadMarkdown(lang);
  const html = marked.parse(md); // 'marked' is provided by marked.min.js
  const contentEl = document.getElementById("content");
  if (contentEl) {
    contentEl.innerHTML = html;
  }

  // Keep the selector in sync with the actual language used
  const select = document.getElementById("lang-switch");
  if (select && SUPPORTED_LANGS.includes(lang)) {
    select.value = lang;
  }
}

// Setup language selector behavior
function setupLangSwitch() {
  const select = document.getElementById("lang-switch");
  if (!select) return;

  select.addEventListener("change", async (ev) => {
    const lang = ev.target.value || DEFAULT_LANG;
    try {
      // Remember language choice
      window.localStorage.setItem("minisite_lang", lang);
    } catch (e) {
      // Ignore storage errors (private mode, etc.)
    }
    await renderContent(lang);
  });
}

// Decide initial language (stored preference > browser > default)
function detectInitialLanguage() {
  let lang = DEFAULT_LANG;

  try {
    const stored = window.localStorage.getItem("minisite_lang");
    if (stored && SUPPORTED_LANGS.includes(stored)) {
      return stored;
    }
  } catch (e) {
    // Ignore
  }

  if (navigator.language) {
    const browserLang = navigator.language.slice(0, 2).toLowerCase();
    if (SUPPORTED_LANGS.includes(browserLang)) {
      lang = browserLang;
    }
  }

  return lang;
}

// Init
document.addEventListener("DOMContentLoaded", async () => {
  setupLangSwitch();
  const initialLang = detectInitialLanguage();
  await renderContent(initialLang);
});
