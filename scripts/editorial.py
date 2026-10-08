"""Accurate publishing metadata and clean, semantic imported article HTML."""
import html
from html.parser import HTMLParser

AUTHOR_INFO = {
    'Dinesh Jeengar': {
        'role': 'Owner & publisher',
        'bio': 'Dinesh Jeengar owns and publishes The Fitness Falcon. Articles share general information about fitness and everyday wellness; no medical qualification or clinical review is implied by this byline.',
        'initial': 'D',
        'gradient': 'linear-gradient(135deg, #5541f8 0%, #3b82f6 100%)',
    },
    'The Fitness Falcon': {
        'role': 'Publication byline',
        'bio': 'This article is published by The Fitness Falcon. Dinesh Jeengar is the site owner and publisher. The byline does not imply a medical qualification or clinical review.',
        'initial': 'F',
        'gradient': 'linear-gradient(135deg, #0ea5e9 0%, #2563eb 100%)',
    },
}

def author_slug(name):
    return 'dinesh-jeengar' if name == 'Dinesh Jeengar' else 'the-fitness-falcon'

class ArticleHTML(HTMLParser):
    allowed = set('p h1 h2 h3 h4 h5 h6 ul ol li strong b em i u blockquote table thead tbody tfoot tr th td caption figure figcaption img a br hr sup sub pre code dl dt dd'.split())
    void = {'img', 'br', 'hr'}
    discard = {'script', 'style', 'button', 'svg', 'noscript'}
    attrs = {'id', 'href', 'src', 'alt', 'title', 'width', 'height', 'loading', 'srcset', 'sizes', 'colspan', 'rowspan', 'scope', 'start', 'type', 'target', 'rel'}
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.output = []
        self.hidden = 0
    def handle_starttag(self, tag, attrs):
        if tag in self.discard:
            self.hidden += 1
            return
        if self.hidden or tag not in self.allowed:
            return
        safe = []
        for name, value in attrs:
            if name not in self.attrs or value is None:
                continue
            if name in {'href', 'src'} and value.strip().lower().startswith(('javascript:', 'data:', 'vbscript:')):
                continue
            safe.append(f' {name}="{html.escape(value, quote=True)}"')
        self.output.append(f'<{tag}{"".join(safe)}>')
    def handle_endtag(self, tag):
        if tag in self.discard:
            self.hidden = max(0, self.hidden - 1)
        elif not self.hidden and tag in self.allowed and tag not in self.void:
            self.output.append(f'</{tag}>')
    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.void:
            self.handle_endtag(tag)
    def handle_data(self, data):
        if not self.hidden:
            self.output.append(data)
    def handle_entityref(self, name):
        if not self.hidden:
            self.output.append(f'&{name};')
    def handle_charref(self, name):
        if not self.hidden:
            self.output.append(f'&#{name};')

def clean_article_html(content):
    parser = ArticleHTML()
    parser.feed(content)
    parser.close()
    return ''.join(parser.output).strip()

def normalize_author(post):
    """Keep the confirmed owner's name; replace unverified persona credentials."""
    if post['author'] in {'Dinesh', 'Dinesh Jeengar', 'dinesh'}:
        name = 'Dinesh Jeengar'
    else:
        name = 'The Fitness Falcon'
    post['author'] = name
    for key, value in AUTHOR_INFO[name].items():
        post['author_' + key] = value
    return post
