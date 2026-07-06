import os
import re
import subprocess
from CalendarLogger import logger
from ColorThemeGenerator import writeGeneratedColors

ASSETS_SRC = os.path.join(os.getcwd(), 'html-template/assets')

SCSS_DIR = os.path.join(ASSETS_SRC, 'scss')
SCSS_ENTRY = os.path.join(SCSS_DIR, 'minimal.scss')
CSS_OUTPUT = 'css/minimal.css'

JS_FILES = [
    'js/utility.js',
    'js/navigation.js',
    'js/filter.js',
    'js/bookmarks.js',
    'js/history.js',
    'js/events.js',
    'js/calendar.js',
    'js/theme.js',
    'js/init.js',
]

DART_SASS = os.path.join(os.getcwd(), 'node_modules/.bin/sass')
UGLIFYJS = os.path.join(os.getcwd(), 'node_modules/.bin/uglifyjs')


def compileSass(source_map=False, output_path=None):
    """Compile SCSS using Dart Sass. Returns CSS string, or (css, map) if source_map=True.
    output_path is the destination CSS file path (needed for correct source map paths)."""
    generated = writeGeneratedColors(SCSS_DIR)
    logger.debug('Wrote %s' % generated)

    if source_map:
        map_path = (output_path + '.map') if output_path else 'minimal.css.map'
        cmd = [DART_SASS, '--no-charset', '--source-map', SCSS_ENTRY, output_path]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            raise RuntimeError('Dart Sass failed: %s' % result.stderr.strip())
        with open(output_path) as f:
            css = f.read()
        with open(map_path) as f:
            srcmap = f.read()
        return css, srcmap

    cmd = [DART_SASS, '--no-charset', '--no-source-map', SCSS_ENTRY]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise RuntimeError('Dart Sass failed: %s' % result.stderr.strip())
    return result.stdout


def inlineCss():
    """Compile SCSS and return a single minified <style> block."""
    css = compileSass()
    return '<style>' + minifyCss(css) + '</style>'


def linkCss():
    """Return <link> tag pointing to compiled CSS (written by writeHtml)."""
    return '<link rel="stylesheet" href="assets/%s">' % CSS_OUTPUT


def inlineJs():
    """Concatenate all JS files and return a single minified <script> block."""
    parts = []
    for name in JS_FILES:
        with open(os.path.join(ASSETS_SRC, name)) as f:
            parts.append(f.read())
    return '<script>' + minifyJs('\n'.join(parts)) + '</script>'


def linkJs():
    """Return <script src> tags pointing to external JS files (for dev builds)."""
    return '\n'.join('<script src="assets/%s"></script>' % name for name in JS_FILES)


def minifyCss(text):
    """Naive CSS minifier: strip comments, collapse whitespace, remove
    unnecessary spaces around punctuation."""
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\s*([{}:;,>~+])\s*', r'\1', text)
    text = re.sub(r';}', '}', text)
    return text.strip()


def minifyJs(text):
    """Minify JS with uglify-js if available, otherwise fall back to naive minifier."""
    if os.path.isfile(UGLIFYJS):
        try:
            result = subprocess.run(
                [UGLIFYJS, '--compress', '--mangle'],
                input=text, capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout
            logger.warning('uglifyjs failed: %s' % result.stderr.strip())
        except Exception as e:
            logger.warning('uglifyjs unavailable: %s' % e)
    return _naiveMinifyJs(text)


def _naiveMinifyJs(text):
    """Fallback: strip // line comments and /* block comments */,
    then collapse blank lines. WARNING: this will destroy // inside string
    literals — use String.fromCharCode(47, 47) instead."""
    text = re.sub(r'//.*', '', text)
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    return '\n'.join(lines)
