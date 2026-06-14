#!/usr/bin/env python3
"""Fix keymap-drawer labels for bare DE_* keycodes.

keymap-drawer must run the C preprocessor (our keymap uses #define'd layer
numbers in conditional_layers), which expands DE_* locale keycodes into raw
ZMK_HID_USAGE(...) expressions before our label maps can catch them. This
script rewrites those expanded strings in the parsed YAML back into the
characters they actually produce on a German OS.

Usage: relabel.py <in.yaml> <out.yaml>
"""
import re
import sys

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
}

TOKEN_RE = re.compile(r"KEYBOARD ([A-Z0-9 ]+?)\)")


def fix(value: str) -> str:
    if "ZMK HID USAGE" not in value:
        return value
    mod = "LS" if "LS(" in value else "RA" if "RA(" in value else ""
    m = TOKEN_RE.search(value)
    if not m:
        return value
    token = m.group(1).strip()
    sym = TABLE.get((mod, token))
    if sym is None:
        return value
    # Emit a YAML-safe single-quoted scalar (these symbols are YAML-special).
    return "'" + sym.replace("'", "''") + "'"


def main() -> None:
    src, dst = sys.argv[1], sys.argv[2]
    out_lines, n = [], 0
    for line in open(src):
        new = re.sub(
            r"(\(+(?:LS|RA)?\(*ZMK HID USAGE[^\n]*?\)+)",
            lambda mm: fix(mm.group(1)),
            line,
        )
        if new != line:
            n += 1
        out_lines.append(new)
    open(dst, "w").write("".join(out_lines))
    print(f"relabeled {n} lines -> {dst}")


if __name__ == "__main__":
    main()
