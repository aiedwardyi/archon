from __future__ import annotations

import re
import time
from typing import Callable, TypeVar

from google.genai.errors import ClientError

T = TypeVar("T")


def call_with_retry(fn: Callable[[], T], max_retries: int = 2) -> T:
    """
    Retry Gemini calls on 429 RESOURCE_EXHAUSTED using server-provided retryDelay when present.
    """
    for attempt in range(max_retries + 1):
        try:
            return fn()
        except ClientError as e:
            msg = str(e)
            if "RESOURCE_EXHAUSTED" not in msg and "429" not in msg:
                raise

            delay = _extract_retry_delay_seconds(msg) or 30
            if attempt == max_retries:
                raise
            time.sleep(delay)


def _extract_retry_delay_seconds(text: str) -> int | None:
    # Examples in errors:
    # - "retryDelay': '26s'"
    # - "Please retry in 26.0397s."
    m = re.search(r"retryDelay'\s*:\s*'(\d+)s'", text)
    if m:
        return int(m.group(1))
    m = re.search(r"retry in\s+(\d+)", text, flags=re.IGNORECASE)
    if m:
        return int(m.group(1))
    return None
