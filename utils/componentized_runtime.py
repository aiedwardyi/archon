from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
from html import escape as html_escape
from pathlib import Path
from typing import Any

from utils.offline_engineer_scaffold import build_vite_react_ts_scaffold


TEXT_EXTENSIONS = {
    ".css",
    ".html",
    ".js",
    ".jsx",
    ".json",
    ".md",
    ".mjs",
    ".ts",
    ".tsx",
    ".txt",
    ".yml",
    ".yaml",
}

TEXT_FILENAMES = {
    ".gitignore",
    "index.html",
    "package.json",
    "README.md",
    "tsconfig.json",
    "tsconfig.node.json",
    "vite.config.ts",
}

NON_EDITABLE_COMPONENTIZED_FILENAMES = {
    "package-lock.json",
}

SKIP_DIRS = {
    ".git",
    ".npm-cache",
    ".vite",
    "__pycache__",
    "assets",
    "dist",
    "node_modules",
}

API_ASSET_URL_RE = re.compile(r"/api/assets/\d+/\d+/([^\"'()\s>]+)")
LOCAL_CODE_IMPORT_RE = re.compile(r'((?:from\s+|import\s*\(\s*|import\s+)[\"\'])(\.\.?/[^\"\']+?)\.(tsx|ts|jsx|js)([\"\'])')
BASE_CSS_IMPORT_LINE_RE = re.compile(r'^\s*import\s+[\"\'][^\"\']*base\.css[\"\'];?\s*$\n?', re.MULTILINE)
BASE_CSS_IMPORT_ANY_RE = re.compile(r'import\s+[\"\'][^\"\']*base\.css[\"\'];?\s*')
MAIN_BASE_CSS_IMPORT_RE = re.compile(
    r'^\s*import\s+[\"\'][^\"\']*base\.css[\"\'];?\s*(?:(?:/\*.*\*/)|(?://.*))?\s*$',
    re.MULTILINE,
)
MAIN_ENTRY_INVALID_IMPORT_NOTE_RE = re.compile(r"^\s*import\s+it(?:\b|[.])", re.IGNORECASE)
INLINE_COMMENT_RUNON_RE = re.compile(
    r"//\s*([^\n]*?)(?=(?:import\b|const|let|var|function|export\b|return\b|interface\b|type\b|class\b|use[A-Z]\w*|[A-Z][A-Za-z0-9_]*\s*[.(<]))"
)
INLINE_BLOCK_COMMENT_CODE_BLEED_RE = re.compile(
    r"/\*\s*(?P<comment>[^*]*?)\s{2,}(?P<prop>[A-Za-z_$][\w$]*)\s*:\s*(?P<prefix>[^*]*?)\*/\s*\n\s*",
    re.MULTILINE,
)
BLOCK_COMMENT_CONTROL_FLOW_BLEED_RE = re.compile(
    r"/\*\s*(?P<comment>[^*]*?)\s+(?P<code>(?:if\s*\([^*]+\)\s*\{|for\s*\([^*]+\)\s*\{|while\s*\([^*]+\)\s*\{|return\b[^*;{}]*[;{]|const\s+[A-Za-z_$][\w$]*\s*=|let\s+[A-Za-z_$][\w$]*\s*=|var\s+[A-Za-z_$][\w$]*\s*=|set[A-Z]\w*\s*\([^*]*\)))\s*\*/",
    re.MULTILINE,
)
UNTERMINATED_BLOCK_COMMENT_LINE_NOTE_RE = re.compile(
    r"(?P<indent>[ \t]*)/\*\s*(?P<comment>[^*\n]{2,240}?)\s*//\s*(?P<tail>[^*\n]{2,240}?)\s+(?P<code>(?:console\.[A-Za-z_$][\w$]*\s*\(|return\b|const\b|let\b|var\b|if\s*\(|for\s*\(|while\s*\(|switch\s*\(|set[A-Z]\w*\s*\(|[A-Za-z_$][\w$]*\s*=|[A-Za-z_$][\w$]*\s*\())(?P<rest>[^\n]*)",
    re.MULTILINE,
)
MULTILINE_BLOCK_COMMENT_LINE_NOTE_RE = re.compile(
    r"(?P<indent>[ \t]*)/\*\s*(?P<comment>[^*\n]{2,240}?)\s*\r?\n"
    r"(?P=indent)[ \t]*//\s*(?P<tail>[^*\n]{2,240}?)\s*\*/",
    re.MULTILINE,
)
INLINE_BLOCK_COMMENT_CONTINUATION_RE = re.compile(
    r"(?m)^(?P<prefix>[^\n]*?)/\*\s*(?P<comment>[^*\n]{2,240}?)\s{2,}(?P<code>(?:[)}\]],?\s*[^\n]*|[A-Za-z_:][-A-Za-z0-9_:.]*=\s*[^\n]*|[A-Za-z_$][\w$]*\s*:\s*[^\n]*|(?:const|let|var|return|if|for|while|switch)\b[^\n]*|set[A-Z]\w*\s*\([^\n]*))(?:\s*//\s*(?P<label>[^*\n]{2,200}?))?\s*(?:\*/)?\s*$",
    re.MULTILINE,
)
INLINE_BLOCK_COMMENT_SWALLOWED_CALL_RE = re.compile(
    r"(?m)^(?P<indent>[ \t]*)(?P<stmt>[^\n]*?;)\s*/\*\s*(?P<comment1>[^*\n]{1,200}?)\s+"
    r"(?P<callee>[A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)*\()\s*\*/\s*$\n"
    r"(?P=indent)(?P<argline>[^*\n]+?\)\s*;?)\s*/\*\s*(?P<comment2>[^*\n]{1,200}?)\s*\*/\s*$"
)
MULTILINE_BLOCK_COMMENT_CODE_START_RE = re.compile(
    r"(?:console\.[A-Za-z_$][\w$]*\s*\(|return\b|const\b|let\b|var\b|if\s*\(|for\s*\(|while\s*\(|switch\s*\(|set[A-Z]\w*\s*\(|[A-Za-z_$][\w$]*\s*=|[A-Za-z_$][\w$]*\s*\()"
)
INTERFACE_FIELD_COMMENT_BLEED_RE = re.compile(
    r"(?P<field>[A-Za-z_$][\w$]*\??\s*:\s*[^;{}\n]+;)\s*/\*\s*(?P<comment>[^*]*?)\}\s*\*/\s*\n(?=\s*(?:interface|type|const|let|var|function|export|class)\b)",
    re.MULTILINE,
)
RUNON_NATURAL_LANGUAGE_NOTE_RE = re.compile(
    r"(?:(?<=;)|(?<=\n)|^)\s*(?:Return|Note|Explanation|Data)\s*\((?P<note>[^)\n]{2,160})\)\s*(?=(?:const\b|let\b|var\b|return\b|set[A-Z]\w*\b|[A-Za-z_$][\w$]*\s*=))",
    re.MULTILINE,
)
RUNON_EXPLANATORY_LABEL_RE = re.compile(
    r"(?m)^(?P<label>[A-Za-z][A-Za-z0-9/&,\- ':]+(?:\([^)\n]{1,120}\))?)\s{2,}(?=(?:[)}]\s*)*(?:const\b|let\b|var\b|function\b|return\b|set[A-Z]\w*\b|[A-Za-z_$][\w$]*\s*=|[)}]))"
)
LOWERCASE_OBJECT_FIELD_LABEL_RE = re.compile(
    r"(?m)^(?P<indent>[ \t]*)(?P<label>[a-z][A-Za-z0-9/&,\- ']{2,120}?)\s{2,}(?P<field>[A-Za-z_$][\w$]*\s*:\s*[^\n]+)$"
)
BARE_SECTION_LABEL_RE = re.compile(
    r"(?m)^(?P<label>[A-Za-z][A-Za-z0-9/&,\- ':]+(?:\([^)\n]{1,120}\))?)\s*$\n(?=\s*(?:/\*|//|const|let|var|function|export|type|interface|class|return|if|for|while|switch|set[A-Z]\w*\(|[A-Za-z_$][\w$]*\(|[)}]))"
)
COMMENT_FILENAME_LABEL_RE = re.compile(
    r"(?m)^/\*\s*(?P<comment>[^*\n]{1,200}?)\s*\*/\s*$\n^(?P<filename>[A-Za-z0-9_-]+\.(?:tsx|ts|jsx|js|css|html|json|md))\s*$"
)
COMMENT_NOTE_CONTINUATION_RE = re.compile(
    r"(?m)^(?P<indent>[ \t]*)/\*\s*(?P<comment>[^*\n]{2,200}?)\s*\*/\s*$\n"
    r"(?P=indent)(?P<tail>[a-z][A-Za-z0-9_./&,\- '()]{6,180})\s*$\n"
    r"(?=(?P=indent)(?:const|let|var|function|export|type|interface|class)\b)"
)
INLINE_BLOCK_COMMENT_NOTE_CODE_BLEED_RE = re.compile(
    r"(?m)^(?P<prefix>[^\n]*?)/\*\s*(?P<comment>[^*\n]{1,80})\s*\*/\s*$\n"
    r"(?P<indent>[ \t]*)(?P<tail>[A-Za-z][A-Za-z0-9_./&,\- '()]{4,160}?)\s{2,}"
    r"(?P<code>(?:if\s*\(|for\s*\(|while\s*\(|const\b|let\b|var\b|return\b|set[A-Z]\w*\(|[A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)*\s*\()[^\n]*)"
)
UNTERMINATED_INLINE_BLOCK_COMMENT_RE = re.compile(
    r"(?m)^(?P<prefix>[^\n]*?(?:;|\)|\}|\]|\>))\s*/\*\s*(?P<comment>[^*\n]{2,240})$"
)
JSX_COMMENT_SWALLOWED_TAG_BOUNDARY_RE = re.compile(
    r"/\*\s*[\s\S]{0,320}?(?P<boundary>(?:/?>)\s*</[A-Za-z][A-Za-z0-9-]*>\s*<[A-Za-z][A-Za-z0-9-]*)\s*\*/",
    re.MULTILINE,
)
URL_PROTOCOL_COMMENT_BLEED_RE = re.compile(r"(?P<scheme>https?):/\*\s*")
ATTR_VALUE_ORPHAN_COMMENT_CLOSE_RE = re.compile(
    r"(?P<attr>[A-Za-z_:][-A-Za-z0-9_:.]*)=(?P<quote>[\"'])\s*\*/\s*"
)
TRAILING_SECTION_LINE_COMMENT_RE = re.compile(
    r"(?P<stmt>(?:\)\s*;|}\s*;))\s*//\s*(?P<label>[^*\n]{2,120}?)\s*\*/\s*(?=\r?\n\s*(?:const|function|export|type|interface|class))",
    re.MULTILINE,
)
ORPHAN_COMMENT_CLOSE_AFTER_STATEMENT_RE = re.compile(
    r"(?P<stmt>(?:\)\s*;|}\s*;|\]\s*;))\s*\*/(?=\s*(?:\r?\n\s*)?(?:const|function|export|type|interface|class|return|$))",
    re.MULTILINE,
)
CONTROL_FLOW_ORPHAN_COMMENT_CLOSE_RE = re.compile(
    r"(?P<prefix>\b(?:if|for|while|switch)\s*\()\s*\*/\s*(?:\r?\n\s*)?",
    re.MULTILINE,
)
BLOCK_COMMENT_SWALLOWED_ARRAY_CLOSE_RE = re.compile(
    r"/\*\s*(?P<comment>[\s\S]{0,600}?)\];\s*\*/\s*(?=\r?\n\s*(?:export|const|let|var|function|interface|type|class)\b)",
    re.MULTILINE,
)
COMMENT_SPLIT_IDENTIFIER_RE = re.compile(
    r"/\*\s*(?P<comment>[^*]*?)\s{2,}(?P<prefix>[a-z][A-Za-z0-9_$]{1,32})\s*\*/\s*\n(?P<suffix>[A-Z][A-Za-z0-9_$]{1,64})(?P<rest>[^\n]*)",
    re.MULTILINE,
)
COMMENT_TAIL_SPLIT_IDENTIFIER_RE = re.compile(
    r"/\*\s*(?P<expr>[^*\n]*?\.[a-z][A-Za-z0-9_$]{1,32})\s*\*/\s*\n(?P<suffix>[A-Z][A-Za-z0-9_$]{1,64})(?P<rest>[^\n]*)",
    re.MULTILINE,
)
ORPHAN_COMMENT_SPLIT_IDENTIFIER_RE = re.compile(
    r"(?<![A-Za-z0-9_$])(?P<prefix>[a-z][A-Za-z0-9_$]{1,32})\s*\*/\s*\n(?P<indent>[ \t]*)(?P<suffix>[A-Z][A-Za-z0-9_$]{1,64})(?P<rest>[^\n]*)",
    re.MULTILINE,
)
ORPHAN_COMMENT_SPLIT_DOTTED_IDENTIFIER_RE = re.compile(
    r"(?P<prefix>(?:[A-Za-z_$][\w$]*\.){1,6})\s*\*/\s*(?:\r?\n\s*)?(?P<suffix>[A-Za-z_$][\w$]{0,63})(?P<rest>[^\n]*)",
    re.MULTILINE,
)
ORPHAN_COMMENT_SPLIT_STRING_LITERAL_RE = re.compile(
    r"(?P<prefix>(?:\?|:|=|\(|,|\{)\s*)(?P<quote>['\"])\s*\*/\s*\n(?P<indent>[ \t]*)(?P<content>[^'\"\n]{1,120})(?P=quote)",
    re.MULTILINE,
)
JSX_EXPR_COMMENT_SPLIT_IDENTIFIER_RE = re.compile(
    r"\{(?P<prefix>[a-z][A-Za-z0-9_$]{1,32})\s*\*/\s*\n(?P<indent>[ \t]*)(?P<suffix>[A-Z][A-Za-z0-9_$]{1,64})(?P<rest>[^}]*)\}",
    re.MULTILINE,
)
ORPHAN_COMMENT_CLOSE_IN_STRING_LITERAL_RE = re.compile(
    r"(?P<prefix>(?:\[|,|:|=|\(|\{)\s*)(?P<quote>['\"])(?P<before>[^'\"\n]*?)\s*\*/\s*\n\s*(?P<after>[^'\"\n]*?)(?P=quote)",
    re.MULTILINE,
)
ALPINE_JSX_DIRECTIVE_NOTE_RE = re.compile(
    r"/\*\s*@ts-ignore\s*\*/\s*Alpine\.js specific directive",
    re.IGNORECASE,
)
ALPINE_JSX_DIRECTIVE_TEXT_RE = re.compile(
    r"\s*Alpine\.js specific directive",
    re.IGNORECASE,
)
ALPINE_JSX_ATTR_RE = re.compile(
    r"(?P<leading>\s+)(?:x-[A-Za-z0-9_.:-]+|@[A-Za-z0-9_.:-]+)\s*=\s*(?:\{`[^`]*`\}|\{[^{}]*\}|\"[^\"]*\"|'[^']*')",
    re.MULTILINE,
)
LINK_SELF_CLOSING_WITH_CHILDREN_RE = re.compile(
    r"<Link(?P<attrs>[^<>]*?)\s*/>(?P<inner>[\s\S]{0,2400}?)</Link>",
    re.MULTILINE,
)
LINK_WRAPPER_CLOSER_LEAK_RE = re.compile(
    r"<Link(?P<attrs>[^<>]*?)>(?P<body>[\s\S]{0,1800}?<svg\b[\s\S]{0,1200}?</svg>[\s\S]{0,200}?)(?P<closer></(?:div|nav|aside|main|section|article|header|footer)>)",
    re.MULTILINE,
)
SELF_CLOSING_LINK_WRAPPER_CLOSER_LEAK_RE = re.compile(
    r"<Link(?P<attrs>[^<>]*?)\s*/>(?P<body>[\s\S]{0,1800}?<svg\b[\s\S]{0,1200}?</svg>[\s\S]{0,200}?)(?P<closer></(?:div|nav|aside|main|section|article|header|footer)>)",
    re.MULTILINE,
)
ORPHAN_JSX_CLOSING_BRACE_LINE_RE = re.compile(
    r"(?m)^[ \t]*}\s*(?=\r?\n[ \t]*</[A-Za-z][A-Za-z0-9-]*>)"
)
JSX_BLOCK_COMMENT_BLEED_RE = re.compile(
    r"(?P<open>\(\s*)/\*\s*(?P<comment>[^*]*?)\s{2,}(?P<jsx><[A-Za-z][\s\S]*?)\{(?P<prefix>[a-z][A-Za-z0-9_$]{1,32})\s*\*/\s*\n(?P<indent>[ \t]*)(?P<suffix>[A-Z][A-Za-z0-9_$]{1,64})(?P<rest>[^\n]*)",
    re.MULTILINE,
)
JSX_TEXT_COMMENT_CLOSE_BLEED_RE = re.compile(
    r">(?P<prefix>[^<>{\n]{1,120}?)\s*\*/\s*(?:\r?\n\s*(?:\d+\s*\|\s*)?)?(?P<suffix>[A-Za-z][^<>{\n]{0,120}?)\s*<",
    re.MULTILINE,
)
JSX_CODE_TAG_RE = re.compile(
    r"(?P<open><code\b[^>]*>)(?P<body>[\s\S]{0,12000}?)(?P<close></code>)",
    re.IGNORECASE,
)
JSX_CODE_TEMPLATE_LITERAL_RE = re.compile(
    r"(?P<open><code\b[^>]*>\s*)\{\s*`(?P<body>[\s\S]{0,12000}?)`\s*\}(?P<close>\s*</code>)",
    re.IGNORECASE,
)
JSX_PRE_TEXT_TAG_RE = re.compile(
    r"(?P<open><pre\b[^>]*>)(?P<body>(?:(?!<code\b)[\s\S]){0,12000}?)(?P<close></pre>)",
    re.IGNORECASE,
)
INLINE_COMPONENT_SCRIPT_TAG_RE = re.compile(
    r"<script\b[^>]*>[\s\S]{0,20000}?</script>",
    re.IGNORECASE,
)
VOID_JSX_ELEMENT_RE = re.compile(
    r"(?<![A-Za-z0-9_\"'])<(?P<tag>area|base|br|col|embed|hr|img|input|link|meta|param|source|track|wbr"
    r"|circle|ellipse|line|path|polygon|polyline|rect|stop|use)\b(?P<attrs>[^<>]*?)(?<!/)>",
    re.IGNORECASE,
)
JSX_TAG_TOKEN_RE = re.compile(r"</?(?P<tag>[A-Za-z][A-Za-z0-9.-]*)\b[^>]*?/?>")
JSX_LINE_OPEN_TAG_RE = re.compile(r"^(?P<indent>[ \t]*)<(?P<tag>[A-Za-z][A-Za-z0-9.-]*)\b(?P<rest>[^>]*)>\s*$")
JSX_LINE_CLOSE_TAG_RE = re.compile(r"^(?P<indent>[ \t]*)</(?P<tag>[A-Za-z][A-Za-z0-9.-]*)>\s*$")
JSX_EVENT_HANDLER_ARROW_BLEED_RE = re.compile(
    r"(?P<prefix>\bon[A-Z][A-Za-z0-9_]*=\{\s*)(?P<param>\(?\s*[A-Za-z_$][\w$]*\s*\)?)\s*=\s*/>"
)
JSX_TYPED_EVENT_HANDLER_ARROW_BLEED_RE = re.compile(
    r"(?P<prefix>\bon[A-Z][A-Za-z0-9_]*=\{\s*\([^)]*\))\s*=\s*/>(?P<suffix>\s*\{)"
)
GENERIC_ARROW_BLEED_RE = re.compile(
    r"(?P<prefix>(?:\(|,)\s*)(?P<param>\(\s*[^)\n]{1,160}\)|[A-Za-z_$][\w$]*)\s*=\s*/>(?=\s*\S)"
)
RELATIONAL_OPERATOR_BLEED_RE = re.compile(
    r"(?P<prefix>[A-Za-z0-9_$\]})\"'])\s*/(?P<op>[<>])\s*=(?=\s*[-+0-9A-Za-z_(])"
)
TERNARY_BRANCH_START_RE = re.compile(r"(?P<marker>\?|:|&&|\|\|)\s*\(\s*$")
TERNARY_BRANCH_CLOSE_RE = re.compile(r"^\)\s*(?::\s*\(|(?:[)\]},;]+)?)\s*$")
TERNARY_BRANCH_SEPARATOR_RE = re.compile(r"^\)\s*:\s*\(\s*$")
MAP_BRANCH_START_RE = re.compile(r"\.map\([^\n]{0,240}?=>\s*\(\s*$")
MAP_BRANCH_CLOSE_RE = re.compile(r"^\)\)+\}\s*,?\s*$")
CSS_DATA_URI_ESCAPED_QUOTE_BLEED_RE = re.compile(
    r"\\'\\''(?=\s+[A-Za-z-]+=)"
)
JSX_ATTR_COMMENT_BLEED_RE = re.compile(
    r"(?P<attr>\b[A-Za-z_:][-A-Za-z0-9_:.]*=\{[^}\n]+\}|\b[A-Za-z_:][-A-Za-z0-9_:.]*=(?:\"[^\n\"]*\"|'[^\n']*'))\s*/\*\s*(?P<comment>[^*\n]{1,160})\s*\*/"
)
JSX_ATTR_LINE_COMMENT_BLEED_RE = re.compile(
    r"(?P<attr>\b[A-Za-z_:][-A-Za-z0-9_:.]*=\{[^}\n]+\}|\b[A-Za-z_:][-A-Za-z0-9_:.]*=(?:\"[^\n\"]*\"|'[^\n']*'))\s*//\s*(?P<comment>[^\n]{1,160})"
)
JSX_TEXT_LINE_COMMENT_CLOSE_BLEED_RE = re.compile(
    r"(?P<prefix></[A-Za-z][A-Za-z0-9.-]*>\s*)(?P<head>[^<>{}\n]{0,120}?)\s*\*/\s*(?:\r?\n\s*)?(?P<tail>[A-Za-z][^<>{}\n]{0,120})(?P<suffix>\s*</[A-Za-z])",
    re.MULTILINE,
)
DECLARATION_BOUNDARY_RE = re.compile(
    r"(?<=})(?=(?:interface\b|type\b|const\b|let\b|var\b|function\b|export\b|class\b|return\b))"
)
PACKAGE_IMPORT_RE = re.compile(
    r'^\s*(?:import(?:.+?\sfrom\s+)?|export.+?\sfrom\s+)[\"\']([^\"\']+)[\"\']',
    re.MULTILINE,
)
LOCAL_CSS_IMPORT_RE = re.compile(r'^\s*import\s+[\"\'](\.?\.?/[^\"\']+\.css)[\"\'];?', re.MULTILINE)
LOCAL_REL_IMPORT_RE = re.compile(
    r'(?:from\s+[\"\'](?P<from>\.{1,2}/[^\"\']+)[\"\']|import\s*\(\s*[\"\'](?P<dynamic>\.{1,2}/[^\"\']+)[\"\']\s*\)|import\s+[\"\'](?P<bare>\.{1,2}/[^\"\']+)[\"\'])'
)
EMPTY_CURRENCY_FORMAT_ARG_RE = re.compile(
    r"formatCurrency\(\s*(?P<value>[^,\n]+?)\s*,\s*['\"]\s*['\"]\s*\)"
)
FORMAT_CURRENCY_GUARD_RE = re.compile(r"currency\s*:\s*currency\b")
GOOGLE_FONT_IMPORT_RE = re.compile(r"https://fonts\.googleapis\.com/[^\s\"')]+")
CSS_VARIABLE_RE = re.compile(r"(--[\w-]+)\s*:\s*([^;}{]+);")
HEX_COLOR_RE = re.compile(r"#[0-9a-fA-F]{3,8}\b")
KEYFRAME_RE = re.compile(r"@keyframes\s+([A-Za-z_][\w-]*)")
JSON_ESCAPE_NOISE_RE = re.compile(r"\\[nrt]")
GENERATED_ASSET_REFERENCE_RE = re.compile(
    r"(?:^|[\"'(\s=])(?:\./)?generated-assets/(?P<filename>[^\"')\s]+)",
    re.IGNORECASE,
)
REMOTE_OBJECT_IMAGE_URL_RE = re.compile(
    r"(?P<prefix>\b(?:image|imageUrl|imageSrc|src)\s*:\s*)(?P<quote>['\"])(?P<url>https?://[^'\"\n]+)(?P=quote)",
    re.IGNORECASE,
)
REMOTE_NAMED_OBJECT_IMAGE_URL_RE = re.compile(
    r"(?P<prefix>\{[\s\S]{0,260}?\bname\s*:\s*(?P<name_quote>['\"])(?P<name>[^'\"]+)(?P=name_quote)[\s\S]{0,260}?\b(?:image|imageUrl|imageSrc|src)\s*:\s*)(?P<quote>['\"])(?P<url>https?://[^'\"\n]+)(?P=quote)",
    re.IGNORECASE,
)
REMOTE_JSX_IMAGE_SRC_RE = re.compile(
    r"(?P<prefix><img[^>]*?\bsrc=)(?P<quote>['\"])(?P<url>https?://[^'\"\n>]+)(?P=quote)(?P<rest>[^>]*>)",
    re.IGNORECASE,
)
REMOTE_BADGE_OBJECT_IMAGE_RE = re.compile(
    r"(?P<prefix>\{\s*name\s*:\s*(?P<name_quote>['\"])(?P<name>[^'\"]+)(?P=name_quote)(?P<body>[\s\S]{0,260}?image\s*:\s*))(?P<url_quote>['\"])(?P<url>https?://[^'\"]+)(?P=url_quote)",
    re.IGNORECASE,
)
RUNTIME_GENERATED_ASSET_REFERENCE_RE = re.compile(
    r'(?P<prefix>^|["\'(\s=,:])(?P<path>(?:\./)?/?generated-assets/(?P<subpath>[^"\'\s)]+))',
    re.IGNORECASE,
)
FONT_FAMILY_RE = re.compile(r"font-family\s*:\s*([^;}{]+);")
BORDER_RADIUS_RE = re.compile(r"border-radius\s*:\s*([^;}{]+);")
BOX_SHADOW_RE = re.compile(r"box-shadow\s*:\s*([^;}{]+);")
MEDIA_QUERY_RE = re.compile(r"@media[^{]*?(?:max|min)-width\s*:\s*([0-9]+px)", re.IGNORECASE)
INVALID_SEVEN_DIGIT_HEX_RE = re.compile(r"#(?P<value>[0-9a-fA-F]{7})(?![0-9a-fA-F])")
SVG_XMLNS_PROTOCOL_SLASH_RE = re.compile(
    r'(?P<prefix>\bxmlns\s*=\s*)(?P<quote>["\'])(?P<scheme>https?):(?P<rest>(?!//)[^"\']+)(?P=quote)'
)
MISSING_PROTOCOL_SLASH_JSX_ATTR_RE = re.compile(
    r'(?P<prefix>\b(?:src|href)=["\'])(?P<scheme>https?):(?P<rest>(?!//)[^"\']+)(?P<suffix>["\'])',
    re.IGNORECASE,
)
MISSING_PROTOCOL_SLASH_OBJECT_FIELD_RE = re.compile(
    r'(?P<prefix>\b(?:src|href|image|imageUrl|imageSrc)\s*:\s*["\'])(?P<scheme>https?):(?P<rest>(?!//)[^"\']+)(?P<suffix>["\'])',
    re.IGNORECASE,
)
JS_EVENT_HANDLER_RE = re.compile(r"\bon(Click|Change|Submit|Input|KeyDown|KeyUp|MouseEnter|MouseLeave|Focus|Blur)\s*=")
DOM_EVENT_LISTENER_RE = re.compile(r"addEventListener\(\s*['\"]([a-z]+)['\"]")
CSS_BLOCK_RE = re.compile(r"(?P<selector>[^{}]+)\{(?P<body>[^{}]*)\}", re.MULTILINE)
GOOGLE_FONT_IMPORT_LINE_RE = re.compile(r"^\s*@import\s+url\([^)]+fonts\.googleapis\.com[^)]*\)\s*;\s*$", re.MULTILINE)
LIGHTWEIGHT_CHART_CANDLE_HELPER_RE = re.compile(
    r"const generateRandomCandlestickData = \(count: number, basePrice: number\): CandlestickData\[\] => \{[\s\S]{0,2400}?return data;\};",
    re.MULTILINE,
)
LIGHTWEIGHT_CHART_LINE_HELPER_RE = re.compile(
    r"const generateLineData = \(count: number, basePrice: number\): LineData\[\] => \{[\s\S]{0,2400}?return data;\};",
    re.MULTILINE,
)
LIGHTWEIGHT_CHART_DATA_CALLBACK_RE = re.compile(
    r"const getChartDataForSymbol = useCallback\(\(symbol: string, timeframe: typeof chartTimeframe\) => \{[\s\S]{0,2400}?\}, \[\]\);",
    re.MULTILINE,
)
LIGHTWEIGHT_CHART_SETUP_EFFECT_RE = re.compile(
    r"useEffect\(\(\) => \{\s*if \(chartContainerRef\.current\) \{\s*if \(!chartRef\.current\) \{[\s\S]{0,3200}?\}\s*\}, \[currentChartData, currentVolumeData\]\);",
    re.MULTILINE,
)
DUPLICATE_LABEL_OBJECT_FIELD_RE = re.compile(
    r"(?P<prefix>\{[^{}]{0,240}\blabel\s*:\s*['\"][^'\"]+['\"][^{}]{0,240}),\s*label\s*:\s*(?P<value>['\"][^'\"]+['\"])",
    re.MULTILINE,
)
COMMENTED_DESTRUCTURED_PROP_RE = re.compile(
    r"^(?P<indent>[ \t]*)/\*\s*(?P<name>[A-Za-z_$][\w$]*)\s*,?\s*\*/\s*$",
    re.MULTILINE,
)
SPLIT_STATE_SETTER_RE = re.compile(
    r"(?P<prefix>\bset)\s*\n\s*(?P<rest>[A-Z][A-Za-z0-9_$]+)(?=\s*\()",
    re.MULTILINE,
)
SPLIT_CAMEL_IDENTIFIER_OPERATOR_RE = re.compile(
    r"(?P<prefix>\b[a-z][A-Za-z0-9_$]{1,32})\s+(?P<suffix>[A-Z][A-Za-z0-9_$]{1,32})(?=\s*(?:<=|>=|===|==|!==|!=|<|>))"
)
ORPHAN_PROSE_COMMENT_LINE_RE = re.compile(
    r"^(?P<indent>[ \t]*)(?P<prose>[A-Z][A-Za-z0-9$%/(),.:'` =+\-<>]{8,240}?)(?:\s*/\*\s*(?P<tail>[^\n]{1,240}?)\s*\*/)?\s*$",
    re.MULTILINE,
)
SINGLE_LINE_JSX_TAG_RE = re.compile(
    r"<(?P<tag>[A-Za-z][A-Za-z0-9.-]*)\b(?P<body>[^<>\n]*?)(?P<self_close>/?)>",
    re.MULTILINE,
)
JSX_ATTRIBUTE_TOKEN_RE = re.compile(
    r"(?P<leading>\s+)(?P<name>[A-Za-z_:][-A-Za-z0-9_:.]*)(?P<value>\s*=\s*(?:\{[^{}\n]*\}|\"[^\n\"]*\"|'[^\n']*'))",
    re.MULTILINE,
)
COMPONENT_SELF_CLOSING_WITH_CHILDREN_RE = re.compile(
    r"<(?P<tag>[A-Z][A-Za-z0-9.]*)\b(?P<attrs>[\s\S]{0,800}?)\s*/>(?P<inner>[\s\S]{1,5000}?)</(?P=tag)>",
    re.MULTILINE,
)
LOGICAL_SVG_SIBLING_CONDITION_RE = re.compile(
    r"\{(?P<expr>[^{}\n]{1,240}?&&)\s*(?P<first><(?:path|circle|rect|line|polyline|polygon|ellipse|g|text|use)\b[^>]*/>)(?P<siblings>(?:\s*<(?:path|circle|rect|line|polyline|polygon|ellipse|g|text|use)\b[^>]*/>)+)\s*\}",
    re.MULTILINE,
)
BARE_JSX_ARRAY_MAP_EXPRESSION_RE = re.compile(
    r"(?P<prefix>\{/\*[^*\n]{1,200}\*/\})(?P<expr>\[[^\n]{1,240}?\]\.map\([\s\S]{1,1600}?\)\))(?P<suffix>\})",
    re.MULTILINE,
)
INLINE_JSX_ATTRIBUTE_BLOCK_COMMENT_RE = re.compile(
    r"(?P<attr>\b[A-Za-z_:][-A-Za-z0-9_:.]*\s*=\s*(?:\{[^{}\n]*\}|\"[^\n\"]*\"|'[^\n']*'))\s*/\*[\s\S]{0,200}?(?=\s+[A-Za-z_:][-A-Za-z0-9_:.]*\s*=)",
    re.MULTILINE,
)
ORPHAN_SVG_PROP_CLOSER_LINE_RE = re.compile(
    r"(?m)^(?P<indent>[ \t]*)</svg>\s*$\n(?P=indent)(?P<prop>[A-Za-z_$][\w$]*=\{<svg\b)"
)
ROUTE_PATH_COMMENT_BLEED_RE = re.compile(
    r"(?P<prefix><Route\b[\s\S]{0,320}?\bpath\s*=\s*)(?P<quote>[\"'])(?P<value>[^\"'\n]*?/\*[^\"'\n]*?)(?P=quote)",
    re.MULTILINE,
)
COMPONENTIZED_JSX_RETURN_RE = re.compile(
    r"return\s*\(\s*(?P<body><[\s\S]{1,12000}?)\s*\);",
    re.MULTILINE,
)
REACT_ICONS_FEATHER_IMPORT_RE = re.compile(
    r"import\s*\{(?P<names>[\s\S]*?)\}\s*from\s*(?P<quote>['\"])react-icons/fi(?P=quote)\s*;?",
    re.MULTILINE,
)

SAFE_COMPONENTIZED_DEPENDENCIES = {
    "@heroicons/react": "^2.2.0",
    "clsx": "^2.1.1",
    "lucide-react": "^0.564.0",
    "react-feather": "^2.0.10",
    "recharts": "2.15.0",
}

SAFE_COMPONENTIZED_RESPONSIVE_TAIL = """/* Responsive Adjustments */
@media (max-width: 1200px) {
  .kpi-grid {
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  }
  .grid-2col,
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
  .main-content {
    margin-left: 240px;
  }
  .content-area {
    padding: var(--spacing-xxl) var(--spacing-lg);
  }
  .activity-feed {
    position: static;
    max-height: 400px;
    overflow-y: auto;
  }
  .header-bar {
    padding: 0 var(--spacing-lg);
  }
  .sidebar {
    border-right: none;
  }
}

@media (max-width: 768px) {
  .sidebar {
    display: none;
  }
  .main-content {
    margin-left: 0;
  }
  .header-bar {
    flex-direction: column;
    height: auto;
    padding: var(--spacing-md) var(--spacing-lg);
    gap: var(--spacing-md);
    align-items: flex-start;
  }
  .header-actions {
    width: 100%;
    justify-content: space-between;
    gap: var(--spacing-sm);
  }
  .header-search {
    min-width: unset;
    flex-grow: 1;
  }
  .content-area {
    padding: var(--spacing-xxl) var(--spacing-md);
  }
  .kpi-grid {
    grid-template-columns: 1fr;
  }
  .data-table th,
  .data-table td {
    padding: var(--spacing-sm) var(--spacing-md);
    font-size: 0.8rem;
  }
  .data-table .cell-action {
    font-size: 0.7rem;
  }
  .activity-feed {
    padding: var(--spacing-lg) var(--spacing-md);
  }
  .activity-item {
    padding: var(--spacing-sm) var(--spacing-md);
  }
  .chart-header {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--spacing-md);
  }
  .chart-actions {
    flex-direction: column;
    width: 100%;
  }
  .chart-period-toggles {
    width: 100%;
    justify-content: space-around;
  }
  .interactive-chip {
    width: 100%;
    justify-content: center;
  }
}
"""

COMPONENTIZED_MODULE_EXTENSIONS = (".tsx", ".ts", ".jsx", ".js")
COMPONENTIZED_REACT_ICON_EXPORT_ALIASES: dict[str, str] = {
    "FiUndo": "FiRotateCcw",
    "FiRedo": "FiRotateCw",
}
COMPONENTIZED_IMPORT_ALIAS_CANDIDATES: dict[str, tuple[str, ...]] = {
    "CharacterCards": ("CharacterSection",),
    "Characters": ("CharacterSection",),
    "Hero": ("HeroSection",),
    "HeroBanner": ("HeroSection",),
    "MapSection": ("WorldMap",),
    "NavBar": ("Navbar",),
    "SiteFooter": ("Footer",),
    "WeaponGallery": ("WeaponShowcase", "WeaponSection"),
    "WeaponSection": ("WeaponShowcase",),
    "Weapons": ("WeaponShowcase", "WeaponSection"),
    "WorldMapSection": ("WorldMap",),
}

DISPLAY_SELECTOR_HINTS = (
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    ".page-title",
    ".section-title",
    ".chart-title",
    ".panel-title",
    ".topbar-brand",
    ".logo-text",
    ".feed-header",
)

OVERRIDE_DISPLAY_FONT_RE = re.compile(r"(--font-display\s*:\s*)'Inter'[^;]*;", re.IGNORECASE)
NUMERIC_SELECTOR_HINTS = (
    ".kpi-value",
    ".kpi-delta",
    ".ticker-price",
    ".ticker-delta",
    ".watch-price",
    ".watch-delta",
    ".feed-time",
    ".asset-table td",
    ".table-number",
    ".numeric",
    ".price",
    ".delta",
)
MAIN_CSS_IMPORT_LINE_RE = re.compile(r'^\s*import\s+["\'](?P<path>\./[^"\']+\.css)["\'];?\s*(?:(?:/\*.*\*/)|(?://.*))?\s*$')
MAIN_ENTRY_PREFERRED_CSS_ORDER = ("./index.css", "./style.css", "./styles.css", "./base.css")
POLISH_GUARD_IMPORT = "./polish-guard.css"
POLISH_GUARD_RUNTIME_IMPORT = "./polish-guard"
POLISH_GUARD_ARCHETYPES = {"dashboard", "fintech", "game"}
COMPONENTIZED_UTILITY_FALLBACKS: dict[str, str] = {
    "font-display": "font-family: var(--font-display, 'Space Grotesk', 'Inter', sans-serif); letter-spacing: -0.02em;",
    "font-body": "font-family: var(--font-body, 'Inter', sans-serif);",
    "font-mono": "font-family: var(--font-mono, 'JetBrains Mono', monospace); font-variant-numeric: tabular-nums;",
    "text-color-primary-text": "color: var(--color-primary-text, var(--text, #f4f8fc));",
    "text-color-secondary-text": "color: var(--color-secondary-text, var(--text-secondary, #b8c6d8));",
    "text-color-muted-text": "color: var(--color-muted-text, var(--text-muted, #6f7f95));",
    "text-color-primary-accent": "color: var(--color-primary-accent, var(--accent, #10b981));",
    "text-color-success": "color: var(--color-success, var(--accent, #10b981));",
    "text-color-danger": "color: var(--color-danger, #f87171);",
    "text-h1": "font-family: var(--font-display, 'Space Grotesk', 'Inter', sans-serif); font-size: var(--font-size-h1, clamp(2.5rem, 4vw, 3.5rem)); line-height: 1.05;",
    "text-h2": "font-family: var(--font-display, 'Space Grotesk', 'Inter', sans-serif); font-size: var(--font-size-h2, clamp(1.875rem, 3vw, 2.5rem)); line-height: 1.1;",
    "text-h3": "font-family: var(--font-display, 'Space Grotesk', 'Inter', sans-serif); font-size: var(--font-size-h3, clamp(1.25rem, 2vw, 1.75rem)); line-height: 1.2;",
    "top-1/2": "top: 50%;",
    "-translate-y-1/2": "transform: translateY(-50%);",
}
COMPONENTIZED_UTILITY_FALLBACK_MARKER = "/* Generated componentized utility fallbacks */"
COMPONENTIZED_FIELD_ALIAS_GROUPS: tuple[tuple[str, ...], ...] = (
    ("changePercent", "change24hPercent", "dayChangePercent"),
    ("change", "change24h", "dayChange"),
    ("price", "priceUsd", "assetPrice"),
    ("value", "valueUsd", "totalValueUsd"),
)


def infer_scaffold_mode(code_dir: Path, plan_data: dict[str, Any] | None = None) -> str:
    if plan_data:
        for milestone in plan_data.get("milestones", []):
            for task in milestone.get("tasks", []):
                if task.get("execution_hint") == "engineer":
                    mode = str(task.get("scaffold_mode") or "").strip()
                    if mode:
                        return mode

    package_json = code_dir / "package.json"
    if package_json.exists():
        return "componentized_app"
    return "legacy_single_page"


def is_componentized_workspace(code_dir: Path, plan_data: dict[str, Any] | None = None) -> bool:
    return infer_scaffold_mode(code_dir, plan_data=plan_data) == "componentized_app"


def collect_existing_code_context(
    code_dir: Path,
    *,
    max_files: int = 48,
    max_chars_per_file: int = 24_000,
) -> str | None:
    if not code_dir.exists():
        return None

    rendered: list[str] = []
    file_count = 0

    for path in sorted(code_dir.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(code_dir).as_posix()
        if any(part in SKIP_DIRS for part in path.relative_to(code_dir).parts[:-1]):
            continue
        if rel.startswith("assets/"):
            continue

        name = path.name
        if name in NON_EDITABLE_COMPONENTIZED_FILENAMES:
            continue
        if path.suffix.lower() not in TEXT_EXTENSIONS and name not in TEXT_FILENAMES:
            continue

        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        if len(content) > max_chars_per_file:
            content = content[:max_chars_per_file] + "\n/* TRUNCATED FOR CONTEXT */\n"

        rendered.append(f"--- FILE: {rel} ---\n{content}\n--- END FILE ---")
        file_count += 1
        if file_count >= max_files:
            rendered.append("--- NOTE: Additional files omitted for context size. ---")
            break

    if not rendered:
        return None
    return "\n\n".join(rendered)


def collect_selected_code_context(
    code_dir: Path,
    rel_paths: list[str],
    *,
    max_chars_per_file: int = 24_000,
) -> str | None:
    rendered: list[str] = []
    for rel_path in rel_paths:
        normalized = rel_path.replace("\\", "/").strip("/")
        if not normalized:
            continue
        path = code_dir / normalized
        if not path.exists() or not path.is_file():
            continue
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if len(content) > max_chars_per_file:
            content = content[:max_chars_per_file] + "\n/* TRUNCATED FOR CONTEXT */\n"
        rendered.append(f"--- FILE: {normalized} ---\n{content}\n--- END FILE ---")
    if not rendered:
        return None
    return "\n\n".join(rendered)


def _collect_workspace_text_blob(code_dir: Path, *, max_chars_per_file: int = 24_000) -> str:
    if not code_dir.exists():
        return ""

    chunks: list[str] = []
    for rel_path in collect_componentized_editable_files(code_dir):
        path = code_dir / rel_path
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if len(content) > max_chars_per_file:
            content = content[:max_chars_per_file]
        chunks.append(content)
    return "\n".join(chunks)


def _limited_sorted_set(values: Any, *, limit: int) -> list[str]:
    seen: list[str] = []
    for value in values:
        normalized = str(value).strip()
        if not normalized or normalized in seen:
            continue
        seen.append(normalized)
        if len(seen) >= limit:
            break
    return sorted(seen)


def extract_visual_dna(code_dir: Path) -> dict[str, Any]:
    combined = _collect_workspace_text_blob(code_dir)
    if not combined:
        return {
            "google_font_imports": [],
            "font_families": [],
            "css_variables": {},
            "hex_colors": [],
            "keyframes": [],
            "radius_values": [],
            "shadow_values": [],
        }

    css_variables: dict[str, str] = {}
    for name, value in CSS_VARIABLE_RE.findall(combined):
        if name not in css_variables and len(css_variables) < 48:
            css_variables[name] = " ".join(value.strip().split())

    return {
        "google_font_imports": _limited_sorted_set(GOOGLE_FONT_IMPORT_RE.findall(combined), limit=8),
        "font_families": _limited_sorted_set(
            (" ".join(match.strip().split()) for match in FONT_FAMILY_RE.findall(combined)),
            limit=16,
        ),
        "css_variables": css_variables,
        "hex_colors": _limited_sorted_set((value.lower() for value in HEX_COLOR_RE.findall(combined)), limit=32),
        "keyframes": _limited_sorted_set(KEYFRAME_RE.findall(combined), limit=24),
        "radius_values": _limited_sorted_set(
            (" ".join(match.strip().split()) for match in BORDER_RADIUS_RE.findall(combined)),
            limit=16,
        ),
        "shadow_values": _limited_sorted_set(
            (" ".join(match.strip().split()) for match in BOX_SHADOW_RE.findall(combined)),
            limit=16,
        ),
    }


def extract_feature_inventory(code_dir: Path) -> dict[str, Any]:
    combined = _collect_workspace_text_blob(code_dir)
    normalized = combined.lower()
    if not combined:
        return {
            "event_handlers": [],
            "responsive_breakpoints": [],
            "detected_features": [],
            "polish_features": [],
        }

    event_handlers = {
        event.lower()
        for event in JS_EVENT_HANDLER_RE.findall(combined)
    }
    event_handlers.update(DOM_EVENT_LISTENER_RE.findall(normalized))

    feature_patterns = {
        "tabs": ("data-tab", "activetab", "role=\"tab\"", "tablist"),
        "filters": ("filtered", "setfilter", "categoryfilter", "filterpill"),
        "search": ("searchquery", "setsearch", "searchterm", "searchinput", 'aria-label="search', 'placeholder="search'),
        "cart": ("addtocart", "cartitems", "setcart", "subtotal"),
        "wishlist": ("wishlist", "saveditems"),
        "loyalty": ("loyalty", "reward points", "rewards tier", "points balance"),
        "modal_or_dialog": ("modal", "dialog", "aria-modal"),
        "drawer_or_sheet": ("drawer", "sheet", "slideover"),
        "accordion": ("accordion", "expandedindex", "faq-item"),
        "carousel": ("carousel", "current slide", "setcurrentslide"),
        "toast_notifications": ("toast", "notification", "showtoast"),
        "form_validation": ("onsubmit", "seterrors", "validation", "error message"),
        "mobile_nav": ("mobilemenu", "nav-open", "setismenuopen", "hamburger"),
        "scroll_reveal": ("intersectionobserver", "scrollreveal", "reveal-on-scroll"),
        "chart_state": ("recharts", "chart", "selectedrange", "sparkline", "tooltip"),
        "table_sorting": ("sortconfig", "sortkey", "sortdirection", "sortable"),
        "table_filtering": ("filteredrows", "filteredtransactions", "filteredcustomers"),
        "range_selector": ("7d", "30d", "90d", "1y", "selectedrange"),
        "watchlist": ("watchlist", "watch list"),
        "game_loop": ("streak", "score", "nextquestion", "difficulty"),
    }

    detected_features = [
        feature
        for feature, signals in feature_patterns.items()
        if any(signal in normalized for signal in signals)
    ]

    polish_patterns = {
        "custom_scrollbar": ("::-webkit-scrollbar", "scrollbar-width"),
        "selection_styling": ("::selection",),
        "sticky_header": ("position: sticky", "sticky top"),
        "count_up_numbers": ("countup", "requestanimationframe", "animatevalue"),
        "animated_gradients": ("linear-gradient", "radial-gradient", "background-size"),
    }
    polish_features = [
        feature
        for feature, signals in polish_patterns.items()
        if any(signal in normalized for signal in signals)
    ]

    return {
        "event_handlers": _limited_sorted_set(event_handlers, limit=16),
        "responsive_breakpoints": _limited_sorted_set(MEDIA_QUERY_RE.findall(combined), limit=12),
        "detected_features": detected_features[:24],
        "polish_features": polish_features[:16],
    }


def build_componentized_preview(
    code_dir: Path,
    *,
    timeout_seconds: int = 180,
) -> dict[str, Any]:
    package_json = code_dir / "package.json"
    if not package_json.exists():
        return {
            "status": "skipped",
            "reason": "package.json not found",
            "dist_index": None,
        }

    npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
    env = os.environ.copy()
    env.setdefault("CI", "1")
    npm_cache_dir = code_dir / ".npm-cache"
    npm_cache_dir.mkdir(parents=True, exist_ok=True)
    env.setdefault("npm_config_cache", str(npm_cache_dir))
    env.setdefault("NPM_CONFIG_CACHE", str(npm_cache_dir))

    commands: list[list[str]] = []
    install_required = not (code_dir / "node_modules").exists()
    if install_required:
        commands.append([npm_cmd, "install"])
    commands.append([npm_cmd, "run", "build"])

    logs: list[dict[str, Any]] = []
    try:
        for command in commands:
            completed = subprocess.run(
                command,
                cwd=code_dir,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                env=env,
                check=False,
            )
            logs.append(
                {
                    "command": command,
                    "returncode": completed.returncode,
                    "stdout": completed.stdout[-12_000:],
                    "stderr": completed.stderr[-12_000:],
                }
            )
            if completed.returncode != 0:
                if install_required and command[:2] == [npm_cmd, "install"] and "ERESOLVE" in (completed.stderr or ""):
                    retry_command = [npm_cmd, "install", "--legacy-peer-deps"]
                    retry = subprocess.run(
                        retry_command,
                        cwd=code_dir,
                        capture_output=True,
                        text=True,
                        timeout=timeout_seconds,
                        env=env,
                        check=False,
                    )
                    logs.append(
                        {
                            "command": retry_command,
                            "returncode": retry.returncode,
                            "stdout": retry.stdout[-12_000:],
                            "stderr": retry.stderr[-12_000:],
                        }
                    )
                    if retry.returncode == 0:
                        continue
                missing_safe_dependency = None
                if command[:3] == [npm_cmd, "run", "build"]:
                    missing_safe_dependency = _extract_missing_safe_dependency(completed)
                if missing_safe_dependency:
                    reinstall_command = [npm_cmd, "install"]
                    reinstall = subprocess.run(
                        reinstall_command,
                        cwd=code_dir,
                        capture_output=True,
                        text=True,
                        timeout=timeout_seconds,
                        env=env,
                        check=False,
                    )
                    logs.append(
                        {
                            "command": reinstall_command,
                            "returncode": reinstall.returncode,
                            "stdout": reinstall.stdout[-12_000:],
                            "stderr": reinstall.stderr[-12_000:],
                        }
                    )
                    if reinstall.returncode == 0:
                        retry = subprocess.run(
                            command,
                            cwd=code_dir,
                            capture_output=True,
                            text=True,
                            timeout=timeout_seconds,
                            env=env,
                            check=False,
                        )
                        logs.append(
                            {
                                "command": command,
                                "returncode": retry.returncode,
                                "stdout": retry.stdout[-12_000:],
                                "stderr": retry.stderr[-12_000:],
                            }
                        )
                        if retry.returncode == 0:
                            continue
                if command[:3] == [npm_cmd, "run", "build"] and _should_retry_with_vite_build(completed, code_dir):
                    retry_command = [npm_cmd, "exec", "vite", "build"]
                    retry = subprocess.run(
                        retry_command,
                        cwd=code_dir,
                        capture_output=True,
                        text=True,
                        timeout=timeout_seconds,
                        env=env,
                        check=False,
                    )
                    logs.append(
                        {
                            "command": retry_command,
                            "returncode": retry.returncode,
                            "stdout": retry.stdout[-12_000:],
                            "stderr": retry.stderr[-12_000:],
                        }
                    )
                    if retry.returncode == 0:
                        continue
                return {
                    "status": "error",
                    "reason": f"{' '.join(command)} failed",
                    "dist_index": None,
                    "logs": logs,
                }
    except FileNotFoundError:
        return {
            "status": "error",
            "reason": f"{npm_cmd} not found",
            "dist_index": None,
            "logs": logs,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "status": "error",
            "reason": f"Build timed out after {timeout_seconds}s",
            "dist_index": None,
            "logs": logs + [{"command": exc.cmd, "returncode": None, "stdout": "", "stderr": "timeout"}],
        }

    dist_index = code_dir / "dist" / "index.html"
    if dist_index.exists():
        _make_dist_index_portable(dist_index)
    return {
        "status": "success" if dist_index.exists() else "error",
        "reason": None if dist_index.exists() else "dist/index.html not found after build",
        "dist_index": str(dist_index) if dist_index.exists() else None,
        "logs": logs,
    }


def _should_retry_with_vite_build(completed: subprocess.CompletedProcess[str], code_dir: Path) -> bool:
    stdout = completed.stdout or ""
    stderr = completed.stderr or ""
    combined = f"{stdout}\n{stderr}"
    if "The TypeScript Compiler - Version" not in combined:
        return False
    if (code_dir / "tsconfig.json").exists():
        return False
    return True


def _extract_missing_safe_dependency(completed: subprocess.CompletedProcess[str]) -> str | None:
    combined = f"{completed.stdout or ''}\n{completed.stderr or ''}"
    match = re.search(
        r'failed to resolve import ["\'](?P<package>[^"\']+)["\']|Could not resolve ["\'](?P<package_alt>[^"\']+)["\']',
        combined,
        re.IGNORECASE,
    )
    if not match:
        return None
    package_name = (match.group("package") or match.group("package_alt") or "").strip()
    if package_name in SAFE_COMPONENTIZED_DEPENDENCIES:
        return package_name
    return None


def collect_componentized_editable_files(code_dir: Path) -> list[str]:
    editable_files: list[str] = []
    if not code_dir.exists():
        return editable_files

    for path in sorted(code_dir.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(code_dir)
        if any(part in SKIP_DIRS for part in rel.parts[:-1]):
            continue
        name = path.name
        if name in NON_EDITABLE_COMPONENTIZED_FILENAMES:
            continue
        if path.suffix.lower() not in TEXT_EXTENSIONS and name not in TEXT_FILENAMES:
            continue
        editable_files.append(rel.as_posix())
    return editable_files


def collect_componentized_direct_dependencies(
    code_dir: Path,
    rel_paths: list[str],
    *,
    max_depth: int = 1,
) -> list[str]:
    root = code_dir.resolve()
    discovered: set[str] = set()
    pending: list[tuple[str, int]] = [
        (path.replace("\\", "/").strip("/"), 0) for path in rel_paths if path
    ]
    seen: set[str] = set()

    while pending:
        rel_path, depth = pending.pop(0)
        if rel_path in seen or depth >= max_depth:
            seen.add(rel_path)
            continue
        seen.add(rel_path)

        source_path = code_dir / rel_path
        if not source_path.exists() or not source_path.is_file():
            continue
        try:
            source = source_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        for raw_import in _iter_local_import_specifiers(source):
            resolved_rel = _resolve_local_import_path(code_dir, rel_path, raw_import)
            if not resolved_rel or resolved_rel in seen:
                continue
            discovered.add(resolved_rel)
            pending.append((resolved_rel, depth + 1))

    return sorted(discovered)


def collect_componentized_reverse_dependents(
    code_dir: Path,
    rel_paths: list[str],
    *,
    max_depth: int = 1,
) -> list[str]:
    editable_files = collect_componentized_editable_files(code_dir)
    if not editable_files:
        return []

    frontier = {
        path.replace("\\", "/").strip("/")
        for path in rel_paths
        if path
    }
    discovered: set[str] = set()
    root = code_dir.resolve()

    depth = 0
    while frontier and depth < max_depth:
        next_frontier: set[str] = set()
        for rel_path in editable_files:
            normalized = rel_path.replace("\\", "/").strip("/")
            if normalized in frontier or normalized in discovered:
                continue
            source_path = code_dir / normalized
            if not source_path.exists() or not source_path.is_file():
                continue
            try:
                source = source_path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue

            imported_paths: set[str] = set()
            for raw_import in _iter_local_import_specifiers(source):
                resolved_rel = _resolve_local_import_path(code_dir, normalized, raw_import)
                if not resolved_rel:
                    continue
                try:
                    (code_dir / resolved_rel).resolve().relative_to(root)
                except ValueError:
                    continue
                imported_paths.add(resolved_rel)

            if imported_paths.intersection(frontier):
                discovered.add(normalized)
                next_frontier.add(normalized)
        frontier = next_frontier
        depth += 1

    return sorted(discovered)


def _backfill_componentized_utility_classes(code_dir: Path) -> list[str]:
    base_css_path = code_dir / "src" / "base.css"
    if not base_css_path.exists():
        return []

    referenced_tokens: set[str] = set()
    for rel_path in collect_componentized_editable_files(code_dir):
        if not rel_path.endswith((".ts", ".tsx", ".js", ".jsx")):
            continue
        path = code_dir / rel_path
        try:
            source = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for token in COMPONENTIZED_UTILITY_FALLBACKS:
            if token in source:
                referenced_tokens.add(token)

    if not referenced_tokens:
        return []

    try:
        existing_css = base_css_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []

    block_lines: list[str] = []
    for token in sorted(referenced_tokens):
        selector = "." + token.replace("/", "\\/")
        if selector in existing_css:
            continue
        block_lines.append(f"{selector} {{ {COMPONENTIZED_UTILITY_FALLBACKS[token]} }}")

    if not block_lines:
        return []

    append_block = COMPONENTIZED_UTILITY_FALLBACK_MARKER + "\n" + "\n".join(block_lines) + "\n"
    updated_css = existing_css.rstrip() + "\n\n" + append_block
    base_css_path.write_text(updated_css, encoding="utf-8")
    return ["src/base.css"]


def rewrite_componentized_asset_api_urls(text: str) -> str:
    rewritten = API_ASSET_URL_RE.sub(lambda m: f"generated-assets/{Path(m.group(1)).name}", text)
    return _normalize_componentized_generated_asset_paths(rewritten)


def _normalize_componentized_generated_asset_paths(source: str) -> str:
    return re.sub(r'([("\'=\s])\/generated-assets\/', r"\1generated-assets/", source)


def _supports_componentized_polish_guard(ui_archetype: str) -> bool:
    return ui_archetype in POLISH_GUARD_ARCHETYPES or ui_archetype.startswith("game_")


def _stable_componentized_asset_choice(filename: str, candidates: list[Path]) -> Path | None:
    unique_candidates = sorted(dict.fromkeys(candidates), key=lambda path: path.name.lower())
    if not unique_candidates:
        return None
    digest = hashlib.sha1(filename.encode("utf-8")).digest()
    index = int.from_bytes(digest[:4], "big") % len(unique_candidates)
    return unique_candidates[index]


def _tokenize_componentized_asset_name(filename: str) -> set[str]:
    stopwords = {
        "generated",
        "assets",
        "asset",
        "image",
        "img",
        "file",
        "final",
        "cover",
    }
    return {
        token
        for token in re.split(r"[^a-z0-9]+", Path(filename).stem.lower())
        if token and token not in stopwords
    }


def _build_componentized_svg_placeholder(filename: str) -> bytes:
    ordered_tokens = [
        token.capitalize()
        for token in re.split(r"[^a-z0-9]+", Path(filename).stem.lower())
        if token and len(token) > 1
    ]
    label = " ".join(ordered_tokens) or "Game Asset"
    label = " ".join(label.split()[:3])
    palette = (
        ("#0f766e", "#5eead4"),
        ("#1d4ed8", "#93c5fd"),
        ("#be123c", "#fda4af"),
        ("#92400e", "#fcd34d"),
        ("#4c1d95", "#c4b5fd"),
    )
    accent_from, accent_to = palette[int(hashlib.sha1(filename.encode("utf-8")).hexdigest()[:2], 16) % len(palette)]
    safe_label = html_escape(label)
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256" fill="none">'
        "<defs>"
        f'<linearGradient id="g" x1="24" y1="20" x2="228" y2="236" gradientUnits="userSpaceOnUse">'
        f'<stop stop-color="{accent_from}"/><stop offset="1" stop-color="{accent_to}"/>'
        "</linearGradient>"
        '<linearGradient id="card" x1="20" y1="24" x2="236" y2="232" gradientUnits="userSpaceOnUse">'
        '<stop stop-color="#0f172a"/><stop offset="1" stop-color="#111827"/>'
        "</linearGradient>"
        "</defs>"
        '<rect width="256" height="256" rx="28" fill="#020617"/>'
        '<rect x="18" y="18" width="220" height="220" rx="24" fill="url(#card)" stroke="#FFFFFF" stroke-opacity="0.12"/>'
        '<rect x="38" y="38" width="180" height="180" rx="28" fill="url(#g)" opacity="0.2"/>'
        '<path d="M128 66 176 90v52c0 32-19 55-48 72-29-17-48-40-48-72V90l48-24Z" fill="url(#g)" opacity="0.95"/>'
        '<path d="M128 98v60m-28-30h56" stroke="#E5F7FF" stroke-width="14" stroke-linecap="round"/>'
        f'<text x="128" y="212" text-anchor="middle" fill="#E5E7EB" font-family="Inter, Arial, sans-serif" font-size="22" font-weight="700" letter-spacing="1.4">{safe_label}</text>'
        "</svg>"
    )
    return svg.encode("utf-8")


def _build_componentized_remote_image_placeholder_filename(label: str, url: str) -> str:
    raw = label.strip()
    if not raw:
        raw = Path(url.split("?", 1)[0]).stem.replace("-", " ").replace("_", " ")
    tokens = [
        token
        for token in re.split(r"[^a-z0-9]+", raw.lower())
        if token and token not in {"https", "http", "com", "www", "image", "img", "photo", "placeholder"}
    ]
    slug = "_".join(tokens[:4]) or "image_asset"
    return f"{slug}.svg"


def _sync_componentized_generated_asset_references(code_dir: Path) -> list[str]:
    public_dir = code_dir / "public" / "generated-assets"
    if not public_dir.exists():
        return []

    existing_files = _collect_componentized_generated_asset_index(code_dir)

    referenced: set[str] = set()
    for rel_path in collect_componentized_editable_files(code_dir):
        path = code_dir / rel_path
        try:
            source = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        normalized = _normalize_componentized_generated_asset_paths(source)
        if normalized != source:
            path.write_text(normalized, encoding="utf-8")
        for match in GENERATED_ASSET_REFERENCE_RE.finditer(normalized):
            referenced.add(match.group("filename").strip())

    created_aliases: list[str] = []
    for filename in sorted(referenced):
        lowered = filename.lower()
        if lowered in existing_files:
            continue
        dest = public_dir / filename
        if dest.suffix.lower() == ".svg":
            dest.write_bytes(_build_componentized_svg_placeholder(filename))
            existing_files[lowered] = dest
            created_aliases.append(f"public/generated-assets/{filename}")
            continue
        alias_source = _select_componentized_generated_asset_alias(filename, existing_files)
        if not alias_source:
            continue
        shutil.copy2(alias_source, dest)
        existing_files[lowered] = dest
        created_aliases.append(f"public/generated-assets/{filename}")
    return created_aliases


def _collect_componentized_generated_asset_index(code_dir: Path) -> dict[str, Path]:
    public_dir = code_dir / "public" / "generated-assets"
    if not public_dir.exists():
        return {}
    return {
        path.name.lower(): path
        for path in public_dir.iterdir()
        if path.is_file()
    }


def _select_componentized_generated_asset_reference(code_dir: Path, filename: str) -> str | None:
    existing_files = _collect_componentized_generated_asset_index(code_dir)
    if not existing_files:
        return None
    lowered = filename.lower()
    if lowered in existing_files:
        return f"generated-assets/{existing_files[lowered].name}"
    alias_source = _select_componentized_generated_asset_alias(filename, existing_files)
    if not alias_source:
        return None
    return f"generated-assets/{alias_source.name}"


def _select_componentized_generated_asset_alias(
    filename: str,
    existing_files: dict[str, Path],
) -> Path | None:
    lowered = filename.lower()
    requested_suffix = Path(lowered).suffix.lower()
    if requested_suffix == ".svg":
        svg_candidates = [
            path
            for existing_name, path in existing_files.items()
            if Path(existing_name).suffix.lower() == ".svg"
        ]
        return _stable_componentized_asset_choice(filename, svg_candidates)

    request_tokens = _tokenize_componentized_asset_name(filename)
    semantic_preferences = [
        (
            {"map", "world", "atlas", "realm", "landscape", "location", "region", "landmark"},
            {"map", "world", "atlas", "realm", "landscape", "region", "landmark", "background"},
        ),
        (
            {"hero", "background", "banner", "cover"},
            {"hero", "background", "banner", "cover", "landscape"},
        ),
        (
            {"badge", "crest", "emblem", "sigil", "icon", "ability", "abilities", "showcase", "evolution", "stage"},
            {"illustration", "showcase", "map", "landmark", "background", "portrait", "character"},
        ),
        (
            {"portrait", "character", "hero", "villain", "ally", "monster", "pokemon", "creature", "guardian"},
            {"portrait", "character", "hero", "monster", "creature", "guardian"},
        ),
        (
            {"weapon", "device", "artifact", "gear"},
            {"weapon", "device", "artifact", "gear", "illustration", "showcase"},
        ),
    ]

    scored_candidates: list[tuple[int, Path]] = []
    for existing_name, path in existing_files.items():
        if Path(existing_name).suffix.lower() == ".svg":
            continue
        existing_tokens = _tokenize_componentized_asset_name(existing_name)
        score = len(request_tokens & existing_tokens) * 10
        for request_group, candidate_group in semantic_preferences:
            if request_tokens & request_group and existing_tokens & candidate_group:
                score += 6
        if "background" in request_tokens and "background" in existing_tokens:
            score += 3
        if "portrait" in request_tokens and "portrait" in existing_tokens:
            score += 3
        if score > 0:
            scored_candidates.append((score, path))

    if scored_candidates:
        top_score = max(score for score, _ in scored_candidates)
        return _stable_componentized_asset_choice(
            filename,
            [path for score, path in scored_candidates if score == top_score],
        )

    showcase_candidates = [
        path
        for existing_name, path in existing_files.items()
        if Path(existing_name).suffix.lower() != ".svg"
        and any(token in existing_name for token in ("illustration", "showcase", "map", "landmark"))
    ]
    portrait_candidates = [
        path
        for existing_name, path in existing_files.items()
        if Path(existing_name).suffix.lower() != ".svg"
        and any(token in existing_name for token in ("portrait", "character", "hero"))
    ]
    background_candidates = [
        path
        for existing_name, path in existing_files.items()
        if Path(existing_name).suffix.lower() != ".svg"
        and any(token in existing_name for token in ("background", "banner"))
    ]
    generic_candidates = [
        path
        for existing_name, path in existing_files.items()
        if Path(existing_name).suffix.lower() != ".svg"
    ]

    if request_tokens & {"badge", "crest", "emblem", "sigil", "icon", "ability", "abilities"}:
        return _stable_componentized_asset_choice(filename, showcase_candidates or portrait_candidates or generic_candidates)
    if request_tokens & {"evolution", "stage", "companion", "team", "roster"}:
        return _stable_componentized_asset_choice(filename, showcase_candidates or portrait_candidates or generic_candidates)
    if request_tokens & {"map", "world", "atlas", "region", "landmark", "location"}:
        return _stable_componentized_asset_choice(filename, showcase_candidates or background_candidates or generic_candidates)
    if request_tokens & {"portrait", "character", "hero", "villain", "ally", "monster", "pokemon", "creature"}:
        return _stable_componentized_asset_choice(filename, portrait_candidates or showcase_candidates or generic_candidates)
    return _stable_componentized_asset_choice(filename, generic_candidates)


def _iter_local_import_specifiers(source: str) -> list[str]:
    imports: list[str] = []
    for match in LOCAL_REL_IMPORT_RE.finditer(source):
        specifier = (
            match.group("from")
            or match.group("dynamic")
            or match.group("bare")
            or ""
        ).strip()
        if specifier:
            imports.append(specifier.replace("\\", "/"))
    return imports


def _resolve_local_import_path(code_dir: Path, rel_path: str, specifier: str) -> str | None:
    source_dir = (code_dir / rel_path).parent
    raw_target = (source_dir / specifier).resolve()
    try:
        raw_target.relative_to(code_dir.resolve())
    except ValueError:
        return None

    candidates: list[Path] = [raw_target]
    if raw_target.suffix:
        if raw_target.suffix in TEXT_EXTENSIONS and raw_target.exists():
            return raw_target.relative_to(code_dir).as_posix()
    else:
        for suffix in (".ts", ".tsx", ".js", ".jsx", ".css"):
            candidates.append(raw_target.with_suffix(suffix))
        if raw_target.is_dir() or not raw_target.exists():
            for index_name in ("index.ts", "index.tsx", "index.js", "index.jsx", "index.css"):
                candidates.append(raw_target / index_name)

    root = code_dir.resolve()
    for candidate in candidates:
        try:
            candidate.resolve().relative_to(root)
        except ValueError:
            continue
        if candidate.exists() and candidate.is_file():
            return candidate.relative_to(code_dir).as_posix()
    return None


def stage_componentized_design_assets(version_dir: Path, design_assets: list[dict[str, Any]]) -> list[dict[str, str]]:
    public_dir = version_dir / "code" / "public" / "generated-assets"
    public_dir.mkdir(parents=True, exist_ok=True)

    staged_assets: list[dict[str, str]] = []
    for asset in design_assets:
        key = str(asset.get("key") or "asset").strip() or "asset"
        purpose = str(asset.get("purpose") or "Design asset").strip() or "Design asset"
        local_path = asset.get("local_path")
        if local_path:
            src = Path(local_path)
            if not src.is_absolute():
                src = (version_dir.parent.parent.parent / src).resolve()
            if src.exists() and src.is_file():
                suffix = src.suffix or ".png"
                filename = f"{key}{suffix.lower()}"
                dest = public_dir / filename
                shutil.copy2(src, dest)
                staged_assets.append({
                    "key": key,
                    "purpose": purpose,
                    "path": f"generated-assets/{filename}",
                })
                continue

        url = str(asset.get("url") or "").strip()
        if url:
            staged_assets.append({
                "key": key,
                "purpose": purpose,
                "path": url,
            })
    return staged_assets


def ensure_componentized_workspace_support(
    code_dir: Path,
    *,
    base_css_content: str | None = None,
    ui_archetype: str | None = None,
) -> dict[str, list[str]]:
    code_dir.mkdir(parents=True, exist_ok=True)

    created_files: list[str] = []
    rewritten_files: list[str] = []
    extracted_css_chunks: list[str] = []
    is_game_archetype = bool(ui_archetype and (ui_archetype == "game" or ui_archetype.startswith("game_")))
    game_map_asset_reference = (
        _select_componentized_generated_asset_reference(code_dir, "region_world_map.png")
        if is_game_archetype
        else None
    )

    for rel_path, content in _componentized_support_files().items():
        target = code_dir / rel_path
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            created_files.append(rel_path)

    polish_created, polish_rewritten = _sync_componentized_polish_guard(
        code_dir,
        ui_archetype=ui_archetype,
    )
    created_files.extend(polish_created)
    rewritten_files.extend(polish_rewritten)

    if base_css_content:
        base_css_path = code_dir / "src" / "base.css"
        if not base_css_path.exists():
            base_css_path.parent.mkdir(parents=True, exist_ok=True)
            base_css_path.write_text(base_css_content, encoding="utf-8")
            created_files.append("src/base.css")
        else:
            original_base = base_css_path.read_text(encoding="utf-8", errors="replace")
            updated_base = _normalize_componentized_base_css(original_base, reference_css=base_css_content)
            if updated_base != original_base:
                base_css_path.write_text(updated_base, encoding="utf-8")
                rewritten_files.append("src/base.css")

        main_path = code_dir / "src" / "main.tsx"
        if main_path.exists():
            original_main = main_path.read_text(encoding="utf-8", errors="replace")
            updated_main = _normalize_componentized_main_entry(
                _ensure_css_import(original_main, './base.css')
            )
            if updated_main != original_main:
                main_path.write_text(updated_main, encoding="utf-8")
                rewritten_files.append("src/main.tsx")

    for rel_path in collect_componentized_editable_files(code_dir):
        path = code_dir / rel_path
        original = path.read_text(encoding="utf-8", errors="replace")
        updated = _normalize_componentized_file(rel_path, original)
        if is_game_archetype:
            updated = _normalize_componentized_game_remote_badge_images(updated)
            updated = _normalize_componentized_remote_image_urls(updated)
            updated = _normalize_componentized_game_empty_image_fields(
                updated,
                fallback_asset_path=game_map_asset_reference,
            )
            if rel_path.endswith((".tsx", ".jsx")):
                updated = _normalize_componentized_game_detail_ctas(updated)
                updated = _normalize_componentized_game_placeholder_maps(
                    updated,
                    fallback_asset_path=game_map_asset_reference,
                )
        elif ui_archetype in {"ecommerce", "portfolio"}:
            updated = _normalize_componentized_remote_image_urls(updated)
        if rel_path.endswith((".tsx", ".jsx")):
            updated, extracted_css = _extract_componentized_css_tail(updated)
            if extracted_css:
                extracted_css_chunks.append(extracted_css)
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            rewritten_files.append(rel_path)

    if extracted_css_chunks:
        index_css_path = code_dir / "src" / "index.css"
        index_css_path.parent.mkdir(parents=True, exist_ok=True)
        existing_css = index_css_path.read_text(encoding="utf-8", errors="replace") if index_css_path.exists() else ""
        appended_css = "\n\n".join(chunk.strip() for chunk in extracted_css_chunks if chunk.strip()).strip()
        if appended_css:
            combined_css = existing_css.rstrip() + ("\n\n" if existing_css.strip() else "") + appended_css + "\n"
            index_css_path.write_text(combined_css, encoding="utf-8")
            if "src/index.css" not in rewritten_files:
                rewritten_files.append("src/index.css")

    created_files.extend(_backfill_missing_local_css_imports(code_dir))
    created_files.extend(_sync_componentized_generated_asset_references(code_dir))
    rewritten_files.extend(_rewrite_componentized_import_aliases(code_dir))
    rewritten_files.extend(_normalize_componentized_design_overrides(code_dir))
    rewritten_files.extend(_backfill_componentized_utility_classes(code_dir))

    synced_dependencies = _sync_componentized_package_dependencies(code_dir)
    if synced_dependencies:
        rewritten_files.append("package.json")
    created_files.extend(_ensure_componentized_vite_bin_shims(code_dir))

    return {
        "created_files": created_files,
        "rewritten_files": rewritten_files,
    }


def summarize_componentized_build_error(build_result: dict[str, Any], *, max_chars: int = 4000) -> str:
    if not build_result:
        return "No build logs were captured."

    chunks: list[str] = []
    reason = str(build_result.get("reason") or "").strip()
    if reason:
        chunks.append(f"Reason: {reason}")

    for log in (build_result.get("logs") or [])[-3:]:
        command = " ".join(log.get("command") or [])
        stdout = str(log.get("stdout") or "").strip()
        stderr = str(log.get("stderr") or "").strip()
        block = [f"$ {command}"]
        if stdout:
            block.append(stdout[-1500:])
        if stderr:
            block.append(stderr[-1500:])
        chunks.append("\n".join(block))

    summary = "\n\n".join(chunks).strip()
    if len(summary) > max_chars:
        summary = summary[-max_chars:]
    return summary or "No build logs were captured."


def relative_mount_root(code_dir: Path, target: Path) -> str:
    rel_parent = target.relative_to(code_dir).parent.as_posix()
    return "" if rel_parent == "." else rel_parent


def rewrite_preview_file_references(
    html: str,
    *,
    mount_prefix: str,
    root_dir: str,
) -> str:
    def _src_href_repl(match: re.Match[str]) -> str:
        prefix, raw_path, suffix = match.groups()
        value = raw_path.strip()
        lower = value.lower()
        if lower.startswith(("http://", "https://", "data:", "mailto:", "tel:", "#", "/api/", "/published/")):
            return match.group(0)
        if lower.endswith((".css", ".js", ".mjs", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico")):
            normalized = _normalize_asset_path(value, root_dir)
            return f"{prefix}{mount_prefix}/{normalized}{suffix}"
        return match.group(0)

    html = re.sub(r'((?:src|href)=["\'])([^"\']+)(["\'])', _src_href_repl, html, flags=re.IGNORECASE)

    def _css_url_repl(match: re.Match[str]) -> str:
        prefix, raw_path, suffix = match.groups()
        value = raw_path.strip()
        lower = value.lower()
        if lower.startswith(("http://", "https://", "data:", "mailto:", "tel:", "#", "/api/", "/published/")):
            return match.group(0)
        return f"{prefix}{mount_prefix}/{_normalize_asset_path(value, root_dir)}{suffix}"

    html = re.sub(
        r'(url\(["\']?)(/assets/[^)"\']+)(["\']?\))',
        _css_url_repl,
        html,
        flags=re.IGNORECASE,
    )
    html = re.sub(
        r'(url\(["\']?)(?:\./|\.\./)?([^)"\']+\.(?:png|jpg|jpeg|gif|webp|svg|ico|css|js|mjs))(["\']?\))',
        _css_url_repl,
        html,
        flags=re.IGNORECASE,
    )
    return html


def rewrite_preview_runtime_asset_references(
    content: str,
    *,
    mount_prefix: str,
    root_dir: str,
) -> str:
    normalized_root = f"{mount_prefix}/{root_dir}".strip("/")
    if not normalized_root:
        return content

    def _repl(match: re.Match[str]) -> str:
        prefix = match.group("prefix")
        subpath = match.group("subpath").lstrip("/")
        return f"{prefix}/{normalized_root}/generated-assets/{subpath}"

    return RUNTIME_GENERATED_ASSET_REFERENCE_RE.sub(_repl, content)


def _normalize_asset_path(raw_path: str, root_dir: str) -> str:
    value = raw_path.split("?", 1)[0].split("#", 1)[0]
    if value.startswith("/assets/"):
        prefix = f"{root_dir}/" if root_dir else ""
        return f"{prefix}{value.lstrip('/')}".strip("/")
    if value.startswith("/"):
        prefix = f"{root_dir}/" if root_dir else ""
        return f"{prefix}{value.lstrip('/')}".strip("/")

    value = value.replace("\\", "/")
    while value.startswith("./"):
        value = value[2:]
    while value.startswith("../"):
        value = value[3:]

    if root_dir:
        return f"{root_dir}/{value}".strip("/")
    return value.strip("/")


def write_preview_build_manifest(version_dir: Path, data: dict[str, Any]) -> None:
    path = version_dir / "last_preview_build.json"
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _componentized_support_files() -> dict[str, str]:
    scaffold = build_vite_react_ts_scaffold(app_dir="componentized-support").files
    prefix = "componentized-support/"
    keep = {
        "package.json",
        "index.html",
        "vite.config.ts",
        "tsconfig.json",
        "tsconfig.node.json",
        "src/main.tsx",
        "src/App.tsx",
        "src/vite-env.d.ts",
        "src/index.css",
    }
    files: dict[str, str] = {}
    for path, content in scaffold.items():
        normalized = path.replace("\\", "/")
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix):]
        if normalized in keep:
            files[normalized] = content

    files["src/index.css"] = "/* App-specific overrides live here. Keep this file intentionally minimal. */\n"

    files["public/vite.svg"] = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" fill="none">'
        '<rect width="64" height="64" rx="16" fill="#111827"/>'
        '<path d="M18 44L32 14L46 44H38L32 30L26 44H18Z" fill="#10B981"/>'
        "</svg>\n"
    )
    return files


def _backfill_missing_local_css_imports(code_dir: Path) -> list[str]:
    created: list[str] = []
    for rel_path in collect_componentized_editable_files(code_dir):
        if not rel_path.endswith((".ts", ".tsx", ".js", ".jsx")):
            continue
        source_path = code_dir / rel_path
        try:
            source = source_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for raw_import in LOCAL_CSS_IMPORT_RE.findall(source):
            import_path = raw_import.replace("\\", "/")
            target = (source_path.parent / import_path).resolve()
            try:
                target.relative_to(code_dir.resolve())
            except ValueError:
                continue
            if target.exists():
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("/* Generated fallback stylesheet to satisfy a referenced local CSS import. */\n", encoding="utf-8")
            created.append(target.relative_to(code_dir).as_posix())
    return created


def _rewrite_componentized_import_aliases(code_dir: Path) -> list[str]:
    rewritten: list[str] = []
    root_dir = code_dir.resolve()

    for rel_path in collect_componentized_editable_files(code_dir):
        if not rel_path.endswith((".ts", ".tsx", ".js", ".jsx")):
            continue
        source_path = code_dir / rel_path
        try:
            original = source_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        def _replace(match: re.Match[str]) -> str:
            raw_import = match.group("from") or match.group("dynamic") or match.group("bare")
            if not raw_import:
                return match.group(0)
            resolved = _resolve_componentized_import_alias(
                source_path=source_path,
                raw_import=raw_import,
                root_dir=root_dir,
            )
            if not resolved or resolved == raw_import:
                return match.group(0)
            return match.group(0).replace(raw_import, resolved)

        updated = LOCAL_REL_IMPORT_RE.sub(_replace, original)
        if updated != original:
            source_path.write_text(updated, encoding="utf-8")
            rewritten.append(rel_path)

    return rewritten


def _resolve_componentized_import_alias(
    *,
    source_path: Path,
    raw_import: str,
    root_dir: Path,
) -> str | None:
    normalized_import = raw_import.replace("\\", "/")
    if not normalized_import.startswith("."):
        return None

    target_base = (source_path.parent / normalized_import).resolve()
    try:
        target_base.relative_to(root_dir)
    except ValueError:
        return None

    if _componentized_module_exists(target_base):
        return normalized_import

    module_name = target_base.name
    for candidate_name in COMPONENTIZED_IMPORT_ALIAS_CANDIDATES.get(module_name, ()):
        candidate_base = target_base.parent / candidate_name
        if not _componentized_module_exists(candidate_base):
            continue
        rel_path = Path(os.path.relpath(candidate_base, source_path.parent)).as_posix()
        return rel_path if rel_path.startswith(".") else f"./{rel_path}"

    return None


def _componentized_module_exists(module_base: Path) -> bool:
    if module_base.is_dir():
        for ext in COMPONENTIZED_MODULE_EXTENSIONS:
            if (module_base / f"index{ext}").exists():
                return True
    for ext in COMPONENTIZED_MODULE_EXTENSIONS:
        if Path(f"{module_base}{ext}").exists():
            return True
    return False


def _normalize_componentized_game_remote_badge_images(source: str) -> str:
    def _replace(match: re.Match[str]) -> str:
        badge_name = match.group("name").strip()
        if not _looks_like_componentized_badge_label(badge_name):
            return match.group(0)
        filename = _build_componentized_badge_placeholder_filename(badge_name)
        return (
            f"{match.group('prefix')}{match.group('url_quote')}"
            f"generated-assets/{filename}"
            f"{match.group('url_quote')}"
        )

    return REMOTE_BADGE_OBJECT_IMAGE_RE.sub(_replace, source)


def _normalize_componentized_game_empty_image_fields(
    source: str,
    fallback_asset_path: str | None = None,
) -> str:
    if not fallback_asset_path or "image" not in source:
        return source
    empty_image_re = re.compile(
        r"(?P<prefix>\bimage\s*:\s*)(?P<quote>[\"'])(?P<value>\s*)(?P=quote)",
        re.IGNORECASE,
    )
    if not empty_image_re.search(source):
        return source

    def _replace(match: re.Match[str]) -> str:
        return f"{match.group('prefix')}{match.group('quote')}{fallback_asset_path}{match.group('quote')}"

    return empty_image_re.sub(_replace, source)


def _normalize_componentized_game_placeholder_maps(
    source: str,
    fallback_asset_path: str | None = None,
) -> str:
    placeholder_img_re = re.compile(
        r'<img(?P<attrs>[^>]*?)src=(?P<quote>["\'])data:image/svg\+xml,[^"\']*(?:Placeholder|PLACEHOLDER)[^"\']*(?P=quote)(?P<rest>[^>]*)/?>',
        re.IGNORECASE | re.DOTALL,
    )
    updated = source
    if placeholder_img_re.search(updated):
        updated = placeholder_img_re.sub(
            (
                '<div className="runtime-world-map-fallback">'
                '<div className="runtime-world-map-grid" aria-hidden="true"></div>'
                '<div className="runtime-world-map-copy">'
                '<span className="runtime-world-map-eyebrow">Strategic Atlas</span>'
                '<strong className="runtime-world-map-title">World Survey Interface</strong>'
                '<p className="runtime-world-map-text">Key regions remain explorable through the dossiers and sector cards below.</p>'
                '</div>'
                '</div>'
            ),
            updated,
        )
    if fallback_asset_path and "Map Placeholder" in updated:
        placeholder_card_re = re.compile(
            r"<div(?P<attrs>[^>]*)>\s*Map Placeholder\s*</div>",
            re.IGNORECASE | re.DOTALL,
        )
        replacement = (
            f'<img className="location-image" src={{region.image || "{fallback_asset_path}"}} '
            'alt={`${region.name} map illustration`} loading="lazy" />'
            if "region.name" in updated or "region.image" in updated
            else f'<img className="location-image" src="{fallback_asset_path}" alt="World map illustration" loading="lazy" />'
        )
        updated = placeholder_card_re.sub(replacement, updated)
    return updated


def _normalize_componentized_remote_image_urls(source: str) -> str:
    def _replace_named_object(match: re.Match[str]) -> str:
        url = match.group("url").strip()
        label = match.group("name").strip()
        filename = _build_componentized_remote_image_placeholder_filename(label, url)
        return f"{match.group('prefix')}{match.group('quote')}generated-assets/{filename}{match.group('quote')}"

    updated = REMOTE_NAMED_OBJECT_IMAGE_URL_RE.sub(_replace_named_object, source)

    def _replace_object(match: re.Match[str]) -> str:
        url = match.group("url").strip()
        filename = _build_componentized_remote_image_placeholder_filename("", url)
        return f"{match.group('prefix')}{match.group('quote')}generated-assets/{filename}{match.group('quote')}"

    updated = REMOTE_OBJECT_IMAGE_URL_RE.sub(_replace_object, updated)

    def _replace_jsx(match: re.Match[str]) -> str:
        url = match.group("url").strip()
        rest = match.group("rest") or ">"
        alt_match = re.search(r"""\balt=(['"])(?P<alt>[^'"]+)\1""", rest, flags=re.IGNORECASE)
        label = alt_match.group("alt") if alt_match else ""
        filename = _build_componentized_remote_image_placeholder_filename(label, url)
        return f"{match.group('prefix')}{match.group('quote')}generated-assets/{filename}{match.group('quote')}{rest}"

    updated = REMOTE_JSX_IMAGE_SRC_RE.sub(_replace_jsx, updated)

    def _replace_assignment(match: re.Match[str]) -> str:
        url = match.group("url").strip()
        filename = _build_componentized_remote_image_placeholder_filename("", url)
        return f"{match.group('prefix')}{match.group('quote')}generated-assets/{filename}{match.group('quote')}"

    updated = re.sub(
        r"(?P<prefix>\b[A-Za-z_$][\w$.]*\.src\s*=\s*)(?P<quote>['\"])(?P<url>https?://[^'\"]+)(?P=quote)",
        _replace_assignment,
        updated,
        flags=re.IGNORECASE,
    )

    def _replace_style_url(match: re.Match[str]) -> str:
        url = match.group("url").strip()
        filename = _build_componentized_remote_image_placeholder_filename("", url)
        return f"{match.group('prefix')}generated-assets/{filename}{match.group('suffix')}"

    return re.sub(
        r"(?P<prefix>backgroundImage\s*:\s*['\"]url\()(?P<url>https?://[^'\"\)]+)(?P<suffix>\)['\"])",
        _replace_style_url,
        updated,
        flags=re.IGNORECASE,
    )


def _normalize_componentized_game_detail_ctas(source: str) -> str:
    component_re = re.compile(
        r"const\s+(?P<component>[A-Za-z_$][\w$]*)\s*:\s*React\.FC<[^>]+>\s*=\s*\(\{\s*(?P<params>[^}]*)\}\s*\)\s*=>\s*\{(?P<body>[\s\S]*?)\n\};",
        re.DOTALL,
    )
    map_re = re.compile(
        r"\{(?P<collection>\w+)\.map\(\((?P<params>[^)]*)\)\s*=>\s*\((?P<body>.*?)\)\)\}",
        re.DOTALL,
    )
    button_re = re.compile(
        r"<button(?P<attrs>[^>]*)className=(?P<quote>[\"'])(?P<classname>[^\"']*\b(?:btn-primary|weapon-cta)\b[^\"']*)(?P=quote)(?P<tail>[^>]*)>(?P<label>.*?)</button>",
        re.DOTALL,
    )

    def build_detail_markup(item_var: str, summary_label: str, class_name: str, attrs: str, tail: str) -> str:
        summary_attrs = " ".join(part.strip() for part in (attrs, tail) if part.strip()).strip()
        summary_attr_text = f" {summary_attrs}" if summary_attrs else ""
        return (
            f'<details className="runtime-inline-detail">'
            f'<summary className="{class_name}"{summary_attr_text}>{summary_label}</summary>'
            f'<div className="runtime-inline-detail-panel">'
            f'<div className="runtime-inline-detail-kicker">{{{item_var}.type || {item_var}.region || {item_var}.owner || "Archive Detail"}}</div>'
            f'<h4 className="runtime-inline-detail-title">{{{item_var}.name || {item_var}.title || "Field Brief"}}</h4>'
            f'<p className="runtime-inline-detail-copy">{{{item_var}.description || {item_var}.desc || {item_var}.lore || "This dossier uses local mock archive data to keep the interaction alive."}}</p>'
            f'<div className="runtime-inline-detail-stats">'
            f'{{typeof {item_var}.atk === "number" ? <span className="runtime-inline-detail-chip">ATK {{{item_var}.atk}}</span> : null}}'
            f'{{typeof {item_var}.mag === "number" ? <span className="runtime-inline-detail-chip">MAG {{{item_var}.mag}}</span> : null}}'
            f'{{typeof {item_var}.def === "number" ? <span className="runtime-inline-detail-chip">DEF {{{item_var}.def}}</span> : null}}'
            f'{{typeof {item_var}.spd === "number" ? <span className="runtime-inline-detail-chip">SPD {{{item_var}.spd}}</span> : null}}'
            f'</div>'
            f'</div>'
            f'</details>'
        )

    def build_component_detail_markup(params: list[str], summary_label: str, class_name: str, attrs: str, tail: str) -> str:
        summary_attrs = " ".join(
            part.strip()
            for part in (attrs, tail)
            if part.strip() and "onClick=" not in part
        ).strip()
        summary_attr_text = f" {summary_attrs}" if summary_attrs else ""
        kicker_var = next((name for name in ("role", "type", "region", "owner") if name in params), None)
        title_var = "name" if "name" in params else ("title" if "title" in params else None)
        copy_var = next((name for name in ("description", "desc", "lore") if name in params), None)
        detail_object_var = next(
            (
                name
                for name in ("item", "entry", "region", "location", "character", "pokemon", "weapon", "artifact", "card", "profile")
                if name in params
            ),
            None,
        )

        if "stats" in params:
            stats_expr = (
                '<div className="runtime-inline-detail-stats">'
                '{stats.map((stat, index) => ('
                '<span className="runtime-inline-detail-chip" key={index}>{stat.label} {stat.value}</span>'
                '))}'
                '</div>'
            )
        else:
            chip_nodes: list[str] = []
            for name in ("weapon", "owner", "atk", "mag", "def", "spd"):
                if name not in params:
                    continue
                if name in {"atk", "mag", "def", "spd"}:
                    chip_nodes.append(
                        f'{{typeof {name} === "number" ? <span className="runtime-inline-detail-chip">{name.upper()} {{{name}}}</span> : null}}'
                    )
                else:
                    chip_nodes.append(
                        f'{{{name} ? <span className="runtime-inline-detail-chip">{name.capitalize()} {{{name}}}</span> : null}}'
                    )
            stats_expr = f'<div className="runtime-inline-detail-stats">{"".join(chip_nodes)}</div>' if chip_nodes else ""

        kicker_expr = (
            f"{{{kicker_var}}}"
            if kicker_var and (kicker_var != detail_object_var or title_var or copy_var)
            else (
                f'{{{detail_object_var}.type || {detail_object_var}.region || {detail_object_var}.owner || "Archive Detail"}}'
                if detail_object_var
                else "Archive Detail"
            )
        )
        title_expr = (
            f"{{{title_var}}}"
            if title_var
            else (
                f'{{{detail_object_var}.name || {detail_object_var}.title || "Field Brief"}}'
                if detail_object_var
                else "Field Brief"
            )
        )
        copy_expr = (
            f"{{{copy_var}}}"
            if copy_var
            else (
                f'{{{detail_object_var}.description || {detail_object_var}.desc || {detail_object_var}.lore || "This dossier uses local mock archive data to keep the interaction alive."}}'
                if detail_object_var
                else "This dossier uses local mock archive data to keep the interaction alive."
            )
        )
        return (
            f'<details className="runtime-inline-detail">'
            f'<summary className="{class_name}"{summary_attr_text}>{summary_label}</summary>'
            f'<div className="runtime-inline-detail-panel">'
            f'<div className="runtime-inline-detail-kicker">{kicker_expr}</div>'
            f'<h4 className="runtime-inline-detail-title">{title_expr}</h4>'
            f'<p className="runtime-inline-detail-copy">{copy_expr}</p>'
            f'{stats_expr}'
            f'</div>'
            f'</details>'
        )

    def patch_body(item_var: str, body: str) -> str:
        def replace_button(match: re.Match[str]) -> str:
            attrs = match.group("attrs") or ""
            tail = match.group("tail") or ""
            if "onClick=" in attrs or "onClick=" in tail:
                return match.group(0)
            label = re.sub(r"\s+", " ", match.group("label") or "").strip()
            if not label:
                return match.group(0)
            lowered = label.lower()
            if not any(keyword in lowered for keyword in ("inspect", "view", "access", "open", "logs", "schematic", "dossier", "details")):
                return match.group(0)
            class_name = re.sub(r"\s+", " ", match.group("classname")).strip()
            return build_detail_markup(item_var, label, class_name, attrs, tail)

        return button_re.sub(replace_button, body)

    def replace_component(match: re.Match[str]) -> str:
        params = [part.strip() for part in match.group("params").split(",") if part.strip()]
        body = match.group("body")
        if "alert(" not in body or "<button" not in body:
            return match.group(0)

        button_match = re.search(
            r"<button(?P<before>[^>]*)onClick=\{(?P<handler>[A-Za-z_$][\w$]*)\}(?P<after>[^>]*)className=(?P<quote>[\"'])(?P<classname>[^\"']*\b(?:btn-primary|weapon-cta)\b[^\"']*)(?P=quote)(?P<tail>[^>]*)>(?P<label>.*?)</button>",
            body,
            re.DOTALL,
        ) or re.search(
            r"<button(?P<before>[^>]*)className=(?P<quote>[\"'])(?P<classname>[^\"']*\b(?:btn-primary|weapon-cta)\b[^\"']*)(?P=quote)(?P<mid>[^>]*)onClick=\{(?P<handler>[A-Za-z_$][\w$]*)\}(?P<tail>[^>]*)>(?P<label>.*?)</button>",
            body,
            re.DOTALL,
        )
        if not button_match:
            return match.group(0)

        label = re.sub(r"\s+", " ", button_match.group("label") or "").strip()
        if not label:
            return match.group(0)
        attrs = " ".join(
            part.strip()
            for part in (
                button_match.groupdict().get("before", ""),
                button_match.groupdict().get("after", ""),
                button_match.groupdict().get("mid", ""),
            )
            if part and part.strip()
        ).strip()
        replacement = build_component_detail_markup(
            params,
            label,
            re.sub(r"\s+", " ", button_match.group("classname")).strip(),
            attrs,
            button_match.group("tail") or "",
        )
        updated_body = body.replace(button_match.group(0), replacement, 1)
        handler = button_match.group("handler")
        updated_body = re.sub(
            rf"\n?\s*const\s+{re.escape(handler)}\s*=\s*\(\)\s*=>\s*\{{[\s\S]*?\n\s*\}};\s*",
            "\n",
            updated_body,
            count=1,
        )
        updated_body = re.sub(
            rf"\s+onClick=\{{{re.escape(handler)}\}}",
            "",
            updated_body,
        )
        updated_body = re.sub(
            r"\n\s*const \[showDetails,\s*setShowDetails\] = useState\(false\);\s*",
            "\n",
            updated_body,
            count=1,
        )
        return match.group(0).replace(body, updated_body)

    updated = component_re.sub(replace_component, source)

    def replace_map(match: re.Match[str]) -> str:
        params = (match.group("params") or "").strip()
        item_var = params.split(",", 1)[0].strip()
        body = match.group("body")
        if not item_var or not body or "<button" not in body:
            return match.group(0)
        updated_body = patch_body(item_var, body)
        if updated_body == body:
            return match.group(0)
        return "{%s.map((%s) => (%s))}" % (match.group("collection"), params, updated_body)

    return map_re.sub(replace_map, updated)


def _looks_like_componentized_badge_label(label: str) -> bool:
    tokens = _tokenize_componentized_asset_name(label)
    return bool(tokens & {"badge", "crest", "emblem", "sigil", "icon"})


def _build_componentized_badge_placeholder_filename(label: str) -> str:
    tokens = [
        token
        for token in _tokenize_componentized_asset_name(label)
        if token not in {"badge", "crest", "emblem", "sigil", "icon", "gym", "collection"}
    ]
    if not tokens:
        tokens = ["emblem"]
    return f"badge_{'_'.join(tokens[:3])}.svg"


def _ensure_css_import(source: str, import_path: str) -> str:
    return _ensure_main_side_effect_import(source, import_path)


def _ensure_main_side_effect_import(source: str, import_path: str) -> str:
    import_line_variants = {f'import "{import_path}";', f"import '{import_path}';"}
    if any(line.strip() in import_line_variants for line in source.splitlines()):
        return source
    lines = source.splitlines()
    import_line = f'import "{import_path}";'
    insert_at = 0
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("import "):
            insert_at = idx + 1
    lines.insert(insert_at, import_line)
    return "\n".join(lines) + ("\n" if source.endswith("\n") else "")


def _remove_css_import(source: str, import_path: str) -> str:
    return _remove_main_side_effect_import(source, import_path)


def _remove_main_side_effect_import(source: str, import_path: str) -> str:
    lines = source.splitlines()
    filtered = [
        line
        for line in lines
        if line.strip() not in {f'import "{import_path}";', f"import '{import_path}';"}
    ]
    if filtered == lines:
        return source
    return "\n".join(filtered).rstrip() + "\n"


def _normalize_componentized_file(rel_path: str, source: str) -> str:
    updated = rewrite_componentized_asset_api_urls(source)

    if rel_path == "index.html":
        updated = _normalize_componentized_index_html(updated)
    elif rel_path == "package.json":
        updated = _normalize_componentized_package_json(updated)
    elif rel_path in {"tsconfig.json", "tsconfig.node.json"}:
        updated = _normalize_componentized_tsconfig(updated)
    elif rel_path == "src/index.css":
        updated = _normalize_componentized_index_css(updated)
        updated = _repair_componentized_css_data_uri_quote_bleed(updated)
    elif rel_path.endswith(".css"):
        updated = _repair_componentized_css_data_uri_quote_bleed(updated)
    elif rel_path.endswith((".ts", ".tsx", ".js", ".jsx")):
        updated = LOCAL_CODE_IMPORT_RE.sub(r"\1\2\4", updated)
        updated = _normalize_componentized_react_icons_imports(updated)
        updated = _normalize_componentized_field_aliases(updated)
        updated = _repair_componentized_lightweight_chart_corruption(updated)
        updated = _repair_componentized_tradingview_scaffold_corruption(updated)
        updated = _repair_interface_field_comment_bleed(updated)
        updated = _repair_inline_block_comment_code_bleed(updated)
        updated = _repair_block_comment_control_flow_bleed(updated)
        updated = _repair_unterminated_block_comment_line_notes(updated)
        updated = _repair_multiline_block_comment_code_bleed(updated)
        updated = _repair_multiline_block_comment_line_notes(updated)
        updated = _repair_inline_block_comment_continuations(updated)
        updated = _repair_inline_block_comment_note_code_bleed(updated)
        updated = _repair_inline_block_comment_swallowed_calls(updated)
        updated = _repair_unterminated_inline_block_comments(updated)
        updated = _repair_componentized_comment_prose_continuations(updated)
        updated = _repair_componentized_orphan_svg_import_comment_lines(updated)
        updated = _repair_componentized_split_state_setters(updated)
        updated = _repair_componentized_split_camel_identifiers(updated)
        updated = _repair_componentized_commented_destructured_props(updated)
        updated = _repair_componentized_orphan_prose_comment_lines(updated)
        updated = _normalize_run_on_inline_comments(updated)
        updated = _repair_componentized_comment_split_identifiers(updated)
        updated = _repair_componentized_comment_tail_split_identifiers(updated)
        updated = _repair_componentized_jsx_comment_swallowed_tag_boundaries(updated)
        updated = _repair_componentized_jsx_block_comment_bleed(updated)
        updated = _repair_componentized_jsx_text_comment_bleed(updated)
        updated = _repair_componentized_jsx_attribute_comment_bleed(updated)
        updated = _repair_componentized_inline_jsx_attribute_block_comments(updated)
        updated = _repair_componentized_jsx_tag_comment_lines(updated)
        updated = _repair_componentized_jsx_text_comment_line_bleed(updated)
        updated = _repair_componentized_jsx_handler_comment_close_bleed(updated)
        updated = _repair_componentized_jsx_expression_comment_split_identifiers(updated)
        updated = _repair_componentized_orphan_comment_split_identifiers(updated)
        updated = _repair_componentized_orphan_comment_split_dotted_identifiers(updated)
        updated = _repair_componentized_orphan_comment_split_string_literals(updated)
        updated = _repair_componentized_orphan_comment_close_in_string_literals(updated)
        updated = _strip_componentized_inline_script_tags(updated)
        updated = _strip_componentized_alpine_jsx_directives(updated)
        updated = _normalize_componentized_void_jsx_elements(updated)
        updated = _repair_componentized_inline_svg_shape_nesting(updated)
        updated = _strip_void_svg_closing_tags(updated)
        updated = _wrap_sibling_svg_elements_in_fragments(updated)
        updated = _repair_componentized_logical_svg_sibling_conditions(updated)
        updated = _normalize_componentized_declaration_boundaries(updated)
        updated = _hoist_componentized_chart_helper_declarations(updated)
        updated = _repair_componentized_comment_note_continuations(updated)
        updated = _normalize_run_on_natural_language_notes(updated)
        updated = _normalize_lowercase_object_field_labels(updated)
        updated = _normalize_run_on_explanatory_labels(updated)
        updated = _normalize_bare_section_labels(updated)
        updated = _normalize_comment_filename_labels(updated)
        updated = _normalize_componentized_jsx_code_template_literals(updated)
        updated = _repair_componentized_jsx_code_block_literals(updated)
        updated = _repair_componentized_duplicate_jsx_attributes(updated)
        updated = _repair_componentized_jsx_event_handler_arrow_bleed(updated)
        updated = _repair_componentized_split_quoted_literals(updated)
        updated = _repair_componentized_generic_arrow_bleed(updated)
        updated = _repair_componentized_relational_operator_bleed(updated)
        updated = _repair_componentized_comment_url_bleed(updated)
        updated = _repair_componentized_missing_protocol_slashes(updated)
        updated = _repair_componentized_svg_namespace_protocol(updated)
        updated = _repair_componentized_split_svg_value_attributes(updated)
        updated = _repair_componentized_bare_jsx_array_map_expressions(updated)
        updated = _repair_componentized_route_path_comment_bleeds(updated)
        updated = _repair_componentized_inline_jsx_return_boundaries(updated)
        updated = _repair_componentized_link_wrapper_closer_leaks(updated)
        updated = _repair_componentized_orphan_svg_prop_closer_lines(updated)
        updated = _repair_componentized_icon_prop_svg_closer_bleeds(updated)
        updated = _repair_componentized_inline_svg_text_boundary_leaks(updated)
        updated = _repair_componentized_tooltip_foreign_object_closers(updated)
        updated = _repair_componentized_self_closing_component_orphan_closers(updated)
        updated = _repair_componentized_self_closing_component_children(updated)
        updated = _repair_componentized_ternary_branch_orphan_closing_tags(updated)
        updated = _repair_componentized_layout_main_wrapper_leaks(updated)
        updated = _repair_componentized_svg_html_boundary_leaks(updated)
        updated = _repair_componentized_orphaned_parent_family_children(updated)
        updated = _repair_componentized_jsx_root_returns(updated)
        updated = _normalize_run_on_imports(updated)
        updated = _normalize_componentized_currency_formatting(updated)
        updated = _normalize_componentized_preview_router(updated)
        if rel_path.replace("\\", "/") == "src/main.tsx":
            updated = _normalize_componentized_main_entry(updated)
            updated = _ensure_css_import(updated, "./base.css")
            updated = _normalize_componentized_main_entry(updated)
        elif "base.css" in updated:
            updated = BASE_CSS_IMPORT_ANY_RE.sub("", updated)
            updated = BASE_CSS_IMPORT_LINE_RE.sub("", updated)
        updated = _repair_componentized_link_self_closing_children(updated)
        updated = _repair_componentized_bare_react_fragment_closers(updated)
        updated = _repair_componentized_inline_mismatched_closing_tags(updated)
        updated = _repair_componentized_link_wrapper_closer_leaks(updated)
        updated = _repair_componentized_inline_svg_shape_nesting(updated)
        updated = _repair_componentized_self_closing_component_orphan_closers(updated)
        updated = _remove_componentized_orphan_jsx_closing_brace_lines(updated)
        updated = _repair_componentized_multiline_map_branch_closers(updated)
        updated = _repair_componentized_map_branch_wrapper_closers(updated)
        updated = _repair_componentized_missing_sibling_closing_tags(updated)
        updated = _repair_componentized_jsx_branch_missing_closers(updated)
        updated = _remove_componentized_duplicate_closing_tag_lines(updated)
        # Last-resort: strip orphan */ closers that survived all prior repairs
        updated = _repair_orphan_block_comment_close(updated)
        # Last-resort: close unclosed JSX tags before ); at end of return blocks
        updated = _repair_jsx_return_unclosed_tags(updated)
        updated = _strip_void_svg_closing_tags(updated)
        updated = _remove_componentized_orphan_closing_tag_lines(updated)
        updated = _repair_componentized_icon_prop_svg_closer_bleeds(updated)
        updated = _repair_componentized_inline_svg_text_boundary_leaks(updated)
        updated = _repair_componentized_tooltip_foreign_object_closers(updated)
        updated = _repair_componentized_duplicate_self_closing_slashes(updated)
        updated = _remove_componentized_self_closed_component_closer_lines(updated)
        updated = _repair_componentized_svg_html_boundary_leaks(updated)
        updated = _repair_componentized_terminal_wrapper_closers(updated)
        updated = _repair_componentized_layout_main_wrapper_leaks(updated)
        updated = _repair_componentized_commented_destructured_props(updated)
        updated = _repair_componentized_orphan_prose_comment_lines(updated)
        updated = _repair_componentized_split_state_setters(updated)
        updated = _repair_componentized_split_camel_identifiers(updated)
        updated = _repair_componentized_orphan_svg_prop_closer_lines(updated)
        updated = _repair_componentized_icon_prop_svg_closer_bleeds(updated)
        updated = _repair_componentized_duplicate_self_closing_slashes(updated)
        updated = _remove_componentized_self_closed_component_closer_lines(updated)
        updated = _repair_componentized_chart_footer_wrapper_closers(updated)
        updated = _repair_componentized_multiline_map_branch_closers(updated)
        updated = _repair_componentized_map_branch_wrapper_closers(updated)
        updated = _repair_componentized_split_quoted_literals(updated)
        updated = _repair_componentized_multiline_map_branch_closers(updated)

    return updated


def _normalize_componentized_react_icons_imports(source: str) -> str:
    if "react-icons/fi" not in source:
        return source

    replacements: dict[str, str] = {}

    def _replace_import(match: re.Match[str]) -> str:
        raw_names = match.group("names")
        quote = match.group("quote")
        parts = [part.strip() for part in raw_names.replace("\n", " ").split(",") if part.strip()]
        normalized_parts: list[str] = []
        seen: set[str] = set()

        for part in parts:
            alias_split = re.split(r"\s+as\s+", part, maxsplit=1)
            imported_name = alias_split[0].strip()
            replacement_name = COMPONENTIZED_REACT_ICON_EXPORT_ALIASES.get(imported_name, imported_name)
            if replacement_name != imported_name:
                replacements[imported_name] = replacement_name

            exported_token = replacement_name
            local_token = alias_split[1].strip() if len(alias_split) == 2 else replacement_name
            dedupe_key = f"{exported_token}::{local_token}"
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            if len(alias_split) == 2:
                normalized_parts.append(f"{exported_token} as {local_token}")
            else:
                normalized_parts.append(exported_token)

        return f"import {{ {', '.join(normalized_parts)} }} from {quote}react-icons/fi{quote};"

    updated = REACT_ICONS_FEATHER_IMPORT_RE.sub(_replace_import, source)
    for old_name, new_name in replacements.items():
        updated = re.sub(rf"\b{re.escape(old_name)}\b", new_name, updated)
    return updated


def _normalize_componentized_package_json(source: str) -> str:
    candidate = _repair_json_leading_comma_noise(_repair_json_escape_noise(source))
    try:
        data = json.loads(candidate)
    except json.JSONDecodeError:
        return candidate

    if not isinstance(data, dict):
        return candidate

    scripts = data.setdefault("scripts", {})
    if isinstance(scripts, dict):
        vite_cli = "node ./node_modules/vite/bin/vite.js"

        def _rewrite_vite_command(value: str, fallback: str) -> str:
            command = str(value or "").strip()
            if not command:
                return fallback
            if "tsc" in command:
                return fallback
            if vite_cli in command:
                return command
            if re.search(r"(?<![\w./-])vite(?![\w./-])", command):
                return re.sub(r"(?<![\w./-])vite(?![\w./-])", vite_cli, command)
            return command

        build_value = str(scripts.get("build") or "").strip()
        scripts["build"] = _rewrite_vite_command(build_value, f"{vite_cli} build")
        scripts["dev"] = _rewrite_vite_command(str(scripts.get("dev") or "").strip(), vite_cli)
        scripts["preview"] = _rewrite_vite_command(
            str(scripts.get("preview") or "").strip(),
            f"{vite_cli} preview",
        )

    normalized = json.dumps(data, indent=2, ensure_ascii=False)
    return normalized + "\n"


def _repair_json_escape_noise(source: str) -> str:
    if "\\n" not in source and "\\r" not in source and "\\t" not in source:
        return source

    repaired: list[str] = []
    in_string = False
    escaped = False
    idx = 0
    while idx < len(source):
        char = source[idx]
        if in_string:
            repaired.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            idx += 1
            continue

        if char == '"':
            in_string = True
            repaired.append(char)
            idx += 1
            continue

        if char == "\\" and idx + 1 < len(source):
            next_char = source[idx + 1]
            if next_char in {"n", "r"}:
                repaired.append("\n")
                idx += 2
                continue
            if next_char == "t":
                repaired.append("\t")
                idx += 2
                continue

        repaired.append(char)
        idx += 1

    repaired_source = "".join(repaired)
    if repaired_source == source and JSON_ESCAPE_NOISE_RE.search(source):
        return source.replace("\\n", "\n").replace("\\r", "\n").replace("\\t", "\t")
    return repaired_source


def _strip_json_comments(source: str) -> str:
    repaired: list[str] = []
    in_string = False
    escaped = False
    in_line_comment = False
    in_block_comment = False
    idx = 0

    while idx < len(source):
        char = source[idx]
        next_char = source[idx + 1] if idx + 1 < len(source) else ""

        if in_line_comment:
            if char in "\r\n":
                in_line_comment = False
                repaired.append(char)
            idx += 1
            continue

        if in_block_comment:
            if char == "*" and next_char == "/":
                in_block_comment = False
                idx += 2
                continue
            if char in "\r\n":
                repaired.append(char)
            idx += 1
            continue

        if in_string:
            repaired.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            idx += 1
            continue

        if char == '"':
            in_string = True
            repaired.append(char)
            idx += 1
            continue

        if char == "/" and next_char == "/":
            in_line_comment = True
            idx += 2
            continue

        if char == "/" and next_char == "*":
            in_block_comment = True
            idx += 2
            continue

        repaired.append(char)
        idx += 1

    return "".join(repaired)


def _repair_json_leading_comma_noise(source: str) -> str:
    source = re.sub(r'(?m)^[ \t]*,[ \t]*(?:(?:/\*.*\*/)|(?://.*))?$', "", source)
    return re.sub(r'(^[ \t]*),([ \t]*(?:"|\{|\[))', r"\1\2", source, flags=re.MULTILINE)


def _repair_json_missing_property_commas(source: str) -> str:
    value_expr = r'(?:"(?:[^"\\]|\\.)*"|\btrue\b|\bfalse\b|\bnull\b|-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?|\}|\])'
    return re.sub(
        rf"({value_expr})(\s*\n\s*)(?=\")",
        r"\1,\2",
        source,
    )


def _sync_componentized_package_dependencies(code_dir: Path) -> list[str]:
    package_json_path = code_dir / "package.json"
    if not package_json_path.exists():
        return []

    try:
        data = json.loads(package_json_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []

    if not isinstance(data, dict):
        return []

    dependencies = data.setdefault("dependencies", {})
    dev_dependencies = data.setdefault("devDependencies", {})
    if not isinstance(dependencies, dict) or not isinstance(dev_dependencies, dict):
        return []

    detected_packages: set[str] = set()
    for rel_path in collect_componentized_editable_files(code_dir):
        if not rel_path.endswith((".ts", ".tsx", ".js", ".jsx")):
            continue
        path = code_dir / rel_path
        try:
            source = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for match in PACKAGE_IMPORT_RE.finditer(source):
            specifier = match.group(1).strip()
            if not specifier or specifier.startswith((".", "/", "node:")):
                continue
            package_name = _root_package_name(specifier)
            if package_name in SAFE_COMPONENTIZED_DEPENDENCIES:
                detected_packages.add(package_name)

    added: list[str] = []
    for package_name in sorted(detected_packages):
        if package_name in dependencies or package_name in dev_dependencies:
            continue
        dependencies[package_name] = SAFE_COMPONENTIZED_DEPENDENCIES[package_name]
        added.append(package_name)

    if not added:
        return []

    normalized = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    package_json_path.write_text(normalized, encoding="utf-8")
    return added


def _ensure_componentized_vite_bin_shims(code_dir: Path) -> list[str]:
    vite_entry = code_dir / "node_modules" / "vite" / "bin" / "vite.js"
    if not vite_entry.exists():
        return []

    bin_dir = code_dir / "node_modules" / ".bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    created: list[str] = []

    vite_cmd = bin_dir / "vite.cmd"
    if not vite_cmd.exists():
        vite_cmd.write_text(
            "@ECHO off\r\n"
            "SETLOCAL\r\n"
            "node \"%~dp0\\..\\vite\\bin\\vite.js\" %*\r\n",
            encoding="utf-8",
        )
        created.append("node_modules/.bin/vite.cmd")

    vite_sh = bin_dir / "vite"
    if not vite_sh.exists():
        vite_sh.write_text(
            "#!/bin/sh\n"
            "basedir=$(dirname \"$0\")\n"
            "node \"$basedir/../vite/bin/vite.js\" \"$@\"\n",
            encoding="utf-8",
        )
        created.append("node_modules/.bin/vite")

    return created


def _normalize_componentized_tsconfig(source: str) -> str:
    source = _repair_json_missing_property_commas(
        _repair_json_leading_comma_noise(_strip_json_comments(_repair_json_escape_noise(source)))
    )
    try:
        data = json.loads(source)
    except json.JSONDecodeError:
        return source

    if not isinstance(data, dict):
        return source

    compiler_options = data.setdefault("compilerOptions", {})
    if isinstance(compiler_options, dict):
        # Strip comment-like keys the LLM sometimes emits as pseudo-comments
        # e.g. "/* Bundler mode */": "", "/* Linting */": ""
        comment_keys = [k for k in compiler_options if k.startswith("/*") or k.startswith("//")]
        for k in comment_keys:
            del compiler_options[k]
        compiler_options["noUnusedLocals"] = False
        compiler_options["noUnusedParameters"] = False
        compiler_options.setdefault("allowImportingTsExtensions", True)

    normalized = json.dumps(data, indent=2, ensure_ascii=False)
    return normalized + "\n"


def _normalize_componentized_index_css(source: str) -> str:
    stripped = source.strip()
    if (
        "font-family: system-ui" in stripped
        and ".page {" in stripped
        and ".card {" in stripped
    ):
        return "/* App-specific overrides live here. Keep this file intentionally minimal. */\n"
    updated = re.sub(r"^\s*@extend\s+[^;]+;\s*$\n?", "", source, flags=re.MULTILINE)
    updated = _normalize_componentized_invalid_hex_colors(updated)
    updated = _normalize_componentized_broken_responsive_tail(updated)
    return updated


def _normalize_componentized_design_overrides(code_dir: Path) -> list[str]:
    base_css_path = code_dir / "src" / "base.css"
    if not base_css_path.exists():
        return []

    try:
        base_css = base_css_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []

    base_lower = base_css.lower()
    has_display_font = "space grotesk" in base_lower or "outfit" in base_lower
    has_mono_font = "jetbrains mono" in base_lower
    if not has_display_font and not has_mono_font:
        return []

    rewritten: list[str] = []
    for rel_path in collect_componentized_editable_files(code_dir):
        normalized = rel_path.replace("\\", "/")
        if not normalized.endswith(".css") or normalized == "src/base.css":
            continue
        if normalized not in {"src/index.css", "src/style.css", "src/styles.css"} and not normalized.startswith("src/styles/"):
            continue

        path = code_dir / normalized
        try:
            source = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        updated = _normalize_componentized_override_css(
            source,
            has_display_font=has_display_font,
            has_mono_font=has_mono_font,
        )
        if updated != source:
            path.write_text(updated, encoding="utf-8")
            rewritten.append(normalized)

    return rewritten


def _sync_componentized_polish_guard(
    code_dir: Path,
    *,
    ui_archetype: str | None,
) -> tuple[list[str], list[str]]:
    normalized_archetype = (ui_archetype or "").strip().lower()
    guard_path = code_dir / "src" / "polish-guard.css"
    runtime_path = code_dir / "src" / "polish-guard.ts"
    main_path = code_dir / "src" / "main.tsx"
    target_css = _build_componentized_polish_guard_css(normalized_archetype)
    target_runtime = _build_componentized_polish_guard_runtime(normalized_archetype)
    created_files: list[str] = []
    rewritten_files: list[str] = []

    if target_css is None:
        if guard_path.exists():
            guard_path.unlink()
            rewritten_files.append("src/polish-guard.css")
        if runtime_path.exists():
            runtime_path.unlink()
            rewritten_files.append("src/polish-guard.ts")
        if main_path.exists():
            original_main = main_path.read_text(encoding="utf-8", errors="replace")
            updated_main = _normalize_componentized_main_entry(
                _remove_main_side_effect_import(
                    _remove_css_import(original_main, POLISH_GUARD_IMPORT),
                    POLISH_GUARD_RUNTIME_IMPORT,
                )
            )
            if updated_main != original_main:
                main_path.write_text(updated_main, encoding="utf-8")
                rewritten_files.append("src/main.tsx")
        return created_files, rewritten_files

    guard_path.parent.mkdir(parents=True, exist_ok=True)
    if not guard_path.exists():
        guard_path.write_text(target_css, encoding="utf-8")
        created_files.append("src/polish-guard.css")
    else:
        original_css = guard_path.read_text(encoding="utf-8", errors="replace")
        if original_css != target_css:
            guard_path.write_text(target_css, encoding="utf-8")
            rewritten_files.append("src/polish-guard.css")

    if target_runtime is not None:
        if not runtime_path.exists():
            runtime_path.write_text(target_runtime, encoding="utf-8")
            created_files.append("src/polish-guard.ts")
        else:
            original_runtime = runtime_path.read_text(encoding="utf-8", errors="replace")
            if original_runtime != target_runtime:
                runtime_path.write_text(target_runtime, encoding="utf-8")
                rewritten_files.append("src/polish-guard.ts")
    elif runtime_path.exists():
        runtime_path.unlink()
        rewritten_files.append("src/polish-guard.ts")

    if main_path.exists():
        original_main = main_path.read_text(encoding="utf-8", errors="replace")
        if target_runtime is None:
            main_with_runtime = _remove_main_side_effect_import(original_main, POLISH_GUARD_RUNTIME_IMPORT)
        else:
            main_with_runtime = _ensure_main_side_effect_import(original_main, POLISH_GUARD_RUNTIME_IMPORT)
        updated_main = _normalize_componentized_main_entry(
            _ensure_css_import(
                main_with_runtime,
                POLISH_GUARD_IMPORT,
            )
        )
        if updated_main != original_main:
            main_path.write_text(updated_main, encoding="utf-8")
            rewritten_files.append("src/main.tsx")

    return created_files, rewritten_files


def _build_componentized_polish_guard_css(ui_archetype: str) -> str | None:
    if not _supports_componentized_polish_guard(ui_archetype):
        return None

    if ui_archetype == "game" or ui_archetype.startswith("game_"):
        return (
            "/* Runtime shell polish guard for game fan-page shells. */\n"
            ".hero-cinematic {\n"
            "  position: relative !important;\n"
            "  isolation: isolate;\n"
            "}\n\n"
            ".hero-cinematic .hero-bg-image,\n"
            ".hero-cinematic .hero-bg-overlay {\n"
            "  pointer-events: none;\n"
            "}\n\n"
            ".hero-cinematic .hero-content {\n"
            "  position: relative;\n"
            "  z-index: 3;\n"
            "  padding-bottom: clamp(5.5rem, 10vh, 7.5rem) !important;\n"
            "}\n\n"
            ".hero-cinematic .hero-ctas {\n"
            "  position: relative;\n"
            "  z-index: 3;\n"
            "  margin-bottom: clamp(4.8rem, 9vh, 6.8rem) !important;\n"
            "}\n\n"
            ".hero-cinematic > .scroll-indicator,\n"
            ".hero-cinematic .hero-content > .scroll-indicator {\n"
            "  position: absolute !important;\n"
            "  left: 50% !important;\n"
            "  bottom: clamp(18px, 3vw, 30px) !important;\n"
            "  transform: translateX(-50%) !important;\n"
            "  z-index: 4 !important;\n"
            "  width: max-content;\n"
            "  display: inline-flex;\n"
            "  flex-direction: column;\n"
            "  align-items: center;\n"
            "  gap: 0.35rem;\n"
            "  pointer-events: none;\n"
            "}\n\n"
            ".hero-cinematic .scroll-indicator,\n"
            ".hero-cinematic .scroll-indicator .mouse-icon,\n"
            ".hero-cinematic .scroll-indicator-text {\n"
            "  filter: drop-shadow(0 12px 24px rgba(4, 10, 22, 0.32));\n"
            "}\n\n"
            ".hero-eyebrow,\n"
            ".eyebrow,\n"
            ".nav-link,\n"
            ".nav-links a,\n"
            ".section-title,\n"
            ".char-name,\n"
            ".character-name,\n"
            ".pokemon-name,\n"
            ".badge-name,\n"
            ".location-name,\n"
            ".location-card h3,\n"
            ".hero-title-name,\n"
            ".hero-title-numeral,\n"
            ".scroll-indicator-text {\n"
            "  font-family: var(--font-display, 'Space Grotesk', 'Inter', sans-serif) !important;\n"
            "}\n\n"
            ".pokemon-name,\n"
            ".badge-name,\n"
            ".location-name,\n"
            ".char-name,\n"
            ".character-name {\n"
            "  font-size: clamp(1.02rem, 0.46vw + 0.96rem, 1.32rem) !important;\n"
            "  font-weight: 700 !important;\n"
            "  letter-spacing: 0.03em !important;\n"
            "}\n\n"
            ".badge-details,\n"
            ".char-role,\n"
            ".pokemon-type,\n"
            ".location-region,\n"
            ".section-subtitle {\n"
            "  font-family: var(--font-body, 'Inter', sans-serif) !important;\n"
            "}\n\n"
            ".fade-up-section,\n"
            ".scroll-reveal,\n"
            ".fade-in-up {\n"
            "  opacity: 1 !important;\n"
            "  transform: none !important;\n"
            "}\n\n"
            ".ability-card img[src$='.svg'],\n"
            ".badge-card img[src$='.svg'],\n"
            ".evolution-stage img[src$='.svg'],\n"
            ".world-map-image img[src$='.svg'] {\n"
            "  object-fit: contain !important;\n"
            "  padding: 0.8rem;\n"
            "  background: linear-gradient(135deg, rgba(255, 255, 255, 0.06), rgba(255, 255, 255, 0.015));\n"
            "}\n\n"
            ".runtime-inline-detail {\n"
            "  margin-top: 1rem;\n"
            "}\n\n"
            ".runtime-inline-detail > summary {\n"
            "  list-style: none;\n"
            "  cursor: pointer;\n"
            "}\n\n"
            ".runtime-inline-detail > summary::-webkit-details-marker {\n"
            "  display: none;\n"
            "}\n\n"
            ".runtime-inline-detail-panel {\n"
            "  margin-top: 0.85rem;\n"
            "  padding: 1rem 1.05rem;\n"
            "  border: 1px solid rgba(255, 255, 255, 0.1);\n"
            "  border-radius: 18px;\n"
            "  background: linear-gradient(180deg, rgba(72, 171, 240, 0.12), rgba(7, 12, 20, 0.78));\n"
            "  box-shadow: 0 18px 36px rgba(0, 0, 0, 0.24);\n"
            "  animation: runtimeGameDetailIn 220ms ease-out;\n"
            "}\n\n"
            ".runtime-inline-detail-kicker {\n"
            "  font-size: 0.72rem;\n"
            "  letter-spacing: 0.18em;\n"
            "  text-transform: uppercase;\n"
            "  color: rgba(110, 214, 255, 0.88);\n"
            "}\n\n"
            ".runtime-inline-detail-title {\n"
            "  margin: 0.45rem 0 0.35rem;\n"
            "  font-size: 1rem;\n"
            "}\n\n"
            ".runtime-inline-detail-copy {\n"
            "  margin: 0;\n"
            "  color: rgba(228, 235, 255, 0.82);\n"
            "}\n\n"
            ".runtime-inline-detail-stats {\n"
            "  display: flex;\n"
            "  flex-wrap: wrap;\n"
            "  gap: 0.55rem;\n"
            "  margin-top: 0.85rem;\n"
            "}\n\n"
            ".runtime-inline-detail-chip {\n"
            "  display: inline-flex;\n"
            "  align-items: center;\n"
            "  padding: 0.35rem 0.7rem;\n"
            "  border-radius: 999px;\n"
            "  border: 1px solid rgba(110, 214, 255, 0.24);\n"
            "  background: rgba(9, 20, 35, 0.72);\n"
            "  color: rgba(110, 214, 255, 0.96);\n"
            "  font-size: 0.75rem;\n"
            "  letter-spacing: 0.08em;\n"
            "  text-transform: uppercase;\n"
            "}\n\n"
            ".runtime-world-map-fallback {\n"
            "  position: relative;\n"
            "  min-height: clamp(260px, 36vw, 420px);\n"
            "  overflow: hidden;\n"
            "  border-radius: 28px;\n"
            "  border: 1px solid rgba(255, 255, 255, 0.08);\n"
            "  background: radial-gradient(circle at 50% 35%, rgba(72, 171, 240, 0.12), transparent 34%), linear-gradient(135deg, rgba(10, 18, 29, 0.98), rgba(6, 9, 16, 0.94));\n"
            "}\n\n"
            ".runtime-world-map-grid {\n"
            "  position: absolute;\n"
            "  inset: 0;\n"
            "  background-image: linear-gradient(rgba(110, 214, 255, 0.09) 1px, transparent 1px), linear-gradient(90deg, rgba(110, 214, 255, 0.09) 1px, transparent 1px);\n"
            "  background-size: 56px 56px;\n"
            "  mask-image: radial-gradient(circle at center, black 48%, transparent 100%);\n"
            "}\n\n"
            ".runtime-world-map-copy {\n"
            "  position: relative;\n"
            "  z-index: 1;\n"
            "  display: grid;\n"
            "  place-items: center;\n"
            "  min-height: inherit;\n"
            "  padding: 2rem;\n"
            "  text-align: center;\n"
            "}\n\n"
            ".runtime-world-map-eyebrow {\n"
            "  display: inline-block;\n"
            "  margin-bottom: 0.65rem;\n"
            "  font-size: 0.72rem;\n"
            "  letter-spacing: 0.22em;\n"
            "  text-transform: uppercase;\n"
            "  color: rgba(110, 214, 255, 0.82);\n"
            "}\n\n"
            ".runtime-world-map-title {\n"
            "  display: block;\n"
            "  font-size: clamp(1.4rem, 2vw + 1rem, 2.2rem);\n"
            "  letter-spacing: 0.06em;\n"
            "  text-transform: uppercase;\n"
            "}\n\n"
            ".runtime-world-map-text {\n"
            "  max-width: 34rem;\n"
            "  margin: 0.8rem auto 0;\n"
            "  color: rgba(228, 235, 255, 0.82);\n"
            "}\n\n"
            "@keyframes runtimeGameDetailIn {\n"
            "  from { opacity: 0; transform: translateY(8px) scale(0.985); }\n"
            "  to { opacity: 1; transform: translateY(0) scale(1); }\n"
            "}\n"
        )

    if ui_archetype == "fintech":
        accent_glow = "rgba(24, 144, 255, 0.32)"
        accent_soft = "rgba(78, 168, 255, 0.16)"
        topbar_tint = "rgba(8, 14, 24, 0.82)"
        body_gradient = (
            "radial-gradient(circle at top right, rgba(0, 122, 255, 0.16), transparent 28%),\n"
            "    radial-gradient(circle at bottom left, rgba(26, 188, 156, 0.1), transparent 22%),"
        )
    else:
        accent_glow = "rgba(79, 144, 255, 0.28)"
        accent_soft = "rgba(79, 144, 255, 0.14)"
        topbar_tint = "rgba(7, 12, 20, 0.78)"
        body_gradient = (
            "radial-gradient(circle at top right, rgba(61, 117, 255, 0.16), transparent 26%),\n"
            "    radial-gradient(circle at bottom left, rgba(15, 193, 132, 0.08), transparent 24%),"
        )
    dashboard_specific_css = (
        ".dashboard-layout .kpi-card,\n"
        ".dashboard-shell .kpi-card {\n"
        "  --guard-panel-accent: rgba(var(--accent-rgb, 79, 144, 255), 0.52);\n"
        "  background: linear-gradient(158deg, rgba(var(--accent-rgb, 79, 144, 255), 0.14), rgba(255, 255, 255, 0.018) 52%),\n"
        "    var(--card-bg, var(--surface, #111827)) !important;\n"
        "}\n\n"
        ".dashboard-layout .kpi-card:nth-child(4n + 2),\n"
        ".dashboard-layout .kpi-card:nth-child(4n + 3),\n"
        ".dashboard-layout .kpi-card:nth-child(4n),\n"
        ".dashboard-shell .kpi-card:nth-child(4n + 2),\n"
        ".dashboard-shell .kpi-card:nth-child(4n + 3),\n"
        ".dashboard-shell .kpi-card:nth-child(4n) {\n"
        "  --guard-panel-accent: rgba(var(--accent-rgb, 79, 144, 255), 0.52);\n"
        "}\n\n"
        ".dashboard-layout .data-table thead th,\n"
        ".dashboard-layout .asset-table thead th,\n"
        ".dashboard-shell .data-table thead th,\n"
        ".dashboard-shell .asset-table thead th {\n"
        "  font-size: 0.76rem !important;\n"
        "  font-weight: 700 !important;\n"
        "  color: rgba(226, 232, 240, 0.74) !important;\n"
        "  letter-spacing: 0.12em !important;\n"
        "}\n\n"
        ".dashboard-layout .activity-item,\n"
        ".dashboard-layout .market-watch-item,\n"
        ".dashboard-shell .activity-item,\n"
        ".dashboard-shell .market-watch-item {\n"
        "  cursor: pointer;\n"
        "}\n\n"
        ".dashboard-layout .activity-item .activity-time,\n"
        ".dashboard-layout .market-watch-item .market-watch-name,\n"
        ".dashboard-shell .activity-item .activity-time,\n"
        ".dashboard-shell .market-watch-item .market-watch-name {\n"
        "  font-size: 0.74rem !important;\n"
        "  font-weight: 700 !important;\n"
        "  text-transform: uppercase;\n"
        "  letter-spacing: 0.12em !important;\n"
        "  color: rgba(160, 174, 192, 0.8) !important;\n"
        "}\n\n"
        ".dashboard-layout .cell-action,\n"
        ".dashboard-layout .table-action,\n"
        ".dashboard-layout .action-link,\n"
        ".dashboard-shell .cell-action,\n"
        ".dashboard-shell .table-action,\n"
        ".dashboard-shell .action-link {\n"
        "  display: inline-flex;\n"
        "  align-items: center;\n"
        "  gap: 0.3rem;\n"
        "  padding: 0.34rem 0.7rem;\n"
        "  border-radius: 999px;\n"
        "  border: 1px solid rgba(var(--accent-rgb, 79, 144, 255), 0.22);\n"
        "  background: linear-gradient(135deg, rgba(var(--accent-rgb, 79, 144, 255), 0.16), rgba(255, 255, 255, 0.03));\n"
        "  box-shadow: 0 10px 18px rgba(2, 6, 23, 0.18);\n"
        "  font-size: 0.76rem !important;\n"
        "  font-weight: 700 !important;\n"
        "  letter-spacing: 0.08em !important;\n"
        "  text-transform: uppercase;\n"
        "}\n\n"
        ".dashboard-layout .cell-action:hover,\n"
        ".dashboard-layout .table-action:hover,\n"
        ".dashboard-layout .action-link:hover,\n"
        ".dashboard-shell .cell-action:hover,\n"
        ".dashboard-shell .table-action:hover,\n"
        ".dashboard-shell .action-link:hover {\n"
        "  transform: translateY(-1px);\n"
        "  border-color: rgba(var(--accent-rgb, 79, 144, 255), 0.42);\n"
        "  box-shadow: 0 16px 26px rgba(2, 6, 23, 0.24), 0 0 0 1px rgba(var(--accent-rgb, 79, 144, 255), 0.18);\n"
        "}\n\n"
        if ui_archetype == "dashboard"
        else ""
    )

    return (
        f"/* Runtime shell polish guard for {ui_archetype} app shells. */\n"
        ":root {\n"
        "  color-scheme: dark;\n"
        "  --guard-surface: rgba(255, 255, 255, 0.02);\n"
        "  --guard-border-strong: rgba(255, 255, 255, 0.09);\n"
        f"  --guard-accent-soft: {accent_soft};\n"
        f"  --guard-accent-glow: {accent_glow};\n"
        "  --guard-shadow-card: 0 18px 40px rgba(3, 8, 18, 0.34), 0 4px 14px rgba(3, 8, 18, 0.22);\n"
        "  --guard-shadow-elevated: 0 22px 50px rgba(2, 6, 23, 0.42), 0 8px 18px rgba(2, 6, 23, 0.24);\n"
        "  --guard-kpi-accent-a: rgba(79, 144, 255, 0.82);\n"
        "  --guard-kpi-accent-b: rgba(16, 185, 129, 0.8);\n"
        "  --guard-kpi-accent-c: rgba(255, 191, 87, 0.8);\n"
        "  --guard-kpi-accent-d: rgba(248, 113, 113, 0.76);\n"
        "  --guard-chart-accent: rgba(79, 144, 255, 0.82);\n"
        "  --guard-activity-accent: rgba(16, 185, 129, 0.8);\n"
        "  --guard-table-accent: rgba(255, 191, 87, 0.78);\n"
        "}\n\n"
        "body {\n"
        f"  background: {body_gradient}\n"
        "    var(--bg, #0a1018) !important;\n"
        "}\n\n"
        ".fintech-shell,\n"
        ".dashboard-shell,\n"
        ".dashboard-layout,\n"
        ".app-shell,\n"
        ".main-content,\n"
        ".main-content-wrapper,\n"
        ".main-content-area,\n"
        ".content-area {\n"
        "  position: relative;\n"
        "}\n\n"
        ".guard-fixed-sidebar-shell {\n"
        "  display: grid !important;\n"
        "  grid-template-columns: var(--guard-sidebar-offset, 240px) minmax(0, 1fr) !important;\n"
        "  align-items: start !important;\n"
        "}\n\n"
        ".guard-fixed-sidebar-shell > .main-content,\n"
        ".guard-fixed-sidebar-shell > .content-area,\n"
        ".guard-fixed-sidebar-shell > .dashboard-main,\n"
        ".guard-fixed-sidebar-shell > .workspace-main,\n"
        ".guard-fixed-sidebar-shell > main {\n"
        "  grid-column: 2 / -1 !important;\n"
        "  min-width: 0 !important;\n"
        "  width: auto !important;\n"
        "}\n\n"
        ".guard-fixed-sidebar-shell > .main-content {\n"
        "  margin-left: 0 !important;\n"
        "}\n\n"
        ".guard-fixed-sidebar-shell .content-area,\n"
        ".guard-fixed-sidebar-shell .dashboard-main,\n"
        ".guard-fixed-sidebar-shell .workspace-main,\n"
        ".guard-fixed-sidebar-shell .kpi-grid,\n"
        ".guard-fixed-sidebar-shell .data-table-wrapper,\n"
        ".guard-fixed-sidebar-shell .chart-card {\n"
        "  min-width: 0 !important;\n"
        "  width: 100% !important;\n"
        "}\n\n"
        ".guard-fixed-sidebar-shell .kpi-grid {\n"
        "  grid-template-columns: repeat(auto-fit, minmax(min(220px, 100%), 1fr)) !important;\n"
        "}\n\n"
        ".guard-fixed-sidebar-shell .grid-2col,\n"
        ".guard-fixed-sidebar-shell .content-grid,\n"
        ".guard-fixed-sidebar-shell .dashboard-grid {\n"
        "  grid-template-columns: minmax(0, 1.7fr) minmax(320px, 0.96fr) !important;\n"
        "  align-items: start !important;\n"
        "}\n\n"
        ".guard-direct-rail-shell {\n"
        "  grid-template-columns: var(--guard-sidebar-offset, 240px) minmax(0, 1fr) minmax(280px, 360px) !important;\n"
        "  align-items: start !important;\n"
        "}\n\n"
        ".guard-direct-rail-shell > .main-content,\n"
        ".guard-direct-rail-shell > .main-content-wrapper,\n"
        ".guard-direct-rail-shell > .main-content-area,\n"
        ".guard-direct-rail-shell > .content-area,\n"
        ".guard-direct-rail-shell > .dashboard-main,\n"
        ".guard-direct-rail-shell > .workspace-main,\n"
        ".guard-direct-rail-shell > main {\n"
        "  grid-column: 2 / 3 !important;\n"
        "  min-width: 0 !important;\n"
        "}\n\n"
        ".guard-direct-rail-shell > .right-rail,\n"
        ".guard-direct-rail-shell > .right-sidebar,\n"
        ".guard-direct-rail-shell > .support-rail,\n"
        ".guard-direct-rail-shell > .insights-rail,\n"
        ".guard-direct-rail-shell > .side-panel {\n"
        "  grid-column: 3 / 4 !important;\n"
        "  width: auto !important;\n"
        "  min-width: 0 !important;\n"
        "  max-width: 100% !important;\n"
        "  align-self: start !important;\n"
        "  position: sticky;\n"
        "  top: clamp(1rem, 1.8vw, 1.5rem);\n"
        "}\n\n"
        ".guard-nested-rail-shell {\n"
        "  grid-template-columns: var(--guard-sidebar-offset, 240px) minmax(0, 1fr) 0 !important;\n"
        "}\n\n"
        ".guard-main-rail-split {\n"
        "  display: grid !important;\n"
        "  grid-template-columns: minmax(0, 1.72fr) minmax(300px, 0.96fr) !important;\n"
        "  gap: clamp(1rem, 1.8vw, 1.75rem) !important;\n"
        "  align-items: start !important;\n"
        "  min-width: 0 !important;\n"
        "}\n\n"
        ".guard-main-rail-split > * {\n"
        "  min-width: 0 !important;\n"
        "}\n\n"
        ".guard-main-rail-primary {\n"
        "  min-width: 0 !important;\n"
        "  width: 100% !important;\n"
        "}\n\n"
        ".guard-main-rail-secondary {\n"
        "  min-width: min(320px, 100%) !important;\n"
        "  width: min(360px, 100%) !important;\n"
        "  max-width: 100% !important;\n"
        "  align-self: start !important;\n"
        "  position: sticky;\n"
        "  top: clamp(1rem, 1.8vw, 1.5rem);\n"
        "}\n\n"
        "@media (max-width: 1080px) {\n"
        "  .guard-fixed-sidebar-shell .grid-2col,\n"
        "  .guard-fixed-sidebar-shell .content-grid,\n"
        "  .guard-fixed-sidebar-shell .dashboard-grid {\n"
        "    grid-template-columns: 1fr !important;\n"
        "  }\n"
        "}\n\n"
        "@media (max-width: 1180px) {\n"
        "  .guard-direct-rail-shell {\n"
        "    grid-template-columns: var(--guard-sidebar-offset, 240px) minmax(0, 1fr) !important;\n"
        "  }\n"
        "  .guard-direct-rail-shell > .right-rail,\n"
        "  .guard-direct-rail-shell > .right-sidebar,\n"
        "  .guard-direct-rail-shell > .support-rail,\n"
        "  .guard-direct-rail-shell > .insights-rail,\n"
        "  .guard-direct-rail-shell > .side-panel {\n"
        "    grid-column: 2 / -1 !important;\n"
        "    position: static;\n"
        "    width: 100% !important;\n"
        "  }\n"
        "  .guard-main-rail-split {\n"
        "    grid-template-columns: 1fr !important;\n"
        "  }\n"
        "  .guard-main-rail-secondary {\n"
        "    position: static;\n"
        "    width: 100% !important;\n"
        "    min-width: 0 !important;\n"
        "  }\n"
        "}\n\n"
        ".topbar,\n"
        ".top-bar,\n"
        ".header-bar,\n"
        ".sidebar,\n"
        ".left-sidebar {\n"
        f"  background: linear-gradient(180deg, {topbar_tint}, rgba(8, 12, 18, 0.9)) !important;\n"
        "  backdrop-filter: blur(18px);\n"
        "  border-color: var(--guard-border-strong) !important;\n"
        "}\n\n"
        "h1,\n"
        ".h1,\n"
        "h2,\n"
        ".h2,\n"
        "h3,\n"
        ".h3,\n"
        ".page-title,\n"
        ".panel-title,\n"
        ".chart-title,\n"
        ".topbar-brand,\n"
        ".logo-text,\n"
        ".sidebar-group-label,\n"
        ".feed-header {\n"
        "  font-family: var(--font-display, 'Space Grotesk', 'Inter', sans-serif) !important;\n"
        "}\n\n"
        "h1,\n"
        ".h1,\n"
        ".page-title,\n"
        ".topbar-brand,\n"
        ".logo-text {\n"
        "  letter-spacing: -0.04em;\n"
        "}\n\n"
        "h1,\n"
        ".h1,\n"
        ".page-title {\n"
        "  font-size: clamp(2.45rem, 2.25vw + 1.32rem, 3.45rem) !important;\n"
        "  line-height: 1.04 !important;\n"
        "}\n\n"
        ".page-title,\n"
        ".feed-header {\n"
        "  font-weight: 700 !important;\n"
        "}\n\n"
        "h2,\n"
        ".h2 {\n"
        "  font-size: clamp(1.45rem, 1vw + 1.05rem, 2.05rem) !important;\n"
        "  line-height: 1.14 !important;\n"
        "}\n\n"
        "h3,\n"
        ".h3,\n"
        ".panel-title {\n"
        "  font-size: clamp(1.02rem, 0.52vw + 0.96rem, 1.34rem) !important;\n"
        "  line-height: 1.24 !important;\n"
        "}\n\n"
        ".topbar-brand,\n"
        ".logo-text {\n"
        "  font-size: clamp(1.1rem, 0.7vw + 0.95rem, 1.45rem) !important;\n"
        "  font-weight: 700 !important;\n"
        "}\n\n"
        ".kpi-value,\n"
        ".kpi-delta,\n"
        ".ticker-price,\n"
        ".ticker-delta,\n"
        ".watchlist-price,\n"
        ".watchlist-delta,\n"
        ".watch-price,\n"
        ".watch-delta,\n"
        ".news-feed-time,\n"
        ".text-mono,\n"
        ".table-cell,\n"
        ".guard-mono-count,\n"
        ".portfolio-value .value-amount,\n"
        ".chart-axis-label,\n"
        ".candlestick-chart-svg text,\n"
        "svg text.text-mono,\n"
        ".feed-time,\n"
        ".asset-table td,\n"
        ".data-table td,\n"
        ".table-number,\n"
        ".numeric,\n"
        ".numeric-value,\n"
        ".price,\n"
        ".delta {\n"
        "  font-family: var(--font-mono, 'JetBrains Mono', monospace) !important;\n"
        "  font-variant-numeric: tabular-nums !important;\n"
        "}\n\n"
        ".kpi-card,\n"
        ".panel,\n"
        ".card,\n"
        ".chart-card,\n"
        ".ticker-card,\n"
        ".watchlist-feed-panel,\n"
        ".watchlist-panel,\n"
        ".news-feed-panel,\n"
        ".news-feed-section,\n"
        ".news-feed-item,\n"
        ".activity-feed,\n"
        ".asset-table-panel,\n"
        ".data-table-wrapper,\n"
        ".data-table,\n"
        ".sidebar-item.active {\n"
        "  border-color: var(--guard-border-strong) !important;\n"
        "  box-shadow: var(--guard-shadow-card) !important;\n"
        "}\n\n"
        ".kpi-card,\n"
        ".panel,\n"
        ".chart-card,\n"
        ".ticker-card,\n"
        ".watchlist-feed-panel,\n"
        ".watchlist-panel,\n"
        ".news-feed-panel,\n"
        ".news-feed-section,\n"
        ".news-feed-item,\n"
        ".asset-table-panel,\n"
        ".data-table-wrapper,\n"
        ".data-table {\n"
        "  background: linear-gradient(180deg, rgba(255, 255, 255, 0.035), rgba(255, 255, 255, 0.012)),\n"
        "    var(--card-bg, var(--surface, #111827)) !important;\n"
        "}\n\n"
        ".kpi-card:nth-child(4n + 1) {\n"
        "  --guard-panel-accent: var(--guard-kpi-accent-a);\n"
        "  background: linear-gradient(160deg, rgba(79, 144, 255, 0.13), rgba(255, 255, 255, 0.012) 44%),\n"
        "    var(--card-bg, var(--surface, #111827)) !important;\n"
        "}\n\n"
        ".kpi-card:nth-child(4n + 2) {\n"
        "  --guard-panel-accent: var(--guard-kpi-accent-b);\n"
        "  background: linear-gradient(160deg, rgba(16, 185, 129, 0.12), rgba(255, 255, 255, 0.012) 46%),\n"
        "    var(--card-bg, var(--surface, #111827)) !important;\n"
        "}\n\n"
        ".kpi-card:nth-child(4n + 3) {\n"
        "  --guard-panel-accent: var(--guard-kpi-accent-c);\n"
        "  background: linear-gradient(160deg, rgba(255, 191, 87, 0.12), rgba(255, 255, 255, 0.012) 46%),\n"
        "    var(--card-bg, var(--surface, #111827)) !important;\n"
        "}\n\n"
        ".kpi-card:nth-child(4n) {\n"
        "  --guard-panel-accent: var(--guard-kpi-accent-d);\n"
        "  background: linear-gradient(160deg, rgba(248, 113, 113, 0.1), rgba(255, 255, 255, 0.012) 44%),\n"
        "    var(--card-bg, var(--surface, #111827)) !important;\n"
        "}\n\n"
        ".kpi-card.elevated {\n"
        "  box-shadow: var(--guard-shadow-elevated) !important;\n"
        "}\n\n"
        ".chart-card,\n"
        ".chart-panel,\n"
        ".performance-panel,\n"
        ".hero-chart {\n"
        "  --guard-panel-accent: var(--guard-chart-accent);\n"
        "  background: linear-gradient(158deg, rgba(79, 144, 255, 0.13), rgba(255, 255, 255, 0.014) 46%),\n"
        "    var(--card-bg, var(--surface, #111827)) !important;\n"
        "}\n\n"
        ".activity-feed,\n"
        ".activity-panel,\n"
        ".activity-feed-card,\n"
        ".timeline-panel {\n"
        "  --guard-panel-accent: var(--guard-activity-accent);\n"
        "  background: linear-gradient(162deg, rgba(16, 185, 129, 0.13), rgba(255, 255, 255, 0.016) 46%),\n"
        "    var(--card-bg, var(--surface, #111827)) !important;\n"
        "}\n\n"
        ".data-table-wrapper,\n"
        ".asset-table-panel,\n"
        ".table-panel,\n"
        ".holdings-panel,\n"
        ".positions-panel {\n"
        "  --guard-panel-accent: var(--guard-table-accent);\n"
        "  background: linear-gradient(166deg, rgba(255, 191, 87, 0.13), rgba(255, 255, 255, 0.014) 45%),\n"
        "    var(--card-bg, var(--surface, #111827)) !important;\n"
        "}\n\n"
        ".watchlist-feed-panel,\n"
        ".watchlist-panel,\n"
        ".watchlist-card,\n"
        ".activity-feed,\n"
        ".activity-panel,\n"
        ".alerts-panel,\n"
        ".alert-panel {\n"
        "  background: linear-gradient(160deg, rgba(87, 153, 255, 0.12), rgba(255, 255, 255, 0.016) 42%),\n"
        "    var(--card-bg, var(--surface, #111827)) !important;\n"
        "}\n\n"
        ".news-feed-panel,\n"
        ".news-feed-section,\n"
        ".news-panel,\n"
        ".briefing-panel {\n"
        "  background: linear-gradient(160deg, rgba(255, 191, 87, 0.12), rgba(255, 255, 255, 0.016) 44%),\n"
        "    var(--card-bg, var(--surface, #111827)) !important;\n"
        "}\n\n"
        ".kpi-card:hover,\n"
        ".panel:hover,\n"
        ".chart-card:hover,\n"
        ".ticker-card:hover,\n"
        ".news-feed-item:hover,\n"
        ".card:hover {\n"
        "  transform: translateY(-3px);\n"
        "  box-shadow: var(--guard-shadow-elevated) !important;\n"
        "}\n\n"
        ".kpi-card::before,\n"
        ".panel::before,\n"
        ".news-feed-item::before,\n"
        ".chart-card::before {\n"
        "  content: \"\";\n"
        "  position: absolute;\n"
        "  inset: 0;\n"
        "  border-radius: inherit;\n"
        "  pointer-events: none;\n"
        "  background: linear-gradient(180deg, rgba(255, 255, 255, 0.045), transparent 30%);\n"
        "  opacity: 0.55;\n"
        "}\n\n"
        ".kpi-card,\n"
        ".panel,\n"
        ".news-feed-item,\n"
        ".chart-card,\n"
        ".activity-feed,\n"
        ".activity-panel,\n"
        ".activity-feed-card,\n"
        ".data-table-wrapper,\n"
        ".asset-table-panel,\n"
        ".table-panel,\n"
        ".holdings-panel,\n"
        ".positions-panel {\n"
        "  position: relative;\n"
        "  overflow: hidden;\n"
        "  isolation: isolate;\n"
        "}\n\n"
        ".kpi-card::after,\n"
        ".chart-card::after,\n"
        ".chart-panel::after,\n"
        ".performance-panel::after,\n"
        ".hero-chart::after,\n"
        ".activity-feed::after,\n"
        ".activity-panel::after,\n"
        ".activity-feed-card::after,\n"
        ".timeline-panel::after,\n"
        ".data-table-wrapper::after,\n"
        ".asset-table-panel::after,\n"
        ".table-panel::after,\n"
        ".holdings-panel::after,\n"
        ".positions-panel::after {\n"
        "  content: \"\";\n"
        "  position: absolute;\n"
        "  inset: 0 0 auto 0;\n"
        "  height: 3px;\n"
        "  background: linear-gradient(90deg, var(--guard-panel-accent, rgba(255, 255, 255, 0.38)), transparent 82%);\n"
        "  opacity: 0.98;\n"
        "  pointer-events: none;\n"
        "}\n\n"
        ".kpi-value {\n"
        "  font-size: clamp(2rem, 1vw + 1.6rem, 2.9rem) !important;\n"
        "  letter-spacing: -0.05em !important;\n"
        "}\n\n"
        ".kpi-label,\n"
        ".data-table th,\n"
        ".asset-table th,\n"
        ".sidebar-group-label,\n"
        ".value-label {\n"
        "  text-transform: uppercase;\n"
        "  letter-spacing: 0.09em !important;\n"
        "}\n\n"
        ".asset-table thead th,\n"
        ".data-table thead th {\n"
        "  background: rgba(255, 255, 255, 0.02);\n"
        "}\n\n"
        ".asset-table,\n"
        ".data-table {\n"
        "  width: 100% !important;\n"
        "  table-layout: fixed;\n"
        "  border-collapse: collapse;\n"
        "}\n\n"
        ".asset-table th,\n"
        ".asset-table td,\n"
        ".data-table th,\n"
        ".data-table td,\n"
        ".table-cell {\n"
        "  vertical-align: middle;\n"
        "}\n\n"
        ".asset-table td,\n"
        ".data-table td,\n"
        ".table-cell {\n"
        "  padding-top: 0.82rem !important;\n"
        "  padding-bottom: 0.82rem !important;\n"
        "}\n\n"
        ".asset-table td > *,\n"
        ".data-table td > * {\n"
        "  min-width: 0;\n"
        "}\n\n"
        ".asset-table .text-right,\n"
        ".data-table .text-right,\n"
        ".table-number,\n"
        ".numeric,\n"
        ".numeric-value,\n"
        ".price,\n"
        ".delta {\n"
        "  text-align: right !important;\n"
        "  white-space: nowrap;\n"
        "}\n\n"
        ".asset-table tbody tr:hover,\n"
        ".data-table tbody tr:hover,\n"
        ".watch-item:hover,\n"
        ".feed-item:hover {\n"
        "  background: rgba(255, 255, 255, 0.025);\n"
        "}\n\n"
        ".primary-btn,\n"
        ".chart-period-btn.active,\n"
        ".range-pill.active,\n"
        ".interactive-chip,\n"
        ".chart-action-btn,\n"
        ".asset-table-action-btn,\n"
        ".guard-accent-action,\n"
        ".guard-tonal-action,\n"
        ".sidebar-item.active,\n"
        ".status-chip,\n"
        ".market-pill {\n"
        "  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.04), 0 10px 20px rgba(2, 6, 23, 0.22);\n"
        "}\n\n"
        ".primary-btn,\n"
        ".chart-period-btn.active,\n"
        ".range-pill.active,\n"
        ".interactive-chip,\n"
        ".chart-action-btn,\n"
        ".asset-table-action-btn,\n"
        ".guard-accent-action {\n"
        "  background: linear-gradient(135deg, rgba(var(--accent-rgb, 16, 185, 129), 0.24), var(--guard-accent-soft)) !important;\n"
        "  border-color: rgba(var(--accent-rgb, 16, 185, 129), 0.32) !important;\n"
        "  color: var(--text, #f8fafc) !important;\n"
        "}\n\n"
        ".guard-tonal-action {\n"
        "  background: linear-gradient(135deg, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0.028)) !important;\n"
        "  border-color: rgba(255, 255, 255, 0.12) !important;\n"
        "  color: var(--text, #f8fafc) !important;\n"
        "}\n\n"
        ".activity-feed,\n"
        ".watchlist-card,\n"
        ".watchlist-panel {\n"
        "  overflow: hidden;\n"
        "}\n\n"
        ".activity-feed .feed-header,\n"
        ".watchlist-card .feed-header,\n"
        ".watchlist-panel .feed-header {\n"
        "  background: linear-gradient(180deg, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.02));\n"
        "  border-bottom-color: rgba(255, 255, 255, 0.08) !important;\n"
        "}\n\n"
        ".activity-feed {\n"
        "  display: grid;\n"
        "  gap: 0.95rem;\n"
        "}\n\n"
        ".activity-feed > div {\n"
        "  display: grid;\n"
        "  gap: 0.78rem;\n"
        "}\n\n"
        ".activity-item,\n"
        ".watchlist-item,\n"
        ".feed-item {\n"
        "  position: relative;\n"
        "  transition: transform 160ms ease, background 160ms ease, box-shadow 160ms ease !important;\n"
        "}\n\n"
        ".activity-item {\n"
        "  display: grid;\n"
        "  grid-template-columns: auto minmax(0, 1fr);\n"
        "  gap: 0.85rem;\n"
        "  align-items: start;\n"
        "  padding: 1rem 1.05rem;\n"
        "  border-radius: 18px;\n"
        "  background: linear-gradient(180deg, rgba(255, 255, 255, 0.03), rgba(255, 255, 255, 0.012));\n"
        "}\n\n"
        ".activity-item > div:last-child {\n"
        "  min-width: 0;\n"
        "  display: grid;\n"
        "  gap: 0.34rem;\n"
        "}\n\n"
        ".activity-item:hover,\n"
        ".watchlist-item:hover,\n"
        ".feed-item:hover {\n"
        "  transform: translateX(2px);\n"
        "  box-shadow: inset 2px 0 0 rgba(var(--accent-rgb, 16, 185, 129), 0.55);\n"
        "}\n\n"
        ".activity-item .activity-text {\n"
        "  line-height: 1.58 !important;\n"
        "  font-size: 0.95rem !important;\n"
        "}\n\n"
        ".watchlist-price,\n"
        ".activity-time,\n"
        ".cell-action,\n"
        ".table-action,\n"
        ".action-link {\n"
        "  font-family: var(--font-mono, 'JetBrains Mono', monospace) !important;\n"
        "}\n\n"
        ".activity-item .activity-time {\n"
        "  font-size: 0.82rem !important;\n"
        "  letter-spacing: 0.02em;\n"
        "  opacity: 0.78;\n"
        "}\n\n"
        ".cell-action,\n"
        ".table-action,\n"
        ".action-link,\n"
        ".trade-btn {\n"
        "  color: rgba(var(--accent-rgb, 16, 185, 129), 0.92) !important;\n"
        "  text-decoration: none;\n"
        "}\n\n"
        ".cell-action:hover,\n"
        ".table-action:hover,\n"
        ".action-link:hover,\n"
        ".trade-btn:hover {\n"
        "  color: var(--text, #f8fafc) !important;\n"
        "  text-shadow: 0 0 14px rgba(var(--accent-rgb, 16, 185, 129), 0.24);\n"
        "}\n\n"
        ".chart-action-btn,\n"
        ".chart-timeframe-btn,\n"
        ".chart-period-btn,\n"
        ".interactive-chip,\n"
        ".asset-table-action-btn,\n"
        ".guard-accent-action,\n"
        ".guard-tonal-action {\n"
        "  transition: transform 160ms ease, box-shadow 160ms ease, border-color 160ms ease, background 160ms ease, color 160ms ease !important;\n"
        "}\n\n"
        ".chart-action-btn:hover,\n"
        ".chart-timeframe-btn:hover,\n"
        ".chart-period-btn:hover,\n"
        ".interactive-chip:hover,\n"
        ".asset-table-action-btn:hover,\n"
        ".guard-accent-action:hover,\n"
        ".guard-tonal-action:hover {\n"
        "  transform: translateY(-1px);\n"
        "  box-shadow: 0 16px 28px rgba(2, 6, 23, 0.28), 0 0 0 1px rgba(255, 255, 255, 0.08);\n"
        "}\n\n"
        ".chart-action-btn:active,\n"
        ".chart-timeframe-btn:active,\n"
        ".chart-period-btn:active,\n"
        ".interactive-chip:active,\n"
        ".asset-table-action-btn:active,\n"
        ".guard-accent-action:active,\n"
        ".guard-tonal-action:active {\n"
        "  transform: translateY(0);\n"
        "}\n\n"
        "button:focus-visible,\n"
        ".interactive-chip:focus-visible,\n"
        ".chart-period-btn:focus-visible,\n"
        ".chart-action-btn:focus-visible,\n"
        ".asset-table-action-btn:focus-visible,\n"
        ".sidebar-item:focus-visible,\n"
        ".cell-action:focus-visible,\n"
        ".table-action:focus-visible,\n"
        ".action-link:focus-visible {\n"
        "  outline: 2px solid rgba(var(--accent-rgb, 16, 185, 129), 0.72);\n"
        "  outline-offset: 2px;\n"
        "  box-shadow: 0 0 0 4px rgba(var(--accent-rgb, 16, 185, 129), 0.16), 0 12px 24px rgba(2, 6, 23, 0.22) !important;\n"
        "}\n\n"
        ".news-feed-panel .news-items,\n"
        ".watchlist-feed-panel .news-feed,\n"
        ".news-feed-section .news-feed,\n"
        ".news-panel .news-items,\n"
        ".briefing-panel .news-items {\n"
        "  display: grid;\n"
        "  gap: 0.9rem;\n"
        "}\n\n"
        ".news-feed-panel .news-item,\n"
        ".watchlist-feed-panel .news-feed-item,\n"
        ".news-feed-section .news-feed-item,\n"
        ".news-panel .news-item,\n"
        ".briefing-panel .news-item,\n"
        ".guard-news-secondary {\n"
        "  position: relative;\n"
        "  padding: 0.95rem 1rem;\n"
        "  border: 1px solid rgba(255, 255, 255, 0.06);\n"
        "  border-radius: 18px;\n"
        "  background: linear-gradient(180deg, rgba(255, 255, 255, 0.028), rgba(255, 255, 255, 0.012));\n"
        "}\n\n"
        ".news-feed-panel .news-item:first-child,\n"
        ".watchlist-feed-panel .news-feed-item:first-child,\n"
        ".news-feed-section .news-feed-item:first-child,\n"
        ".news-panel .news-item:first-child,\n"
        ".briefing-panel .news-item:first-child,\n"
        ".guard-news-lead {\n"
        "  padding: 1.2rem 1.25rem;\n"
        "  border-color: rgba(255, 255, 255, 0.12);\n"
        "  background: linear-gradient(145deg, rgba(255, 255, 255, 0.065), rgba(255, 255, 255, 0.02) 62%), rgba(18, 24, 38, 0.92) !important;\n"
        "  box-shadow: 0 18px 34px rgba(2, 6, 23, 0.22);\n"
        "}\n\n"
        ".news-item-title,\n"
        ".news-feed-title,\n"
        ".feed-title {\n"
        "  font-family: var(--font-display, 'Space Grotesk', 'Inter', sans-serif) !important;\n"
        "  letter-spacing: -0.02em;\n"
        "}\n\n"
        ".news-feed-panel .news-item:first-child .news-item-title,\n"
        ".watchlist-feed-panel .news-feed-item:first-child .news-feed-title,\n"
        ".news-feed-section .news-feed-item:first-child .news-feed-title,\n"
        ".news-panel .news-item:first-child .news-item-title,\n"
        ".briefing-panel .news-item:first-child .news-item-title,\n"
        ".guard-news-lead .news-item-title,\n"
        ".guard-news-lead .news-feed-title,\n"
        ".guard-news-lead .feed-title {\n"
        "  font-size: clamp(1.05rem, 0.55vw + 0.96rem, 1.38rem) !important;\n"
        "  line-height: 1.22 !important;\n"
        "  font-weight: 600 !important;\n"
        "}\n\n"
        ".news-item-meta,\n"
        ".news-feed-meta,\n"
        ".feed-meta {\n"
        "  display: flex;\n"
        "  flex-wrap: wrap;\n"
        "  align-items: center;\n"
        "  gap: 0.45rem 0.7rem;\n"
        "}\n\n"
        ".news-item-source,\n"
        ".news-feed-source,\n"
        ".feed-source,\n"
        ".news-tag,\n"
        ".news-feed-tag,\n"
        ".badge {\n"
        "  text-transform: uppercase;\n"
        "  letter-spacing: 0.08em;\n"
        "  font-size: 0.7rem !important;\n"
        "}\n\n"
        ".news-item-time,\n"
        ".news-feed-time,\n"
        ".feed-time {\n"
        "  opacity: 0.82;\n"
        "}\n\n"
        ".hero-chart svg,\n"
        ".chart-card svg,\n"
        ".chart-content svg {\n"
        "  filter: drop-shadow(0 10px 26px rgba(2, 6, 23, 0.24));\n"
        "}\n\n"
        ".chart-card,\n"
        ".hero-chart,\n"
        ".asset-table-panel {\n"
        "  outline: 1px solid rgba(255, 255, 255, 0.02);\n"
        "}\n"
        f"{dashboard_specific_css}"
    )


def _build_componentized_polish_guard_runtime(ui_archetype: str) -> str | None:
    if not _supports_componentized_polish_guard(ui_archetype):
        return None
    if ui_archetype == "game" or ui_archetype.startswith("game_"):
        return None

    return (
        f"// Runtime numeric polish guard for {ui_archetype} shells.\n"
        "// Keep text mutations opt-in so React-managed dashboards do not reconcile against rewritten numeric nodes.\n"
        "const COUNT_SELECTORS = [\n"
        '  "[data-countup]"\n'
        "] as const;\n\n"
        "const MONO_SELECTORS = [\n"
        '  ...COUNT_SELECTORS,\n'
        '  ".kpi-value",\n'
        '  ".kpi-delta",\n'
        '  ".portfolio-value .value-amount",\n'
        '  ".stat-value",\n'
        '  ".numeric-value",\n'
        '  ".ticker-price",\n'
        '  ".ticker-delta",\n'
        '  ".watchlist-price",\n'
        '  ".watchlist-delta",\n'
        '  ".news-feed-time",\n'
        '  ".price",\n'
        '  ".delta",\n'
        '  ".text-mono",\n'
        '  ".table-cell",\n'
        '  ".candlestick-chart-svg text"\n'
        "] as const;\n\n"
        "const NEWS_PANEL_SELECTORS = [\n"
        '  ".watchlist-feed-panel",\n'
        '  ".news-feed-section",\n'
        '  ".news-feed",\n'
        '  ".news-feed-panel",\n'
        '  ".news-panel",\n'
        '  ".briefing-panel"\n'
        "] as const;\n\n"
        "const ACTION_SELECTORS = [\n"
        '  ".chart-action-btn",\n'
        '  ".interactive-chip",\n'
        '  ".asset-table-action-btn",\n'
        '  ".primary-btn",\n'
        '  "button"\n'
        "] as const;\n\n"
        "const SHELL_LAYOUT_SELECTORS = [\n"
        '  ".dashboard-layout",\n'
        '  ".dashboard-shell",\n'
        '  ".fintech-shell",\n'
        '  ".app-shell"\n'
        "] as const;\n\n"
        "const NEWS_ITEM_SELECTOR = '.news-feed-item, .news-item, .feed-item, article, li';\n"
        "const SHELL_MAIN_SELECTOR = '.main-content, .main-content-wrapper, .main-content-area, .content-area, .dashboard-main, .workspace-main, main';\n"
        "const SHELL_SIDEBAR_SELECTOR = '.sidebar, .app-sidebar, .left-sidebar, .left-rail, .side-rail';\n"
        "const SHELL_RIGHT_RAIL_SELECTOR = '.right-rail, .right-sidebar, .support-rail, .insights-rail, .side-panel';\n"
        "const PRIMARY_ACTION_RE = /\\b(buy|trade|deposit|rebalance|review|add position|open)\\b/i;\n"
        "const SECONDARY_ACTION_RE = /\\b(sell|withdraw|trim|hedge|close|reduce)\\b/i;\n\n"
        "function parseCountValue(text: string): { value: number; prefix: string; suffix: string; decimals: number } | null {\n"
        "  const trimmed = text.trim();\n"
        "  if (!trimmed || /[A-Za-z]{3,}/.test(trimmed)) {\n"
        "    return null;\n"
        "  }\n"
        "  const match = trimmed.match(/^([^\\d+-]*)([+-]?[\\d,]+(?:\\.\\d+)?)(.*)$/);\n"
        "  if (!match) {\n"
        "    return null;\n"
        "  }\n"
        "  const numeric = Number(match[2].replace(/,/g, ''));\n"
        "  if (!Number.isFinite(numeric) || Math.abs(numeric) < 1) {\n"
        "    return null;\n"
        "  }\n"
        "  const decimals = (match[2].split('.')[1] || '').length;\n"
        "  return { value: numeric, prefix: match[1], suffix: match[3], decimals };\n"
        "}\n\n"
        "function formatCountValue(value: number, prefix: string, suffix: string, decimals: number): string {\n"
        "  return `${prefix}${value.toLocaleString(undefined, { minimumFractionDigits: decimals, maximumFractionDigits: decimals })}${suffix}`;\n"
        "}\n\n"
        "function animateCount(node: HTMLElement): void {\n"
        "  if (node.dataset.guardCountAnimated === '1') {\n"
        "    return;\n"
        "  }\n"
        "  const parsed = parseCountValue(node.textContent || '');\n"
        "  if (!parsed) {\n"
        "    return;\n"
        "  }\n"
        "  node.dataset.guardCountAnimated = '1';\n"
        "  const target = parsed.value;\n"
        "  const duration = 900;\n"
        "  const start = performance.now();\n"
        "  const initial = Math.max(0, target * 0.2);\n"
        "  const step = (now: number) => {\n"
        "    const progress = Math.min((now - start) / duration, 1);\n"
        "    const eased = 1 - Math.pow(1 - progress, 3);\n"
        "    const current = initial + (target - initial) * eased;\n"
        "    node.textContent = formatCountValue(current, parsed.prefix, parsed.suffix, parsed.decimals);\n"
        "    if (progress < 1) {\n"
        "      window.requestAnimationFrame(step);\n"
        "    } else {\n"
        "      node.textContent = formatCountValue(target, parsed.prefix, parsed.suffix, parsed.decimals);\n"
        "    }\n"
        "  };\n"
        "  window.requestAnimationFrame(step);\n"
        "}\n\n"
        "function shouldAnimateCount(node: HTMLElement): boolean {\n"
        "  return node.childElementCount === 0 && Boolean(parseCountValue(node.textContent || ''));\n"
        "}\n\n"
        "function applyCountGuard(root: ParentNode = document): void {\n"
        "  const monoSelector = MONO_SELECTORS.join(',');\n"
        "  root.querySelectorAll<Element>(monoSelector).forEach((node) => {\n"
        "    node.classList.add('guard-mono-count');\n"
        "  });\n"
        "  const countSelector = COUNT_SELECTORS.join(',');\n"
        "  root.querySelectorAll<HTMLElement>(countSelector).forEach((node) => {\n"
        "    if (shouldAnimateCount(node)) {\n"
        "      animateCount(node);\n"
        "    }\n"
        "  });\n"
        "}\n\n"
        "function applyNewsHierarchyGuard(root: ParentNode = document): void {\n"
        "  NEWS_PANEL_SELECTORS.forEach((selector) => {\n"
        "    root.querySelectorAll<HTMLElement>(selector).forEach((panel) => {\n"
        "      const items = Array.from(panel.querySelectorAll<HTMLElement>(NEWS_ITEM_SELECTOR)).filter((item) => {\n"
        "        return Boolean((item.textContent || '').trim());\n"
        "      });\n"
        "      items.forEach((item, index) => {\n"
        "        item.classList.toggle('guard-news-lead', index === 0);\n"
        "        item.classList.toggle('guard-news-secondary', index > 0);\n"
        "      });\n"
        "    });\n"
        "  });\n"
        "}\n\n"
        "function applyActionGuard(root: ParentNode = document): void {\n"
        "  const selector = ACTION_SELECTORS.join(',');\n"
        "  root.querySelectorAll<HTMLElement>(selector).forEach((node) => {\n"
        "    const text = (node.textContent || '').replace(/\\s+/g, ' ').trim();\n"
        "    if (!text) {\n"
        "      return;\n"
        "    }\n"
        "    if (PRIMARY_ACTION_RE.test(text)) {\n"
        "      node.classList.add('guard-accent-action');\n"
        "      node.classList.remove('guard-tonal-action');\n"
        "      return;\n"
        "    }\n"
        "    if (SECONDARY_ACTION_RE.test(text)) {\n"
        "      node.classList.add('guard-tonal-action');\n"
        "    }\n"
        "  });\n"
        "}\n\n"
        "function resetNestedRailGuard(shell: HTMLElement): void {\n"
        "  shell.classList.remove('guard-nested-rail-shell');\n"
        "  shell.style.removeProperty('grid-template-columns');\n"
        "  shell.style.removeProperty('align-items');\n"
        "  const main = shell.querySelector<HTMLElement>(SHELL_MAIN_SELECTOR);\n"
        "  if (main) {\n"
        "    main.style.removeProperty('display');\n"
        "    main.style.removeProperty('grid-template-columns');\n"
        "    main.style.removeProperty('gap');\n"
        "    main.style.removeProperty('align-items');\n"
        "    main.style.removeProperty('min-width');\n"
        "    Array.from(main.children).forEach((child) => {\n"
        "      if (!(child instanceof HTMLElement)) {\n"
        "        return;\n"
        "      }\n"
        "      child.style.removeProperty('grid-column');\n"
        "      child.style.removeProperty('width');\n"
        "      child.style.removeProperty('min-width');\n"
        "      child.style.removeProperty('max-width');\n"
        "      child.style.removeProperty('align-self');\n"
        "      child.style.removeProperty('position');\n"
        "      child.style.removeProperty('top');\n"
        "    });\n"
        "  }\n"
        "  shell.querySelectorAll<HTMLElement>('.guard-main-rail-split, .guard-main-rail-primary, .guard-main-rail-secondary').forEach((node) => {\n"
        "    node.classList.remove('guard-main-rail-split', 'guard-main-rail-primary', 'guard-main-rail-secondary');\n"
        "  });\n"
        "}\n\n"
        "function resetDirectRailGuard(shell: HTMLElement): void {\n"
        "  shell.classList.remove('guard-direct-rail-shell');\n"
        "  shell.style.removeProperty('grid-template-columns');\n"
        "  shell.style.removeProperty('align-items');\n"
        "  const main = shell.querySelector<HTMLElement>(SHELL_MAIN_SELECTOR);\n"
        "  if (main) {\n"
        "    main.style.removeProperty('grid-column');\n"
        "    main.style.removeProperty('min-width');\n"
        "  }\n"
        "  Array.from(shell.children).forEach((child) => {\n"
        "    if (!(child instanceof HTMLElement) || !child.matches(SHELL_RIGHT_RAIL_SELECTOR)) {\n"
        "      return;\n"
        "    }\n"
        "    child.style.removeProperty('grid-column');\n"
        "    child.style.removeProperty('width');\n"
        "    child.style.removeProperty('min-width');\n"
        "    child.style.removeProperty('max-width');\n"
        "    child.style.removeProperty('align-self');\n"
        "    child.style.removeProperty('position');\n"
        "    child.style.removeProperty('top');\n"
        "  });\n"
        "}\n\n"
        "function applyDirectRailGuard(shell: HTMLElement, sidebarWidth: number, main: HTMLElement): boolean {\n"
        "  if (typeof window === 'undefined' || window.innerWidth < 1180) {\n"
        "    resetDirectRailGuard(shell);\n"
        "    return false;\n"
        "  }\n"
        "  const shellStyle = window.getComputedStyle(shell);\n"
        "  if (!shellStyle.display.includes('grid')) {\n"
        "    resetDirectRailGuard(shell);\n"
        "    return false;\n"
        "  }\n"
        "  const shellChildren = Array.from(shell.children).filter((child): child is HTMLElement => child instanceof HTMLElement);\n"
        "  const directRail = shellChildren.find((child) => child.matches(SHELL_RIGHT_RAIL_SELECTOR));\n"
        "  if (!directRail) {\n"
        "    resetDirectRailGuard(shell);\n"
        "    return false;\n"
        "  }\n"
        "  const mainRect = main.getBoundingClientRect();\n"
        "  const directRailRect = directRail.getBoundingClientRect();\n"
        "  const railWrappedBelow = directRailRect.top > mainRect.top + 72;\n"
        "  const railOverlappingMain = directRailRect.left < mainRect.right - 80;\n"
        "  if (!railWrappedBelow && !railOverlappingMain) {\n"
        "    resetDirectRailGuard(shell);\n"
        "    return false;\n"
        "  }\n"
        "  shell.classList.add('guard-direct-rail-shell');\n"
        "  shell.style.setProperty('grid-template-columns', `var(--guard-sidebar-offset, 240px) minmax(0, 1fr) minmax(280px, 360px)`);\n"
        "  shell.style.setProperty('align-items', 'start');\n"
        "  main.style.setProperty('grid-column', '2 / 3');\n"
        "  main.style.setProperty('min-width', '0');\n"
        "  directRail.style.setProperty('grid-column', '3 / 4');\n"
        "  directRail.style.setProperty('width', 'auto');\n"
        "  directRail.style.setProperty('min-width', '0');\n"
        "  directRail.style.setProperty('max-width', '100%');\n"
        "  directRail.style.setProperty('align-self', 'start');\n"
        "  directRail.style.setProperty('position', 'sticky');\n"
        "  directRail.style.setProperty('top', 'clamp(1rem, 1.8vw, 1.5rem)');\n"
        "  shell.style.setProperty('--guard-sidebar-offset', `${Math.max(180, sidebarWidth || 240)}px`);\n"
        "  return true;\n"
        "}\n\n"
        "function applyNestedRailGuard(shell: HTMLElement, sidebarWidth: number): boolean {\n"
        "  if (typeof window === 'undefined' || window.innerWidth < 1180) {\n"
        "    resetNestedRailGuard(shell);\n"
        "    return false;\n"
        "  }\n"
        "  const shellChildren = Array.from(shell.children).filter((child): child is HTMLElement => child instanceof HTMLElement);\n"
        "  if (shellChildren.some((child) => child.matches(SHELL_RIGHT_RAIL_SELECTOR))) {\n"
        "    resetNestedRailGuard(shell);\n"
        "    return false;\n"
        "  }\n"
        "  const main = shell.querySelector<HTMLElement>(SHELL_MAIN_SELECTOR);\n"
        "  if (!main) {\n"
        "    resetNestedRailGuard(shell);\n"
        "    return false;\n"
        "  }\n"
        "  const mainChildren = Array.from(main.children).filter((child): child is HTMLElement => child instanceof HTMLElement);\n"
        "  const nestedRail = mainChildren.find((child) => child.matches(SHELL_RIGHT_RAIL_SELECTOR));\n"
        "  const primaryPanels = mainChildren.filter((child) => child !== nestedRail);\n"
        "  if (!nestedRail || primaryPanels.length !== 1) {\n"
        "    resetNestedRailGuard(shell);\n"
        "    return false;\n"
        "  }\n"
        "  shell.classList.add('guard-nested-rail-shell');\n"
        "  shell.style.setProperty('grid-template-columns', `var(--guard-sidebar-offset, 240px) minmax(0, 1fr) 0`);\n"
        "  shell.style.setProperty('align-items', 'start');\n"
        "  main.classList.add('guard-main-rail-split');\n"
        "  main.style.setProperty('display', 'grid');\n"
        "  main.style.setProperty('grid-template-columns', 'minmax(0, 1.72fr) minmax(300px, 0.96fr)');\n"
        "  main.style.setProperty('gap', 'clamp(1rem, 1.8vw, 1.75rem)');\n"
        "  main.style.setProperty('align-items', 'start');\n"
        "  main.style.setProperty('min-width', '0');\n"
        "  nestedRail.classList.add('guard-main-rail-secondary');\n"
        "  nestedRail.style.setProperty('grid-column', '2 / 3');\n"
        "  nestedRail.style.setProperty('min-width', 'min(320px, 100%)');\n"
        "  nestedRail.style.setProperty('width', 'min(360px, 100%)');\n"
        "  nestedRail.style.setProperty('max-width', '100%');\n"
        "  nestedRail.style.setProperty('align-self', 'start');\n"
        "  nestedRail.style.setProperty('position', 'sticky');\n"
        "  nestedRail.style.setProperty('top', 'clamp(1rem, 1.8vw, 1.5rem)');\n"
        "  primaryPanels[0].classList.add('guard-main-rail-primary');\n"
        "  primaryPanels[0].style.setProperty('grid-column', '1 / 2');\n"
        "  primaryPanels[0].style.setProperty('min-width', '0');\n"
        "  primaryPanels[0].style.setProperty('width', '100%');\n"
        "  shell.style.setProperty('--guard-sidebar-offset', `${Math.max(180, sidebarWidth || 240)}px`);\n"
        "  return true;\n"
        "}\n\n"
        "function applyShellLayoutGuard(root: ParentNode = document): void {\n"
        "  if (typeof window === 'undefined' || window.innerWidth < 960) {\n"
        "    return;\n"
        "  }\n"
        "  SHELL_LAYOUT_SELECTORS.forEach((selector) => {\n"
        "    root.querySelectorAll<HTMLElement>(selector).forEach((shell) => {\n"
        "      const sidebar = shell.querySelector<HTMLElement>(SHELL_SIDEBAR_SELECTOR);\n"
        "      const main = shell.querySelector<HTMLElement>(SHELL_MAIN_SELECTOR);\n"
        "      if (!sidebar || !main) {\n"
        "        resetNestedRailGuard(shell);\n"
        "        shell.classList.remove('guard-fixed-sidebar-shell');\n"
        "        shell.style.removeProperty('--guard-sidebar-offset');\n"
        "        return;\n"
        "      }\n"
        "      const shellStyle = window.getComputedStyle(shell);\n"
        "      const sidebarStyle = window.getComputedStyle(sidebar);\n"
        "      const sidebarWidth = Math.round(sidebar.getBoundingClientRect().width);\n"
        "      const mainRect = main.getBoundingClientRect();\n"
        "      const directRailActive = applyDirectRailGuard(shell, sidebarWidth, main);\n"
        "      const nestedRailActive = directRailActive ? false : applyNestedRailGuard(shell, sidebarWidth);\n"
        "      const fixedSidebarGrid = shellStyle.display.includes('grid') && sidebarStyle.position === 'fixed';\n"
        "      const contentCollapsed = sidebarWidth > 0 && mainRect.width > 0 && mainRect.width <= Math.max(sidebarWidth + 80, window.innerWidth * 0.42);\n"
        "      const contentPinnedLeft = sidebarWidth > 0 && mainRect.x < Math.max(16, sidebarWidth - 12);\n"
        "      if (fixedSidebarGrid && (contentCollapsed || contentPinnedLeft)) {\n"
        "        shell.classList.add('guard-fixed-sidebar-shell');\n"
        "        shell.style.setProperty('--guard-sidebar-offset', `${Math.max(64, sidebarWidth)}px`);\n"
        "      } else {\n"
        "        shell.classList.remove('guard-fixed-sidebar-shell');\n"
        "        if (!directRailActive && !nestedRailActive) {\n"
        "          shell.style.removeProperty('--guard-sidebar-offset');\n"
        "        }\n"
        "      }\n"
        "    });\n"
        "  });\n"
        "}\n\n"
        "function applyPolishGuard(root: ParentNode = document): void {\n"
        "  applyCountGuard(root);\n"
        "  applyNewsHierarchyGuard(root);\n"
        "  applyActionGuard(root);\n"
        "  applyShellLayoutGuard(root);\n"
        "}\n\n"
        "let polishGuardFrame = 0;\n\n"
        "function schedulePolishGuard(): void {\n"
        "  if (typeof window === 'undefined' || polishGuardFrame) {\n"
        "    return;\n"
        "  }\n"
        "  polishGuardFrame = window.requestAnimationFrame(() => {\n"
        "    polishGuardFrame = 0;\n"
        "    applyPolishGuard(document);\n"
        "  });\n"
        "}\n\n"
        "if (typeof window !== 'undefined') {\n"
        "  window.addEventListener('load', () => {\n"
        "    applyPolishGuard(document);\n"
        "    window.addEventListener('resize', schedulePolishGuard);\n"
        "    const observer = new MutationObserver(() => schedulePolishGuard());\n"
        "    observer.observe(document.body, { childList: true, subtree: true });\n"
        "    schedulePolishGuard();\n"
        "  }, { once: true });\n"
        "}\n"
    )


def _normalize_componentized_base_css(source: str, *, reference_css: str) -> str:
    updated = source
    reference_lines = GOOGLE_FONT_IMPORT_LINE_RE.findall(reference_css)
    if reference_lines:
        reference_import_block = "\n".join(line.strip() for line in reference_lines if line.strip())
        if reference_import_block:
            updated = GOOGLE_FONT_IMPORT_LINE_RE.sub("", updated).lstrip()
            updated = f"{reference_import_block}\n\n{updated}".lstrip()

    reference_lower = reference_css.lower()
    has_display_font = "space grotesk" in reference_lower or "outfit" in reference_lower
    has_mono_font = "jetbrains mono" in reference_lower

    updated = _normalize_componentized_override_css(
        updated,
        has_display_font=has_display_font,
        has_mono_font=has_mono_font,
    )

    updated_lower = updated.lower()
    appended_rules: list[str] = []
    if has_display_font and "space grotesk" not in updated_lower:
        appended_rules.append(
            ".page-title, .topbar-brand, .panel-title, .chart-title, .section-title, .feed-header, h1, h2, h3 {\n"
            "  font-family: 'Space Grotesk', 'Inter', sans-serif;\n"
            "}\n"
        )
    if has_mono_font and "jetbrains mono" not in updated_lower:
        appended_rules.append(
            ".kpi-value, .kpi-delta, .ticker-price, .ticker-delta, .watch-price, .watch-delta, .feed-time, .asset-table td, .table-number, .numeric-value {\n"
            "  font-family: 'JetBrains Mono', monospace;\n"
            "  font-variant-numeric: tabular-nums;\n"
            "}\n"
        )
    if appended_rules:
        updated = updated.rstrip() + "\n\n" + "\n".join(rule.rstrip() for rule in appended_rules) + "\n"

    return updated


def _normalize_componentized_override_css(
    source: str,
    *,
    has_display_font: bool,
    has_mono_font: bool,
) -> str:
    updated = source
    updated = _normalize_componentized_invalid_hex_colors(updated)
    updated = _normalize_componentized_broken_responsive_tail(updated)

    if has_mono_font:
        updated = updated.replace("Roboto Mono", "JetBrains Mono")
        updated = updated.replace("Fira Code", "JetBrains Mono")

    if has_display_font:
        updated = OVERRIDE_DISPLAY_FONT_RE.sub(r"\1'Space Grotesk', 'Inter', sans-serif;", updated)
        updated = _rewrite_override_selector_font_family(
            updated,
            selector_hints=DISPLAY_SELECTOR_HINTS,
            font_family="'Space Grotesk', 'Inter', sans-serif",
        )
    if has_mono_font:
        updated = _rewrite_override_selector_font_family(
            updated,
            selector_hints=NUMERIC_SELECTOR_HINTS,
            font_family="'JetBrains Mono', monospace",
        )

    return updated


def _normalize_componentized_invalid_hex_colors(source: str) -> str:
    return INVALID_SEVEN_DIGIT_HEX_RE.sub(
        lambda match: f"#{match.group('value')[:6]}",
        source,
    )


def _normalize_componentized_broken_responsive_tail(source: str) -> str:
    marker = "/* Responsive Adjustments */"
    marker_index = source.find(marker)
    if marker_index < 0:
        return source

    tail = source[marker_index:]
    if "}}." not in tail and "}}@media" not in tail:
        return source

    head = source[:marker_index].rstrip()
    if not head:
        return SAFE_COMPONENTIZED_RESPONSIVE_TAIL
    return f"{head}\n\n{SAFE_COMPONENTIZED_RESPONSIVE_TAIL}"


def _rewrite_override_selector_font_family(
    source: str,
    *,
    selector_hints: tuple[str, ...],
    font_family: str,
) -> str:
    def _repl(match: re.Match[str]) -> str:
        selector = match.group("selector")
        selector_lower = selector.lower()
        if not any(hint in selector_lower for hint in selector_hints):
            return match.group(0)

        body = match.group("body")
        if "font-family" in body.lower():
            body = re.sub(r"font-family\s*:\s*[^;]+;", f"font-family: {font_family};", body, flags=re.IGNORECASE)
        else:
            stripped = body.rstrip()
            joiner = "\n" if stripped else ""
            body = f"{stripped}{joiner}  font-family: {font_family};\n"
        return f"{selector}{{{body}}}"

    return CSS_BLOCK_RE.sub(_repl, source)


def _normalize_componentized_index_html(source: str) -> str:
    title_match = re.search(r"<title[^>]*>(.*?)</title>", source, re.IGNORECASE | re.DOTALL)
    title = title_match.group(1).strip() if title_match else "App"
    if not title:
        title = "App"
    return (
        "<!doctype html>\n"
        '<html lang="en">\n'
        "  <head>\n"
        '    <meta charset="UTF-8" />\n'
        '    <link rel="icon" type="image/svg+xml" href="/vite.svg" />\n'
        '    <meta name="viewport" content="width=device-width, initial-scale=1.0" />\n'
        f"    <title>{title}</title>\n"
        "  </head>\n"
        "  <body>\n"
        '    <div id="root"></div>\n'
        '    <script type="module" src="/src/main.tsx"></script>\n'
        "  </body>\n"
        "</html>\n"
    )


def _normalize_run_on_inline_comments(source: str) -> str:
    if "//" not in source:
        return source
    return INLINE_COMMENT_RUNON_RE.sub(lambda m: f"/* {m.group(1).strip()} */\n", source)


def _repair_componentized_lightweight_chart_corruption(source: str) -> str:
    if "lightweight-charts" not in source:
        return source

    updated = source
    if "Start from Jan 1, 2023" in updated:
        updated = LIGHTWEIGHT_CHART_CANDLE_HELPER_RE.sub(
            (
                "const generateRandomCandlestickData = (count: number, basePrice: number): CandlestickData[] => {\n"
                "  const data: CandlestickData[] = [];\n"
                "  let lastPrice = basePrice;\n"
                "  for (let i = 0; i < count; i++) {\n"
                "    const open = lastPrice + (Math.random() - 0.5) * 5;\n"
                "    const close = open + (Math.random() - 0.5) * 10;\n"
                "    const high = Math.max(open, close) + Math.random() * 5;\n"
                "    const low = Math.min(open, close) - Math.random() * 5;\n"
                "    lastPrice = close;\n"
                "    data.push({\n"
                "      time: (1672531200 + i * 86400) as Time,\n"
                "      open,\n"
                "      high,\n"
                "      low,\n"
                "      close,\n"
                "    });\n"
                "  }\n"
                "  return data;\n"
                "};"
            ),
            updated,
        )
    if "Simulate small fluctuations data.push({" in updated:
        updated = LIGHTWEIGHT_CHART_LINE_HELPER_RE.sub(
            (
                "const generateLineData = (count: number, basePrice: number): LineData[] => {\n"
                "  const data: LineData[] = [];\n"
                "  let lastValue = basePrice;\n"
                "  for (let i = 0; i < count; i++) {\n"
                "    lastValue += (Math.random() - 0.5) * 2;\n"
                "    data.push({\n"
                "      time: (1672531200 + i * 86400) as Time,\n"
                "      value: lastValue,\n"
                "    });\n"
                "  }\n"
                "  return data;\n"
                "};"
            ),
            updated,
        )
    if "Default for 1M if (timeframe === '1D') count = 30; Hourly" in updated or "Simulate volume }));" in updated:
        updated = LIGHTWEIGHT_CHART_DATA_CALLBACK_RE.sub(
            (
                "const getChartDataForSymbol = useCallback((symbol: string, timeframe: typeof chartTimeframe) => {\n"
                "  const basePrice = (symbol === 'SPY' ? 500 : (symbol === 'GOOGL' ? 150 : 170)) + Math.random() * 20;\n"
                "  let count = 60; /* Default for 1M */\n"
                "  if (timeframe === '1D') count = 30;\n"
                "  if (timeframe === '1W') count = 7;\n"
                "  if (timeframe === '1Y') count = 250;\n"
                "  if (timeframe === 'ALL') count = 500;\n"
                "  const newCandlestickData = generateRandomCandlestickData(count, basePrice);\n"
                "  const newVolumeData = newCandlestickData.map((datum) => ({\n"
                "    time: datum.time,\n"
                "    value: Math.random() * 10000000 + 5000000,\n"
                "  }));\n"
                "  setCurrentChartData(newCandlestickData);\n"
                "  setCurrentVolumeData(newVolumeData);\n"
                "}, []);"
            ),
            updated,
        )
    if "axisPressedMo/* useMove: true, */" in updated:
        updated = LIGHTWEIGHT_CHART_SETUP_EFFECT_RE.sub(
            (
                "useEffect(() => {\n"
                "  if (!chartContainerRef.current) {\n"
                "    return;\n"
                "  }\n"
                "\n"
                "  if (!chartRef.current) {\n"
                "    const chart = createChart(chartContainerRef.current, {\n"
                "      layout: {\n"
                "        backgroundColor: 'transparent',\n"
                "        textColor: '#E0E0E0',\n"
                "      },\n"
                "      grid: {\n"
                "        vertLines: { color: '#2A2A2E' },\n"
                "        horzLines: { color: '#2A2A2E' },\n"
                "      },\n"
                "      rightPriceScale: {\n"
                "        borderColor: '#2A2A2E',\n"
                "      },\n"
                "      timeScale: {\n"
                "        borderColor: '#2A2A2E',\n"
                "        timeVisible: true,\n"
                "        secondsVisible: false,\n"
                "      },\n"
                "      crosshair: {\n"
                "        mode: 0, /* Magnet mode */\n"
                "      },\n"
                "      handleScroll: { vertTouchDrag: true },\n"
                "      handleScale: { axisPressedMouseMove: true },\n"
                "    });\n"
                "    chartRef.current = chart;\n"
                "    candlestickSeriesRef.current = chart.addCandlestickSeries({\n"
                "      upColor: '#00C853',\n"
                "      downColor: '#FF3D00',\n"
                "      borderVisible: false,\n"
                "      wickUpColor: '#00C853',\n"
                "      wickDownColor: '#FF3D00',\n"
                "    });\n"
                "    volumeSeriesRef.current = chart.addLineSeries({\n"
                "      color: '#A0A0A5',\n"
                "      lineWidth: 1,\n"
                "      priceFormat: {\n"
                "        type: 'volume',\n"
                "      },\n"
                "      overlay: true,\n"
                "      scaleMargins: {\n"
                "        top: 0.8,\n"
                "        bottom: 0,\n"
                "      },\n"
                "    });\n"
                "  }\n"
                "\n"
                "  const handleResize = () => {\n"
                "    chartRef.current?.applyOptions({ width: chartContainerRef.current?.clientWidth || 0 });\n"
                "  };\n"
                "\n"
                "  handleResize();\n"
                "  window.addEventListener('resize', handleResize);\n"
                "\n"
                "  if (candlestickSeriesRef.current && currentChartData.length > 0) {\n"
                "    candlestickSeriesRef.current.setData(currentChartData);\n"
                "    chartRef.current?.timeScale().fitContent();\n"
                "  }\n"
                "  if (volumeSeriesRef.current && currentVolumeData.length > 0) {\n"
                "    volumeSeriesRef.current.setData(currentVolumeData);\n"
                "  }\n"
                "\n"
                "  return () => {\n"
                "    window.removeEventListener('resize', handleResize);\n"
                "  };\n"
                "}, [currentChartData, currentVolumeData]);"
            ),
            updated,
        )

    return updated


def _repair_componentized_tradingview_scaffold_corruption(source: str) -> str:
    if "CandlestickChart" not in source:
        return source
    if 'container_id: "tradingview_chart"' not in source:
        return source
    if "return () =>widget.remove();" not in source and "TradingView." not in source:
        return source

    return (
        "import React from 'react';\n"
        "\n"
        "type ChartDatum = {\n"
        "  x: number;\n"
        "  open: number;\n"
        "  close: number;\n"
        "  high: number;\n"
        "  low: number;\n"
        "  color: string;\n"
        "};\n"
        "\n"
        "export const CandlestickChart: React.FC = () => {\n"
        "  const chartData: ChartDatum[] = [\n"
        "    { x: 60, open: 198, close: 214, high: 220, low: 190, color: 'var(--success)' },\n"
        "    { x: 120, open: 214, close: 206, high: 224, low: 202, color: 'var(--danger)' },\n"
        "    { x: 180, open: 206, close: 218, high: 226, low: 200, color: 'var(--success)' },\n"
        "    { x: 240, open: 218, close: 211, high: 229, low: 205, color: 'var(--danger)' },\n"
        "    { x: 300, open: 211, close: 227, high: 235, low: 208, color: 'var(--success)' },\n"
        "    { x: 360, open: 227, close: 221, high: 238, low: 216, color: 'var(--danger)' },\n"
        "    { x: 420, open: 221, close: 236, high: 242, low: 218, color: 'var(--success)' },\n"
        "    { x: 480, open: 236, close: 231, high: 246, low: 226, color: 'var(--danger)' },\n"
        "    { x: 540, open: 231, close: 244, high: 250, low: 228, color: 'var(--success)' },\n"
        "    { x: 600, open: 244, close: 238, high: 252, low: 233, color: 'var(--danger)' },\n"
        "    { x: 660, open: 238, close: 247, high: 255, low: 236, color: 'var(--success)' },\n"
        "    { x: 720, open: 247, close: 241, high: 258, low: 239, color: 'var(--danger)' },\n"
        "    { x: 780, open: 241, close: 252, high: 262, low: 238, color: 'var(--success)' },\n"
        "    { x: 840, open: 252, close: 246, high: 265, low: 243, color: 'var(--danger)' },\n"
        "    { x: 900, open: 246, close: 259, high: 270, low: 244, color: 'var(--success)' },\n"
        "  ];\n"
        "  const chartHeight = 300;\n"
        "  const chartPadding = 20;\n"
        "  const candleWidth = 10;\n"
        "  const scaleY = (value: number) => chartHeight - ((value - 180) / 90) * (chartHeight - chartPadding * 2) - chartPadding;\n"
        "\n"
        "  return (\n"
        "    <div className=\"chart-svg-container\">\n"
        "      <svg viewBox=\"0 0 1000 300\" preserveAspectRatio=\"none\" className=\"candlestick-chart\">\n"
        "        {[190, 205, 220, 235, 250, 265].map((value) => (\n"
        "          <line\n"
        "            key={`grid-${value}`}\n"
        "            x1=\"0\"\n"
        "            y1={scaleY(value)}\n"
        "            x2=\"1000\"\n"
        "            y2={scaleY(value)}\n"
        "            stroke=\"var(--border)\"\n"
        "            strokeWidth=\"0.5\"\n"
        "            strokeDasharray=\"3 3\"\n"
        "          />\n"
        "        ))}\n"
        "        {chartData.map((datum, index) => {\n"
        "          const yOpen = scaleY(datum.open);\n"
        "          const yClose = scaleY(datum.close);\n"
        "          const yHigh = scaleY(datum.high);\n"
        "          const yLow = scaleY(datum.low);\n"
        "          const rectY = Math.min(yOpen, yClose);\n"
        "          const rectHeight = Math.max(Math.abs(yOpen - yClose), 4);\n"
        "          return (\n"
        "            <g key={index}>\n"
        "              <line x1={datum.x} y1={yHigh} x2={datum.x} y2={yLow} stroke={datum.color} strokeWidth=\"1.5\" />\n"
        "              <rect x={datum.x - candleWidth / 2} y={rectY} width={candleWidth} height={rectHeight} fill={datum.color} rx=\"2\" />\n"
        "            </g>\n"
        "          );\n"
        "        })}\n"
        "        {['Mon', 'Tue', 'Wed', 'Thu', 'Fri'].map((label, index) => (\n"
        "          <text key={label} x={90 + index * 200} y=\"286\" className=\"axis-label\">\n"
        "            {label}\n"
        "          </text>\n"
        "        ))}\n"
        "        {[190, 205, 220, 235, 250, 265].map((value) => (\n"
        "          <text key={`label-${value}`} x=\"985\" y={scaleY(value) + 4} textAnchor=\"end\" className=\"axis-label space-mono\">\n"
        "            {`$${value}`}\n"
        "          </text>\n"
        "        ))}\n"
        "      </svg>\n"
        "    </div>\n"
        "  );\n"
        "};\n"
        "\n"
        "export default CandlestickChart;\n"
    )


def _repair_interface_field_comment_bleed(source: str) -> str:
    def _repl(match: re.Match[str]) -> str:
        comment = " ".join(match.group("comment").replace("}", " ").split()).strip()
        comment_block = f" /* {comment} */" if comment else ""
        return f"{match.group('field')}{comment_block}\n}}\n"

    return INTERFACE_FIELD_COMMENT_BLEED_RE.sub(_repl, source)


def _repair_inline_block_comment_code_bleed(source: str) -> str:
    def _repl(match: re.Match[str]) -> str:
        comment = " ".join(match.group("comment").split()).strip()
        prop = match.group("prop").strip()
        prefix = " ".join(match.group("prefix").split()).strip()
        comment_block = f"/* {comment} */\n" if comment else ""
        if prefix:
            return f"{comment_block}{prop}: {prefix}"
        return f"{comment_block}{prop}: "

    return INLINE_BLOCK_COMMENT_CODE_BLEED_RE.sub(_repl, source)


def _repair_block_comment_control_flow_bleed(source: str) -> str:
    def _repl(match: re.Match[str]) -> str:
        comment = " ".join(match.group("comment").split()).strip()
        code = " ".join(match.group("code").split()).strip()
        comment_block = f"/* {comment} */\n" if comment else ""
        return f"{comment_block}{code}"

    return BLOCK_COMMENT_CONTROL_FLOW_BLEED_RE.sub(_repl, source)


def _repair_unterminated_block_comment_line_notes(source: str) -> str:
    def _repl(match: re.Match[str]) -> str:
        if "*/" in match.group(0):
            return match.group(0)
        comment = " ".join(
            " ".join(part.split()).strip()
            for part in (match.group("comment"), match.group("tail"))
            if part and part.strip()
        ).strip()
        indent = match.group("indent")
        code = f"{match.group('code')}{match.group('rest')}".lstrip()
        comment_block = f"{indent}/* {comment} */\n" if comment else ""
        return f"{comment_block}{indent}{code}"

    return UNTERMINATED_BLOCK_COMMENT_LINE_NOTE_RE.sub(_repl, source)


def _repair_multiline_block_comment_line_notes(source: str) -> str:
    return MULTILINE_BLOCK_COMMENT_LINE_NOTE_RE.sub(
        lambda match: (
            f"{match.group('indent')}/* "
            f"{' '.join((match.group('comment') + ' ' + match.group('tail')).split()).strip()} */"
        ),
        source,
    )


def _repair_componentized_comment_prose_continuations(source: str) -> str:
    lines = source.splitlines()
    if len(lines) < 2:
        return source

    repaired_lines: list[str] = []
    index = 0
    changed = False
    prose_starters = ("e.g.,", "for example", "such as", "function, e.g.,")

    while index < len(lines):
        line = lines[index]
        comment_closed = line.rstrip().endswith("*/")
        if "/*" not in line or ("*/" in line and not comment_closed) or index + 1 >= len(lines):
            repaired_lines.append(line)
            index += 1
            continue

        next_line = lines[index + 1]
        stripped = next_line.strip()
        if not stripped:
            repaired_lines.append(line)
            index += 1
            continue

        suffix_match = re.match(r"^(?P<text>.*?)(?P<suffix>[)};\]]+)\s*$", stripped)
        if not suffix_match:
            repaired_lines.append(line)
            index += 1
            continue

        prose = " ".join(suffix_match.group("text").split()).strip(" ,")
        suffix = suffix_match.group("suffix")
        if not prose:
            repaired_lines.append(line)
            index += 1
            continue

        lowered = prose.lower()
        if not lowered.startswith(prose_starters):
            repaired_lines.append(line)
            index += 1
            continue

        if any(token in prose for token in ("{", "}", "<", ">", "=", ":")):
            repaired_lines.append(line)
            index += 1
            continue

        comment_prefix = line.rstrip()
        if comment_closed:
            comment_prefix = comment_prefix[: comment_prefix.rfind("*/")].rstrip()
        repaired_lines.append(f"{comment_prefix} {prose} */")
        repaired_lines.append(f"{re.match(r'[ \t]*', next_line).group(0)}{suffix}")
        changed = True
        index += 2

    if index < len(lines):
        repaired_lines.extend(lines[index:])

    if not changed:
        return source
    return "\n".join(repaired_lines) + ("\n" if source.endswith("\n") else "")


def _repair_inline_block_comment_continuations(source: str) -> str:
    def _repl(match: re.Match[str]) -> str:
        prefix = match.group("prefix").rstrip()
        comment = " ".join(
            " ".join(part.split()).strip()
            for part in (match.group("comment"), match.group("label"))
            if part and part.strip()
        ).strip()
        code = match.group("code").strip()
        indent_match = re.match(r"[ \t]*", match.group("prefix"))
        indent = indent_match.group(0) if indent_match else ""
        comment_block = f"{prefix} /* {comment} */" if prefix else f"{indent}/* {comment} */"
        return f"{comment_block}\n{indent}{code}"

    return INLINE_BLOCK_COMMENT_CONTINUATION_RE.sub(_repl, source)


def _repair_multiline_block_comment_code_bleed(source: str) -> str:
    lines = source.splitlines()
    if len(lines) < 2:
        return source

    repaired_lines: list[str] = []
    index = 0
    changed = False

    while index < len(lines):
        line = lines[index]
        if "/*" not in line or "*/" in line or index + 1 >= len(lines):
            repaired_lines.append(line)
            index += 1
            continue

        prefix, comment_tail = line.split("/*", 1)
        if not prefix.strip() or not comment_tail.strip():
            repaired_lines.append(line)
            index += 1
            continue

        code_match = MULTILINE_BLOCK_COMMENT_CODE_START_RE.search(comment_tail)
        if not code_match or code_match.start() <= 0:
            repaired_lines.append(line)
            index += 1
            continue

        next_line = lines[index + 1]
        if "*/" not in next_line:
            repaired_lines.append(line)
            index += 1
            continue

        comment = " ".join(comment_tail[: code_match.start()].split()).strip()
        swallowed_code = comment_tail[code_match.start() :].strip()
        closing_prefix, closing_suffix = next_line.split("*/", 1)
        continuation_code = closing_prefix
        continuation_comment = ""

        if "//" in closing_prefix:
            continuation_code, continuation_comment = closing_prefix.split("//", 1)

        prefix_line = prefix.rstrip()
        if comment:
            prefix_line = f"{prefix_line} /* {comment} */"
        repaired_lines.append(prefix_line)
        repaired_lines.append(swallowed_code)

        continuation_code = continuation_code.rstrip()
        if continuation_code.strip():
            repaired_lines.append(continuation_code)

        continuation_comment = " ".join(continuation_comment.split()).strip()
        if continuation_comment:
            repaired_lines.append(f"/* {continuation_comment} */")

        trailing = closing_suffix.strip()
        if trailing:
            repaired_lines.append(trailing)

        changed = True
        index += 2

    if not changed:
        return source
    return "\n".join(repaired_lines) + ("\n" if source.endswith("\n") else "")


def _normalize_run_on_natural_language_notes(source: str) -> str:
    updated = RUNON_NATURAL_LANGUAGE_NOTE_RE.sub(
        lambda match: f"/* {match.group('note').strip()} */\n",
        source,
    )
    lines = updated.splitlines()
    normalized_lines: list[str] = []
    index = 0

    while index < len(lines):
        line = lines[index]
        comment_match = re.match(r"^([ \t]*)/\*\s*([^*\n]{2,200}?)\s*\*/\s*$", line)
        if not comment_match:
            normalized_lines.append(line)
            index += 1
            continue

        indent = comment_match.group(1)
        comment_parts = [comment_match.group(2).strip()]
        note_index = index + 1
        consumed_note = False

        while note_index < len(lines):
            candidate = lines[note_index]
            stripped = candidate.strip()
            if not stripped:
                break
            if stripped.startswith(("/*", "//", "*", "*/", "{", "}", ")", "]", "</", "<")):
                break
            if re.match(
                r"^(?:const|let|var|if|for|while|switch|return|export|import|function|type|interface|window|document)\b",
                stripped,
            ):
                break
            if re.match(r"^class(?:\s+[A-Za-z_$]|[{(<])", stripped):
                break
            if re.match(r"^[A-Za-z_$][\w$]*\s*=", stripped):
                break
            if re.match(r"^(?:\.\.\.)?[A-Za-z_$][\w$]*\s*(?::|,\s*$)", stripped):
                break
            if re.match(r"^[A-Za-z_$][\w$]*\s*\(", stripped):
                break
            if not re.search(r"[A-Za-z]", stripped):
                break
            if re.match(r"^[A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)*$", stripped):
                break

            comment_parts.append(stripped)
            note_index += 1
            consumed_note = True

        if consumed_note:
            merged = " ".join(" ".join(part.split()) for part in comment_parts if part).strip()
            normalized_lines.append(f"{indent}/* {merged} */")
            index = note_index
            continue

        normalized_lines.append(line)
        index += 1

    return "\n".join(normalized_lines) + ("\n" if updated.endswith("\n") else "")


def _normalize_run_on_explanatory_labels(source: str) -> str:
    return RUNON_EXPLANATORY_LABEL_RE.sub(
        lambda match: f"/* {match.group('label').strip()} */\n",
        source,
    )


def _normalize_lowercase_object_field_labels(source: str) -> str:
    return LOWERCASE_OBJECT_FIELD_LABEL_RE.sub(
        lambda match: f"{match.group('indent')}/* {match.group('label').strip()} */\n{match.group('indent')}{match.group('field').strip()}",
        source,
    )


def _normalize_bare_section_labels(source: str) -> str:
    return BARE_SECTION_LABEL_RE.sub(
        lambda match: f"/* {match.group('label').strip()} */\n",
        source,
    )


def _normalize_comment_filename_labels(source: str) -> str:
    return COMMENT_FILENAME_LABEL_RE.sub(
        lambda match: f"/* {match.group('comment').strip()} {match.group('filename').strip()} */",
        source,
    )


def _repair_componentized_comment_note_continuations(source: str) -> str:
    return COMMENT_NOTE_CONTINUATION_RE.sub(
        lambda match: (
            f"{match.group('indent')}/* "
            f"{' '.join((match.group('comment') + ' ' + match.group('tail')).split()).strip()} */\n"
        ),
        source,
    )


def _repair_inline_block_comment_note_code_bleed(source: str) -> str:
    def _repl(match: re.Match[str]) -> str:
        prefix = match.group("prefix").rstrip()
        if ";" in prefix:
            return match.group(0)
        merged = " ".join((match.group("comment") + " " + match.group("tail")).split()).strip()
        return f"{prefix} /* {merged} */\n{match.group('indent')}{match.group('code').lstrip()}"

    return INLINE_BLOCK_COMMENT_NOTE_CODE_BLEED_RE.sub(_repl, source)


def _repair_inline_block_comment_swallowed_calls(source: str) -> str:
    def _repl(match: re.Match[str]) -> str:
        comment1 = " ".join(match.group("comment1").split()).strip()
        comment2 = " ".join(match.group("comment2").split()).strip()
        line = match.group("stmt").rstrip()
        if comment1:
            line = f"{line} /* {comment1} */"
        call_line = f"{match.group('indent')}{match.group('callee')}{match.group('argline').lstrip()}"
        trailing_closers = ""
        if comment2:
            closer_match = re.search(r"(?P<body>.*?)(?P<closers>[}\])]+)$", comment2)
            if closer_match:
                comment2 = closer_match.group("body").rstrip()
                trailing_closers = closer_match.group("closers")
        if comment2:
            call_line = f"{call_line} /* {comment2} */"
        if trailing_closers:
            return f"{line}\n{call_line}\n{match.group('indent')}{trailing_closers}"
        return f"{line}\n{call_line}"

    return INLINE_BLOCK_COMMENT_SWALLOWED_CALL_RE.sub(_repl, source)


def _repair_unterminated_inline_block_comments(source: str) -> str:
    def _repl(match: re.Match[str]) -> str:
        line = match.group(0)
        if "*/" in line:
            return line
        comment = " ".join(match.group("comment").split()).strip()
        if not comment:
            return line
        return f"{match.group('prefix').rstrip()} /* {comment} */"

    return UNTERMINATED_INLINE_BLOCK_COMMENT_RE.sub(_repl, source)


def _repair_componentized_comment_url_bleed(source: str) -> str:
    updated = URL_PROTOCOL_COMMENT_BLEED_RE.sub(
        lambda match: f"{match.group('scheme')}://",
        source,
    )
    updated = ATTR_VALUE_ORPHAN_COMMENT_CLOSE_RE.sub(
        lambda match: f"{match.group('attr')}={match.group('quote')}",
        updated,
    )

    def _rewrite_section_comment(match: re.Match[str]) -> str:
        label = " ".join(match.group("label").split()).strip()
        if not label:
            return match.group("stmt") + "\n"
        return f"{match.group('stmt')}\n/* {label} */\n"

    updated = BLOCK_COMMENT_SWALLOWED_ARRAY_CLOSE_RE.sub(
        lambda match: f"/* {' '.join(match.group('comment').split()).strip()} */\n];",
        updated,
    )
    updated = TRAILING_SECTION_LINE_COMMENT_RE.sub(_rewrite_section_comment, updated)
    updated = ORPHAN_COMMENT_CLOSE_AFTER_STATEMENT_RE.sub(
        lambda match: match.group("stmt"),
        updated,
    )
    updated = CONTROL_FLOW_ORPHAN_COMMENT_CLOSE_RE.sub(
        lambda match: match.group("prefix"),
        updated,
    )
    return updated


def _repair_componentized_svg_namespace_protocol(source: str) -> str:
    return SVG_XMLNS_PROTOCOL_SLASH_RE.sub(
        lambda match: (
            f"{match.group('prefix')}{match.group('quote')}"
            f"{match.group('scheme')}://{match.group('rest')}"
            f"{match.group('quote')}"
        ),
        source,
    )


def _repair_componentized_missing_protocol_slashes(source: str) -> str:
    updated = MISSING_PROTOCOL_SLASH_JSX_ATTR_RE.sub(
        lambda match: (
            f"{match.group('prefix')}{match.group('scheme')}://"
            f"{match.group('rest')}{match.group('suffix')}"
        ),
        source,
    )
    return MISSING_PROTOCOL_SLASH_OBJECT_FIELD_RE.sub(
        lambda match: (
            f"{match.group('prefix')}{match.group('scheme')}://"
            f"{match.group('rest')}{match.group('suffix')}"
        ),
        updated,
    )


def _repair_componentized_orphaned_parent_family_children(source: str) -> str:
    parent_tags = {"aside", "nav", "section"}
    family_keywords = frozenset({"drawer", "menu", "nav", "panel", "rail", "sidebar", "sidenav"})
    void_tags = frozenset({
        "area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "param", "source", "track", "wbr",
        "circle", "ellipse", "line", "path", "polygon", "polyline", "rect", "stop", "use",
    })

    def _is_multiline_open(line: str) -> re.Match[str] | None:
        match = JSX_LINE_OPEN_TAG_RE.match(line)
        if not match:
            return None
        token = match.group(0)
        tag = match.group("tag")
        rest = match.group("rest")
        if token.rstrip().endswith("/>") or f"</{tag}>" in rest:
            return None
        return match

    def _extract_family_tokens(line: str, tag: str) -> set[str]:
        families: set[str] = set()

        for match in re.finditer(
            r'className\s*=\s*(?:"([^"]*)"|\'([^\']*)\'|\{`([^`]*)`\})',
            line,
        ):
            raw_value = next((group for group in match.groups() if group is not None), "")
            cleaned = re.sub(r"\$\{[^}]*\}", " ", raw_value).lower()
            for class_name in cleaned.split():
                normalized = re.sub(r"[^a-z0-9_-]", "", class_name)
                if not normalized:
                    continue
                parts = [part for part in re.split(r"[-_]", normalized) if part]
                if normalized in family_keywords:
                    families.add(normalized)
                if len(parts) >= 2 and parts[0] in family_keywords:
                    families.add(parts[0])
                for part in parts:
                    if part in family_keywords:
                        families.add(part)

        if tag.lower() == "aside":
            families.add("sidebar")
        elif tag.lower() == "nav":
            families.add("nav")

        return families

    def _extract_group_family(line: str) -> tuple[str, str] | None:
        open_match = _is_multiline_open(line)
        if not open_match:
            return None
        tag = open_match.group("tag")

        for match in re.finditer(
            r'className\s*=\s*(?:"([^"]*)"|\'([^\']*)\'|\{`([^`]*)`\})',
            line,
        ):
            raw_value = next((group for group in match.groups() if group is not None), "")
            cleaned = re.sub(r"\$\{[^}]*\}", " ", raw_value).lower()
            for class_name in cleaned.split():
                normalized = re.sub(r"[^a-z0-9_-]", "", class_name)
                parts = [part for part in re.split(r"[-_]", normalized) if part]
                if len(parts) >= 2 and parts[0] in family_keywords and parts[1] == "group":
                    return parts[0], tag

        return None

    def _find_parent_boundary(lines: list[str], start_index: int, opener_indent: int, families: set[str]) -> int | None:
        for scan_index in range(start_index + 1, len(lines)):
            stripped = lines[scan_index].strip()
            if not stripped:
                continue

            open_match = _is_multiline_open(lines[scan_index])
            if not open_match:
                continue

            boundary_indent = len(open_match.group("indent"))
            boundary_families = _extract_family_tokens(lines[scan_index], open_match.group("tag"))
            if boundary_indent <= opener_indent and families.isdisjoint(boundary_families):
                return scan_index

        return None

    def _collect_unclosed_block_tags(block_lines: list[str]) -> list[str]:
        block = "\n".join(block_lines)
        stack: list[str] = []

        for match in JSX_TAG_TOKEN_RE.finditer(block):
            token = match.group(0)
            tag = match.group("tag")
            lower_tag = tag.lower()

            if token.startswith("</"):
                if stack and stack[-1] == tag:
                    stack.pop()
                    continue
                for reverse_index in range(len(stack) - 1, -1, -1):
                    if stack[reverse_index] == tag:
                        del stack[reverse_index:]
                        break
                continue

            is_html_void = tag[0].islower() and lower_tag in void_tags
            if token.endswith("/>") or is_html_void:
                continue
            stack.append(tag)

        return stack

    lines = source.splitlines()
    changed = False

    repaired_lines: list[str] = []
    pending_extra_group_close = 0
    group_stack: list[tuple[str, str, int]] = []

    for line in lines:
        open_match = _is_multiline_open(line)
        if open_match:
            group_family = _extract_group_family(line)
            if group_family:
                family, tag = group_family
                indent = len(open_match.group("indent"))
                while group_stack and group_stack[-1] == (family, tag, indent):
                    repaired_lines.append(f"{open_match.group('indent')}</{tag}>")
                    group_stack.pop()
                    pending_extra_group_close += 1
                    changed = True
                group_stack.append((family, tag, indent))
            repaired_lines.append(line)
            continue

        close_match = JSX_LINE_CLOSE_TAG_RE.match(line)
        if close_match:
            tag = close_match.group("tag")
            if tag == "div" and group_stack and group_stack[-1][1] == "div":
                group_stack.pop()
                repaired_lines.append(line)
                continue

            if tag in parent_tags and pending_extra_group_close > 0:
                previous_index = len(repaired_lines) - 1
                while previous_index >= 0 and not repaired_lines[previous_index].strip():
                    previous_index -= 1
                if previous_index >= 0 and repaired_lines[previous_index].strip() == "</div>":
                    del repaired_lines[previous_index]
                    pending_extra_group_close -= 1
                    changed = True

            repaired_lines.append(line)
            continue

        repaired_lines.append(line)

    updated_lines = repaired_lines

    for _ in range(4):
        pass_changed = False

        for index, line in enumerate(updated_lines):
            open_match = _is_multiline_open(line)
            if not open_match:
                continue

            opener_indent = len(open_match.group("indent"))
            opener_families = _extract_family_tokens(line, open_match.group("tag"))
            if not opener_families:
                continue

            boundary_index = _find_parent_boundary(updated_lines, index, opener_indent, opener_families)
            if boundary_index is None:
                continue

            previous_index = index - 1
            while previous_index >= 0 and not updated_lines[previous_index].strip():
                previous_index -= 1
            if previous_index < 0 or not JSX_LINE_CLOSE_TAG_RE.match(updated_lines[previous_index]):
                continue

            block_start = previous_index
            while block_start > 0:
                candidate = updated_lines[block_start - 1]
                if not candidate.strip() or JSX_LINE_CLOSE_TAG_RE.match(candidate):
                    block_start -= 1
                    continue
                break

            parent_tag = ""
            parent_indent = ""
            for search_index in range(block_start - 1, -1, -1):
                parent_open_match = _is_multiline_open(updated_lines[search_index])
                if not parent_open_match:
                    continue
                if parent_open_match.group("tag") not in parent_tags:
                    continue
                if len(parent_open_match.group("indent")) > opener_indent:
                    continue
                parent_families = _extract_family_tokens(
                    updated_lines[search_index],
                    parent_open_match.group("tag"),
                )
                if opener_families.isdisjoint(parent_families):
                    continue
                parent_tag = parent_open_match.group("tag")
                parent_indent = parent_open_match.group("indent")
                break

            if not parent_tag:
                continue

            remove_from = None
            for close_index in range(block_start, index):
                close_match = JSX_LINE_CLOSE_TAG_RE.match(updated_lines[close_index])
                if close_match and close_match.group("tag") == parent_tag:
                    remove_from = close_index
                    break

            if remove_from is None:
                continue

            orphan_block_lines = updated_lines[index:boundary_index]
            if not orphan_block_lines:
                continue

            insertion_lines = [
                f"{open_match.group('indent')}</{tag}>"
                for tag in reversed(_collect_unclosed_block_tags(orphan_block_lines))
            ]
            insertion_lines.append(f"{parent_indent}</{parent_tag}>")

            pruned_lines = updated_lines[:remove_from] + updated_lines[index:]
            adjusted_boundary = boundary_index - (index - remove_from)
            updated_lines = (
                pruned_lines[:adjusted_boundary]
                + insertion_lines
                + pruned_lines[adjusted_boundary:]
            )
            changed = True
            pass_changed = True
            break

        if not pass_changed:
            break

    if not changed:
        return source
    return "\n".join(updated_lines) + ("\n" if source.endswith("\n") else "")


def _repair_componentized_jsx_root_returns(source: str) -> str:
    void_tags = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

    def _has_single_top_level_jsx_root(body: str) -> bool:
        stack: list[str] = []
        top_level_roots = 0
        cursor = 0

        for match in JSX_TAG_TOKEN_RE.finditer(body):
            if not stack and body[cursor:match.start()].strip():
                return False

            token = match.group(0)
            tag = match.group("tag")
            lower_tag = tag.lower()

            if token.startswith("</"):
                for reverse_index in range(len(stack) - 1, -1, -1):
                    if stack[reverse_index] == tag:
                        del stack[reverse_index]
                        break
                cursor = match.end()
                continue

            if not stack:
                top_level_roots += 1
                if top_level_roots > 1:
                    return False

            if not token.endswith("/>") and lower_tag not in void_tags:
                stack.append(tag)

            cursor = match.end()

        if not stack and body[cursor:].strip():
            return False

        return top_level_roots == 1

    def _repl(match: re.Match[str]) -> str:
        body = match.group("body").strip()
        if not body.startswith("<"):
            return match.group(0)
        if body.startswith(("<>", "<React.Fragment")):
            return match.group(0)
        if not body.endswith(">"):
            return match.group(0)
        if ";" in body:
            return match.group(0)
        if _has_single_top_level_jsx_root(body):
            return match.group(0)
        if "\n" not in body:
            return f"return (<>{body}</>);"

        indented = "\n".join(
            f"    {line}" if line else ""
            for line in body.splitlines()
        )
        return f"return (\n  <>\n{indented}\n  </>\n);"

    return COMPONENTIZED_JSX_RETURN_RE.sub(_repl, source)


def _repair_componentized_comment_split_identifiers(source: str) -> str:
    def _repl(match: re.Match[str]) -> str:
        comment = " ".join(match.group("comment").split()).strip()
        prefix = match.group("prefix").strip()
        suffix = match.group("suffix").strip()
        rest = match.group("rest") or ""
        comment_block = f"/* {comment} */\n" if comment else ""
        return f"{comment_block}{prefix}{suffix}{rest}"

    return COMMENT_SPLIT_IDENTIFIER_RE.sub(_repl, source)


def _repair_componentized_comment_tail_split_identifiers(source: str) -> str:
    return COMMENT_TAIL_SPLIT_IDENTIFIER_RE.sub(
        lambda match: f"{match.group('expr').strip()}{match.group('suffix').strip()}{match.group('rest') or ''}",
        source,
    )


def _repair_componentized_orphan_comment_split_identifiers(source: str) -> str:
    updated = source

    for _ in range(8):
        def _repl(match: re.Match[str]) -> str:
            line_start = updated.rfind("\n", 0, match.start()) + 1
            if "/*" in updated[line_start:match.start()]:
                return match.group(0)
            prefix = match.group("prefix").strip()
            suffix = match.group("suffix").strip()
            rest = match.group("rest") or ""
            return f"{prefix}{suffix}{rest}"

        repaired = ORPHAN_COMMENT_SPLIT_IDENTIFIER_RE.sub(_repl, updated)
        if repaired == updated:
            break
        updated = repaired

    return updated


def _repair_componentized_orphan_comment_split_dotted_identifiers(source: str) -> str:
    updated = source

    for _ in range(8):
        def _repl(match: re.Match[str]) -> str:
            line_start = updated.rfind("\n", 0, match.start()) + 1
            if "/*" in updated[line_start:match.start()]:
                return match.group(0)
            prefix = match.group("prefix").strip()
            suffix = match.group("suffix").strip()
            rest = match.group("rest") or ""
            return f"{prefix}{suffix}{rest}"

        repaired = ORPHAN_COMMENT_SPLIT_DOTTED_IDENTIFIER_RE.sub(_repl, updated)
        if repaired == updated:
            break
        updated = repaired

    return updated


def _repair_componentized_orphan_comment_split_string_literals(source: str) -> str:
    def _repl(match: re.Match[str]) -> str:
        prefix = match.group("prefix")
        quote = match.group("quote")
        content = match.group("content").strip()
        return f"{prefix}{quote}{content}{quote}"

    return ORPHAN_COMMENT_SPLIT_STRING_LITERAL_RE.sub(_repl, source)


def _repair_componentized_jsx_expression_comment_split_identifiers(source: str) -> str:
    return JSX_EXPR_COMMENT_SPLIT_IDENTIFIER_RE.sub(
        lambda match: f"{{{match.group('prefix').strip()}{match.group('suffix').strip()}{match.group('rest')}}}",
        source,
    )


def _repair_componentized_orphan_comment_close_in_string_literals(source: str) -> str:
    updated = source

    for _ in range(8):
        repaired = ORPHAN_COMMENT_CLOSE_IN_STRING_LITERAL_RE.sub(
            lambda match: (
                f"{match.group('prefix')}{match.group('quote')}"
                f"{match.group('before').rstrip()}{match.group('after').lstrip()}"
                f"{match.group('quote')}"
            ),
            updated,
        )
        if repaired == updated:
            break
        updated = repaired

    return updated


def _repair_componentized_jsx_comment_swallowed_tag_boundaries(source: str) -> str:
    return JSX_COMMENT_SWALLOWED_TAG_BOUNDARY_RE.sub(
        lambda match: match.group("boundary"),
        source,
    )


def _strip_componentized_alpine_jsx_directives(source: str) -> str:
    updated = ALPINE_JSX_DIRECTIVE_NOTE_RE.sub("", source)
    updated = ALPINE_JSX_DIRECTIVE_TEXT_RE.sub("", updated)
    for _ in range(8):
        repaired = ALPINE_JSX_ATTR_RE.sub("", updated)
        if repaired == updated:
            break
        updated = repaired
    return updated


def _strip_componentized_inline_script_tags(source: str) -> str:
    if "<script" not in source.lower():
        return source

    def _replace(match: re.Match[str]) -> str:
        block = match.group(0)
        lowered = block.lower()
        if 'type="module"' in lowered or "src=" in lowered:
            return block
        return "{/* Removed broken inline script from generated component */}"

    return INLINE_COMPONENT_SCRIPT_TAG_RE.sub(_replace, source)


def _repair_componentized_link_self_closing_children(source: str) -> str:
    return LINK_SELF_CLOSING_WITH_CHILDREN_RE.sub(
        lambda match: f"<Link{match.group('attrs')}>{match.group('inner')}</Link>",
        source,
    )


def _repair_componentized_bare_react_fragment_closers(source: str) -> str:
    if "</React>" not in source:
        return source
    if "<React>" in source:
        return source
    open_fragments = len(re.findall(r"<React\.Fragment\b", source))
    closed_fragments = source.count("</React.Fragment>")
    if open_fragments <= closed_fragments:
        return re.sub(r"(?m)^\s*</React>\s*$\n?", "", source)
    return re.sub(r"(?m)^(\s*)</React>\s*$", r"\1</React.Fragment>", source)


def _remove_componentized_orphan_jsx_closing_brace_lines(source: str) -> str:
    updated = source
    lines = updated.splitlines()
    if not lines:
        return updated

    void_tags = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

    def _infer_recent_unclosed_tag(line_index: int) -> str | None:
        stack: list[str] = []

        for history_index in range(max(0, line_index - 16), line_index):
            history = lines[history_index].strip()
            if not history:
                continue
            if re.match(r"^(?:return\s*\(|const|let|var|function|export|if|for|while|switch)\b", history):
                stack.clear()
                continue

            for match in JSX_TAG_TOKEN_RE.finditer(history):
                token = match.group(0)
                tag = match.group("tag")
                lower_tag = tag.lower()
                if token.startswith("</"):
                    for reverse_index in range(len(stack) - 1, -1, -1):
                        if stack[reverse_index] == tag:
                            del stack[reverse_index]
                            break
                    continue
                if token.endswith("/>") or lower_tag in void_tags:
                    continue
                stack.append(tag)

        return stack[-1] if stack else None

    filtered_lines: list[str] = []

    for index, line in enumerate(lines):
        if line.strip() != "}":
            filtered_lines.append(line)
            continue

        previous = ""
        for prev_index in range(index - 1, -1, -1):
            candidate = lines[prev_index].strip()
            if candidate:
                previous = candidate
                break

        following = ""
        for next_index in range(index + 1, len(lines)):
            candidate = lines[next_index].strip()
            if candidate:
                following = candidate
                break

        recent_balance = 0
        for history_index in range(index - 1, max(-1, index - 8), -1):
            history = lines[history_index].strip()
            if not history:
                continue
            if re.match(r"^(?:return\s*\(|const|let|var|function|export|if|for|while|switch)\b", history):
                break
            if "<" in history or "{" in history or "}" in history:
                recent_balance += history.count("{") - history.count("}")

        if (
            previous
            and following.startswith("<")
            and re.search(r"<[A-Za-z/]", previous)
            and previous.count("{") == previous.count("}")
            and recent_balance <= 0
        ):
            inferred_tag = _infer_recent_unclosed_tag(index)
            if inferred_tag:
                indent = re.match(r"[ \t]*", line).group(0)
                filtered_lines.append(f"{indent}</{inferred_tag}>")
                continue
            continue

        filtered_lines.append(line)

    return "\n".join(filtered_lines) + ("\n" if updated.endswith("\n") else "")


def _repair_componentized_missing_sibling_closing_tags(source: str) -> str:
    lines = source.splitlines()
    if not lines:
        return source

    void_tags = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
    repaired_lines: list[str] = []
    stack: list[tuple[str, int]] = []

    for line in lines:
        open_match = JSX_LINE_OPEN_TAG_RE.match(line)
        close_match = JSX_LINE_CLOSE_TAG_RE.match(line)
        current_indent = len((open_match or close_match).group("indent")) if (open_match or close_match) else None
        current_tag = (open_match or close_match).group("tag") if (open_match or close_match) else None
        is_open = bool(open_match)
        is_close = bool(close_match)

        if is_open:
            token = open_match.group(0)
            rest = open_match.group("rest")
            if token.endswith("/>") or current_tag.lower() in void_tags or f"</{current_tag}>" in rest:
                is_open = False

        if current_indent is not None:
            while stack and stack[-1][1] >= current_indent:
                top_tag, top_indent = stack[-1]
                if is_close and current_tag == top_tag and top_indent == current_indent:
                    break
                if is_open and top_indent < current_indent:
                    break
                repaired_lines.append(f"{' ' * top_indent}</{top_tag}>")
                stack.pop()

        repaired_lines.append(line)

        if is_close:
            for reverse_index in range(len(stack) - 1, -1, -1):
                if stack[reverse_index][0] == current_tag:
                    del stack[reverse_index]
                    break
            continue

        if is_open and current_indent is not None:
            stack.append((current_tag, current_indent))

    return "\n".join(repaired_lines) + ("\n" if source.endswith("\n") else "")


def _remove_componentized_duplicate_closing_tag_lines(source: str) -> str:
    lines = source.splitlines()
    if not lines:
        return source

    repaired_lines: list[str] = []
    changed = False

    for line in lines:
        close_match = re.fullmatch(r"[ \t]*</(?P<tag>[A-Za-z][A-Za-z0-9.-]*)>\s*", line)
        if close_match:
            tag = close_match.group("tag")
            indent = re.match(r"[ \t]*", line).group(0)
            previous_non_empty = next((existing for existing in reversed(repaired_lines) if existing.strip()), "")
            previous_close_match = re.fullmatch(
                rf"(?P<indent>[ \t]*)</{re.escape(tag)}>\s*",
                previous_non_empty,
            )
            if previous_close_match and previous_close_match.group("indent") == indent:
                changed = True
                continue

        repaired_lines.append(line)

    if not changed:
        return source
    return "\n".join(repaired_lines) + ("\n" if source.endswith("\n") else "")


def _repair_componentized_inline_mismatched_closing_tags(source: str) -> str:
    void_tags = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

    def _repair_body(body: str) -> str:
        tokens = list(JSX_TAG_TOKEN_RE.finditer(body))
        if not tokens:
            return body

        rebuilt: list[str] = []
        stack: list[str] = []
        last_index = 0
        changed = False

        for match in tokens:
            start, end = match.span()
            token = match.group(0)
            tag = match.group("tag")
            lower_tag = tag.lower()
            is_close = token.startswith("</")
            is_self_closing = token.endswith("/>")
            line_start = body.rfind("\n", 0, start) + 1
            has_inline_prefix = bool(body[line_start:start].strip())

            rebuilt.append(body[last_index:start])

            if not is_close:
                rebuilt.append(token)
                if not is_self_closing and lower_tag not in void_tags:
                    stack.append(tag)
                last_index = end
                continue

            if stack and stack[-1] == tag:
                stack.pop()
                rebuilt.append(token)
                last_index = end
                continue

            if not has_inline_prefix:
                rebuilt.append(token)
                last_index = end
                continue

            if stack and tag in stack:
                while stack and stack[-1] != tag:
                    rebuilt.append(f"</{stack.pop()}>")
                    changed = True
                if stack and stack[-1] == tag:
                    stack.pop()
                rebuilt.append(token)
                last_index = end
                continue

            if stack:
                corrected_tag = stack.pop()
                rebuilt.append(f"</{corrected_tag}>")
                changed = True
                last_index = end
                continue

            rebuilt.append(token)
            last_index = end

        rebuilt.append(body[last_index:])
        repaired = "".join(rebuilt)
        return repaired if changed else body

    def _repair_return(match: re.Match[str]) -> str:
        body = match.group("body")
        repaired = _repair_body(body)
        if repaired == body:
            return match.group(0)
        return match.group(0).replace(body, repaired, 1)

    return COMPONENTIZED_JSX_RETURN_RE.sub(
        _repair_return,
        source,
    )


def _repair_componentized_jsx_block_comment_bleed(source: str) -> str:
    def _repl(match: re.Match[str]) -> str:
        comment = " ".join(match.group("comment").split()).strip()
        jsx = match.group("jsx").strip()
        prefix = match.group("prefix").strip()
        suffix = match.group("suffix").strip()
        rest = match.group("rest") or ""
        indent = match.group("indent") or ""
        comment_block = f"{indent}/* {comment} */\n" if comment else ""
        return f"(\n{comment_block}{indent}{jsx}{{{prefix}{suffix}{rest}"

    return JSX_BLOCK_COMMENT_BLEED_RE.sub(_repl, source)


def _repair_componentized_jsx_text_comment_bleed(source: str) -> str:
    def _repl(match: re.Match[str]) -> str:
        prefix = " ".join(match.group("prefix").split()).strip()
        suffix = " ".join(match.group("suffix").split()).strip()
        if not prefix or not suffix:
            return match.group(0)
        return f">{prefix} {suffix}<"

    return JSX_TEXT_COMMENT_CLOSE_BLEED_RE.sub(_repl, source)


def _repair_componentized_jsx_attribute_comment_bleed(source: str) -> str:
    updated = JSX_ATTR_COMMENT_BLEED_RE.sub(
        lambda match: match.group("attr"),
        source,
    )
    return JSX_ATTR_LINE_COMMENT_BLEED_RE.sub(
        lambda match: match.group("attr"),
        updated,
    )


def _repair_componentized_jsx_tag_comment_lines(source: str) -> str:
    lines = source.splitlines()
    if not lines:
        return source

    updated_lines: list[str] = []
    inside_open_tag = False
    changed = False

    for line in lines:
        stripped = line.strip()

        if inside_open_tag and re.fullmatch(r"\{?/\*[\s\S]{0,200}?\*/\}?", stripped):
            changed = True
            if ">" in stripped:
                inside_open_tag = False
            continue

        if inside_open_tag:
            repaired = re.sub(r"\s*\{/\*[\s\S]{0,200}?\*/\}", "", line)
            repaired = re.sub(r"\s*/\*[\s\S]{0,200}?\*/", "", repaired)
            if repaired != line:
                changed = True
            line = repaired

        updated_lines.append(line)

        line_without_strings = re.sub(r"(['\"]).*?\1", "", line)
        if not inside_open_tag:
            stripped_without_strings = line_without_strings.lstrip()
            inside_open_tag = (
                stripped_without_strings.startswith("<")
                and not stripped_without_strings.startswith(("</", "<!", "<?", "<>"))
                and ">" not in stripped_without_strings
            )
        elif ">" in line_without_strings:
            inside_open_tag = False

    if not changed:
        return source
    return "\n".join(updated_lines) + ("\n" if source.endswith("\n") else "")


def _repair_componentized_jsx_text_comment_line_bleed(source: str) -> str:
    def _replace(match: re.Match[str]) -> str:
        parts = [match.group("head").strip(), match.group("tail").strip()]
        merged = " ".join(part for part in parts if part)
        return f"{match.group('prefix')}{merged}{match.group('suffix')}"

    return JSX_TEXT_LINE_COMMENT_CLOSE_BLEED_RE.sub(_replace, source)


def _repair_componentized_jsx_code_block_literals(source: str) -> str:
    def _escape_braces(body: str) -> str:
        if "{" not in body and "}" not in body and "<" not in body and ">" not in body:
            return body
        updated = body.replace("<", "&lt;").replace(">", "&gt;")
        updated = updated.replace("{{", "&#123;").replace("}}", "&#125;")
        updated = updated.replace("{", "&#123;").replace("}", "&#125;")
        return updated

    updated = JSX_CODE_TAG_RE.sub(
        lambda match: f"{match.group('open')}{_escape_braces(match.group('body'))}{match.group('close')}",
        source,
    )
    return JSX_PRE_TEXT_TAG_RE.sub(
        lambda match: f"{match.group('open')}{_escape_braces(match.group('body'))}{match.group('close')}",
        updated,
    )


def _normalize_componentized_jsx_code_template_literals(source: str) -> str:
    return JSX_CODE_TEMPLATE_LITERAL_RE.sub(
        lambda match: f"{match.group('open')}{{{json.dumps(match.group('body'))}}}{match.group('close')}",
        source,
    )


def _normalize_componentized_void_jsx_elements(source: str) -> str:
    return VOID_JSX_ELEMENT_RE.sub(
        lambda match: f"<{match.group('tag')}{match.group('attrs').rstrip()} />",
        source,
    )


def _strip_void_svg_closing_tags(source: str) -> str:
    """Remove closing tags for SVG elements that are always void/self-closing.

    The LLM sometimes writes <path d="..." /></path> or <circle .../></circle>.
    The closing tags are invalid and cause build errors.
    """
    SVG_VOID = ("circle", "ellipse", "line", "path", "polygon", "polyline", "rect", "stop", "use")
    pattern = re.compile(
        r"</(?:" + "|".join(SVG_VOID) + r")\s*>",
        re.IGNORECASE,
    )
    return pattern.sub("", source)


def _wrap_sibling_svg_elements_in_fragments(source: str) -> str:
    """Wrap bare sibling SVG child elements in React fragments.

    Fixes the common LLM pattern where icon objects have:
      name: ( <path .../><circle .../> )
    which needs to be:
      name: ( <><path .../><circle .../></> )
    """
    SVG_CHILDREN = frozenset({"path", "circle", "rect", "line", "polyline", "polygon", "ellipse", "g", "text", "use"})
    SIBLING_SVG_RE = re.compile(
        r"(?P<prefix>\(\s*\n?\s*)"
        r"(?P<first><(?:" + "|".join(SVG_CHILDREN) + r")\b[^>]*/>)"
        r"(?P<siblings>(?:\s*<(?:" + "|".join(SVG_CHILDREN) + r")\b[^>]*/>)+)"
        r"(?P<suffix>\s*\))",
    )

    def _repl(match: re.Match[str]) -> str:
        return f"{match.group('prefix')}<>{match.group('first')}{match.group('siblings')}</>{match.group('suffix')}"

    return SIBLING_SVG_RE.sub(_repl, source)


def _repair_componentized_logical_svg_sibling_conditions(source: str) -> str:
    return LOGICAL_SVG_SIBLING_CONDITION_RE.sub(
        lambda match: f"{{{match.group('expr')} (<>{match.group('first')}{match.group('siblings')}</>)}}",
        source,
    )


def _repair_componentized_inline_svg_shape_nesting(source: str) -> str:
    shape_tags = r"path|circle|rect|line|polyline|polygon|ellipse|use"
    pattern = re.compile(
        rf"<(?P<tag>{shape_tags})\b(?P<attrs>[^<>]*?)>(?=\s*<(?:{shape_tags})\b)",
        re.IGNORECASE,
    )
    return pattern.sub(
        lambda match: f"<{match.group('tag')}{match.group('attrs').rstrip()} />",
        source,
    )


def _repair_componentized_link_wrapper_closer_leaks(source: str) -> str:
    if "<Link" not in source or "<svg" not in source:
        return source

    def _looks_like_sidebar_item(body: str) -> bool:
        if "<Link" in body or "</Link>" in body:
            return False
        text = re.sub(r"<[^>]+>", " ", body)
        return bool(re.search(r"[A-Za-z0-9][A-Za-z0-9/&,\- ']{1,80}", text))

    def _replace_open(match: re.Match[str]) -> str:
        body = match.group("body")
        if not _looks_like_sidebar_item(body):
            return match.group(0)
        return f"<Link{match.group('attrs')}>{body}</Link>"

    updated = LINK_WRAPPER_CLOSER_LEAK_RE.sub(_replace_open, source)

    def _replace_self_closing(match: re.Match[str]) -> str:
        body = match.group("body")
        if not _looks_like_sidebar_item(body):
            return match.group(0)
        return f"<Link{match.group('attrs')}>{body}</Link>"

    return SELF_CLOSING_LINK_WRAPPER_CLOSER_LEAK_RE.sub(_replace_self_closing, updated)


def _repair_componentized_icon_prop_svg_closer_bleeds(source: str) -> str:
    pattern = re.compile(
        r"(?P<prefix>\bicon=\{<svg\b[\s\S]{0,1600}?)(?P<closer></[A-Z][A-Za-z0-9.]*>)(?P<suffix>\})"
    )
    return pattern.sub(
        lambda match: (
            match.group("prefix")
            if "</svg>" in match.group("prefix")
            else f"{match.group('prefix')}</svg>{match.group('suffix')}"
        ),
        source,
    )


def _repair_componentized_inline_svg_text_boundary_leaks(source: str) -> str:
    if "<svg" not in source:
        return source

    pattern = re.compile(
        r"(?P<prefix><svg\b[\s\S]{0,1600}?<(?:path|line|polyline|polygon|rect|circle|ellipse)\b[^>]*?/>)\s*(?P<text>[A-Z0-9$][^<]{0,80})(?P<suffix></(?:button|span|div|a|p|h[1-6])>)"
    )

    def _repl(match: re.Match[str]) -> str:
        svg_segment = match.group("prefix").rsplit("<svg", 1)[-1]
        if "</svg>" in svg_segment:
            return match.group(0)
        return f"{match.group('prefix')}</svg>{match.group('text')}{match.group('suffix')}"

    repaired = pattern.sub(_repl, source)
    return repaired if repaired != source else source


def _repair_componentized_tooltip_foreign_object_closers(source: str) -> str:
    if "{tooltip.visible && (" not in source or "<foreignObject" not in source:
        return source

    pattern = re.compile(
        r"(?P<prefix>\{tooltip\.visible\s*&&\s*\(\s*<g>[\s\S]{0,2400}?<foreignObject\b[\s\S]{0,1200}?</div>)(?P<suffix>\s*\)\})"
    )

    def _repl(match: re.Match[str]) -> str:
        if "</foreignObject>" in match.group("prefix"):
            return match.group(0)
        return f"{match.group('prefix')}</foreignObject></g>{match.group('suffix')}"

    repaired = pattern.sub(_repl, source)
    return repaired if repaired != source else source


def _repair_componentized_self_closing_component_orphan_closers(source: str) -> str:
    open_tag_re = re.compile(r"<(?P<tag>[A-Z][A-Za-z0-9.]*)\b")
    closer_template = r"</{}\s*>"
    repaired: list[str] = []
    cursor = 0
    idx = 0
    changed = False

    def _find_tag_end(start_index: int) -> int:
        brace_depth = 0
        in_single = False
        in_double = False
        in_template = False
        escaped = False
        scan = start_index

        while scan < len(source):
            char = source[scan]
            if in_single:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == "'":
                    in_single = False
                scan += 1
                continue

            if in_double:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_double = False
                scan += 1
                continue

            if in_template:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == "`":
                    in_template = False
                scan += 1
                continue

            if char == "'":
                in_single = True
            elif char == '"':
                in_double = True
            elif char == "`":
                in_template = True
            elif char == "{":
                brace_depth += 1
            elif char == "}" and brace_depth > 0:
                brace_depth -= 1
            elif char == ">" and brace_depth == 0:
                return scan

            scan += 1

        return -1

    while True:
        match = open_tag_re.search(source, idx)
        if not match:
            break

        tag_end = _find_tag_end(match.start())
        if tag_end == -1:
            break

        tag_text = source[match.start():tag_end + 1]
        if not tag_text.rstrip().endswith("/>"):
            idx = tag_end + 1
            continue

        whitespace_end = tag_end + 1
        while whitespace_end < len(source) and source[whitespace_end].isspace():
            whitespace_end += 1

        closer_match = re.match(closer_template.format(re.escape(match.group("tag"))), source[whitespace_end:])
        if not closer_match:
            idx = tag_end + 1
            continue

        repaired.append(source[cursor:match.start()])
        repaired.append(tag_text)
        repaired.append(source[tag_end + 1:whitespace_end])
        cursor = whitespace_end + closer_match.end()
        idx = cursor
        changed = True

    if not changed:
        return source

    repaired.append(source[cursor:])
    return "".join(repaired)


def _repair_componentized_self_closing_component_children(source: str) -> str:
    updated = source
    for _ in range(6):
        changed = False

        def _replace(match: re.Match[str]) -> str:
            nonlocal changed
            inner = match.group("inner")
            leading = inner.lstrip()
            if "<" not in inner or not inner.strip() or not leading.startswith("<") or leading.startswith("</"):
                return match.group(0)
            changed = True
            return f"<{match.group('tag')}{match.group('attrs')}>{inner}</{match.group('tag')}>"

        repaired = COMPONENT_SELF_CLOSING_WITH_CHILDREN_RE.sub(_replace, updated)
        if not changed:
            return updated
        updated = repaired

    return updated


def _repair_componentized_bare_jsx_array_map_expressions(source: str) -> str:
    return BARE_JSX_ARRAY_MAP_EXPRESSION_RE.sub(
        lambda match: f"{match.group('prefix')}{{{match.group('expr')}}}{match.group('suffix')}",
        source,
    )


def _repair_componentized_inline_jsx_return_boundaries(source: str) -> str:
    lines = source.splitlines()
    if not lines:
        return source

    repaired_lines: list[str] = []
    changed = False

    for line in lines:
        updated = line
        leading_indent = re.match(r"[ \t]*", line).group(0)

        start_match = re.match(r"^(?P<head>[ \t]*return\s*\()(?P<rest>\s*<.+)$", updated)
        if start_match:
            repaired_lines.append(start_match.group("head"))
            updated = f"{leading_indent}  {start_match.group('rest').lstrip()}"
            changed = True

        end_match = re.match(r"^(?P<prefix>.*\S)(?P<space>\s+)(?P<suffix>\)+[;,}]?\s*)$", updated)
        if end_match and "<" in end_match.group("prefix"):
            repaired_lines.append(end_match.group("prefix").rstrip())
            repaired_lines.append(f"{leading_indent}{end_match.group('suffix').strip()}")
            changed = True
            continue

        repaired_lines.append(updated)

    if not changed:
        return source
    return "\n".join(repaired_lines) + ("\n" if source.endswith("\n") else "")


def _repair_componentized_jsx_branch_missing_closers(source: str) -> str:
    lines = source.splitlines()
    if not lines:
        return source

    void_tags = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
    repaired_lines: list[str] = []
    stack: list[tuple[str, int]] = []
    changed = False

    for line in lines:
        stripped = line.strip()
        branch_close_match = re.fullmatch(r"\)+\}\s*", stripped)
        current_indent = len(re.match(r"[ \t]*", line).group(0))

        if branch_close_match:
            while stack and stack[-1][1] > current_indent:
                tag, tag_indent = stack.pop()
                repaired_lines.append(f"{' ' * tag_indent}</{tag}>")
                changed = True
            repaired_lines.append(line)
            continue

        close_match = JSX_LINE_CLOSE_TAG_RE.match(line)
        if close_match:
            current_tag = close_match.group("tag")
            for reverse_index in range(len(stack) - 1, -1, -1):
                if stack[reverse_index][0] == current_tag:
                    del stack[reverse_index]
                    break
            repaired_lines.append(line)
            continue

        open_match = JSX_LINE_OPEN_TAG_RE.match(line)
        repaired_lines.append(line)
        if not open_match:
            continue

        current_tag = open_match.group("tag")
        token = open_match.group(0)
        rest = open_match.group("rest")
        if token.endswith("/>") or current_tag.lower() in void_tags or f"</{current_tag}>" in rest:
            continue
        stack.append((current_tag, len(open_match.group("indent"))))

    if not changed:
        return source
    return "\n".join(repaired_lines) + ("\n" if source.endswith("\n") else "")


def _repair_componentized_multiline_map_branch_closers(source: str) -> str:
    lines = source.splitlines()
    if not lines or ".map(" not in source:
        return source

    void_tags = {
        "area", "base", "br", "circle", "col", "ellipse", "embed", "hr", "img",
        "input", "line", "link", "meta", "param", "path", "polygon", "polyline",
        "rect", "source", "stop", "track", "use", "wbr",
    }
    multi_open_re = re.compile(r"^(?P<indent>[ \t]*)<(?P<tag>[A-Za-z][A-Za-z0-9.-]*)\b(?P<rest>[^>]*)$")

    class _BranchContext:
        def __init__(self) -> None:
            self.tag_stack: list[tuple[str, int]] = []
            self.pending_open: tuple[str, int] | None = None

    contexts: list[_BranchContext] = []
    repaired_lines: list[str] = []
    changed = False

    def _is_map_branch_start(text: str) -> bool:
        return ".map(" in text and "=>" in text and bool(re.search(r"=>\s*\(\s*$", text))

    def _same_closer_after_branch(index: int, closer: str) -> bool:
        branch_close_seen = False
        for candidate in lines[index + 1:]:
            candidate_stripped = candidate.strip()
            if not candidate_stripped:
                continue
            if not branch_close_seen:
                if MAP_BRANCH_CLOSE_RE.fullmatch(candidate_stripped):
                    branch_close_seen = True
                continue
            return candidate_stripped == closer
        return False

    for index, line in enumerate(lines):
        stripped = line.strip()

        if _is_map_branch_start(stripped):
            contexts.append(_BranchContext())
            repaired_lines.append(line)
            continue

        if not contexts:
            repaired_lines.append(line)
            continue

        context = contexts[-1]

        close_match = JSX_LINE_CLOSE_TAG_RE.match(line)
        if close_match:
            current_tag = close_match.group("tag")
            if context.tag_stack:
                top_tag, top_indent = context.tag_stack[-1]
                if current_tag == top_tag:
                    context.tag_stack.pop()
                elif (
                    MAP_BRANCH_CLOSE_RE.fullmatch(next((candidate.strip() for candidate in lines[index + 1:] if candidate.strip()), ""))
                    and _same_closer_after_branch(index, stripped)
                ):
                    repaired_lines.append(f"{' ' * top_indent}</{top_tag}>")
                    context.tag_stack.pop()
                    changed = True
                    continue
                else:
                    for reverse_index in range(len(context.tag_stack) - 1, -1, -1):
                        if context.tag_stack[reverse_index][0] == current_tag:
                            del context.tag_stack[reverse_index]
                            break
            repaired_lines.append(line)
            continue

        if MAP_BRANCH_CLOSE_RE.fullmatch(stripped):
            while context.tag_stack:
                tag, tag_indent = context.tag_stack.pop()
                repaired_lines.append(f"{' ' * tag_indent}</{tag}>")
                changed = True
            repaired_lines.append(line)
            contexts.pop()
            continue

        if context.pending_open is not None:
            pending_tag, pending_indent = context.pending_open
            if ">" in line:
                stripped_line = line.strip()
                if not stripped_line.endswith("/>") and pending_tag.lower() not in void_tags:
                    context.tag_stack.append((pending_tag, pending_indent))
                context.pending_open = None
            repaired_lines.append(line)
            continue

        open_match = JSX_LINE_OPEN_TAG_RE.match(line)
        if open_match:
            current_tag = open_match.group("tag")
            token = open_match.group(0)
            rest = open_match.group("rest")
            if (
                not token.endswith("/>")
                and current_tag.lower() not in void_tags
                and f"</{current_tag}>" not in rest
            ):
                context.tag_stack.append((current_tag, len(open_match.group("indent"))))
            repaired_lines.append(line)
            continue

        multi_open_match = multi_open_re.match(line)
        if multi_open_match:
            current_tag = multi_open_match.group("tag")
            rest = multi_open_match.group("rest")
            if current_tag.lower() not in void_tags and not rest.strip().endswith("/"):
                context.pending_open = (current_tag, len(multi_open_match.group("indent")))

        repaired_lines.append(line)

    if not changed:
        return source
    return "\n".join(repaired_lines) + ("\n" if source.endswith("\n") else "")


def _repair_componentized_map_branch_wrapper_closers(source: str) -> str:
    lines = source.splitlines()
    if not lines:
        return source

    void_tags = {
        "area", "base", "br", "circle", "col", "ellipse", "embed", "hr", "img",
        "input", "line", "link", "meta", "param", "path", "polygon", "polyline",
        "rect", "source", "stop", "track", "use", "wbr",
    }
    wrapper_closer_re = re.compile(r"^</(?P<tag>div|section|article|nav|aside|header|footer|main)>$")

    def _consume_line_tags(line: str, stack: list[str]) -> None:
        sanitized = line.replace("=>", "  ")
        for match in JSX_TAG_TOKEN_RE.finditer(sanitized):
            token = match.group(0)
            tag = match.group("tag")
            lower_tag = tag.lower()

            if token.startswith("</"):
                for reverse_index in range(len(stack) - 1, -1, -1):
                    if stack[reverse_index] == tag:
                        del stack[reverse_index:]
                        break
                continue

            if token.endswith("/>") or lower_tag in void_tags:
                continue
            stack.append(tag)

    result_lines: list[str] = []
    tag_stack: list[str] = []
    branch_outer_stack: list[str] | None = None
    branch_inner_stack: list[str] = []
    moved_closers: list[str] = []
    changed = False

    for index, line in enumerate(lines):
        stripped = line.strip()

        if branch_outer_stack is None and MAP_BRANCH_START_RE.search(stripped):
            branch_outer_stack = tag_stack.copy()
            branch_inner_stack = []
            moved_closers = []
            result_lines.append(line)
            _consume_line_tags(line, tag_stack)
            continue

        if branch_outer_stack is not None:
            closer_match = wrapper_closer_re.fullmatch(stripped)
            next_non_empty = ""
            for candidate in lines[index + 1:]:
                candidate_stripped = candidate.strip()
                if candidate_stripped:
                    next_non_empty = candidate_stripped
                    break

            if (
                closer_match
                and MAP_BRANCH_CLOSE_RE.fullmatch(next_non_empty)
                and closer_match.group("tag") not in branch_inner_stack
                and closer_match.group("tag") in branch_outer_stack
            ):
                same_closer_after_branch = False
                branch_close_seen = False
                non_empty_after_branch = 0
                for candidate in lines[index + 1:]:
                    candidate_stripped = candidate.strip()
                    if not candidate_stripped:
                        continue
                    if not branch_close_seen:
                        if MAP_BRANCH_CLOSE_RE.fullmatch(candidate_stripped):
                            branch_close_seen = True
                        continue
                    non_empty_after_branch += 1
                    if candidate_stripped == stripped:
                        same_closer_after_branch = True
                        break
                    if non_empty_after_branch >= 3:
                        break

                if not same_closer_after_branch:
                    moved_closers.append(line)
                else:
                    changed = True
                changed = True
                continue

        result_lines.append(line)

        if branch_outer_stack is not None and MAP_BRANCH_CLOSE_RE.fullmatch(stripped):
            if moved_closers:
                result_lines.extend(moved_closers)
                for moved in moved_closers:
                    _consume_line_tags(moved, tag_stack)
                moved_closers = []
            branch_outer_stack = None
            branch_inner_stack = []
            _consume_line_tags(line, tag_stack)
            continue

        _consume_line_tags(line, tag_stack)
        if branch_outer_stack is not None:
            _consume_line_tags(line, branch_inner_stack)

    if not changed:
        return source
    return "\n".join(result_lines) + ("\n" if source.endswith("\n") else "")


def _repair_componentized_svg_html_boundary_leaks(source: str) -> str:
    lines = source.splitlines()
    if not lines:
        return source

    repaired_lines: list[str] = []
    svg_stack: list[int] = []
    changed = False
    html_boundary_re = re.compile(r"^<(?:div|section|article|main|aside|header|footer|nav|button|h[1-6]|p|span|ul|ol|li)\b")

    for line in lines:
        stripped = line.strip()
        current_indent = len(re.match(r"[ \t]*", line).group(0))

        if svg_stack and html_boundary_re.match(stripped):
            while svg_stack and current_indent <= svg_stack[-1]:
                svg_indent = svg_stack.pop()
                repaired_lines.append(f"{' ' * svg_indent}</svg>")
                changed = True

        repaired_lines.append(line)
        open_count = len(re.findall(r"<svg\b", line))
        close_count = len(re.findall(r"</svg>", line))
        net_count = open_count - close_count
        if net_count > 0:
            svg_stack.extend([current_indent] * net_count)
        elif net_count < 0:
            for _ in range(min(len(svg_stack), -net_count)):
                svg_stack.pop()

    if not changed:
        return source
    return "\n".join(repaired_lines) + ("\n" if source.endswith("\n") else "")


def _repair_componentized_duplicate_self_closing_slashes(source: str) -> str:
    return re.sub(r"/\s*/>", "/>", source)


def _remove_componentized_self_closed_component_closer_lines(source: str) -> str:
    lines = source.splitlines()
    if not lines:
        return source

    opener_re = re.compile(r"<(?P<tag>[A-Z][A-Za-z0-9.]*)\b")
    has_self_open: dict[str, bool] = {}
    has_non_self_open: dict[str, bool] = {}

    def _find_tag_end(start: int) -> int:
        scan = start
        brace_depth = 0
        in_single = False
        in_double = False
        in_template = False
        escaped = False

        while scan < len(source):
            char = source[scan]

            if in_single:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == "'":
                    in_single = False
                scan += 1
                continue

            if in_double:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_double = False
                scan += 1
                continue

            if in_template:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == "`":
                    in_template = False
                scan += 1
                continue

            if char == "'":
                in_single = True
            elif char == '"':
                in_double = True
            elif char == "`":
                in_template = True
            elif char == "{":
                brace_depth += 1
            elif char == "}" and brace_depth > 0:
                brace_depth -= 1
            elif char == ">" and brace_depth == 0:
                return scan

            scan += 1

        return -1

    scan_index = 0
    while True:
        match = opener_re.search(source, scan_index)
        if not match:
            break

        tag_end = _find_tag_end(match.start())
        if tag_end == -1:
            break

        tag = match.group("tag")
        tag_text = source[match.start():tag_end + 1]
        if tag_text.rstrip().endswith("/>"):
            has_self_open[tag] = True
        else:
            has_non_self_open[tag] = True
        scan_index = tag_end + 1

    repaired_lines: list[str] = []
    changed = False

    for line in lines:
        stripped = line.strip()
        close_match = re.fullmatch(r"</(?P<tag>[A-Z][A-Za-z0-9.]*)>", stripped)
        if close_match:
            tag = close_match.group("tag")
            if has_self_open.get(tag) and not has_non_self_open.get(tag):
                changed = True
                continue

        repaired_lines.append(line)

    if not changed:
        return source
    return "\n".join(repaired_lines) + ("\n" if source.endswith("\n") else "")


def _repair_componentized_inline_jsx_attribute_block_comments(source: str) -> str:
    return INLINE_JSX_ATTRIBUTE_BLOCK_COMMENT_RE.sub(
        lambda match: match.group("attr"),
        source,
    )


def _repair_componentized_route_path_comment_bleeds(source: str) -> str:
    if "<Route" not in source or "path=" not in source or "/*" not in source:
        return source

    return ROUTE_PATH_COMMENT_BLEED_RE.sub(
        lambda match: f"{match.group('prefix')}{match.group('quote')}/{match.group('quote')}",
        source,
    )


def _repair_componentized_orphan_svg_prop_closer_lines(source: str) -> str:
    if "</svg>" not in source or "={<svg" not in source:
        return source

    return ORPHAN_SVG_PROP_CLOSER_LINE_RE.sub(
        lambda match: f"{match.group('indent')}{match.group('prop')}",
        source,
    )


def _repair_componentized_css_data_uri_quote_bleed(source: str) -> str:
    return CSS_DATA_URI_ESCAPED_QUOTE_BLEED_RE.sub(r"\\'", source)


def _repair_componentized_jsx_event_handler_arrow_bleed(source: str) -> str:
    updated = JSX_EVENT_HANDLER_ARROW_BLEED_RE.sub(
        lambda match: f"{match.group('prefix')}{match.group('param').strip()} =>",
        source,
    )
    return JSX_TYPED_EVENT_HANDLER_ARROW_BLEED_RE.sub(
        lambda match: f"{match.group('prefix')} =>{match.group('suffix')}",
        updated,
    )


def _repair_componentized_generic_arrow_bleed(source: str) -> str:
    return GENERIC_ARROW_BLEED_RE.sub(
        lambda match: f"{match.group('prefix')}{match.group('param').strip()} =>",
        source,
    )


def _repair_componentized_relational_operator_bleed(source: str) -> str:
    return RELATIONAL_OPERATOR_BLEED_RE.sub(
        lambda match: f"{match.group('prefix')} {match.group('op')}=",
        source,
    )


def _repair_componentized_ternary_branch_orphan_closing_tags(source: str) -> str:
    void_tags = frozenset({
        "area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "param", "source", "track", "wbr",
        "circle", "ellipse", "line", "path", "polygon", "polyline", "rect", "stop", "use",
    })
    lines = source.splitlines()
    if not any(TERNARY_BRANCH_START_RE.search(line) for line in lines):
        return source
    repairs: list[tuple[int, int, list[str]]] = []

    def _consume_branch_tags(line: str, stack: list[tuple[str, str]]) -> None:
        line_indent = re.match(r"[ \t]*", line).group(0)
        for match in JSX_TAG_TOKEN_RE.finditer(line):
            token = match.group(0)
            tag = match.group("tag")
            lower_tag = tag.lower()

            if token.startswith("</"):
                for reverse_index in range(len(stack) - 1, -1, -1):
                    if stack[reverse_index][0] == tag:
                        del stack[reverse_index:]
                        break
                continue

            is_html_void = tag[0].islower() and lower_tag in void_tags
            if token.endswith("/>") or is_html_void:
                continue
            stack.append((tag, line_indent))

    def _repair_branch_lines(branch_lines: list[str]) -> tuple[list[str], bool]:
        stack: list[tuple[str, str]] = []
        repaired_lines: list[str] = []
        changed = False
        pending_open_tag: tuple[str, str] | None = None

        for line in branch_lines:
            if pending_open_tag is not None:
                stripped = line.strip()
                if stripped.endswith("/>"):
                    pending_open_tag = None
                    repaired_lines.append(line)
                    continue
                if stripped.endswith(">"):
                    stack.append(pending_open_tag)
                    pending_open_tag = None
                    repaired_lines.append(line)
                    continue
                repaired_lines.append(line)
                continue

            close_match = JSX_LINE_CLOSE_TAG_RE.match(line)
            if close_match:
                tag = close_match.group("tag")
                for reverse_index in range(len(stack) - 1, -1, -1):
                    if stack[reverse_index][0] == tag:
                        del stack[reverse_index:]
                        repaired_lines.append(line)
                        break
                else:
                    changed = True
                continue

            multiline_open_match = re.match(r"^(?P<indent>[ \t]*)<(?P<tag>[A-Za-z][A-Za-z0-9.-]*)\b(?![^>]*>)[^>\n]*$", line)
            if multiline_open_match and not line.lstrip().startswith("</"):
                pending_open_tag = (
                    multiline_open_match.group("tag"),
                    multiline_open_match.group("indent"),
                )
                repaired_lines.append(line)
                continue

            _consume_branch_tags(line, stack)
            repaired_lines.append(line)

        if pending_open_tag is not None:
            stack.append(pending_open_tag)

        if stack:
            changed = True
            for tag, indent in reversed(stack):
                repaired_lines.append(f"{indent}</{tag}>")

        return repaired_lines, changed

    for index, line in enumerate(lines):
        start_match = TERNARY_BRANCH_START_RE.search(line)
        if not start_match:
            continue
        if TERNARY_BRANCH_SEPARATOR_RE.match(line.strip()):
            continue

        marker = start_match.group("marker")
        start_indent = len(re.match(r"[ \t]*", line).group(0))
        end_index: int | None = None
        separator_index: int | None = None
        for scan_index in range(index + 1, len(lines)):
            stripped = lines[scan_index].strip()
            if not stripped:
                continue
            scan_indent = len(re.match(r"[ \t]*", lines[scan_index]).group(0))
            if (
                marker == "?"
                and separator_index is None
                and scan_indent <= start_indent
                and TERNARY_BRANCH_SEPARATOR_RE.match(stripped)
            ):
                separator_index = scan_index
                continue
            if scan_indent <= start_indent and TERNARY_BRANCH_CLOSE_RE.match(stripped):
                end_index = scan_index
                break

        if end_index is None or end_index <= index + 1:
            continue

        if separator_index is not None:
            repaired_true_branch, true_changed = _repair_branch_lines(lines[index + 1:separator_index])
            repaired_false_branch, false_changed = _repair_branch_lines(lines[separator_index + 1:end_index])
            if true_changed or false_changed:
                repairs.append(
                    (
                        index + 1,
                        end_index,
                        repaired_true_branch + [lines[separator_index]] + repaired_false_branch,
                    )
                )
            continue

        repaired_branch, branch_changed = _repair_branch_lines(lines[index + 1:end_index])
        if branch_changed:
            repairs.append((index + 1, end_index, repaired_branch))

    if not repairs:
        return source

    for start_index, end_index, repaired_branch in reversed(repairs):
        lines[start_index:end_index] = repaired_branch

    result = "\n".join(lines)
    if source.endswith("\n") and not result.endswith("\n"):
        result += "\n"
    return result


def _repair_componentized_commented_destructured_props(source: str) -> str:
    return COMMENTED_DESTRUCTURED_PROP_RE.sub(
        lambda match: f"{match.group('indent')}{match.group('name')},",
        source,
    )


def _repair_componentized_split_state_setters(source: str) -> str:
    return SPLIT_STATE_SETTER_RE.sub(
        lambda match: f"{match.group('prefix')}{match.group('rest')}",
        source,
    )


def _repair_componentized_split_camel_identifiers(source: str) -> str:
    lines = source.splitlines()
    if not lines:
        return source

    changed = False
    repaired_lines: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("*") or "/*" in line:
            repaired_lines.append(line)
            continue

        updated = SPLIT_CAMEL_IDENTIFIER_OPERATOR_RE.sub(
            lambda match: f"{match.group('prefix')}{match.group('suffix')}",
            line,
        )
        if updated != line:
            changed = True
        repaired_lines.append(updated)

    if not changed:
        return source
    return "\n".join(repaired_lines) + ("\n" if source.endswith("\n") else "")


def _repair_componentized_split_quoted_literals(source: str) -> str:
    literal_re = re.compile(
        r"(?P<prefix>(?:===|!==|==|!=|\(|,|:)\s*)(?P<quote>['\"])\s*\n(?P<indent>[ \t]*)(?P<body>[A-Za-z0-9][^'\"\r\n]{0,160}?)(?P=quote)"
    )

    def _repl(match: re.Match[str]) -> str:
        body = match.group("body").strip()
        if not body:
            return match.group(0)
        return f"{match.group('prefix')}{match.group('quote')}{body}{match.group('quote')}"

    repaired = literal_re.sub(_repl, source)
    return repaired if repaired != source else source


def _repair_componentized_orphan_svg_import_comment_lines(source: str) -> str:
    lines = source.splitlines()
    if not lines or "SVG," not in source:
        return source

    repaired_lines: list[str] = []
    changed = False
    for index, line in enumerate(lines):
        if line.strip() != "SVG,":
            repaired_lines.append(line)
            continue

        upcoming = "\n".join(lines[index + 1:index + 4])
        if re.search(r"/\*\s*Icons?\b", upcoming) or re.search(r"const\s+[A-Za-z0-9_]*Icon\s*=\s*\(\)\s*=>\s*<svg\b", upcoming):
            changed = True
            continue

        repaired_lines.append(line)

    if not changed:
        return source
    return "\n".join(repaired_lines) + ("\n" if source.endswith("\n") else "")


def _repair_componentized_orphan_prose_comment_lines(source: str) -> str:
    lines = source.splitlines()
    if not lines:
        return source

    repaired_lines: list[str] = []
    changed = False

    def _next_significant_line(start_index: int) -> str:
        for candidate in lines[start_index + 1:]:
            stripped = candidate.strip()
            if stripped:
                return stripped
        return ""

    for index, line in enumerate(lines):
        match = ORPHAN_PROSE_COMMENT_LINE_RE.match(line)
        if not match:
            repaired_lines.append(line)
            continue

        stripped = line.strip()
        if stripped.endswith(";"):
            repaired_lines.append(line)
            continue

        if stripped.startswith(("<", "{", "}", ")", "]")):
            repaired_lines.append(line)
            continue

        if re.match(
            r"^(?:const|let|var|function|return|if|for|while|switch|type|interface|export|import)\b",
            stripped,
        ):
            repaired_lines.append(line)
            continue

        next_significant = _next_significant_line(index)
        if not re.match(r"^(?:const|let|var|function|return|if|for|while|switch|type|interface|export)\b", next_significant):
            repaired_lines.append(line)
            continue

        prose = " ".join(
            part
            for part in (
                match.group("prose").strip(),
                (match.group("tail") or "").strip(),
            )
            if part
        )
        repaired_lines.append(f"{match.group('indent')}/* {prose} */")
        changed = True

    if not changed:
        return source
    return "\n".join(repaired_lines) + ("\n" if source.endswith("\n") else "")


def _repair_componentized_duplicate_jsx_attributes(source: str) -> str:
    def _dedupe_body(body: str) -> tuple[str, bool]:
        cursor = 0
        rebuilt: list[str] = []
        seen: set[str] = set()
        changed = False

        while cursor < len(body):
            match = JSX_ATTRIBUTE_TOKEN_RE.search(body, cursor)
            if not match:
                rebuilt.append(body[cursor:])
                break

            rebuilt.append(body[cursor:match.start()])
            name = match.group("name")
            token = f"{match.group('leading')}{name}{match.group('value')}"
            if name in seen:
                changed = True
            else:
                seen.add(name)
                rebuilt.append(token)
            cursor = match.end()

        return "".join(rebuilt), changed

    def _replace_tag(match: re.Match[str]) -> str:
        body = match.group("body")
        updated_body, changed = _dedupe_body(body)
        if not changed:
            return match.group(0)
        return f"<{match.group('tag')}{updated_body}{match.group('self_close')}>"

    return SINGLE_LINE_JSX_TAG_RE.sub(_replace_tag, source)


def _repair_componentized_split_svg_value_attributes(source: str) -> str:
    lines = source.splitlines()
    if not lines:
        return source

    changed = False
    for index in range(1, len(lines)):
        stripped = lines[index].lstrip()
        if re.match(r'^(?:var\([^)]*\)|rgba?\([^)]*\)|#[0-9A-Fa-f]{3,8}|currentColor)"\s+', stripped) is None:
            continue

        previous = lines[index - 1]
        if not re.search(r"<(?:circle|ellipse|path|polygon|polyline|rect|line|stop|use)\b", previous):
            continue
        if "stroke=" not in stripped or "fill=" in previous:
            continue

        indent = re.match(r"[ \t]*", lines[index]).group(0)
        lines[index] = f'{indent}fill="{stripped}'
        changed = True

    if not changed:
        return source
    return "\n".join(lines) + ("\n" if source.endswith("\n") else "")


def _repair_componentized_layout_main_wrapper_leaks(source: str) -> str:
    lines = source.splitlines()
    if not lines or "<main" not in source:
        return source

    layout_root_match = re.search(
        r"^(?P<indent>[ \t]*)<div\b[^>]*className\s*=\s*(?:\"[^\"]*(?:layout|shell|workspace)[^\"]*\"|'[^']*(?:layout|shell|workspace)[^']*'|\{`[^`]*(?:layout|shell|workspace)[^`]*`\})",
        source,
        re.MULTILINE,
    )
    if not layout_root_match:
        return source

    layout_root_indent = layout_root_match.group("indent")
    changed = False

    index = 0
    while index < len(lines):
        if lines[index].strip() != "</div>":
            index += 1
            continue

        previous_index = index - 1
        while previous_index >= 0 and not lines[previous_index].strip():
            previous_index -= 1

        next_index = index + 1
        while next_index < len(lines):
            candidate = lines[next_index].strip()
            if not candidate or re.fullmatch(r"\{/\*[\s\S]{0,200}?\*/\}", candidate):
                next_index += 1
                continue
            break

        previous_line = lines[previous_index].strip() if previous_index >= 0 else ""
        next_line = lines[next_index].lstrip() if next_index < len(lines) else ""

        if previous_line not in {"</aside>", "</section>"} or not next_line.startswith("<main "):
            index += 1
            continue

        del lines[index]
        changed = True
        continue

    last_main_close = None
    for index, line in enumerate(lines):
        if line.strip() == "</main>":
            last_main_close = index

    if last_main_close is not None:
        trailing_has_root_close = False
        for index in range(last_main_close + 1, len(lines)):
            stripped = lines[index].strip()
            if not stripped:
                continue
            if stripped == "</div>":
                trailing_has_root_close = True
                break
            if stripped.startswith(");"):
                break
        if not trailing_has_root_close:
            lines.insert(last_main_close + 1, f"{layout_root_indent}</div>")
            changed = True

    if not changed:
        return source
    return "\n".join(lines) + ("\n" if source.endswith("\n") else "")


def _repair_componentized_jsx_handler_comment_close_bleed(source: str) -> str:
    return re.sub(
        r"(?P<prefix>\bon[A-Z][A-Za-z0-9_]*=\{\([^)]*\)\s*=>\s*\{)\s*\*/\s*",
        lambda match: f"{match.group('prefix')}\n",
        source,
    )


def _repair_orphan_block_comment_close(source: str) -> str:
    """Remove stray */ that appear outside any block comment on a line.

    Common LLM output pattern:
      if (x) { /* note */ } */    ← the trailing */ is orphaned
      return value; */             ← stray */ after code
    """
    lines = source.splitlines()
    updated = []
    for line in lines:
        # Walk the line tracking comment depth
        i = 0
        depth = 0
        segments: list[str] = []
        last = 0
        while i < len(line):
            if line[i:i+2] == "/*":
                depth += 1
                i += 2
            elif line[i:i+2] == "*/":
                if depth > 0:
                    depth -= 1
                    i += 2
                else:
                    # Orphan */ — strip it
                    segments.append(line[last:i])
                    last = i + 2
                    i += 2
            elif line[i] == '"' or line[i] == "'" or line[i] == '`':
                # Skip string literals
                quote = line[i]
                i += 1
                while i < len(line) and line[i] != quote:
                    if line[i] == '\\':
                        i += 1
                    i += 1
                if i < len(line):
                    i += 1
            elif line[i:i+2] == "//":
                # Rest of line is a line comment — stop
                break
            else:
                i += 1
        if last > 0:
            segments.append(line[last:])
            cleaned = "".join(segments).rstrip()
            updated.append(cleaned)
        else:
            updated.append(line)
    result = "\n".join(updated)
    if source.endswith("\n") and not result.endswith("\n"):
        result += "\n"
    return result


def _repair_jsx_return_unclosed_tags(source: str) -> str:
    """Close unclosed JSX tags before ); at end of return blocks.

    Handles the common LLM pattern where a component's return has
    opening tags like <div><div><div> but jumps to ); without closing them.
    """
    VOID_TAGS = frozenset({
        "area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "param", "source", "track", "wbr",
        "circle", "line", "path", "rect", "ellipse", "polygon", "polyline", "stop", "use",
    })

    JSX_OPEN_RE = re.compile(
        r"<(?P<tag>[A-Za-z][A-Za-z0-9.]*)(?:\s|>|$)"
    )
    JSX_CLOSE_RE = re.compile(
        r"</(?P<tag>[A-Za-z][A-Za-z0-9.]*)>"
    )
    JSX_SELF_CLOSE_RE = re.compile(
        r"<[A-Za-z][A-Za-z0-9.]*(?:\s[^>]*)?\s*/>"
    )

    lines = source.splitlines()
    result_lines: list[str] = []
    in_return = False
    return_tag_stack: list[str] = []
    return_indent = ""
    # Stack of saved contexts for nested JSX blocks (e.g. .map(() => (...)))
    saved_contexts: list[tuple[list[str], str]] = []

    def _next_significant_line_info(start_index: int) -> tuple[str, int]:
        for candidate in lines[start_index + 1:]:
            stripped_candidate = candidate.strip()
            if stripped_candidate:
                return stripped_candidate, len(re.match(r"(\s*)", candidate).group(1))
        return "", -1

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Detect start of return ( or arrow function JSX ( => ( )
        if re.match(r"^\s*return\s*\(\s*$", stripped) or (
            in_return and re.search(r"=>\s*\(\s*$", stripped)
        ):
            if in_return:
                # Save current context for nested JSX (e.g., .map callback)
                saved_contexts.append((return_tag_stack, return_indent))
            in_return = True
            return_tag_stack = []
            return_indent = re.match(r"(\s*)", line).group(1)
            result_lines.append(line)
            continue

        # Detect end of return block: line is just ); or )) or ))}
        if in_return and re.match(r"^\s*\)+[;,}]?\s*$", stripped):
            close_indent = re.match(r"(\s*)", line).group(1)
            next_significant, next_indent = _next_significant_line_info(i)
            if (
                next_significant
                and next_indent >= 0
                and len(close_indent) > len(return_indent)
                and re.match(r"^(?:</?[A-Za-z]|<>|</>|\{)", next_significant)
            ):
                result_lines.append(line)
                continue
            if not saved_contexts:
                if next_significant and re.match(r"^(?:</?[A-Za-z]|<>|</>|\{)", next_significant):
                    result_lines.append(line)
                    continue
            # Insert missing closing tags before );
            if return_tag_stack:
                # Determine indentation: use indent of the ); line + some offset
                # Close tags in reverse order
                for tag in reversed(return_tag_stack):
                    result_lines.append(f"{close_indent}  </{tag}>")
                return_tag_stack = []
            # Restore saved context if we were in a nested JSX block
            if saved_contexts:
                return_tag_stack, return_indent = saved_contexts.pop()
            else:
                in_return = False
            result_lines.append(line)
            continue

        if in_return:
            # Track open and close tags in LEFT-TO-RIGHT order
            clean_line = JSX_SELF_CLOSE_RE.sub(lambda m: " " * len(m.group()), stripped)
            clean_line = re.sub(r"['\"`][^'\"`]*['\"`]", lambda m: " " * len(m.group()), clean_line)

            # Collect all open and close events with their positions
            events: list[tuple[int, str, str]] = []  # (pos, "open"|"close", tag)
            for m in JSX_OPEN_RE.finditer(clean_line):
                tag = m.group("tag")
                # Only treat lowercase HTML tags as void — capitalized React
                # components like <Link> are never void even if the lowercase
                # HTML equivalent (<link>) is.
                is_html_void = tag[0].islower() and tag.lower() in VOID_TAGS
                if not is_html_void:
                    # Check self-closing on this line
                    tag_region = clean_line[m.start():]
                    if re.search(rf"<{re.escape(tag)}[^>]*/\s*>", tag_region):
                        continue
                    events.append((m.start(), "open", tag))
            for m in JSX_CLOSE_RE.finditer(clean_line):
                events.append((m.start(), "close", m.group("tag")))

            # Process left to right
            events.sort(key=lambda e: e[0])
            insert_before: list[str] = []
            for _, event_type, tag in events:
                if event_type == "open":
                    return_tag_stack.append(tag)
                else:
                    # If closing tag doesn't match stack top, close intermediates first
                    # (handles misnested tags like <div><header>...</header></div>
                    #  becoming </header> before </div>)
                    found_idx = -1
                    for j in range(len(return_tag_stack) - 1, -1, -1):
                        if return_tag_stack[j] == tag:
                            found_idx = j
                            break
                    if found_idx >= 0 and found_idx < len(return_tag_stack) - 1:
                        # Close everything above the matching tag
                        indent = re.match(r"(\s*)", line).group(1)
                        for k in range(len(return_tag_stack) - 1, found_idx, -1):
                            insert_before.append(f"{indent}</{return_tag_stack[k]}>")
                        del return_tag_stack[found_idx + 1:]

                    if found_idx == -1:
                        # Extra closer with no matching opener — mark for removal
                        line = re.sub(
                            rf"</{re.escape(tag)}>",
                            "",
                            line,
                            count=1,
                        )
                        continue

                    # Pop matching open tag from stack (search from top)
                    for j in range(len(return_tag_stack) - 1, -1, -1):
                        if return_tag_stack[j] == tag:
                            del return_tag_stack[j]
                            break

            # Insert any misnest-repair closing tags before the current line
            if insert_before:
                result_lines.extend(insert_before)

        # Remove lines that became empty after stripping extra closers
        stripped_line = line.strip()
        if in_return and not stripped_line:
            # Skip blank lines created by removing extra closers only if they're truly empty
            pass  # still append — blank lines are fine
        result_lines.append(line)

    result = "\n".join(result_lines)
    if source.endswith("\n") and not result.endswith("\n"):
        result += "\n"
    return result


def _repair_componentized_terminal_wrapper_closers(source: str) -> str:
    void_tags = frozenset({
        "area", "base", "br", "circle", "col", "ellipse", "embed", "hr", "img",
        "input", "line", "link", "meta", "param", "path", "polygon", "polyline",
        "rect", "source", "stop", "track", "use", "wbr",
    })
    open_tag_re = re.compile(r"<(?P<tag>[A-Za-z][A-Za-z0-9.]*)\b(?P<attrs>[^<>]*)>")
    close_tag_re = re.compile(r"</(?P<tag>[A-Za-z][A-Za-z0-9.]*)>")

    lines = source.splitlines()
    if not lines:
        return source

    result_lines: list[str] = []
    in_return = False
    stack: list[str] = []
    changed = False

    for index, line in enumerate(lines):
        stripped = line.strip()
        if re.match(r"^\s*return\s*\(\s*$", stripped):
            in_return = True
            stack = []
            result_lines.append(line)
            continue

        if in_return:
            clean_line = re.sub(r"['\"`][^'\"`]*['\"`]", lambda m: " " * len(m.group(0)), line)
            for match in open_tag_re.finditer(clean_line):
                tag = match.group("tag")
                attrs = match.group("attrs")
                if tag[0].islower() and tag.lower() in void_tags:
                    continue
                if attrs.rstrip().endswith("/"):
                    continue
                stack.append(tag)
            for match in close_tag_re.finditer(clean_line):
                tag = match.group("tag")
                for reverse_index in range(len(stack) - 1, -1, -1):
                    if stack[reverse_index] == tag:
                        del stack[reverse_index]
                        break

            next_non_empty = ""
            for candidate in lines[index + 1:]:
                candidate_stripped = candidate.strip()
                if candidate_stripped:
                    next_non_empty = candidate_stripped
                    break

            if re.match(r"^\)\s*;?\s*$", stripped) and next_non_empty.startswith("}"):
                if stack:
                    close_indent = re.match(r"(\s*)", line).group(1)
                    for tag in reversed(stack):
                        result_lines.append(f"{close_indent}</{tag}>")
                    stack = []
                    changed = True
                in_return = False

        result_lines.append(line)

    if not changed:
        return source
    return "\n".join(result_lines) + ("\n" if source.endswith("\n") else "")


def _repair_componentized_chart_footer_wrapper_closers(source: str) -> str:
    if '<div className="chart-card">' not in source or '<div className="chart-actions">' not in source:
        return source

    actions_index = source.rfind('<div className="chart-actions">')
    if actions_index == -1:
        return source

    tail = source[actions_index:]
    end_matches = list(re.finditer(r"\n(?P<indent>[ \t]*)\)+[;,}]?\s*(?=\n)", tail))
    if not end_matches:
        return source
    end_match = end_matches[-1]

    closers_after_actions = tail[: end_match.start()].count("</div>")
    if closers_after_actions >= 2:
        return source

    insert_at = actions_index + end_match.start()
    end_indent = end_match.group("indent")
    return f"{source[:insert_at]}\n{end_indent}  </div>{source[insert_at:]}"


def _remove_componentized_orphan_closing_tag_lines(source: str) -> str:
    void_tags = frozenset({
        "area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "param", "source", "track", "wbr",
        "circle", "ellipse", "line", "path", "polygon", "polyline", "rect", "stop", "use",
    })
    lines = source.splitlines()
    if not lines:
        return source

    updated_lines: list[str] = []
    stack: list[str] = []
    pending_open_tag: str | None = None
    changed = False

    def _consume_line_tags(line: str) -> None:
        sanitized = line.replace("=>", "  ")
        for match in JSX_TAG_TOKEN_RE.finditer(sanitized):
            token = match.group(0)
            tag = match.group("tag")
            lower_tag = tag.lower()

            if token.startswith("</"):
                for reverse_index in range(len(stack) - 1, -1, -1):
                    if stack[reverse_index] == tag:
                        del stack[reverse_index:]
                        break
                continue

            is_html_void = tag[0].islower() and lower_tag in void_tags
            if token.endswith("/>") or is_html_void:
                continue
            stack.append(tag)

    for line in lines:
        stripped = line.strip()

        if pending_open_tag is not None:
            if re.search(r"/>\s*$", stripped):
                pending_open_tag = None
                updated_lines.append(line)
                continue
            if re.search(r">\s*$", stripped):
                stack.append(pending_open_tag)
                pending_open_tag = None
                updated_lines.append(line)
                continue
            updated_lines.append(line)
            continue

        close_match = JSX_LINE_CLOSE_TAG_RE.match(line)
        if close_match:
            tag = close_match.group("tag")
            for reverse_index in range(len(stack) - 1, -1, -1):
                if stack[reverse_index] == tag:
                    del stack[reverse_index:]
                    updated_lines.append(line)
                    break
            else:
                changed = True
            continue

        open_start_match = re.match(r"^[ \t]*<(?P<tag>[A-Za-z][A-Za-z0-9.-]*)\b", line)
        if open_start_match and not line.lstrip().startswith("</"):
            sanitized = line.replace("=>", "  ")
            if not JSX_TAG_TOKEN_RE.search(sanitized) and ">" not in sanitized:
                pending_open_tag = open_start_match.group("tag")
                updated_lines.append(line)
                continue

        _consume_line_tags(line)
        updated_lines.append(line)

    if not changed:
        return source

    result = "\n".join(updated_lines)
    if source.endswith("\n") and not result.endswith("\n"):
        result += "\n"
    return result


def _normalize_componentized_preview_router(source: str) -> str:
    if "react-router-dom" not in source or "BrowserRouter" not in source:
        return source
    return re.sub(r"\bBrowserRouter\b", "HashRouter", source)


def _normalize_componentized_declaration_boundaries(source: str) -> str:
    return DECLARATION_BOUNDARY_RE.sub("\n", source)


def _hoist_componentized_chart_helper_declarations(source: str) -> str:
    lines = source.splitlines()
    if not lines or ".map(" not in source or "return (" not in source:
        return source

    helper_candidates: list[tuple[int, int, str]] = []
    for idx, line in enumerate(lines):
        match = re.match(
            r"^(?P<indent>\s*)const (?P<name>(?:scale|map)[XY]|[xy]Scale)\s*=\s*.+;\s*(?://.*)?$",
            line,
        )
        if not match:
            continue
        helper_name = match.group("name")
        if source.count(f"{helper_name}(") < 2:
            continue

        previous_window = "\n".join(lines[max(0, idx - 8):idx + 1])
        next_window = "\n".join(lines[idx:min(len(lines), idx + 12)])
        if ".map(" not in previous_window or "return" not in next_window:
            continue

        return_idx = None
        for search_idx in range(idx - 1, -1, -1):
            if re.match(r"^\s*return\s*\(\s*$", lines[search_idx]):
                return_idx = search_idx
                break
        if return_idx is None:
            continue

        helper_candidates.append((idx, return_idx, line.strip()))

    if not helper_candidates:
        return source

    removed_indexes = {candidate[0] for candidate in helper_candidates}
    insertions: dict[int, list[str]] = {}
    for _, return_idx, helper_line in helper_candidates:
        return_indent = re.match(r"^(\s*)", lines[return_idx]).group(1)
        insertions.setdefault(return_idx, [])
        hoisted_line = f"{return_indent}{helper_line}"
        if hoisted_line not in insertions[return_idx]:
            insertions[return_idx].append(hoisted_line)

    rebuilt: list[str] = []
    for idx, line in enumerate(lines):
        if idx in insertions:
            rebuilt.extend(insertions[idx])
        if idx in removed_indexes:
            continue
        rebuilt.append(line)

    updated = "\n".join(rebuilt)
    if source.endswith("\n"):
        updated += "\n"
    return updated


def _normalize_componentized_field_aliases(source: str) -> str:
    updated = source
    for alias_group in COMPONENTIZED_FIELD_ALIAS_GROUPS:
        canonical, *aliases = alias_group
        if canonical not in updated:
            continue
        for alias in aliases:
            updated = re.sub(rf"\b{re.escape(alias)}\b", canonical, updated)
    return DUPLICATE_LABEL_OBJECT_FIELD_RE.sub(
        lambda match: f"{match.group('prefix')}, asset: {match.group('value')}",
        updated,
    )


def _normalize_componentized_currency_formatting(source: str) -> str:
    updated = EMPTY_CURRENCY_FORMAT_ARG_RE.sub(
        lambda match: f"formatCurrency({match.group('value').strip()})",
        source,
    )
    return FORMAT_CURRENCY_GUARD_RE.sub(
        "currency: /^[A-Za-z]{3}$/.test(currency) ? currency.toUpperCase() : 'USD'",
        updated,
    )


def _normalize_run_on_imports(source: str) -> str:
    updated = re.sub(
        r";\s*(?=(?:import\b|const\b|let\b|var\b|function\b|export\b|return\b|if\b|for\b|while\b|switch\b|type\b|interface\b|class\b|use[A-Z]\w*\b|ReactDOM\b|createRoot\b))",
        ";\n",
        source,
    )
    updated = re.sub(r"(?<=['\"])\s*(?=(?:import\b|export\b))", "\n", updated)
    updated = re.sub(
        r"\*/\s*(?=(?:const\b|let\b|var\b|function\b|export\b|return\b|if\b|for\b|while\b|switch\b|type\b|interface\b|class\b|use[A-Z]\w*\b|ReactDOM\b|createRoot\b))",
        "*/\n",
        updated,
    )
    updated = re.sub(r"}\s+(?=return\b)", "}\n", updated)
    return updated


CSS_TAIL_SELECTOR_RE = re.compile(
    r"(?m)^(?:\.[A-Za-z_][\w-]*|#[A-Za-z_][\w-]*|:root|body|html|@media\b[^{]*)\s*\{"
)


def _extract_componentized_css_tail(source: str) -> tuple[str, str]:
    if "{" not in source or ("return" not in source and "export default" not in source):
        return source, ""

    search_start = max(
        source.rfind("return ("),
        source.rfind("return("),
        source.rfind("export default function"),
        source.rfind("const App"),
        0,
    )
    match = CSS_TAIL_SELECTOR_RE.search(source, pos=max(search_start, 0))
    if not match:
        return source, ""

    css_start = match.start()
    tail = source[css_start:]
    export_tail = ""
    export_match = re.search(r"export default\s+[A-Za-z0-9_$.]+\s*;\s*$", tail, flags=re.DOTALL)
    if export_match:
        export_tail = export_match.group(0).strip()
        tail = tail[:export_match.start()]

    css_tail = tail.strip()
    if not css_tail:
        return source, ""

    cleaned = source[:css_start].rstrip()
    if export_tail:
        cleaned = cleaned + "\n\n" + export_tail
    cleaned = cleaned.rstrip() + "\n"
    return cleaned, css_tail


def _normalize_componentized_main_entry(source: str) -> str:
    updated = re.sub(
        r"//\s*([^\n]*?)(?=(?:import\b|ReactDOM\b|createRoot\b|root\.render\b|const\b|let\b|var\b))",
        lambda m: f"/* {m.group(1).strip()} */\n",
        source,
    )
    updated = re.sub(r";\s*(?=import\b)", ";\n", updated)
    updated = re.sub(r";\s*(?=(?:ReactDOM\b|createRoot\b|root\.render\b|const\b|let\b|var\b))", ";\n", updated)
    updated = MAIN_BASE_CSS_IMPORT_RE.sub('import "./base.css";', updated)
    return _normalize_componentized_main_css_order(updated)


def _normalize_componentized_main_css_order(source: str) -> str:
    lines = source.splitlines()
    js_imports: list[str] = []
    css_imports: list[str] = []
    other_lines: list[str] = []

    for line in lines:
        stripped = line.strip()
        css_match = MAIN_CSS_IMPORT_LINE_RE.match(line)
        if css_match:
            css_imports.append(css_match.group("path"))
        elif MAIN_ENTRY_INVALID_IMPORT_NOTE_RE.match(stripped):
            continue
        elif stripped.startswith("import "):
            js_imports.append(line.rstrip())
        else:
            other_lines.append(line)

    if not css_imports:
        return source

    ordered_css_imports: list[str] = []
    seen_css: set[str] = set()
    has_polish_guard = POLISH_GUARD_IMPORT in css_imports
    filtered_css_imports = [path for path in css_imports if path != POLISH_GUARD_IMPORT]
    for import_path in MAIN_ENTRY_PREFERRED_CSS_ORDER:
        if import_path in filtered_css_imports and import_path not in seen_css:
            ordered_css_imports.append(f'import "{import_path}";')
            seen_css.add(import_path)
    for import_path in filtered_css_imports:
        if import_path not in seen_css:
            ordered_css_imports.append(f'import "{import_path}";')
            seen_css.add(import_path)
    if has_polish_guard:
        ordered_css_imports.append(f'import "{POLISH_GUARD_IMPORT}";')

    rebuilt_lines = [*js_imports, *ordered_css_imports]
    if other_lines:
        if rebuilt_lines and any(line.strip() for line in other_lines):
            rebuilt_lines.append("")
        rebuilt_lines.extend(other_lines)

    rebuilt = "\n".join(rebuilt_lines).rstrip() + "\n"
    return rebuilt


def _make_dist_index_portable(dist_index: Path) -> None:
    html = dist_index.read_text(encoding="utf-8", errors="replace")
    updated = re.sub(r'((?:src|href)=["\'])/assets/', r"\1./assets/", html, flags=re.IGNORECASE)
    updated = re.sub(r'((?:src|href)=["\'])/generated-assets/', r"\1./generated-assets/", updated, flags=re.IGNORECASE)
    updated = re.sub(r'((?:src|href)=["\'])/vite\.svg', r"\1./vite.svg", updated, flags=re.IGNORECASE)
    if updated != html:
        dist_index.write_text(updated, encoding="utf-8")


def _root_package_name(specifier: str) -> str:
    if specifier.startswith("@"):
        parts = specifier.split("/")
        return "/".join(parts[:2]) if len(parts) >= 2 else specifier
    return specifier.split("/", 1)[0]
