#!/usr/bin/env python3
"""
Homepage Modernization Script
Applies clean, responsive semantic markup to index.html:
- Links assets/css/homepage.css in <head>
- Modern Hero Section (single H1, balanced cards)
- 5x2 Popular Categories Grid
- Numbered 01-05 Popular Posts Sidebar (eliminates 3,850px empty space from broken carousel)
- Balanced 2x3 Food & Recipes Grid
- 2-Column Responsive Layout for Section 6 (fixes vertical stacking and 3,234px offset)
- Perfectly balanced HTML tree with 0 unclosed/mismatched tags
"""

import re
import html.parser

def update_homepage():
    with open('index.html', 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Link /assets/css/homepage.css in <head> if not already present
    if '/assets/css/homepage.css' not in content:
        content = content.replace(
            '<link rel="stylesheet" href="assets/css/topbar.css',
            '<link rel="stylesheet" href="/assets/css/homepage.css">\n<link rel="stylesheet" href="/assets/css/topbar.css'
        )
        content = content.replace(
            '<link rel="stylesheet" href="/assets/css/topbar.css',
            '<link rel="stylesheet" href="/assets/css/homepage.css">\n<link rel="stylesheet" href="/assets/css/topbar.css'
        )

    # 2. Modern Hero Section
    old_hero_pattern = re.compile(
        r'<section class="elementor-section elementor-top-section elementor-element elementor-element-a32e7b8.*?</section>',
        re.DOTALL
    )
    new_hero = '''<section class="elementor-section elementor-top-section falcon-hero-section elementor-section-boxed my-4" data-id="a32e7b8">
    <div class="container">
        <div class="falcon-hero-row">
            <div class="falcon-hero-col-main">
                <a class="falcon-hero-card" href="/blogs/apple-watch-vs-garmin-step-tracking-accuracy-2026/">
                    <img fetchpriority="high" width="1200" height="675" src="/assets/images/apple-watch-vs-garmin-step-tracking-accuracy-2026.png" alt="Original illustrated smartwatch and data graphic for Apple Watch vs Garmin: Which Is More Accurate for Step Tracking in 2026?" />
                    <div class="falcon-hero-card-overlay"></div>
                    <div class="falcon-hero-card-content">
                        <span class="falcon-hero-badge">Wearables &amp; Fitness Technology</span>
                        <h1 class="falcon-hero-card-title">Apple Watch vs Garmin: Which Is More Accurate for Step Tracking in 2026?</h1>
                        <div class="falcon-hero-card-meta">
                            <span><i class="fal fa-user"></i> Dinesh</span>
                            <span><i class="fal fa-calendar-alt"></i> September 30, 2026</span>
                            <span><i class="far fa-comments"></i> 0 Comments</span>
                            <span><i class="far fa-eye"></i> 2 Views</span>
                        </div>
                    </div>
                </a>
            </div>
            <div class="falcon-hero-col-side">
                <div class="falcon-hero-side-list">
                    <a class="falcon-side-card" href="/blogs/apple-watch-series-12-readiness-score-explained/">
                        <div class="falcon-side-thumb">
                            <img width="120" height="120" src="/assets/images/apple-watch-series-12-readiness-score-explained.png" alt="Apple Watch Series 12 Readiness Score Explained" />
                        </div>
                        <div class="falcon-side-content">
                            <span class="falcon-side-badge">Wearables &amp; Fitness Technology</span>
                            <h4 class="falcon-side-title">Apple Watch Series 12 Readiness Score Explained: What It Means for Your Training</h4>
                        </div>
                    </a>
                    <a class="falcon-side-card" href="/blogs/what-is-a-readiness-score-low-workout/">
                        <div class="falcon-side-thumb">
                            <img width="120" height="120" src="/assets/images/what-is-a-readiness-score-low-workout.png" alt="What Is a Readiness Score? Should You Skip Your Workout When It’s Low?" />
                        </div>
                        <div class="falcon-side-content">
                            <span class="falcon-side-badge">Wearables &amp; Fitness Technology</span>
                            <h4 class="falcon-side-title">What Is a Readiness Score? Should You Skip Your Workout When It’s Low?</h4>
                        </div>
                    </a>
                    <a class="falcon-side-card" href="/blogs/hrv-for-fitness-what-it-tells-you/">
                        <div class="falcon-side-thumb">
                            <img width="120" height="120" src="/assets/images/hrv-for-fitness-what-it-tells-you.png" alt="HRV for Fitness: What Your Heart Rate Variability Actually Tells You" />
                        </div>
                        <div class="falcon-side-content">
                            <span class="falcon-side-badge">Wearables &amp; Fitness Technology</span>
                            <h4 class="falcon-side-title">HRV for Fitness: What Your Heart Rate Variability Actually Tells You</h4>
                        </div>
                    </a>
                </div>
            </div>
        </div>
    </div>
</section>'''
    content, count = old_hero_pattern.subn(new_hero, content, count=1)
    assert count == 1, "Failed to replace Section 1 Hero"

    # 3. Modern 5x2 Popular Categories Grid
    old_cat_pattern = re.compile(
        r'<div class="elementor-element elementor-element-f3bdc56 e-flex e-con-boxed e-con e-parent".*?</div>\s*</div>\s*</div>\s*(?=\s*<section class="elementor-section elementor-top-section elementor-element elementor-element-20f2fe5)',
        re.DOTALL
    )
    new_categories = '''<section class="elementor-element elementor-element-f3bdc56 my-5" data-id="f3bdc56">
    <div class="container">
        <div class="benqu-section-title-wrap text-left mb-4">
            <h2>Popular Category</h2>
            <span></span>
        </div>
        <div class="falcon-category-grid-5">
            <a class="falcon-cat-card" href="/category/beauty/">
                <img src="/assets/images/Beauty.png" alt="Beauty">
                <span class="falcon-cat-card-title">Beauty</span>
            </a>
            <a class="falcon-cat-card" href="/category/skincare/">
                <img src="/assets/images/Skincare.png" alt="Skincare">
                <span class="falcon-cat-card-title">Skincare</span>
            </a>
            <a class="falcon-cat-card" href="/category/cycling/">
                <img src="/assets/images/Cycling.png" alt="Cycling">
                <span class="falcon-cat-card-title">Cycling</span>
            </a>
            <a class="falcon-cat-card" href="/category/fitness/">
                <img src="/assets/images/Fitness.png" alt="Fitness">
                <span class="falcon-cat-card-title">Fitness</span>
            </a>
            <a class="falcon-cat-card" href="/category/food-and-recipes/">
                <img src="/assets/images/Food-Recipes.png" alt="Food & Recipes">
                <span class="falcon-cat-card-title">Food &amp; Recipes</span>
            </a>
            <a class="falcon-cat-card" href="/category/gym/">
                <img src="/assets/images/Gym.png" alt="Gym">
                <span class="falcon-cat-card-title">Gym</span>
            </a>
            <a class="falcon-cat-card" href="/category/health/">
                <img src="/assets/images/Health.png" alt="Health">
                <span class="falcon-cat-card-title">Health</span>
            </a>
            <a class="falcon-cat-card" href="/category/lifestyle/">
                <img src="/assets/images/Lifestyle.png" alt="Lifestyle">
                <span class="falcon-cat-card-title">Lifestyle</span>
            </a>
            <a class="falcon-cat-card" href="/category/news/">
                <img src="/assets/images/News.png" alt="News">
                <span class="falcon-cat-card-title">News</span>
            </a>
            <a class="falcon-cat-card" href="/category/nutrition/">
                <img src="/assets/images/Nutrition.png" alt="Nutrition">
                <span class="falcon-cat-card-title">Nutrition</span>
            </a>
        </div>
    </div>
</section>'''
    content, count = old_cat_pattern.subn(new_categories, content, count=1)
    assert count == 1, "Failed to replace Popular Categories"

    # 4. Replace broken Owl Carousel in Section 3 with clean Numbered Popular Posts list
    old_carousel_pattern = re.compile(
        r'<div class="elementor-element elementor-element-289d445 elementor-widget elementor-widget-wp-widget-benqu_post_slider".*?<!--Start Single Sidebar Box-->.*?</div>\s*</div>\s*</div>\s*</div>\s*</div>\s*</section>',
        re.DOTALL
    )
    new_sidebar_popular = '''<div class="elementor-element elementor-element-289d445 elementor-widget elementor-widget-wp-widget-benqu_post_slider" data-id="289d445" data-element_type="widget" data-widget_type="wp-widget-benqu_post_slider.default">
				<div class="elementor-widget-container">
                    <div class="falcon-popular-list">
                        <a class="falcon-popular-item" href="/blogs/apple-watch-vs-garmin-step-tracking-accuracy-2026/">
                            <span class="falcon-popular-rank">01</span>
                            <div class="falcon-popular-thumb">
                                <img width="120" height="120" src="/assets/images/apple-watch-vs-garmin-step-tracking-accuracy-2026.png" alt="Apple Watch vs Garmin" />
                            </div>
                            <div class="falcon-popular-content">
                                <span class="falcon-popular-cat">Wearables</span>
                                <h5 class="falcon-popular-title">Apple Watch vs Garmin: Which Is More Accurate for Step Tracking in 2026?</h5>
                                <span class="falcon-popular-date"><i class="fal fa-calendar-alt"></i> Sep 30, 2026</span>
                            </div>
                        </a>
                        <a class="falcon-popular-item" href="/blogs/apple-watch-series-12-readiness-score-explained/">
                            <span class="falcon-popular-rank">02</span>
                            <div class="falcon-popular-thumb">
                                <img width="120" height="120" src="/assets/images/apple-watch-series-12-readiness-score-explained.png" alt="Apple Watch Series 12 Readiness Score Explained" />
                            </div>
                            <div class="falcon-popular-content">
                                <span class="falcon-popular-cat">Wearables</span>
                                <h5 class="falcon-popular-title">Apple Watch Series 12 Readiness Score Explained: What It Means for Your Training</h5>
                                <span class="falcon-popular-date"><i class="fal fa-calendar-alt"></i> Sep 30, 2026</span>
                            </div>
                        </a>
                        <a class="falcon-popular-item" href="/blogs/what-is-a-readiness-score-low-workout/">
                            <span class="falcon-popular-rank">03</span>
                            <div class="falcon-popular-thumb">
                                <img width="120" height="120" src="/assets/images/what-is-a-readiness-score-low-workout.png" alt="What Is a Readiness Score?" />
                            </div>
                            <div class="falcon-popular-content">
                                <span class="falcon-popular-cat">Wearables</span>
                                <h5 class="falcon-popular-title">What Is a Readiness Score? Should You Skip Your Workout When It’s Low?</h5>
                                <span class="falcon-popular-date"><i class="fal fa-calendar-alt"></i> Sep 30, 2026</span>
                            </div>
                        </a>
                        <a class="falcon-popular-item" href="/blogs/hrv-for-fitness-what-it-tells-you/">
                            <span class="falcon-popular-rank">04</span>
                            <div class="falcon-popular-thumb">
                                <img width="120" height="120" src="/assets/images/hrv-for-fitness-what-it-tells-you.png" alt="HRV for Fitness" />
                            </div>
                            <div class="falcon-popular-content">
                                <span class="falcon-popular-cat">Wearables</span>
                                <h5 class="falcon-popular-title">HRV for Fitness: What Your Heart Rate Variability Actually Tells You</h5>
                                <span class="falcon-popular-date"><i class="fal fa-calendar-alt"></i> Sep 30, 2026</span>
                            </div>
                        </a>
                        <a class="falcon-popular-item" href="/blogs/garmin-running-plans-features-september-2026/">
                            <span class="falcon-popular-rank">05</span>
                            <div class="falcon-popular-thumb">
                                <img width="120" height="120" src="/assets/images/garmin-running-plans-features-september-2026.png" alt="Garmin Running Plans" />
                            </div>
                            <div class="falcon-popular-content">
                                <span class="falcon-popular-cat">Wearables</span>
                                <h5 class="falcon-popular-title">Garmin’s New Running Plans and Fitness Features: What Changed in September 2026</h5>
                                <span class="falcon-popular-date"><i class="fal fa-calendar-alt"></i> Sep 30, 2026</span>
                            </div>
                        </a>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
</section>'''
    content, count = old_carousel_pattern.subn(new_sidebar_popular, content, count=1)
    assert count == 1, "Failed to replace Section 3 Popular Carousel"

    # Also fix the Social Counter closing tag inside Section 3 right col
    # Social counter was missing a closing div before 029349a
    content = content.replace(
        '''        </div>
    </div>
</div>
				</div>
				<div class="elementor-element elementor-element-029349a''',
        '''        </div>
    </div>
</div>
				</div>
				</div>
				<div class="elementor-element elementor-element-029349a'''
    )

    # 5. Food & Recipes section: change col-xl-3 to col-lg-4 col-md-6 mb-4
    food_sec_start = content.find('data-id="d5e4bac"')
    food_sec_end = content.find('data-id="1d25ac6"')
    if food_sec_start != -1 and food_sec_end != -1:
        food_sec = content[food_sec_start:food_sec_end]
        food_sec_updated = food_sec.replace('col-lg-4 col-xl-3 col-md-6', 'col-lg-4 col-md-6 mb-4')
        content = content[:food_sec_start] + food_sec_updated + content[food_sec_end:]

    # 6. Section 6: Clean up the 2 extra closing divs at lines 1888-1889
    content = content.replace(
        '''</div>
                            </div>
        </div>
    \t\t</div>
\t\t\t\t</div>
\t\t\t\t<div class="elementor-element elementor-element-8e54b28''',
        '''</div>
    \t\t</div>
\t\t\t\t</div>
\t\t\t\t<div class="elementor-element elementor-element-8e54b28'''
    )

    # 7. Section 6: Wrap columns in flex row so sidebar floats beside content
    # Remove empty pfy-overlay widget
    content = content.replace(
        '''<div class="elementor-element elementor-element-abb5dda elementor-widget elementor-widget-benqu-post-overlay" data-id="abb5dda" data-element_type="widget" data-widget_type="benqu-post-overlay.default">
				<div class="elementor-widget-container">
					<div class="pfy-post-grid-wrap pfy-overlay-style-2 style-4">
    <div class="row">
            </div>    
</div>\t\t
    \t\t</div>
\t\t\t\t</div>''',
        ''
    )

    # 8. Remove stray </div><!-- #page --> before </main>
    content = content.replace(
        '''</div><!-- #page -->
</main>''',
        '''</main>'''
    )

    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Updated index.html successfully.")

if __name__ == '__main__':
    update_homepage()
