/**
 * Shared Search Results Component Renderer
 * Renders standardized .falcon-search-card and .falcon-empty-state items.
 */
window.FalconSearch = {
  render(posts) {
    if (!posts || posts.length === 0) {
      return this.renderEmpty();
    }
    const unescape = str => String(str ?? '').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&#39;/g, "'");
    const escape = value => unescape(value).replace(/[&<>"']/g, character => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[character]));

    return posts.map(post => {
      const slug = encodeURIComponent(post.slug || '');
      const thumb = encodeURIComponent(post.thumb || '1-1.png');
      const title = escape(post.title || '');
      const cat = escape(post.cat || 'Fitness');
      const date = escape(post.date || '');

      return `<a href="/blogs/${slug}/" class="falcon-search-card" aria-label="${title}">
  <img src="/assets/images/${thumb}" alt="" class="falcon-search-thumb" loading="lazy" width="52" height="52" />
  <div class="falcon-search-content">
    <h4 class="falcon-search-title">${title}</h4>
    <div class="falcon-search-meta">
      <span class="falcon-search-cat">${cat}</span>
      <span class="falcon-search-separator">&bull;</span>
      <span class="falcon-search-date">${date}</span>
    </div>
  </div>
</a>`;
    }).join('');
  },

  renderEmpty(query) {
    const unescape = str => String(str ?? '').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&#39;/g, "'");
    const escape = value => unescape(value).replace(/[&<>"']/g, character => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[character]));
    const text = query ? `We couldn't find any articles matching "<strong>${escape(query)}</strong>".` : 'Try searching for topics like workouts, nutrition, or health.';

    return `<div class="falcon-empty-state falcon-empty-state-search" role="status">
  <div class="falcon-empty-icon"><i class="fal fa-search" aria-hidden="true"></i></div>
  <h4 class="falcon-empty-title">No articles found</h4>
  <p class="falcon-empty-description">${text}</p>
</div>`;
  }
};
