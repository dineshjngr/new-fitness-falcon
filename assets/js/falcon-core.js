/**
 * The Fitness Falcon - Global Core Architecture Scripts
 * Unified management for Header Search, Mobile Navigation, Theme Switching, Sticky Header, Active States, and Shared Interactions.
 */
(function () {
  'use strict';

  function initSite() {
    // ------------------------------------------------------------------------
    // 1. Search Modal & Live Search Interaction (Desktop & Mobile)
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
      // Keyboard support (Enter / Space)
      btn.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          this.click();
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
      btn.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          this.click();
        }
      });
    });

    // Live search filtering across articles for desktop and mobile search inputs
    const searchInputs = document.querySelectorAll('.benqu_header_search input[type="search"], #liveSearchInput, #search, #search-mobile');
    searchInputs.forEach(function (input) {
      let resultsBox = null;
      if (input.id === 'search-mobile') {
        resultsBox = document.getElementById('mobileSearchResultsDropdown');
      } else {
        resultsBox = document.getElementById('searchResultsDropdown') || document.getElementById('homeSearchResultsDropdown');
      }

      if (!resultsBox && input.parentElement) {
        resultsBox = document.createElement('div');
        resultsBox.id = (input.id || 'search') + '-results-dropdown';
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
          if (window.FalconSearch && typeof window.FalconSearch.renderEmpty === 'function') {
            resultsBox.innerHTML = window.FalconSearch.renderEmpty(query);
          } else {
            resultsBox.innerHTML = '<div style="padding:14px;color:#64748b;font-size:14px;text-align:center;">No articles found matching "<strong>' + escapeHtml(query) + '</strong>"</div>';
          }
        } else if (window.FalconSearch && typeof window.FalconSearch.render === 'function') {
          resultsBox.innerHTML = window.FalconSearch.render(matches);
        }
        resultsBox.style.display = 'block';
      });

      // Pressing Enter in a header search input navigates to full search results page
      input.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') {
          var q = this.value.trim();
          if (q) {
            e.preventDefault();
            window.location.href = '/search/?q=' + encodeURIComponent(q);
          }
        }
      });
    });

    function escapeHtml(str) {
      return String(str || '').replace(/[&<>"']/g, function (m) {
        return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m];
      });
    }

    // Close results dropdown when clicking outside
    document.addEventListener('click', function (e) {
      const insideSearch = e.target.closest('.benqu_header_search, #headerSearchModal, .header-mobile-search');
      if (!insideSearch) {
        const dropdowns = document.querySelectorAll('#searchResultsDropdown, #homeSearchResultsDropdown, #mobileSearchResultsDropdown, .falcon-search-dropdown');
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

    function getStoredTheme() {
      try {
        return localStorage.getItem('theme');
      } catch (e) {
        return null;
      }
    }

    function setStoredTheme(val) {
      try {
        localStorage.setItem('theme', val);
      } catch (e) {
        /* storage disabled or restricted */
      }
    }

    const savedTheme = getStoredTheme();

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

    function toggleTheme() {
      const isCurrentlyDark = document.body.classList.contains('dark-theme');
      const newTheme = isCurrentlyDark ? 'light' : 'dark';
      applyTheme(newTheme);
      setStoredTheme(newTheme);
    }

    if (themeToggleBtn) {
      themeToggleBtn.addEventListener('click', toggleTheme);
      themeToggleBtn.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          toggleTheme();
        }
      });
    }

    if (themeCheckbox) {
      themeCheckbox.addEventListener('change', function () {
        const newTheme = this.checked ? 'dark' : 'light';
        applyTheme(newTheme);
        setStoredTheme(newTheme);
      });
    }

    // ------------------------------------------------------------------------
    // 3. Mobile Navigation Drawer & Accordions
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

    function closeMobileMenu() {
      if (slideBar) slideBar.classList.remove('show');
      document.body.classList.remove('on-side');
      if (bodyOverlay) bodyOverlay.classList.remove('active');
      if (hamburger) hamburger.classList.remove('active');
    }

    if (closeMobile) {
      closeMobile.addEventListener('click', function (e) {
        e.preventDefault();
        closeMobileMenu();
      });
    }

    if (bodyOverlay) {
      bodyOverlay.addEventListener('click', function () {
        closeMobileMenu();
      });
    }

    // Mobile submenu accordion toggles
    const mobileDropdownToggles = document.querySelectorAll('.side-mobile-menu .dropdown-toggle-btn');
    mobileDropdownToggles.forEach(function (btn) {
      btn.addEventListener('click', function (e) {
        e.preventDefault();
        e.stopPropagation();
        const parentLi = this.closest('.menu-item-has-children');
        if (parentLi) {
          const isOpen = parentLi.classList.toggle('open');
          this.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
        }
      });
    });

    // ------------------------------------------------------------------------
    // 5. Global Escape Key Handler for All Modals & Drawers
    // ------------------------------------------------------------------------
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') {
        if (searchModal && searchModal.classList.contains('active')) {
          searchModal.classList.remove('active');
        }
        if (slideBar && slideBar.classList.contains('show')) {
          closeMobileMenu();
        }
      }
    });

    // ------------------------------------------------------------------------
    // 6. Sticky Header Scroll Behavior
    // ------------------------------------------------------------------------
    const stickyHeader = document.getElementById('stickyHeader');
    if (stickyHeader) {
      let isTicking = false;
      window.addEventListener('scroll', function () {
        if (!isTicking) {
          window.requestAnimationFrame(function () {
            if (window.scrollY > 200) {
              stickyHeader.classList.add('stickyHeader');
            } else {
              stickyHeader.classList.remove('stickyHeader');
            }
            isTicking = false;
          });
          isTicking = true;
        }
      }, { passive: true });
    }

    // ------------------------------------------------------------------------
    // 7. Active Navigation State Detection
    // ------------------------------------------------------------------------
    const currentPath = window.location.pathname.replace(/\/index\.html$/, '/');
    const navLinks = document.querySelectorAll('.mainmenu a, .side-mobile-menu a');

    navLinks.forEach(function (link) {
      const href = link.getAttribute('href');
      if (!href || href === '#' || href.startsWith('javascript:')) return;
      const cleanHref = href.split('?')[0].split('#')[0].replace(/\/index\.html$/, '/');

      let isMatch = false;
      if (cleanHref === '/' && currentPath === '/') {
        isMatch = true;
      } else if (cleanHref !== '/' && (currentPath === cleanHref || (cleanHref.length > 1 && currentPath.startsWith(cleanHref)))) {
        isMatch = true;
      }

      if (isMatch) {
        link.classList.add('active');
        const parentLi = link.closest('li');
        if (parentLi) {
          parentLi.classList.add('active', 'current-menu-item');

          // Highlight and expand ancestor menus
          let ancestor = parentLi.parentElement ? parentLi.parentElement.closest('li.menu-item-has-children') : null;
          while (ancestor) {
            ancestor.classList.add('active', 'current-menu-ancestor', 'open');
            const toggle = ancestor.querySelector(':scope > .dropdown-toggle-btn');
            if (toggle) toggle.setAttribute('aria-expanded', 'true');
            ancestor = ancestor.parentElement ? ancestor.parentElement.closest('li.menu-item-has-children') : null;
          }
        }
      }
    });

    // ------------------------------------------------------------------------
    // 8. Breaking News: one headline, independent of carousel styles/plugins.
    // ------------------------------------------------------------------------
    const headlines = document.querySelector('.falcon-breaking-headlines');
    if (headlines) {
      const stories = Array.from(headlines.children);
      let current = 0;
      stories.forEach(function (story, index) {
        story.hidden = index !== 0;
        story.classList.toggle('is-active', index === 0);
      });
      let paused = false;
      headlines.addEventListener('mouseenter', function () { paused = true; });
      headlines.addEventListener('mouseleave', function () { paused = false; });
      if (stories.length > 1 && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        window.setInterval(function () {
          if (paused || document.hidden || headlines.contains(document.activeElement)) return;
          stories[current].hidden = true;
          stories[current].classList.remove('is-active');
          current = (current + 1) % stories.length;
          stories[current].hidden = false;
          stories[current].classList.add('is-active');
        }, 4500);
      }
    }

    // ------------------------------------------------------------------------
    // 9. Single Blog Post Interactions
    // ------------------------------------------------------------------------
    const progressBar = document.getElementById('falconReadingProgress');
    const articleBox = document.querySelector('.falcon-article-box');
    if (progressBar && articleBox) {
      window.addEventListener('scroll', function () {
        const articleRect = articleBox.getBoundingClientRect();
        const articleTop = window.scrollY + articleRect.top;
        const articleHeight = articleRect.height;
        const windowHeight = window.innerHeight;
        const scrollPosition = window.scrollY;

        if (scrollPosition < articleTop) {
          progressBar.style.width = '0%';
        } else if (scrollPosition > articleTop + articleHeight - windowHeight) {
          progressBar.style.width = '100%';
        } else {
          const progress = ((scrollPosition - articleTop) / (articleHeight - windowHeight)) * 100;
          progressBar.style.width = Math.min(100, Math.max(0, progress)) + '%';
        }
      }, { passive: true });
    }

    const tocToggle = document.getElementById('falconTocToggle');
    const tocList = document.getElementById('falconTocList');
    if (tocToggle && tocList) {
      tocToggle.addEventListener('click', function () {
        const isHidden = tocList.style.display === 'none';
        tocList.style.display = isHidden ? 'block' : 'none';
        tocToggle.textContent = isHidden ? 'Hide' : 'Show';
        tocToggle.setAttribute('aria-expanded', isHidden ? 'true' : 'false');
      });
    }

    const copyLinkBtn = document.getElementById('falconCopyLinkBtn');
    const copyTooltip = document.getElementById('falconCopyTooltip');
    if (copyLinkBtn) {
      copyLinkBtn.addEventListener('click', function (e) {
        e.preventDefault();
        const urlToCopy = this.getAttribute('data-url') || window.location.href;
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(urlToCopy).then(showTooltip);
        } else {
          const tempInput = document.createElement('input');
          tempInput.value = urlToCopy;
          document.body.appendChild(tempInput);
          tempInput.select();
          document.execCommand('copy');
          document.body.removeChild(tempInput);
          showTooltip();
        }

        function showTooltip() {
          if (copyTooltip) {
            copyTooltip.classList.add('show');
            setTimeout(function () {
              copyTooltip.classList.remove('show');
            }, 2200);
          }
        }
      });
    }

    const entryTables = document.querySelectorAll('.entry-content table');
    entryTables.forEach(function (tbl) {
      if (!tbl.parentElement.classList.contains('falcon-table-wrapper')) {
        const wrap = document.createElement('div');
        wrap.className = 'falcon-table-wrapper';
        tbl.parentNode.insertBefore(wrap, tbl);
        wrap.appendChild(tbl);
      }
    });

    const entryIframes = document.querySelectorAll('.entry-content iframe');
    entryIframes.forEach(function (iframe) {
      const src = iframe.getAttribute('src') || '';
      if ((src.indexOf('youtube.com') !== -1 || src.indexOf('youtu.be') !== -1 || src.indexOf('vimeo.com') !== -1) &&
          !iframe.parentElement.classList.contains('falcon-video-wrapper')) {
        const wrap = document.createElement('div');
        wrap.className = 'falcon-video-wrapper';
        iframe.parentNode.insertBefore(wrap, iframe);
        wrap.appendChild(iframe);
      }
    });

    // ------------------------------------------------------------------------
    // FAQ Accordion Interaction
    // ------------------------------------------------------------------------
    const faqButtons = document.querySelectorAll('.falcon-faq-question');
    faqButtons.forEach(function (btn) {
      btn.addEventListener('click', function () {
        const isExpanded = btn.getAttribute('aria-expanded') === 'true';
        btn.setAttribute('aria-expanded', isExpanded ? 'false' : 'true');
        btn.classList.toggle('active', !isExpanded);
        const answer = btn.nextElementSibling;
        if (answer && answer.classList.contains('falcon-faq-answer')) {
          answer.style.display = isExpanded ? 'none' : 'block';
        }
      });
    });

    // ------------------------------------------------------------------------
    // In-Page Archive Live Filter
    // ------------------------------------------------------------------------
    const archiveFilter = document.getElementById('archiveFilterInput');
    if (archiveFilter) {
      archiveFilter.addEventListener('input', function () {
        const query = this.value.trim().toLowerCase();
        const grid = document.getElementById('archiveArticlesGrid');
        if (!grid) return;
        const cards = grid.querySelectorAll('.post-card');
        let visibleCount = 0;
        cards.forEach(function (card) {
          const col = card.closest('[class*="col-"]');
          const title = (card.querySelector('.post-card-title') || {}).textContent || '';
          const excerpt = (card.querySelector('.post-card-excerpt') || {}).textContent || '';
          const cat = (card.querySelector('.category-badge') || {}).textContent || '';
          const text = (title + ' ' + excerpt + ' ' + cat).toLowerCase();
          const match = !query || text.indexOf(query) !== -1;
          if (col) {
            col.style.display = match ? '' : 'none';
          }
          if (match) visibleCount++;
        });

        const countEl = document.querySelector('.falcon-filter-count span');
        if (countEl) {
          countEl.textContent = String(visibleCount);
        }

        let emptyMsg = grid.querySelector('.falcon-archive-empty-filter');
        if (visibleCount === 0) {
          if (!emptyMsg) {
            emptyMsg = document.createElement('div');
            emptyMsg.className = 'col-12 falcon-archive-empty-filter';
            emptyMsg.innerHTML = '<div class="falcon-empty-state"><div class="falcon-empty-icon"><i class="fal fa-search"></i></div><h3 class="falcon-empty-title">No matching articles</h3><p class="falcon-empty-description">Try a different keyword or clear your filter.</p></div>';
            grid.appendChild(emptyMsg);
          }
          emptyMsg.style.display = 'block';
        } else if (emptyMsg) {
          emptyMsg.style.display = 'none';
        }
      });
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initSite);
  } else {
    initSite();
  }
})();
