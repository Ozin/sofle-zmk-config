#!/usr/bin/env python3
"""Fix keymap-drawer labels for bare DE_* keycodes.

keymap-drawer must run the C preprocessor (our keymap uses #define'd layer
numbers in conditional_layers), which expands DE_* locale keycodes into raw
ZMK_HID_USAGE(...) expressions before our label maps can catch them. This
script walks the parsed YAML and rewrites those expanded strings into the
characters they actually produce on a German OS.

Usage: relabel.py <in.yaml> <out.yaml>
"""
import re
import sys

import yaml

# (modifier, keyboard-token) -> character produced on a German OS.
# modifier is "LS" (shift), "RA" (AltGr) or "" (none).
TABLE = {
    ("LS", "1 AND EXCLAMATION"): "!",
    ("RA", "Q"): "@",
    ("", "BACKSLASH AND PIPE"): "#",
    ("LS", "4 AND DOLLAR"): "$",
    ("LS", "5 AND PERCENT"): "%",
    ("LS", "6 AND CARET"): "&",
    ("LS", "RIGHT BRACKET AND RIGHT BRACE"): "*",
    ("LS", "8 AND ASTERISK"): "(",
    ("LS", "9 AND LEFT PARENTHESIS"): ")",
    ("RA", "NON US BACKSLASH AND PIPE"): "|",
    ("LS", "0 AND RIGHT PARENTHESIS"): "=",
    ("", "SLASH AND QUESTION MARK"): "-",
    ("", "RIGHT BRACKET AND RIGHT BRACE"): "+",
    ("RA", "7 AND AMPERSAND"): "{",
    ("RA", "0 AND RIGHT PARENTHESIS"): "}",
    ("RA", "8 AND ASTERISK"): "[",
    ("RA", "9 AND LEFT PARENTHESIS"): "]",
    ("LS", "COMMA AND LESS THAN"): ";",
    ("LS", "PERIOD AND GREATER THAN"): ":",
    ("RA", "MINUS AND UNDERSCORE"): "\\",
    # Y/Z are swapped on QWERTZ: DE_Y emits the Z-position scancode (-> y), etc.
    ("", "Z"): "Y",
    ("", "Y"): "Z",
    # Umlaut keycodes (bare, on the GUI layer).
    ("", "APOSTROPHE AND QUOTE"): "ä",
    ("", "SEMICOLON AND COLON"): "ö",
    ("", "LEFT BRACKET AND LEFT BRACE"): "ü",
}

TOKEN_RE = re.compile(r"KEYBOARD ([A-Z0-9 ]+?)\)")


def fix(value):
    if not isinstance(value, str) or "ZMK HID USAGE" not in value:
        return value
    mod = "LS" if "LS(" in value else "RA" if "RA(" in value else ""
    m = TOKEN_RE.search(value)
    if not m:
        return value
    return TABLE.get((mod, m.group(1).strip()), value)


def walk(obj):
    if isinstance(obj, dict):
        return {k: walk(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [walk(v) for v in obj]
    return fix(obj)


def main() -> None:
    src, dst = sys.argv[1], sys.argv[2]
    data = walk(yaml.safe_load(open(src)))
    with open(dst, "w") as f:
        yaml.safe_dump(
            data, f, allow_unicode=True, sort_keys=False,
            default_flow_style=None, width=200,
        )
    print(f"relabeled -> {dst}")


if __name__ == "__main__":
    main()
