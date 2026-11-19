"""Limpeza de texto compartilhada entre os scripts de analise (03 e 04):
remove URLs, badges markdown e tags/entidades HTML de content do SKILL.md,
e centraliza a lista de stopwords de ruido especifico do dataset (metadados
de badge/GitHub, vocabulario de tooling do Claude Code)."""
from __future__ import annotations

import re

URL_RE = re.compile(r"https?://\S+")
MD_IMAGE_LINK_RE = re.compile(r"!?\[[^\]]*\]\([^)]*\)")
HTML_TAG_RE = re.compile(r"<[^>]+>")
HTML_ENTITY_RE = re.compile(r"&[a-z]+;")

# ruido comum em SKILL.md (markdown/HTML/metadados de badge, vocabulario de
# tooling do Claude Code) que nao ajuda a analise de conteudo de seguranca
EXTRA_STOPWORDS = {
    "use", "using", "used", "skill", "skills", "file", "files", "will",
    "one", "e.g", "etc", "based", "including", "name", "description",
    "github", "io", "com", "www", "src", "img", "style", "alt", "href",
    "svg", "td", "tr", "nbsp", "colspan", "shield", "shields", "flat",
    "square", "badge", "badges", "commit", "commits", "release", "releases",
    "fork", "forks", "star", "stars", "license", "readme", "blob", "master",
    "org", "json", "yml", "yaml", "html", "div", "span", "br", "url", "urls",
    "claude", "slash", "command", "commands", "workflow", "workflows",
    "knowledge", "guide", "guides", "phase", "step", "steps", "general",
    "tooling", "stats", "cli", "mcp", "md",
}


def clean_content(text: str) -> str:
    """Remove URLs, badges markdown e tags/entidades HTML de um content bruto."""
    text = MD_IMAGE_LINK_RE.sub(" ", text)
    text = URL_RE.sub(" ", text)
    text = HTML_TAG_RE.sub(" ", text)
    text = HTML_ENTITY_RE.sub(" ", text)
    return text
