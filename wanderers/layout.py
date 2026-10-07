#!/usr/bin/env python3
"""wanderers W-Corne layout — single source of truth.

Generates, from the tables below:
  w-corne-wanderers.vil      Vial saved layout (File → Load saved layout)
  xkb/symbols/wanderers      xkb option `wanderers:magic`: the 20 spare
                             scancodes the Magic layers send, 4 levels each
  xkb/rules/evdev            user rules file mapping the option
  compose-missing.txt        Compose sequences the macros need that the fleet
                             ~/.XCompose lacks (empty when none)

Run:  python3 layout.py            (from this directory)
See README.md for the design and the workflow.
"""
import json
import os
import pathlib
import struct
import sys

HERE = pathlib.Path(__file__).resolve().parent
FLEET_XCOMPOSE = pathlib.Path("/etc/nixos/home/xcompose/XCompose")

# ---------------------------------------------------------------------------
# Board facts (from probe/wcorne-vial-def.json and probe/vialq2.py)
# ---------------------------------------------------------------------------
UID_BYTES = bytes.fromhex("f74728af31f62f36")        # Vial keyboard uid, raw
UID = struct.unpack("<Q", UID_BYTES)[0]
ROWS, COLS = 4, 12
LAYER_COUNT, MACRO_COUNT = 8, 16
VIAL_PROTOCOL, VIA_PROTOCOL = 6, 9

# Physical key order used by every layer table below:
#   row0 L(6) R(6), row1 L(6) R(6), row2 L(6) R(6), thumbs L(3) R(3)  = 42
MATRIX_ORDER = (
    [(r, c) for r in range(3) for c in range(12)]
    + [(3, 3), (3, 4), (3, 5), (3, 6), (3, 7), (3, 8)]
)
EXTRA_KEYS = [(3, 0), (3, 1), (3, 9), (3, 10), (3, 11)]   # in the definition, not on this board
ABSENT = [(3, 2)]                                         # not in the definition at all

L_BASE, L_LOWER, L_RAISE, L_ADJUST, L_MAGIC1, L_MAGIC2, L_MOUSE = range(7)

T, X = "KC_TRNS", "KC_NO"

def RSA(kc_hex):
    """RALT+RSFT+kc as a raw QMK keycode (Vial has no RSA(kc) template)."""
    return 0x1600 | kc_hex

# ---------------------------------------------------------------------------
# Glyph table: Magic1 / Magic2 keys that the HOST maps (xkb option).
# position -> (vial keycode, xkb keycode, L1, L2(Shift), L3(AltGr), L4(AltGr+Shift))
# Positions are Dvorak letters as typed on a Wanderers host.
# F13 is deliberately absent: the desktops bind it to `pbt practice`.
# ---------------------------------------------------------------------------
XKB_KEYS = {
    "p": ("KC_F14",          "FK14",   "π", "Π", "∝", "‰"),
    "y": ("KC_F15",          "FK15",   "θ", "Θ", "∼", "≅"),
    "f": ("KC_F16",          "FK16",   "φ", "Φ", "∫", "∮"),
    "g": ("KC_F17",          "FK17",   "γ", "Γ", "⊤", "⊥"),
    "c": ("KC_F18",          "FK18",   "χ", "Χ", "⊂", "⊃"),
    "r": ("KC_F19",          "FK19",   "ρ", "Ρ", "ℝ", "ℤ"),
    "l": ("KC_F20",          "FK20",   "λ", "Λ", "←", "↔"),
    "a": ("KC_F21",          "FK21",   "α", "Α", "∀", "∧"),
    "e": ("KC_F22",          "FK22",   "ε", "Ε", "∃", "∨"),
    "d": ("KC_F23",          "FK23",   "δ", "Δ", "∂", "∇"),
    "h": ("KC_F24",          "FK24",   "η", "Η", "⋯", "⋮"),
    "t": ("KC_RO",           "AB11",   "τ", "Τ", "⇒", "⇔"),
    "n": ("KC_KANA",         "HKTG",   "ν", "Ν", "ℕ", "ℚ"),
    "s": ("KC_JYEN",         "AE13",   "σ", "Σ", "∑", "∏"),
    "b": ("KC_HENK",         "HENK",   "β", "Β", "∪", "∩"),
    "m": ("KC_MHEN",         "MUHE",   "μ", "Μ", "𝔼", "ℙ"),
    ",": ("KC_LANG1",        "HNGL",   "“", "«", "⟨", "⟦"),
    ".": ("KC_LANG2",        "HJCV",   "”", "»", "⟩", "⟧"),
    ";": ("KC_NONUS_BSLASH", "LSGT",   "¿", "¡", "≠", "≡"),
    "-": ("KC_KP_EQUAL",     "KPEQ",   "–", "—", "÷", "∓"),
}
GREEK_POSITIONS = set("pyfgcrladehtnsbm")                 # alphabetic type (Caps Lock aware)

# Compose macros (Menu + decimal codepoint + Space). Index = Vial macro number.
MACROS = ["—", "…", "·", "→", "≤", "≥", "±", "∞", "•", "°", "×", "≈", "√", "∈", "∅", "κ"]
assert len(MACROS) == MACRO_COUNT
M = {g: "M%d" % i for i, g in enumerate(MACROS)}

def macro_actions(glyph):
    digits = str(ord(glyph))
    taps = ["KC_APPLICATION"] + ["KC_%s" % d for d in digits] + ["KC_SPACE"]
    return [["tap"] + taps]

# ---------------------------------------------------------------------------
# Layers (42 entries each, MATRIX_ORDER). Comments show what gets TYPED.
# ---------------------------------------------------------------------------
BASE = [
    "KC_GESC", "KC_Q", "KC_W", "KC_E", "KC_R", "KC_T",      "KC_Y", "KC_U", "KC_I", "KC_O", "KC_P", "KC_BSPC",
    "KC_TAB",  "KC_A", "KC_S", "KC_D", "KC_F", "KC_G",      "KC_H", "KC_J", "KC_K", "KC_L", "KC_SCLN", "KC_QUOT",
    "KC_LSFT", "KC_Z", "KC_X", "KC_C", "KC_V", "KC_B",      "KC_N", "KC_M", "KC_COMM", "KC_DOT", "KC_SLSH", "KC_RSFT",
    "KC_LGUI", "MO(%d)" % L_LOWER, "LCTL_T(KC_SPC)",        "LALT_T(KC_ENT)", "MO(%d)" % L_RAISE, "KC_RALT",
]

LOWER = [
    # `      1       2       3       4       5          6        7          8           9          0        Del
    "KC_GRV", "KC_1", "KC_2", "KC_3", "KC_4", "KC_5",    "KC_6", "KC_7", "KC_8", "KC_9", "KC_0", "KC_DEL",
    # ___    ^dead(a) `dead(o) ´dead(e) ¨dead(u) ˘dead(i)   Play   PrtSc     Menu     ~dead(n)  F13    —
    T, "RALT(KC_6)", "RALT(KC_GRV)", "RALT(KC_Q)", RSA(0x14), RSA(0x26),
        "KC_MPLY", "KC_PSCREEN", "LSFT(KC_F10)", RSA(0x35), "KC_F13", M["—"],
    # CapsW  Copy     Paste    Cut     Undo     Redo       Mute      Home      PgUp       PgDn       End     LSft
    "QK_CAPS_WORD_TOGGLE", "KC_COPY", "KC_PSTE", "KC_CUT", "KC_UNDO", "KC_AGIN",
        "KC_MUTE", "KC_HOME", "KC_PGUP", "KC_PGDN", "KC_END", "KC_LSFT",
    T, T, T,                                               "KC_VOLD", "MO(%d)" % L_ADJUST, "KC_VOLU",
]

RAISE = [
    # Esc   !        @       #        $       %          ^        &        *        (        )        Ctrl-Bspc
    "KC_ESC", "KC_EXLM", "KC_AT", "KC_HASH", "KC_DLR", "KC_PERC",
        "KC_CIRC", "KC_AMPR", "KC_ASTR", "KC_LPRN", "KC_RPRN", "LCTL(KC_BSPC)",
    # ___   F1 F2 F3 F4 F5                                 F6      /        =        [        ]        \
    T, "KC_F1", "KC_F2", "KC_F3", "KC_F4", "KC_F5",        "KC_F6", "KC_LBRC", "KC_RBRC", "KC_MINS", "KC_EQL", "KC_BSLS",
    # ___   F7 F8 F9 F10 F11                               F12     ←        ↑        ↓        →        Ins
    T, "KC_F7", "KC_F8", "KC_F9", "KC_F10", "KC_F11",      "KC_F12", "KC_LEFT", "KC_UP", "KC_DOWN", "KC_RGHT", "KC_INSERT",
    "OSL(%d)" % L_MAGIC1, "MO(%d)" % L_ADJUST, "OSL(%d)" % L_MAGIC2,    T, T, T,
]

ADJUST = [
    # Boot    Sleep     Bri-      Bri+      Pause      NumLk         ScrLk           EEClr             7  8  9  /
    "QK_BOOT", "KC_SLEP", "KC_BRID", "KC_BRIU", "KC_PAUSE", "KC_NUMLOCK",
        "KC_SCROLLLOCK", "QK_CLEAR_EEPROM", "KC_KP_7", "KC_KP_8", "KC_KP_9", "KC_KP_SLASH",
    # CapsLk  Prev     Play      Next      Stop      Mute          Ins         Menu              4  5  6  *
    "KC_CAPSLOCK", "KC_MPRV", "KC_MPLY", "KC_MNXT", "KC_MSTP", "KC_MUTE",
        "KC_INSERT", "KC_APPLICATION", "KC_KP_4", "KC_KP_5", "KC_KP_6", "KC_KP_ASTERISK",
    # ___     Vol-     Vol+      TG(Ms)    TG(Mag1)  TG(Mag2)      ___  ___  1  2  3  -
    T, "KC_VOLD", "KC_VOLU", "TG(%d)" % L_MOUSE, "TG(%d)" % L_MAGIC1, "TG(%d)" % L_MAGIC2,
        X, X, "KC_KP_1", "KC_KP_2", "KC_KP_3", "KC_KP_MINUS",
    T, T, T,                                               "KC_KP_0", T, "KC_KP_DOT",
]

def xk(pos):            # Magic1: plain scancode -> xkb levels 1/2
    return XKB_KEYS[pos][0]

def xk2(pos):           # Magic2: AltGr+scancode -> xkb levels 3/4
    return "RALT(%s)" % XKB_KEYS[pos][0]

MAGIC1 = [
    # Exit        …        “«        ”»        πΠ        θΘ          φΦ       γΓ       χΧ       ρΡ       λΛ       ·
    "TG(%d)" % L_MAGIC1, M["…"], xk(","), xk("."), xk("p"), xk("y"),
        xk("f"), xk("g"), xk("c"), xk("r"), xk("l"), M["·"],
    # →           αΑ       ≤         εΕ        ≥         ±           δΔ       ηΗ       τΤ       νΝ       σΣ       –—
    M["→"], xk("a"), M["≤"], xk("e"), M["≥"], M["±"],
        xk("d"), xk("h"), xk("t"), xk("n"), xk("s"), xk("-"),
    # ∞           ¿¡       •         °         κ         ×           βΒ       μΜ       ≈        √        ∈        ∅
    M["∞"], xk(";"), M["•"], M["°"], M["κ"], M["×"],
        xk("b"), xk("m"), M["≈"], M["√"], M["∈"], M["∅"],
    T, T, T,                                               T, T, T,
]

MAGIC2 = [
    # Exit        .        ⟨⟦        ⟩⟧        ∝‰        ∼≅          ∫∮       ⊤⊥       ⊂⊃       ℝℤ       ←↔       .
    "TG(%d)" % L_MAGIC2, X, xk2(","), xk2("."), xk2("p"), xk2("y"),
        xk2("f"), xk2("g"), xk2("c"), xk2("r"), xk2("l"), X,
    # .           ∀∧       .         ∃∨        .         .           ∂∇       ⋯⋮       ⇒⇔       ℕℚ       ∑∏       ÷∓
    X, xk2("a"), X, xk2("e"), X, X,
        xk2("d"), xk2("h"), xk2("t"), xk2("n"), xk2("s"), xk2("-"),
    # .           ≠≡       .         .         .         .           ∪∩       𝔼ℙ       .        .        .        .
    X, xk2(";"), X, X, X, X,
        xk2("b"), xk2("m"), X, X, X, X,
    T, T, T,                                               T, T, T,
]

MOUSE = [
    "TG(%d)" % L_MOUSE, X, X, X, X, X,                     X, X, X, X, X, X,
    X, "KC_ACL0", "KC_ACL1", "KC_ACL2", X, X,              X, "KC_WH_L", "KC_WH_U", "KC_WH_D", "KC_WH_R", X,
    "KC_LSFT", X, X, X, X, X,                              X, "KC_MS_L", "KC_MS_U", "KC_MS_D", "KC_MS_R", X,
    "KC_BTN3", "KC_BTN2", "KC_BTN1",                       "KC_BTN1", "KC_BTN2", "KC_BTN3",
]

LAYERS = [BASE, LOWER, RAISE, ADJUST, MAGIC1, MAGIC2, MOUSE]
LAYER_NAMES = ["Base", "Lower", "Raise", "Adjust", "Magic1", "Magic2", "Mouse"]

# Raise: Shift + symbol row -> digit (reverse of normal). QMK ko_make_basic options.
MOD_MASK_SHIFT = 0x22
KO_OPTIONS = 0x80 | 0x07        # enabled | trigger_down | required_mod_down | negative_mod_up
KEY_OVERRIDES = [
    {"trigger": t, "replacement": r, "layers": 1 << L_RAISE, "trigger_mods": MOD_MASK_SHIFT,
     "negative_mod_mask": 0, "suppressed_mods": MOD_MASK_SHIFT, "options": KO_OPTIONS}
    for t, r in zip(
        ["KC_EXLM", "KC_AT", "KC_HASH", "KC_DLR", "KC_PERC", "KC_CIRC", "KC_AMPR", "KC_ASTR", "KC_LPRN", "KC_RPRN"],
        ["KC_1", "KC_2", "KC_3", "KC_4", "KC_5", "KC_6", "KC_7", "KC_8", "KC_9", "KC_0"])
]

# ---------------------------------------------------------------------------
# Generators
# ---------------------------------------------------------------------------
def build_vil():
    layout = []
    for layer in LAYERS + [[T] * 42] * (LAYER_COUNT - len(LAYERS)):
        assert len(layer) == 42, len(layer)
        grid = [[-1] * COLS for _ in range(ROWS)]
        for (r, c), kc in zip(MATRIX_ORDER, layer):
            grid[r][c] = kc
        for r, c in EXTRA_KEYS:
            grid[r][c] = X
        layout.append(grid)
    return {
        "version": 1,
        "uid": UID,
        "layout": layout,
        "encoder_layout": [],
        "layout_options": 0,
        "macro": [macro_actions(g) for g in MACROS],
        "vial_protocol": VIAL_PROTOCOL,
        "via_protocol": VIA_PROTOCOL,
        "tap_dance": [],
        "combo": [],
        "key_override": KEY_OVERRIDES,
        "alt_repeat_key": [],
        "settings": {},
    }

def keysym(ch):
    return "U%04X" % ord(ch)

def build_xkb_symbols():
    lines = [
        "// wanderers:magic — generated by ~/code/crkbd/wanderers/layout.py. Do not edit.",
        "// The W-Corne Magic layers send these otherwise-unused scancodes; the host",
        "// turns them into glyphs. Applied as an OPTION so it lands after inet(evdev),",
        "// which would otherwise override F14..F24 with XF86 keysyms.",
        "partial alphanumeric_keys",
        'xkb_symbols "magic" {',
    ]
    for pos, (vial, xkbname, l1, l2, l3, l4) in XKB_KEYS.items():
        typ = "FOUR_LEVEL_ALPHABETIC" if pos in GREEK_POSITIONS else "FOUR_LEVEL"
        syms = ", ".join("%-6s" % keysym(ch) for ch in (l1, l2, l3, l4))
        lines.append('    key <%s> { type[Group1] = "%s", [ %s ] }; // %s: %s %s %s %s'
                     % (xkbname, typ, syms, pos, l1, l2, l3, l4))
    lines.append("};")
    return "\n".join(lines) + "\n"

XKB_RULES = """! include %S/evdev

! option          = symbols
  wanderers:magic = +wanderers(magic)
"""

def compose_missing():
    if not FLEET_XCOMPOSE.exists():
        return ["(fleet XCompose not found at %s)" % FLEET_XCOMPOSE]
    have = set()
    for line in FLEET_XCOMPOSE.read_text().splitlines():
        if line.startswith("<Multi_key>") and "# U+" in line:
            have.add(int(line.split("# U+")[1].split()[0], 16))
    out = []
    for g in MACROS:
        if ord(g) not in have:
            seq = " ".join("<%s>" % d for d in str(ord(g)))
            out.append('<Multi_key> %s <space>\t: "%s"   # U+%04X' % (seq, g, ord(g)))
    return out

def main():
    vil = build_vil()
    (HERE / "w-corne-wanderers.vil").write_text(json.dumps(vil, ensure_ascii=False, indent=1) + "\n")
    (HERE / "xkb" / "symbols").mkdir(parents=True, exist_ok=True)
    (HERE / "xkb" / "rules").mkdir(parents=True, exist_ok=True)
    (HERE / "xkb" / "symbols" / "wanderers").write_text(build_xkb_symbols())
    (HERE / "xkb" / "rules" / "evdev").write_text(XKB_RULES)
    missing = compose_missing()
    (HERE / "compose-missing.txt").write_text("\n".join(missing) + ("\n" if missing else ""))
    print("vil layers:", len(vil["layout"]), "macros:", len(vil["macro"]), "key overrides:", len(vil["key_override"]))
    print("xkb keys:", len(XKB_KEYS), "compose sequences missing from fleet:", len(missing))
    for m in missing:
        print("  ", m)

if __name__ == "__main__":
    main()
