/**
 * The Fitness Falcon - Global Core Architecture Scripts
 * Unified management for Header Search, Mobile Navigation, Theme Switching, and Shared Interactions.
 */
(function () {
  'use strict';

  function initSite() {
    // ------------------------------------------------------------------------
    // 1. Search Modal & Live Search Interaction
    // ------------------------------------------------------------------------
    const searchModal = document.querySelector('.benqu_header_search') || document.getElementById('headerSearchModal');
    const openBtns = document.querySelectorAll('.pfy-search-btn, #openSearchBtn');
    const closeBtns = document.querySelectorAll('.close-btn, #closeSearchBtn');

    openBtns.forEach(function (btn) {
      btn.addEventListener('click', function (e) {
        e.preventDefault();
        if (searchModal) {
          searchModal.classList.add('active');
          const input = searchModal.querySelector('input[type="search"]');
          if (input) {
            input.focus();
          }
        }
      });
    });

    closeBtns.forEach(function (btn) {
      btn.addEventListener('click', function (e) {
        e.preventDefault();
        if (searchModal) {
          searchModal.classList.remove('active');
        }
      });
    });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && searchModal && searchModal.classList.contains('active')) {
        searchModal.classList.remove('active');
      }
    });

    // Live search filtering across articles
    const searchInputs = document.querySelectorAll('.benqu_header_search input[type="search"], #liveSearchInput, #search');
    searchInputs.forEach(function (input) {
      let resultsBox = document.getElementById('searchResultsDropdown') || document.getElementById('homeSearchResultsDropdown');
      if (!resultsBox && input.parentElement) {
        resultsBox = document.createElement('div');
        resultsBox.id = 'searchResultsDropdown';
        resultsBox.className = 'falcon-search-dropdown';
        resultsBox.style.display = 'none';
        input.parentElement.style.position = 'relative';
        input.parentElement.appendChild(resultsBox);
      }

      input.addEventListener('input', function () {
        const query = this.value.trim().toLowerCase();
        if (!query) {
          if (resultsBox) {
            resultsBox.style.display = 'none';
            resultsBox.innerHTML = '';
          }
          return;
        }

        const posts = window.ALL_POSTS || [];
        const matches = posts.filter(function (p) {
          const title = (p.title || '').toLowerCase();
          const cat = (p.cat || '').toLowerCase();
          return title.indexOf(query) !== -1 || cat.indexOf(query) !== -1;
        }).slice(0, 6);

        if (!resultsBox) return;

        if (matches.length === 0) {
          resultsBox.textContent = 'No articles found matching "' + query + '"';
        } else if (window.FalconSearch && typeof window.FalconSearch.render === 'function') {
          resultsBox.innerHTML = window.FalconSearch.render(matches);
        }
        resultsBox.style.display = 'block';
      });
    });

    // Close results dropdown when clicking outside
    document.addEventListener('click', function (e) {
      const insideSearch = e.target.closest('.benqu_header_search') || e.target.closest('#headerSearchModal');
      if (!insideSearch) {
        const dropdowns = document.querySelectorAll('#searchResultsDropdown, #homeSearchResultsDropdown, .falcon-search-dropdown');
        dropdowns.forEach(function (box) {
          box.style.display = 'none';
        });
      }
    });

    // ------------------------------------------------------------------------
    // 2. Dark/Light Theme Switching
    // ------------------------------------------------------------------------
    const themeToggleBtn = document.getElementById('themeToggleBtn');
    const themeCheckbox = document.querySelector('.benqu-switch-box__input');
    const savedTheme = localStorage.getItem('theme');

    function applyTheme(theme) {
      if (theme === 'dark') {
        document.documentElement.setAttribute('data-theme', 'dark');
        document.body.classList.add('dark-theme');
        if (themeToggleBtn) {
          themeToggleBtn.classList.remove('fa-moon');
          themeToggleBtn.classList.add('fa-sun');
        }
        if (themeCheckbox) {
          themeCheckbox.checked = true;
        }
      } else {
        document.documentElement.setAttribute('data-theme', 'light');
        document.body.classList.remove('dark-theme');
        if (themeToggleBtn) {
          themeToggleBtn.classList.remove('fa-sun');
          themeToggleBtn.classList.add('fa-moon');
        }
        if (themeCheckbox) {
          themeCheckbox.checked = false;
        }
      }
    }

    if (savedTheme) {
      applyTheme(savedTheme);
    }

    if (themeToggleBtn) {
      themeToggleBtn.addEventListener('click', function () {
        const isCurrentlyDark = document.body.classList.contains('dark-theme');
        const newTheme = isCurrentlyDark ? 'light' : 'dark';
        applyTheme(newTheme);
        localStorage.setItem('theme', newTheme);
      });
    }

    if (themeCheckbox) {
      themeCheckbox.addEventListener('change', function () {
        const newTheme = this.checked ? 'dark' : 'light';
        applyTheme(newTheme);
        localStorage.setItem('theme', newTheme);
      });
    }

    // ------------------------------------------------------------------------
    // 3. Mobile Navigation Controls
    // ------------------------------------------------------------------------
    const hamburger = document.querySelector('.hamburger_menu > a');
    const closeMobile = document.querySelector('.close-mobile-menu > a');
    const slideBar = document.querySelector('.slide-bar');
    const bodyOverlay = document.querySelector('.body-overlay');

    if (hamburger && slideBar) {
      hamburger.addEventListener('click', function (e) {
        e.preventDefault();
        slideBar.classList.add('show');
        document.body.classList.add('on-side');
        if (bodyOverlay) bodyOverlay.classList.add('active');
        this.classList.add('active');
      });
    }

    if (closeMobile && slideBar) {
      closeMobile.addEventListener('click', function (e) {
        e.preventDefault();
        slideBar.classList.remove('show');
        document.body.classList.remove('on-side');
        if (bodyOverlay) bodyOverlay.classList.remove('active');
        if (hamburger) hamburger.classList.remove('active');
      });
    }

    if (bodyOverlay && slideBar) {
      bodyOverlay.addEventListener('click', function () {
        slideBar.classList.remove('show');
        document.body.classList.remove('on-side');
        bodyOverlay.classList.remove('active');
        if (hamburger) hamburger.classList.remove('active');
      });
    }

    // ------------------------------------------------------------------------
    // 4. Breaking News Carousel Initialization
    // ------------------------------------------------------------------------
    if (window.jQuery && jQuery.fn.owlCarousel) {
      const ticker = jQuery('.breaking-headline-active');
      if (ticker.length && !ticker.hasClass('owl-loaded')) {
        ticker.owlCarousel({
          items: 1,
          loop: true,
          autoplay: true,
          autoplayTimeout: 3500,
          smartSpeed: 800,
          dots: false,
          nav: false
        });
      }
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initSite);
  } else {
    initSite();
  }
})();
