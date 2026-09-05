from datetime import datetime

org = "harmonic-resonance"
org_name = "HARMONIC resonance"

repo = "groove"
repo_name = "groove"

blog_title = f'{org_name} • {repo_name}'
html_title = f'{org_name} • {repo_name}'
project = f'{org_name} • {repo_name}'
version = '0.1'
release = '0.1.0'

year = datetime.now().year
copyright = f'{year}, {org_name}'
author = f'{org_name}'

blog_baseurl = f'https://{org}.github.io/{repo}'
html_base_url = blog_baseurl
html_baseurl = blog_baseurl

blog_authors = {
    "phi": ("phi ARCHITECT", None),
}

html_context = {
    "display_github": True,
    "github_user": org,
    "github_repo": repo,
    "github_version": "main",
    "conf_py_path": "/docsrc/",
}
