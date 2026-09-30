/* Render search cards safely with the current grouped article routes. */
window.FalconSearch = {
  render(posts) {
    const escape = value => String(value ?? '').replace(/[&<>"']/g, character => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[character]));
    return posts.map(post => `<a href="/blogs/${encodeURIComponent(post.slug)}/" style="display:flex;gap:12px;align-items:center;padding:10px;border-bottom:1px solid #f1f5f9;text-decoration:none;color:inherit"><img src="/assets/images/${encodeURIComponent(post.thumb)}" alt="" width="50" height="50" style="width:50px;height:50px;border-radius:6px;object-fit:cover;flex-shrink:0"><div><div style="font-weight:700;font-size:14px;line-height:1.3;color:#0f172a">${escape(post.title)}</div><span style="font-size:12px;color:#5541f8;font-weight:600">${escape(post.cat)} &bull; ${escape(post.date)}</span></div></a>`).join('');
  }
};
