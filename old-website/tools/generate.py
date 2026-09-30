import xml.etree.ElementTree as ET
import os, re, datetime, html, json

XML_PATH = '/Users/dj/Desktop/vscode/thefitnessfalcon/old-website/thefitnessfalcon.WordPress.2026-09-30 (10).xml'
tree = ET.parse(XML_PATH)
root = tree.getroot()
channel = root.find('channel')
ns = {
    'content': 'http://purl.org/rss/1.0/modules/content/',
    'wp': 'http://wordpress.org/export/1.2/',
    'dc': 'http://purl.org/dc/elements/1.1/'
}

# 1. Attachments map
attachments = {}
for item in channel.findall('item'):
    if item.find('wp:post_type', ns).text == 'attachment':
        pid = item.find('wp:post_id', ns).text
        url_el = item.find('wp:attachment_url', ns)
        if url_el is not None and url_el.text:
            fname = os.path.basename(url_el.text.split('?')[0])
            attachments[pid] = fname

# Author mapping
author_names = {
    'dinesh': 'Dinesh',
    'seo': 'Alex',
    'author': 'Riya Verma',
    'admin': 'The Fitness Falcon Team'
}

# Categories slug map
cat_slug_map = {
    'Beauty': 'beauty',
    'Blog': 'blog',
    'Cycling': 'cycling',
    'Fitness': 'fitness',
    'Food & Recipes': 'food-and-recipes',
    'Food &amp; Recipes': 'food-and-recipes',
    'Wearables &amp; Fitness Technology': 'wearables-fitness-technology',
    'Gym': 'gym',
    'Health': 'health',
    'Lifestyle': 'lifestyle',
    'Nutrition': 'nutrition',
    'Recipes': 'recipes',
    'Skincare': 'skincare',
    'Sports': 'sports',
    'Swimming': 'swimming',
    'Trekking': 'trekking',
    'Wearables & Fitness Technology': 'wearables-fitness-technology',
    'Weight': 'weight',
    'Workout': 'workout',
    'Yoga': 'yoga',
    'News': 'news',
    'The Fitness Falcon': 'the-fitness-falcon'
}

def format_date(d_str):
    try:
        dt = datetime.datetime.strptime(d_str.split()[0], '%Y-%m-%d')
        return dt.strftime('%B %d, %Y')
    except Exception:
        return d_str

# 2. Extract published posts
posts = []
for item in channel.findall('item'):
    pt = item.find('wp:post_type', ns).text
    status = item.find('wp:status', ns).text
    if pt == 'post' and status == 'publish':
        title = item.find('title').text or ''
        slug = item.find('wp:post_name', ns).text or ''
        date_raw = item.find('wp:post_date', ns).text or ''
        date_formatted = format_date(date_raw)
        author_raw = (item.find('dc:creator', ns).text or 'dinesh').lower()
        author = author_names.get(author_raw, 'Dinesh')
        content = item.find('content:encoded', ns).text or ''
        cats = [c.text for c in item.findall('category') if c.attrib.get('domain') == 'category']
        tags = [c.text for c in item.findall('category') if c.attrib.get('domain') == 'post_tag']
        metas = {m.find('wp:meta_key', ns).text: m.find('wp:meta_value', ns).text for m in item.findall('wp:postmeta', ns)}
        thumb_id = metas.get('_thumbnail_id')
        thumb_file = attachments.get(thumb_id, '1-1.png')
        if not os.path.exists(os.path.join('assets/images', thumb_file)):
            thumb_file = '1-1.png'
        
        words = len(re.findall(r'\w+', re.sub(r'<[^>]+>', '', content)))
        read_time = max(1, round(words / 200))
        
        clean_text = re.sub(r'<[^>]+>', ' ', content).strip()
        clean_text = ' '.join(clean_text.split())
        excerpt = clean_text[:160] + '...' if len(clean_text) > 160 else clean_text
        
        posts.append({
            'title': title,
            'slug': slug,
            'date_raw': date_raw,
            'date': date_formatted,
            'author': author,
            'content': content,
            'categories': cats if cats else ['Fitness'],
            'tags': tags,
            'thumb': thumb_file,
            'read_time': read_time,
            'excerpt': excerpt
        })

posts.sort(key=lambda p: p['date_raw'], reverse=True)
print(f'Loaded and sorted {len(posts)} posts.')

# 3. Extract published pages
pages = {}
for item in channel.findall('item'):
    pt = item.find('wp:post_type', ns).text
    status = item.find('wp:status', ns).text
    if pt == 'page' and status == 'publish':
        slug = item.find('wp:post_name', ns).text or ''
        title = item.find('title').text or ''
        content = item.find('content:encoded', ns).text or ''
        if slug in ['about-us', 'contact-us', 'privacy-policy', 'write-for-us', 'team']:
            pages[slug] = {
                'title': title,
                'content': content
            }

print(f'Loaded {len(pages)} static pages.')

# Save search index JSON
search_index = [{'title': p['title'], 'slug': p['slug'], 'thumb': p['thumb'], 'date': p['date'], 'cat': p['categories'][0] if p['categories'] else 'Fitness'} for p in posts]
with open('assets/search_index.json', 'w', encoding='utf-8') as f:
    json.dump(search_index, f)

# Helper to localize content images and links
def clean_content(raw_html, root_prefix):
    def rep_img(match):
        src = match.group(1)
        fname = os.path.basename(src.split('?')[0])
        if os.path.exists(os.path.join('assets/images', fname)):
            return 'src="' + root_prefix + 'assets/images/' + fname + '"'
        return 'src="' + src + '"'
    
    c = re.sub(r'src=[\'\"](?:https?://thefitnessfalcon\.com)?/?[^\"\'\s]+/uploads/[^\"\'\s]*/([^\"\'\s]+)[\'\"]', 
               lambda m: 'src="' + root_prefix + 'assets/images/' + os.path.basename(m.group(1)) + '"', raw_html)
    c = re.sub(r'\s+srcset=[\'\"][^\'\"]*[\'\"]', '', c)
    c = re.sub(r'\s+loading=[\'\"]lazy[\'\"]', '', c)
    c = re.sub(r'\s+decoding=[\'\"]async[\'\"]', '', c)
    
    def rep_link(m):
        url = m.group(1).strip('/')
        if not url:
            return 'href="' + root_prefix + 'index.html"'
        parts = url.split('/')
        if parts[0] == 'category' and len(parts) > 1:
            return 'href="' + root_prefix + 'category/' + parts[1] + '/index.html"'
        else:
            return 'href="' + root_prefix + url + '/index.html"'
            
    c = re.sub(r'href=[\'\"]https?://thefitnessfalcon\.com/([^\'\"]*)[\'\"]', rep_link, c)
    return c

def render_header(root_prefix):
    return '''
    <div class="benqu_header_search" id="headerSearchModal">
        <div class="container">
            <div class="row d-flex justify-content-center">
                <div class="col-md-12">
                    <div class="search-wrap-inner" style="position: relative; max-width: 700px; margin: 0 auto;">
                        <input type="search" id="liveSearchInput" placeholder="Search across all 155 articles..." autocomplete="off" style="width: 100%; padding: 18px 24px; font-size: 18px; border-radius: 50px; border: 2px solid #5541f8; outline: none; background: #fff; color: #111;" />
                        <i class="close-btn fal fa-times" id="closeSearchBtn" style="position: absolute; right: 20px; top: 22px; font-size: 22px; cursor: pointer;"></i>
                        <div id="searchResultsDropdown" style="display: none; position: absolute; top: 75px; left: 0; right: 0; background: #fff; border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.15); max-height: 420px; overflow-y: auto; z-index: 9999; padding: 10px; text-align: left;"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <header class="benqu-main-header pfy-header-2">
        <div class="pfy-top-bar" id="pfytopbar">
            <div class="container">
                <div class="row align-items-center">
                    <div class="col-md-7">
                        <div class="pfy-top-left">
                            <div class="topbar-date">
                                <span><i class="fal fa-calendar-alt"></i> September 30, 2026</span>
                            </div>
                            <div class="tp-news-ticker">
                                <div class="breaking-heading"><i class="far fa-fire-alt"></i> Breaking News</div>
                                <div class="pfy-breakingnews">
                                    <ul class="breaking-headline-active owl-carousel" style="display: block;">
                                        <li><a href="''' + root_prefix + '''apple-watch-vs-garmin-step-tracking-accuracy-2026/index.html">Apple Watch vs Garmin: Which Is More Accurate for Step Tracking in 2026?</a></li>
                                        <li><a href="''' + root_prefix + '''apple-watch-series-12-readiness-score-explained/index.html">Apple Watch Series 12 Readiness Score Explained: What It Means for Your Training</a></li>
                                        <li><a href="''' + root_prefix + '''what-is-a-readiness-score-low-workout/index.html">What Is a Readiness Score? Should You Skip Your Workout When It’s Low?</a></li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-5">
                        <div class="pfy-top-right">
                            <div class="dark-light-mode">
                                <i class="fas fa-moon" id="themeToggleBtn" style="cursor: pointer;"></i>
                            </div>
                            <div class="pfy-top-social">
                                <span>Follow Us</span>
                                <ul>
                                    <li><a href="https://www.facebook.com/people/The-Fitness-Falcon/61553645405177/" target="_blank"><i class="fab fa-facebook-f"></i></a></li>
                                    <li><a href="https://twitter.com/fitnessfalcon_" target="_blank"><i class="fab fa-twitter"></i></a></li>
                                    <li><a href="https://www.instagram.com/thefitnessfalconofficial/" target="_blank"><i class="fab fa-instagram"></i></a></li>
                                    <li><a href="https://www.youtube.com/@TheFitnessFalcon" target="_blank"><i class="fab fa-youtube"></i></a></li>
                                    <li><a href="https://www.pinterest.com/thefitnessfalcon/" target="_blank"><i class="fab fa-pinterest"></i></a></li>
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div class="pfy-main-menu pfy-menu-2">
            <div class="container">
                <div class="row align-items-center">
                    <div class="col-lg-3 col-6">
                        <div class="pfy-logo">
                            <a href="''' + root_prefix + '''index.html">
                                <img src="''' + root_prefix + '''assets/images/1.svg" alt="The Fitness Falcon" style="max-height: 48px;" />
                            </a>
                        </div>
                    </div>
                    <div class="col-lg-7 d-none d-lg-block">
                        <div class="pfy-main-nav text-center">
                            <nav>
                                <ul style="display: flex; justify-content: center; gap: 24px; list-style: none; margin: 0; padding: 0;">
                                    <li><a href="''' + root_prefix + '''category/food-and-recipes/index.html" style="font-weight: 600;">Food &amp; Recipes</a></li>
                                    <li><a href="''' + root_prefix + '''category/fitness/index.html" style="font-weight: 600;">Fitness</a></li>
                                    <li><a href="''' + root_prefix + '''category/health/index.html" style="font-weight: 600;">Health</a></li>
                                    <li><a href="''' + root_prefix + '''category/news/index.html" style="font-weight: 600;">News</a></li>
                                    <li><a href="''' + root_prefix + '''about-us/index.html" style="font-weight: 600;">About Us</a></li>
                                    <li><a href="''' + root_prefix + '''contact-us/index.html" style="font-weight: 600;">Contact Us</a></li>
                                    <li><a href="''' + root_prefix + '''write-for-us/index.html" style="font-weight: 600;">Write For Us</a></li>
                                </ul>
                            </nav>
                        </div>
                    </div>
                    <div class="col-lg-2 col-6 text-end">
                        <div class="pfy-right-action" style="display: flex; align-items: center; justify-content: flex-end; gap: 16px;">
                            <a href="javascript:void(0)" class="pfy-search-btn" id="openSearchBtn" style="font-size: 18px; color: inherit;"><i class="far fa-search"></i></a>
                            <a href="''' + root_prefix + '''blog/index.html" class="d-none d-sm-inline-block" style="background: #5541f8; color: #fff; padding: 8px 18px; border-radius: 20px; font-size: 13px; font-weight: 700; text-decoration: none;">All Articles</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </header>
    '''

def render_footer(root_prefix):
    return '''
    <footer class="benqu-footer" style="background: #0f172a; color: #94a3b8; padding: 60px 0 30px;">
        <div class="container">
            <div class="row">
                <div class="col-lg-4 col-md-6 mb-4">
                    <div class="footer-widget">
                        <a href="''' + root_prefix + '''index.html">
                            <img src="''' + root_prefix + '''assets/images/2.svg" alt="The Fitness Falcon" style="max-height: 45px; margin-bottom: 20px;" />
                        </a>
                        <p style="color: #94a3b8; line-height: 1.7; font-size: 15px;">The Fitness Falcon delivers evidence-based health tips, fitness advice, nutrition insights, workout plans, and wellness guidance for an improved lifestyle.</p>
                    </div>
                </div>
                <div class="col-lg-2 col-md-6 mb-4">
                    <div class="footer-widget">
                        <h4 style="color: #fff; font-weight: 700; font-size: 18px; margin-bottom: 20px;">Quick Links</h4>
                        <ul style="list-style: none; padding: 0; margin: 0; line-height: 2.2;">
                            <li><a href="''' + root_prefix + '''index.html" style="color: #94a3b8; text-decoration: none;">Home</a></li>
                            <li><a href="''' + root_prefix + '''blog/index.html" style="color: #94a3b8; text-decoration: none;">Blog Library</a></li>
                            <li><a href="''' + root_prefix + '''about-us/index.html" style="color: #94a3b8; text-decoration: none;">About Us</a></li>
                            <li><a href="''' + root_prefix + '''contact-us/index.html" style="color: #94a3b8; text-decoration: none;">Contact Us</a></li>
                            <li><a href="''' + root_prefix + '''privacy-policy/index.html" style="color: #94a3b8; text-decoration: none;">Privacy Policy</a></li>
                            <li><a href="''' + root_prefix + '''write-for-us/index.html" style="color: #94a3b8; text-decoration: none;">Write For Us</a></li>
                        </ul>
                    </div>
                </div>
                <div class="col-lg-3 col-md-6 mb-4">
                    <div class="footer-widget">
                        <h4 style="color: #fff; font-weight: 700; font-size: 18px; margin-bottom: 20px;">Top Categories</h4>
                        <ul style="list-style: none; padding: 0; margin: 0; line-height: 2.2;">
                            <li><a href="''' + root_prefix + '''category/fitness/index.html" style="color: #94a3b8; text-decoration: none;">Fitness &amp; Workouts</a></li>
                            <li><a href="''' + root_prefix + '''category/nutrition/index.html" style="color: #94a3b8; text-decoration: none;">Nutrition &amp; Diet</a></li>
                            <li><a href="''' + root_prefix + '''category/food-and-recipes/index.html" style="color: #94a3b8; text-decoration: none;">Food &amp; Recipes</a></li>
                            <li><a href="''' + root_prefix + '''category/health/index.html" style="color: #94a3b8; text-decoration: none;">Health &amp; Wellness</a></li>
                            <li><a href="''' + root_prefix + '''category/lifestyle/index.html" style="color: #94a3b8; text-decoration: none;">Lifestyle</a></li>
                        </ul>
                    </div>
                </div>
                <div class="col-lg-3 col-md-6 mb-4">
                    <div class="footer-widget">
                        <h4 style="color: #fff; font-weight: 700; font-size: 18px; margin-bottom: 20px;">Newsletter</h4>
                        <p style="color: #94a3b8; font-size: 14px;">Subscribe to get our weekly health insights delivered to your inbox.</p>
                        <form onsubmit="event.preventDefault(); alert('Subscribed successfully!');" style="display: flex; flex-direction: column; gap: 10px; margin-top: 15px;">
                            <input type="email" placeholder="Your email address" required style="padding: 12px 16px; border-radius: 8px; border: 1px solid #334155; background: #1e293b; color: #fff; outline: none; font-size: 14px;" />
                            <button type="submit" style="padding: 12px; border-radius: 8px; border: none; background: #5541f8; color: #fff; font-weight: 700; cursor: pointer;">Subscribe</button>
                        </form>
                    </div>
                </div>
            </div>
            <div class="row pt-4 mt-4" style="border-top: 1px solid #1e293b; text-align: center;">
                <div class="col-12">
                    <p style="margin: 0; font-size: 14px; color: #64748b;">&copy; 2026, <strong>The Fitness Falcon</strong> All Rights Reserved.</p>
                </div>
            </div>
        </div>
    </footer>
    '''

def render_sidebar(root_prefix, current_slug=''):
    recent_items = [p for p in posts if p['slug'] != current_slug][:5]
    recent_html = ''
    for rp in recent_items:
        recent_html += '''
        <div style="display: flex; gap: 14px; align-items: center; margin-bottom: 18px;">
            <a href="''' + root_prefix + rp['slug'] + '''/index.html" style="flex-shrink: 0; width: 80px; height: 60px; border-radius: 8px; overflow: hidden; display: block;">
                <img src="''' + root_prefix + 'assets/images/' + rp['thumb'] + '''" alt="''' + html.escape(rp['title']) + '''" style="width: 100%; height: 100%; object-fit: cover;" />
            </a>
            <div>
                <a href="''' + root_prefix + rp['slug'] + '''/index.html" style="font-weight: 700; font-size: 14px; color: #1e293b; text-decoration: none; line-height: 1.35; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">''' + html.escape(rp['title']) + '''</a>
                <span style="font-size: 12px; color: #64748b; margin-top: 4px; display: block;"><i class="fal fa-calendar-alt"></i> ''' + rp['date'] + '''</span>
            </div>
        </div>
        '''

    categories_count = {}
    for p in posts:
        for c in p['categories']:
            categories_count[c] = categories_count.get(c, 0) + 1
    
    top_cats = sorted(categories_count.items(), key=lambda x: x[1], reverse=True)[:8]
    cat_html = ''
    for cat_name, count in top_cats:
        c_slug = cat_slug_map.get(cat_name, cat_name.lower().replace(' ', '-').replace('&', 'and'))
        cat_html += '''
        <li style="display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid #f1f5f9;">
            <a href="''' + root_prefix + 'category/' + c_slug + '''/index.html" style="color: #334155; font-weight: 600; text-decoration: none; font-size: 15px;">''' + cat_name + '''</a>
            <span style="background: #e2e8f0; color: #475569; font-size: 12px; padding: 2px 10px; border-radius: 12px; font-weight: 700;">''' + str(count) + '''</span>
        </li>
        '''

    return '''
    <div class="sidebar-widget-area" style="position: sticky; top: 100px;">
        <div style="background: #fff; border-radius: 16px; padding: 24px; box-shadow: 0 4px 20px rgba(0,0,0,0.04); margin-bottom: 30px; border: 1px solid #f1f5f9;">
            <h3 style="font-size: 18px; font-weight: 900; color: #0f172a; margin-bottom: 20px; border-left: 4px solid #5541f8; padding-left: 12px;">Recent Articles</h3>
            ''' + recent_html + '''
        </div>
        <div style="background: #fff; border-radius: 16px; padding: 24px; box-shadow: 0 4px 20px rgba(0,0,0,0.04); margin-bottom: 30px; border: 1px solid #f1f5f9;">
            <h3 style="font-size: 18px; font-weight: 900; color: #0f172a; margin-bottom: 20px; border-left: 4px solid #5541f8; padding-left: 12px;">Categories</h3>
            <ul style="list-style: none; padding: 0; margin: 0;">
                ''' + cat_html + '''
            </ul>
        </div>
        <div style="background: linear-gradient(135deg, #6366f1 0%, #4338ca 100%); border-radius: 16px; padding: 30px 24px; color: #fff; text-align: center; margin-bottom: 30px;">
            <i class="far fa-envelope-open-text" style="font-size: 40px; margin-bottom: 15px; display: inline-block;"></i>
            <h3 style="font-size: 20px; font-weight: 900; color: #fff; margin-bottom: 10px;">Daily Fitness Digest</h3>
            <p style="font-size: 14px; opacity: 0.9; margin-bottom: 20px;">Get top health tips, workouts, and wellness guides straight to your inbox.</p>
            <form onsubmit="event.preventDefault(); alert('Subscribed successfully!');">
                <input type="email" placeholder="Your email address" required style="width: 100%; padding: 12px 16px; border-radius: 30px; border: none; margin-bottom: 12px; outline: none;" />
                <button type="submit" style="width: 100%; padding: 12px; border-radius: 30px; border: none; background: #fff; color: #4338ca; font-weight: 700; cursor: pointer;">Subscribe Free</button>
            </form>
        </div>
    </div>
    '''

def render_base_head(title, description, root_prefix):
    return '''<!doctype html>
<html lang="en-US">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>''' + html.escape(title) + ''' - The Fitness Falcon</title>
    <meta name="description" content="''' + html.escape(description) + '''" />
    <link rel="icon" href="''' + root_prefix + '''assets/images/cropped-Untitled-design-14-32x32.png" sizes="32x32" />
    <link rel="icon" href="''' + root_prefix + '''assets/images/cropped-Untitled-design-14-192x192.png" sizes="192x192" />
    
    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,wght@0,400;0,500;0,700;0,900;1,400;1,700&display=swap" rel="stylesheet">
    
    <!-- CSS Dependencies -->
    <link rel="stylesheet" href="''' + root_prefix + '''assets/css/bootstrap.min.css" />
    <link rel="stylesheet" href="''' + root_prefix + '''assets/css/all.min.css" />
    <link rel="stylesheet" href="''' + root_prefix + '''assets/css/benqu-style.css" />
    <link rel="stylesheet" href="''' + root_prefix + '''assets/css/post-style.css" />
    <link rel="stylesheet" href="''' + root_prefix + '''assets/css/responsive.css" />
    <link rel="stylesheet" href="''' + root_prefix + '''assets/css/custom-style.css" />
    
    <style>
        body {
            font-family: 'DM Sans', sans-serif !important;
            color: #1e293b;
            background-color: #f8fafc;
        }
        h1, h2, h3, h4, h5, h6 {
            font-family: 'DM Sans', sans-serif !important;
            font-weight: 900 !important;
            color: #0f172a;
        }
        .entry-content {
            font-size: 17px;
            line-height: 1.85;
            color: #334155;
        }
        .entry-content p {
            margin-bottom: 1.5em;
        }
        .entry-content h2 {
            margin-top: 1.8em;
            margin-bottom: 0.7em;
            font-size: 26px;
        }
        .entry-content h3 {
            margin-top: 1.5em;
            margin-bottom: 0.6em;
            font-size: 22px;
        }
        .entry-content img {
            max-width: 100%;
            height: auto;
            border-radius: 12px;
            margin: 20px 0;
        }
        .entry-content ul, .entry-content ol {
            padding-left: 24px;
            margin-bottom: 1.5em;
        }
        .entry-content li {
            margin-bottom: 0.5em;
        }
        .entry-content blockquote {
            border-left: 4px solid #5541f8;
            padding: 16px 24px;
            background: #f1f5f9;
            border-radius: 0 12px 12px 0;
            margin: 24px 0;
            font-style: italic;
        }
        .category-badge {
            display: inline-block;
            background: #5541f8;
            color: #fff;
            font-size: 12px;
            font-weight: 700;
            padding: 4px 14px;
            border-radius: 20px;
            text-decoration: none;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .category-badge:hover {
            background: #3b2ee8;
            color: #fff;
        }
        .post-card {
            background: #fff;
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 4px 20px rgba(0,0,0,0.04);
            border: 1px solid #f1f5f9;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            height: 100%;
            display: flex;
            flex-direction: column;
        }
        .post-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 12px 30px rgba(0,0,0,0.08);
        }
        .post-card-thumb {
            width: 100%;
            height: 200px;
            object-fit: cover;
        }
        .post-card-body {
            padding: 20px;
            flex: 1;
            display: flex;
            flex-direction: column;
        }
        .post-card-title {
            font-size: 18px;
            font-weight: 800;
            color: #0f172a;
            margin: 10px 0;
            line-height: 1.4;
        }
        .post-card-title a {
            color: inherit;
            text-decoration: none;
        }
        .post-card-title a:hover {
            color: #5541f8;
        }
        .post-card-meta {
            font-size: 13px;
            color: #64748b;
            margin-top: auto;
            padding-top: 15px;
            display: flex;
            justify-content: space-between;
        }
    </style>
</head>
<body>
'''

def render_scripts(root_prefix):
    posts_json = json.dumps(search_index)
    return '''
    <!-- JS Dependencies -->
    <script src="''' + root_prefix + '''assets/js/jquery.min.js"></script>
    <script src="''' + root_prefix + '''assets/js/popper.min.js"></script>
    <script src="''' + root_prefix + '''assets/js/bootstrap.min.js"></script>
    <script src="''' + root_prefix + '''assets/js/owl.carousel.min.js"></script>
    <script>
    const ALL_POSTS = ''' + posts_json + ''';

    document.addEventListener('DOMContentLoaded', function() {
        const searchModal = document.getElementById('headerSearchModal');
        const openBtn = document.getElementById('openSearchBtn');
        const closeBtn = document.getElementById('closeSearchBtn');
        const searchInput = document.getElementById('liveSearchInput');
        const resultsBox = document.getElementById('searchResultsDropdown');

        if (openBtn && searchModal) {
            openBtn.addEventListener('click', function(e) {
                e.preventDefault();
                searchModal.classList.add('active');
                if (searchInput) searchInput.focus();
            });
        }
        if (closeBtn && searchModal) {
            closeBtn.addEventListener('click', function() {
                searchModal.classList.remove('active');
            });
        }

        if (searchInput && resultsBox) {
            searchInput.addEventListener('input', function() {
                const query = this.value.trim().toLowerCase();
                if (!query) {
                    resultsBox.style.display = 'none';
                    resultsBox.innerHTML = '';
                    return;
                }
                const matches = ALL_POSTS.filter(function(p) {
                    return p.title.toLowerCase().indexOf(query) !== -1;
                }).slice(0, 6);

                if (matches.length === 0) {
                    resultsBox.innerHTML = '<div style="padding: 16px; text-align: center; color: #64748b;">No articles found matching "' + query + '"</div>';
                } else {
                    let html = '';
                    matches.forEach(function(p) {
                        html += '<a href="''' + root_prefix + '''" + p.slug + "/index.html" style="display: flex; gap: 12px; align-items: center; padding: 10px; border-bottom: 1px solid #f1f5f9; text-decoration: none; color: inherit;">'
                              + '<img src="''' + root_prefix + '''assets/images/" + p.thumb + "" style="width: 50px; height: 50px; border-radius: 6px; object-fit: cover; flex-shrink: 0;" />'
                              + '<div>'
                              + '<div style="font-weight: 700; font-size: 14px; line-height: 1.3; color: #0f172a;">' + p.title + '</div>'
                              + '<span style="font-size: 12px; color: #5541f8; font-weight: 600;">' + p.cat + ' &bull; ' + p.date + '</span>'
                              + '</div>'
                              + '</a>';
                    });
                    resultsBox.innerHTML = html;
                }
                resultsBox.style.display = 'block';
            });
        }

        const toggleBtn = document.getElementById('themeToggleBtn');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', function() {
                document.body.classList.toggle('dark-theme');
                if (document.body.classList.contains('dark-theme')) {
                    this.classList.remove('fa-moon');
                    this.classList.add('fa-sun');
                } else {
                    this.classList.remove('fa-sun');
                    this.classList.add('fa-moon');
                }
            });
        }
    });
    </script>
</body>
</html>
'''

# 4. Generate all Single Post Pages
print('Generating 155 single post pages...')
for post in posts:
    slug = post['slug']
    post_dir = slug
    os.makedirs(post_dir, exist_ok=True)
    
    root_prefix = '../'
    cleaned_content = clean_content(post['content'], root_prefix)
    main_cat = post['categories'][0] if post['categories'] else 'Fitness'
    main_cat_slug = cat_slug_map.get(main_cat, main_cat.lower().replace(' ', '-').replace('&', 'and'))
    
    # Related posts
    related = [p for p in posts if p['slug'] != slug and main_cat in p['categories']][:3]
    if len(related) < 3:
        related = [p for p in posts if p['slug'] != slug][:3]
    
    related_html = ''
    for rel in related:
        rel_cat = rel['categories'][0] if rel['categories'] else 'Fitness'
        related_html += '''
        <div class="col-md-4 mb-4">
            <div class="post-card">
                <a href="''' + root_prefix + rel['slug'] + '''/index.html">
                    <img src="''' + root_prefix + 'assets/images/' + rel['thumb'] + '''" alt="''' + html.escape(rel['title']) + '''" class="post-card-thumb" />
                </a>
                <div class="post-card-body">
                    <span class="category-badge" style="align-self: flex-start; margin-bottom: 8px;">''' + rel_cat + '''</span>
                    <h4 class="post-card-title"><a href="''' + root_prefix + rel['slug'] + '''/index.html">''' + html.escape(rel['title']) + '''</a></h4>
                    <div class="post-card-meta">
                        <span><i class="fal fa-calendar-alt"></i> ''' + rel['date'] + '''</span>
                        <span>''' + str(rel['read_time']) + ''' min read</span>
                    </div>
                </div>
            </div>
        </div>
        '''

    page_html = render_base_head(post['title'], post['excerpt'], root_prefix)
    page_html += render_header(root_prefix)
    page_html += '''
    <main style="padding: 40px 0 80px;">
        <div class="container">
            <div style="margin-bottom: 24px; font-size: 14px; color: #64748b;">
                <a href="''' + root_prefix + '''index.html" style="color: #64748b; text-decoration: none;">Home</a> &nbsp;/&nbsp; 
                <a href="''' + root_prefix + 'category/' + main_cat_slug + '''/index.html" style="color: #5541f8; font-weight: 600; text-decoration: none;">''' + main_cat + '''</a> &nbsp;/&nbsp; 
                <span style="color: #0f172a;">''' + html.escape(post['title'][:40]) + '''...</span>
            </div>

            <div class="row">
                <div class="col-lg-8">
                    <article style="background: #fff; border-radius: 20px; padding: 40px; box-shadow: 0 4px 20px rgba(0,0,0,0.04); border: 1px solid #f1f5f9; margin-bottom: 40px;">
                        <a href="''' + root_prefix + 'category/' + main_cat_slug + '''/index.html" class="category-badge" style="margin-bottom: 16px;">''' + main_cat + '''</a>
                        <h1 style="font-size: 34px; line-height: 1.3; color: #0f172a; margin-bottom: 20px;">''' + html.escape(post['title']) + '''</h1>
                        
                        <div style="display: flex; align-items: center; gap: 16px; padding-bottom: 24px; border-bottom: 1px solid #f1f5f9; margin-bottom: 30px; font-size: 14px; color: #64748b; flex-wrap: wrap;">
                            <span style="font-weight: 700; color: #0f172a;"><i class="fal fa-user" style="color: #5541f8; margin-right: 6px;"></i> By ''' + post['author'] + '''</span>
                            <span><i class="fal fa-calendar-alt" style="margin-right: 6px;"></i> ''' + post['date'] + '''</span>
                            <span><i class="fal fa-clock" style="margin-right: 6px;"></i> ''' + str(post['read_time']) + ''' min read</span>
                            <span><i class="fal fa-comments" style="margin-right: 6px;"></i> 0 Comments</span>
                        </div>

                        <div style="margin-bottom: 36px; border-radius: 16px; overflow: hidden; max-height: 480px;">
                            <img src="''' + root_prefix + 'assets/images/' + post['thumb'] + '''" alt="''' + html.escape(post['title']) + '''" style="width: 100%; height: auto; object-fit: cover;" />
                        </div>

                        <div class="entry-content">
                            ''' + cleaned_content + '''
                        </div>

                        ''' + (('<div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #f1f5f9;"><strong style="margin-right: 10px; color: #0f172a;">Tags:</strong> ' + ' '.join(['<span style="display: inline-block; background: #f1f5f9; color: #475569; padding: 4px 12px; border-radius: 12px; font-size: 13px; margin: 4px;">#' + t + '</span>' for t in post['tags']]) + '</div>') if post['tags'] else '') + '''

                        <div style="background: #f8fafc; border-radius: 16px; padding: 24px; margin-top: 40px; display: flex; gap: 20px; align-items: center; border: 1px solid #e2e8f0;">
                            <div style="width: 70px; height: 70px; border-radius: 50%; background: #5541f8; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 28px; font-weight: 900; flex-shrink: 0;">
                                ''' + post['author'][0] + '''
                            </div>
                            <div>
                                <h4 style="margin: 0 0 6px; font-size: 18px; color: #0f172a;">Written by ''' + post['author'] + '''</h4>
                                <p style="margin: 0; font-size: 14px; color: #64748b; line-height: 1.5;">Fitness and wellness contributor at The Fitness Falcon. Passionate about empowering individuals to achieve active, healthy, and energized lifestyles through evidence-based advice.</p>
                            </div>
                        </div>
                    </article>

                    <div style="margin-top: 40px;">
                        <h3 style="font-size: 22px; font-weight: 900; color: #0f172a; margin-bottom: 24px; border-left: 4px solid #5541f8; padding-left: 12px;">Related Articles</h3>
                        <div class="row">
                            ''' + related_html + '''
                        </div>
                    </div>
                </div>

                <div class="col-lg-4">
                    ''' + render_sidebar(root_prefix, post['slug']) + '''
                </div>
            </div>
        </div>
    </main>
    '''
    page_html += render_footer(root_prefix)
    page_html += render_scripts(root_prefix)

    with open(os.path.join(post_dir, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(page_html)
    with open(slug + '.html', 'w', encoding='utf-8') as f:
        f.write(page_html.replace(root_prefix, ''))

print('Generated all 155 single post pages.')

# 5. Generate Category Archive Pages
categories_dict = {}
for p in posts:
    for c in p['categories']:
        c_slug = cat_slug_map.get(c, c.lower().replace(' ', '-').replace('&', 'and'))
        if c_slug not in categories_dict:
            categories_dict[c_slug] = {'name': c, 'posts': []}
        categories_dict[c_slug]['posts'].append(p)

print('Generating category archive pages...')
for c_slug, cat_data in categories_dict.items():
    cat_dir = os.path.join('category', c_slug)
    os.makedirs(cat_dir, exist_ok=True)
    root_prefix = '../../'
    
    posts_cards = ''
    for p in cat_data['posts']:
        posts_cards += '''
        <div class="col-md-6 col-lg-6 mb-4">
            <div class="post-card">
                <a href="''' + root_prefix + p['slug'] + '''/index.html">
                    <img src="''' + root_prefix + 'assets/images/' + p['thumb'] + '''" alt="''' + html.escape(p['title']) + '''" class="post-card-thumb" />
                </a>
                <div class="post-card-body">
                    <span class="category-badge" style="align-self: flex-start; margin-bottom: 8px;">''' + cat_data['name'] + '''</span>
                    <h4 class="post-card-title"><a href="''' + root_prefix + p['slug'] + '''/index.html">''' + html.escape(p['title']) + '''</a></h4>
                    <p style="font-size: 14px; color: #64748b; line-height: 1.6; margin-bottom: 16px;">''' + html.escape(p['excerpt'][:120]) + '''...</p>
                    <div class="post-card-meta">
                        <span><i class="fal fa-calendar-alt"></i> ''' + p['date'] + '''</span>
                        <span>''' + str(p['read_time']) + ''' min read</span>
                    </div>
                </div>
            </div>
        </div>
        '''

    cat_html = render_base_head(cat_data['name'] + ' Articles', "Explore all health, workout, and wellness articles in " + cat_data['name'] + " on The Fitness Falcon.", root_prefix)
    cat_html += render_header(root_prefix)
    cat_html += '''
    <main style="padding: 40px 0 80px;">
        <div class="container">
            <div style="background: linear-gradient(135deg, #4f46e5 0%, #3b82f6 100%); border-radius: 20px; padding: 48px 36px; color: #fff; margin-bottom: 40px; box-shadow: 0 10px 30px rgba(79, 70, 229, 0.15);">
                <div style="max-width: 600px;">
                    <span style="background: rgba(255,255,255,0.2); padding: 6px 14px; border-radius: 20px; font-size: 13px; font-weight: 700; text-transform: uppercase;">Category Archive</span>
                    <h1 style="color: #fff; font-size: 38px; margin: 16px 0 12px;">''' + html.escape(cat_data['name']) + '''</h1>
                    <p style="color: rgba(255,255,255,0.9); font-size: 16px; margin: 0;">Browsing ''' + str(len(cat_data['posts'])) + ''' comprehensive articles, research-backed guides, and expert advice.</p>
                </div>
            </div>

            <div class="row">
                <div class="col-lg-8">
                    <div class="row">
                        ''' + posts_cards + '''
                    </div>
                </div>
                <div class="col-lg-4">
                    ''' + render_sidebar(root_prefix) + '''
                </div>
            </div>
        </div>
    </main>
    '''
    cat_html += render_footer(root_prefix)
    cat_html += render_scripts(root_prefix)

    with open(os.path.join(cat_dir, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(cat_html)

print('Generated all category pages.')

# 6. Generate Static Pages
for slug, page_data in pages.items():
    p_dir = slug
    os.makedirs(p_dir, exist_ok=True)
    root_prefix = '../'
    cleaned = clean_content(page_data['content'], root_prefix)
    
    p_html = render_base_head(page_data['title'], page_data['title'] + " - The Fitness Falcon", root_prefix)
    p_html += render_header(root_prefix)
    p_html += '''
    <main style="padding: 40px 0 80px;">
        <div class="container">
            <div class="row justify-content-center">
                <div class="col-lg-10">
                    <div style="background: #fff; border-radius: 20px; padding: 48px; box-shadow: 0 4px 20px rgba(0,0,0,0.04); border: 1px solid #f1f5f9;">
                        <h1 style="font-size: 36px; color: #0f172a; margin-bottom: 24px; padding-bottom: 16px; border-bottom: 2px solid #f1f5f9;">''' + html.escape(page_data['title']) + '''</h1>
                        <div class="entry-content">
                            ''' + cleaned + '''
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </main>
    '''
    p_html += render_footer(root_prefix)
    p_html += render_scripts(root_prefix)
    with open(os.path.join(p_dir, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(p_html)
    with open(slug + '.html', 'w', encoding='utf-8') as f:
        f.write(p_html.replace(root_prefix, ''))

# Generate Blog Archive
os.makedirs('blog', exist_ok=True)
root_prefix = '../'
blog_cards = ''
for p in posts:
    c_name = p['categories'][0] if p['categories'] else 'Fitness'
    blog_cards += '''
    <div class="col-md-6 col-lg-4 mb-4">
        <div class="post-card">
            <a href="''' + root_prefix + p['slug'] + '''/index.html">
                <img src="''' + root_prefix + 'assets/images/' + p['thumb'] + '''" alt="''' + html.escape(p['title']) + '''" class="post-card-thumb" />
            </a>
            <div class="post-card-body">
                <span class="category-badge" style="align-self: flex-start; margin-bottom: 8px;">''' + c_name + '''</span>
                <h4 class="post-card-title"><a href="''' + root_prefix + p['slug'] + '''/index.html">''' + html.escape(p['title']) + '''</a></h4>
                <p style="font-size: 14px; color: #64748b; line-height: 1.6; margin-bottom: 16px;">''' + html.escape(p['excerpt'][:110]) + '''...</p>
                <div class="post-card-meta">
                    <span><i class="fal fa-calendar-alt"></i> ''' + p['date'] + '''</span>
                    <span>''' + str(p['read_time']) + ''' min read</span>
                </div>
            </div>
        </div>
    </div>
    '''

b_html = render_base_head("All Articles - Blog", "Read all health, fitness, nutrition, and lifestyle articles on The Fitness Falcon.", root_prefix)
b_html += render_header(root_prefix)
b_html += '''
<main style="padding: 40px 0 80px;">
    <div class="container">
        <div style="text-align: center; margin-bottom: 48px;">
            <span class="category-badge" style="margin-bottom: 12px;">Full Library</span>
            <h1 style="font-size: 40px; color: #0f172a; margin-top: 10px;">The Fitness Falcon Blog</h1>
            <p style="font-size: 18px; color: #64748b; max-width: 650px; margin: 12px auto 0;">Explore our collection of ''' + str(len(posts)) + ''' articles covering workouts, wellness, recipes, and technology.</p>
        </div>
        <div class="row">
            ''' + blog_cards + '''
        </div>
    </div>
</main>
'''
b_html += render_footer(root_prefix)
b_html += render_scripts(root_prefix)
with open('blog/index.html', 'w', encoding='utf-8') as f:
    f.write(b_html)
with open('blog.html', 'w', encoding='utf-8') as f:
    f.write(b_html.replace(root_prefix, ''))

print('Generated static and blog pages.')

# 7. Update Homepage index.html with live links
print('Updating homepage index.html with active live links...')
with open('index.html', 'r', encoding='utf-8') as f:
    home_content = f.read()

# Replace post title links on homepage
for p in posts:
    t_clean = p['title'].strip()
    slug = p['slug']
    home_content = re.sub(
        r'<a([^>]*?)href="javascript:void\(0\)"([^>]*?)>(' + re.escape(t_clean) + r')</a>',
        r'<a\1href="' + slug + r'/index.html"\2>\3</a>',
        home_content
    )

# Menu link replacements
menu_links = {
    'Food & Recipes': 'category/food-and-recipes/index.html',
    'Food &amp; Recipes': 'category/food-and-recipes/index.html',
    'Fitness': 'category/fitness/index.html',
    'Health': 'category/health/index.html',
    'News': 'category/news/index.html',
    'About Us': 'about-us/index.html',
    'Contact Us': 'contact-us/index.html',
    'Write For Us': 'write-for-us/index.html',
    'Beauty': 'category/beauty/index.html',
    'Blog': 'blog/index.html',
    'Cycling': 'category/cycling/index.html',
    'Gym': 'category/gym/index.html',
    'Lifestyle': 'category/lifestyle/index.html',
    'Nutrition': 'category/nutrition/index.html',
}

for m_text, m_href in menu_links.items():
    home_content = re.sub(
        r'<a([^>]*?)href="javascript:void\(0\)"([^>]*?)>\s*(<span>)?' + re.escape(m_text) + r'(</span>)?\s*</a>',
        r'<a\1href="' + m_href + r'"\2>\3' + m_text + r'\4</a>',
        home_content
    )

# Also link the hero post title
home_content = home_content.replace(
    'href="javascript:void(0)">Apple Watch vs Garmin: Which Is More Accurate for Step Tracking in 2026?</a>',
    'href="apple-watch-vs-garmin-step-tracking-accuracy-2026/index.html">Apple Watch vs Garmin: Which Is More Accurate for Step Tracking in 2026?</a>'
)

# Enable clickable pointers in custom style
home_content = re.sub(r'a,\s*button,\s*input\[type="submit"\]\s*\{\s*cursor:\s*default\s*!important;\s*\}', 
                      'a { cursor: pointer; text-decoration: none; }', home_content)

# Remove click neutralizer that blocks navigation
home_content = re.sub(r'document\.addEventListener\(\'click\',\s*function\(e\)\s*\{\s*var link = e\.target\.closest\(\'a\'\);.*?\}\s*,\s*true\);', 
                      '', home_content, flags=re.DOTALL)

# Add search popup to homepage if not present
if 'ALL_POSTS' not in home_content:
    search_script = '''
    <script>
    const ALL_POSTS = ''' + json.dumps(search_index) + ''';
    document.addEventListener('DOMContentLoaded', function() {
        const searchModal = document.querySelector('.benqu_header_search');
        const openBtn = document.querySelector('.pfy-search-btn');
        const closeBtn = document.querySelector('.close-btn');
        
        if (openBtn && searchModal) {
            openBtn.addEventListener('click', function(e) {
                e.preventDefault();
                searchModal.classList.add('active');
                const searchInp = searchModal.querySelector('input[type="search"]');
                if (searchInp) searchInp.focus();
            });
        }
        if (closeBtn && searchModal) {
            closeBtn.addEventListener('click', function() {
                searchModal.classList.remove('active');
            });
        }

        const searchInp = searchModal ? searchModal.querySelector('input[type="search"]') : null;
        if (searchInp) {
            let resultsBox = document.getElementById('homeSearchResultsDropdown');
            if (!resultsBox) {
                resultsBox = document.createElement('div');
                resultsBox.id = 'homeSearchResultsDropdown';
                resultsBox.style.cssText = 'display: none; position: absolute; top: 75px; left: 0; right: 0; background: #fff; border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.15); max-height: 420px; overflow-y: auto; z-index: 9999; padding: 10px; text-align: left;';
                searchInp.parentElement.style.position = 'relative';
                searchInp.parentElement.appendChild(resultsBox);
            }
            searchInp.addEventListener('input', function() {
                const query = this.value.trim().toLowerCase();
                if (!query) {
                    resultsBox.style.display = 'none';
                    resultsBox.innerHTML = '';
                    return;
                }
                const matches = ALL_POSTS.filter(function(p) {
                    return p.title.toLowerCase().indexOf(query) !== -1;
                }).slice(0, 6);

                if (matches.length === 0) {
                    resultsBox.innerHTML = '<div style="padding: 16px; text-align: center; color: #64748b;">No articles found matching "' + query + '"</div>';
                } else {
                    let html = '';
                    matches.forEach(function(p) {
                        html += '<a href="' + p.slug + '/index.html" style="display: flex; gap: 12px; align-items: center; padding: 10px; border-bottom: 1px solid #f1f5f9; text-decoration: none; color: inherit;">'
                              + '<img src="assets/images/' + p.thumb + '" style="width: 50px; height: 50px; border-radius: 6px; object-fit: cover; flex-shrink: 0;" />'
                              + '<div>'
                              + '<div style="font-weight: 700; font-size: 14px; line-height: 1.3; color: #0f172a;">' + p.title + '</div>'
                              + '<span style="font-size: 12px; color: #5541f8; font-weight: 600;">' + p.cat + ' &bull; ' + p.date + '</span>'
                              + '</div>'
                              + '</a>';
                    });
                    resultsBox.innerHTML = html;
                }
                resultsBox.style.display = 'block';
            });
        }
    });
    </script>
    '''
    home_content = home_content.replace('</body>', search_script + '\n</body>')

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(home_content)

print('Site generation complete!')
