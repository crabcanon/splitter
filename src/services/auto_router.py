from __future__ import annotations

import json
import re

from models.domain import LoadedDocument
from models.schemas import SplitterType


class AutoStrategyRouter:
    def choose(self, document: LoadedDocument, *, has_embedding: bool = False) -> SplitterType:
        text = document.text.lstrip()

        if self._looks_like_json(text):
            return SplitterType.JSON
        if self._looks_like_html(text):
            return SplitterType.HTML
        if self._looks_like_markdown(text):
            return SplitterType.MARKDOWN
        if self._looks_like_code(text):
            return SplitterType.CODE
        if has_embedding:
            return SplitterType.SEMANTIC
        return SplitterType.SENTENCE

    def _looks_like_json(self, text: str) -> bool:
        if not text or text[0] not in "[{":
            return False
        try:
            json.loads(text)
        except json.JSONDecodeError:
            return False
        return True

    def _looks_like_html(self, text: str) -> bool:
        return bool(re.search(r"<(html|body|article|section|div|p|h[1-6])[\s>]", text, re.I))

    def _looks_like_markdown(self, text: str) -> bool:
        return bool(
            re.search(r"(?m)^#{1,6}\s+\S+", text)
            or re.search(r"(?m)^[-*+]\s+\S+", text)
            or "```" in text
        )

    def _looks_like_code(self, text: str) -> bool:
        code_markers = [
            r"\bdef\s+\w+\(",
            r"\bclass\s+\w+",
            r"\bfunction\s+\w+\(",
            r"\bimport\s+[\w.]+",
            r"\bfrom\s+[\w.]+\s+import\s+",
            r"=>\s*[{(]",
        ]
        return sum(bool(re.search(pattern, text)) for pattern in code_markers) >= 2
