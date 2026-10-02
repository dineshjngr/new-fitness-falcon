/**
 * The Fitness Falcon — Search Results Page Logic
 * Reads ?q= from the URL, filters ALL_POSTS, renders paginated results.
 */
(function () {
  'use strict';

  var RESULTS_PER_PAGE = 12;

  // -------------------------------------------------------------------------
  // Helpers
  // -------------------------------------------------------------------------
  function getParam(name) {
    return new URLSearchParams(window.location.search).get(name) || '';
  }

  function escapeHtml(str) {
    return String(str || '').replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  function unescapeHtml(str) {
    return String(str || '')
      .replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>')
      .replace(/&quot;/g, '"').replace(/&#39;/g, "'");
  }

  // -------------------------------------------------------------------------
  // Filter posts by query (title + category match)
  // -------------------------------------------------------------------------
  function filterPosts(query) {
    if (!query) return [];
    var q = query.toLowerCase();
    return (window.ALL_POSTS || []).filter(function (p) {
      return (p.title || '').toLowerCase().indexOf(q) !== -1
          || (p.cat   || '').toLowerCase().indexOf(q) !== -1;
    });
  }

  // -------------------------------------------------------------------------
  // Render one article card
  // -------------------------------------------------------------------------
  function renderCard(post) {
    var slug  = post.slug  || '';
    var thumb = post.thumb || '1-1.png';
    var title = escapeHtml(unescapeHtml(post.title || ''));
    var cat   = escapeHtml(unescapeHtml(post.cat   || 'Fitness'));
    var date  = escapeHtml(post.date  || '');

    return '<a href="/blogs/' + slug + '/" class="falcon-result-card" aria-label="' + title + '">'
      + '<img src="/assets/images/' + encodeURIComponent(thumb) + '" alt="" class="falcon-result-card__thumb" loading="lazy" width="400" height="225">'
      + '<div class="falcon-result-card__body">'
      +   '<span class="falcon-result-card__cat">' + cat + '</span>'
      +   '<h2 class="falcon-result-card__title">' + title + '</h2>'
      +   '<span class="falcon-result-card__date">' + date + '</span>'
      + '</div>'
      + '</a>';
  }

  // -------------------------------------------------------------------------
  // Render grid of cards
  // -------------------------------------------------------------------------
  function renderGrid(posts) {
    return '<div class="falcon-results-grid">' + posts.map(renderCard).join('') + '</div>';
  }

  // -------------------------------------------------------------------------
  // Render empty state
  // -------------------------------------------------------------------------
  function renderEmpty(query) {
    var suggestions = [
      { label: 'Fitness', href: '/category/fitness/' },
      { label: 'Nutrition', href: '/category/nutrition/' },
      { label: 'Health', href: '/category/health/' },
      { label: 'Yoga', href: '/category/yoga/' },
      { label: 'Recipes', href: '/category/recipes/' },
      { label: 'Weight', href: '/category/weight/' },
    ];
    var text = query
      ? 'We couldn\'t find any articles matching &ldquo;<strong>' + escapeHtml(query) + '</strong>&rdquo;.'
      : 'Enter a search term above to explore our 155+ articles.';

    return '<div class="falcon-search-empty" role="status" aria-live="polite">'
      + '<i class="fal fa-search falcon-search-empty__icon" aria-hidden="true"></i>'
      + '<h2 class="falcon-search-empty__title">No articles found</h2>'
      + '<p class="falcon-search-empty__desc">' + text + '</p>'
      + (query ? '<div class="falcon-search-empty__suggestions">'
        + '<h3>Browse by topic</h3>'
        + '<div class="falcon-search-empty__tags">'
        + suggestions.map(function (s) {
            return '<a class="falcon-search-empty__tag" href="' + s.href + '">' + s.label + '</a>';
          }).join('')
        + '</div>'
        + '</div>' : '')
      + '</div>';
  }

  // -------------------------------------------------------------------------
  // Render pagination controls
  // -------------------------------------------------------------------------
  function renderPagination(totalPages, currentPage, query) {
    if (totalPages <= 1) return '';

    var html = '<nav class="falcon-search-pagination" aria-label="Search results pagination">';

    // Prev button
    html += '<button class="falcon-search-pagination__btn" id="srPagePrev" aria-label="Previous page"'
          + (currentPage <= 1 ? ' aria-disabled="true" disabled' : '') + '>'
          + '<i class="fal fa-angle-left" aria-hidden="true"></i></button>';

    // Page number buttons (show max 5 around current)
    var start = Math.max(1, currentPage - 2);
    var end   = Math.min(totalPages, start + 4);
    start     = Math.max(1, end - 4);

    if (start > 1) {
      html += '<button class="falcon-search-pagination__btn" data-page="1">1</button>';
      if (start > 2) html += '<span class="falcon-search-pagination__btn" style="border:none;background:none;pointer-events:none;min-width:24px">…</span>';
    }

    for (var i = start; i <= end; i++) {
      html += '<button class="falcon-search-pagination__btn' + (i === currentPage ? ' active' : '') + '" data-page="' + i + '" '
            + (i === currentPage ? 'aria-current="page" aria-disabled="true"' : '') + '>' + i + '</button>';
    }

    if (end < totalPages) {
      if (end < totalPages - 1) html += '<span class="falcon-search-pagination__btn" style="border:none;background:none;pointer-events:none;min-width:24px">…</span>';
      html += '<button class="falcon-search-pagination__btn" data-page="' + totalPages + '">' + totalPages + '</button>';
    }

    // Next button
    html += '<button class="falcon-search-pagination__btn" id="srPageNext" aria-label="Next page"'
          + (currentPage >= totalPages ? ' aria-disabled="true" disabled' : '') + '>'
          + '<i class="fal fa-angle-right" aria-hidden="true"></i></button>';

    html += '</nav>';
    return html;
  }

  // -------------------------------------------------------------------------
  // Main render function
  // -------------------------------------------------------------------------
  function renderResults(query, page) {
    var matches = filterPosts(query);
    var total   = matches.length;
    var totalPages = Math.ceil(total / RESULTS_PER_PAGE);
    page = Math.max(1, Math.min(page, totalPages || 1));

    var pageMatches = matches.slice((page - 1) * RESULTS_PER_PAGE, page * RESULTS_PER_PAGE);

    // Update hero title
    var titleEl = document.getElementById('srTitle');
    if (titleEl) {
      titleEl.innerHTML = query
        ? 'Results for &ldquo;<em>' + escapeHtml(query) + '</em>&rdquo;'
        : 'Search articles';
    }

    // Update count
    var countEl = document.getElementById('srCount');
    if (countEl) {
      if (query && total > 0) {
        countEl.textContent = total + ' article' + (total === 1 ? '' : 's') + ' found';
      } else if (query) {
        countEl.textContent = '';
      } else {
        countEl.textContent = '155 articles available — search to explore';
      }
    }

    // Update document title
    document.title = query
      ? 'Search: ' + query + ' — The Fitness Falcon'
      : 'Search — The Fitness Falcon';

    // Render content
    var container = document.getElementById('srResults');
    if (!container) return;

    if (!query || total === 0) {
      container.innerHTML = renderEmpty(query);
    } else {
      container.innerHTML = renderGrid(pageMatches) + renderPagination(totalPages, page, query);
      // Bind pagination
      container.querySelectorAll('.falcon-search-pagination__btn[data-page]').forEach(function (btn) {
        btn.addEventListener('click', function () {
          var p = parseInt(this.getAttribute('data-page'), 10);
          if (!isNaN(p)) {
            updateUrl(query, p);
            renderResults(query, p);
            window.scrollTo({ top: 0, behavior: 'smooth' });
          }
        });
      });
      var prevBtn = document.getElementById('srPagePrev');
      var nextBtn = document.getElementById('srPageNext');
      if (prevBtn && page > 1) {
        prevBtn.addEventListener('click', function () {
          updateUrl(query, page - 1);
          renderResults(query, page - 1);
          window.scrollTo({ top: 0, behavior: 'smooth' });
        });
      }
      if (nextBtn && page < totalPages) {
        nextBtn.addEventListener('click', function () {
          updateUrl(query, page + 1);
          renderResults(query, page + 1);
          window.scrollTo({ top: 0, behavior: 'smooth' });
        });
      }
    }
  }

  // -------------------------------------------------------------------------
  // Update URL without reload (for pagination)
  // -------------------------------------------------------------------------
  function updateUrl(query, page) {
    var params = new URLSearchParams();
    if (query) params.set('q', query);
    if (page > 1) params.set('page', page);
    var newUrl = '/search/?' + params.toString();
    history.pushState({ query: query, page: page }, '', newUrl);
  }

  // -------------------------------------------------------------------------
  // Search bar form handler on the search results page
  // -------------------------------------------------------------------------
  function initSearchBar() {
    var form  = document.getElementById('srForm');
    var input = document.getElementById('srInput');
    if (!form || !input) return;

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var q = input.value.trim();
      updateUrl(q, 1);
      renderResults(q, 1);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  // -------------------------------------------------------------------------
  // Back/forward navigation support
  // -------------------------------------------------------------------------
  window.addEventListener('popstate', function (e) {
    var state = e.state || {};
    var q = state.query || getParam('q');
    var p = parseInt(state.page || getParam('page') || '1', 10);
    var input = document.getElementById('srInput');
    if (input) input.value = q;
    renderResults(q, p);
  });

  // -------------------------------------------------------------------------
  // Boot
  // -------------------------------------------------------------------------
  function init() {
    var q    = getParam('q');
    var page = parseInt(getParam('page') || '1', 10);

    // Pre-fill the search input
    var input = document.getElementById('srInput');
    if (input && q) input.value = q;

    // Render initial results
    renderResults(q, page);

    // Bind search bar
    initSearchBar();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

}());
