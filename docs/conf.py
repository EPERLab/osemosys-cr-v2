# Configuration file for the Sphinx documentation builder.

# -- Project information

project = 'OSeMOSYS-CR-v2 '
copyright = '2021, EPER Lab'
author = 'EPER Lab'

release = '0.1'
version = '2.0.0'

# -- General configuration

extensions = [
    'sphinx.ext.duration',
    'sphinx.ext.doctest',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.intersphinx',    
    'sphinxcontrib.bibtex']

bibtex_bibfiles = ['Bibliography.bib']  

intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'sphinx': ('https://www.sphinx-doc.org/en/master/', None),
}
intersphinx_disabled_domains = ['std']

templates_path = ['_templates']

# -- Options for HTML output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

html_css_files = ["ccs/hacks.css"]
# -- Options for EPUB output
epub_show_urls = 'footnote'
