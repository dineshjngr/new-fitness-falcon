// PurgeCSS config for vendor stylesheets. Originals live in old-website/css-full/.
// Run: npx purgecss@6.0.0 --config scripts/purge.config.cjs --output assets/css/
module.exports = {
  css: [
    // Font Awesome is split by scripts/purge_css.py: icon rules are purged,
    // the @font-face blocks (malformed upstream, browsers recover) are kept verbatim.
    process.env.FA_A || 'old-website/css-full/fa-icons.css',
    process.env.FA_D || 'old-website/css-full/fa-duotone.css',
    'old-website/css-full/bootstrap.min.css',
    'old-website/css-full/benqu-style.css',
    'old-website/css-full/responsive.css',
  ],
  content: [
    '*.html',
    'blogs/**/*.html', 'category/**/*.html', 'tag/**/*.html', 'author/**/*.html',
    'pages/**/*.html', 'search/**/*.html',
    'components/*.html',
    'assets/js/*.js',
    'scripts/*.py',
  ],
  // Keep @font-face and keyframes; classes toggled by JavaScript at runtime.
  fontFace: false,
  keyframes: false,
  variables: false,
  safelist: {
    standard: ['html', 'body', ':root', 'show', 'active', 'open', 'opened', 'collapse', 'collapsing',
      'collapsed', 'fade', 'sticky', 'is-sticky', 'header-sticky', 'fixed', 'disabled', 'hidden',
      'mean-expand', 'menu-open', 'is-copied', 'is-active', 'is-open', 'loaded', 'visible'],
    deep: [/^data-theme/],
    greedy: [/data-theme/, /dropdown/, /mobile-menu/, /side-mobile/, /offcanvas/, /metismenu/,
      /mm-/, /search/, /sticky/, /modal/, /tooltip/, /^fa-(sun|moon|times|bars|search|chevron|angle|arrow|check|link)/,
      /aria-expanded/, /aria-current/],
  },
};
