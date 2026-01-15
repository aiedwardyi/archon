# utils/json_repair.py
from __future__ import annotations

def repair_json_newlines_in_strings(s: str) -> str:
    """
    Repairs INVALID JSON produced by copy-pasting, where literal newline characters
    appear inside quoted strings.

    Deterministic rule:
      - If we are inside a JSON string (between unescaped double quotes),
        convert literal '\n' and '\r' to a single space.
      - Otherwise, leave characters unchanged.

    This does NOT attempt to fix other JSON issues.
    """
    out: list[str] = []
    in_string = False
    escape = False

    for ch in s:
        if in_string:
            if escape:
                # Previous char was a backslash, so this char is escaped.
                out.append(ch)
                escape = False
                continue

            if ch == "\\":  # start escape sequence inside string
                out.append(ch)
                escape = True
                continue

            if ch == '"':  # end string
                out.append(ch)
                in_string = False
                continue

            # The actual repair: literal newline/carriage return inside a string
            if ch == "\n" or ch == "\r":
                out.append(" ")
                continue

            # Optional: tabs inside strings are legal if escaped; literal tab is a control char.
            # If your pasted JSON includes literal tabs, fix them too:
            if ch == "\t":
                out.append(" ")
                continue

            out.append(ch)
            continue

        # not in string
        if ch == '"':
            out.append(ch)
            in_string = True
            continue

        out.append(ch)

    return "".join(out)
