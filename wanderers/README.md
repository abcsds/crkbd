# wanderers — W-Corne layout

Personal layout for beto's Corne, mirroring the Epomaker Luma40 `wanderers`
QMK keymap (`~/code/EpomakerQMK/keyboards/epomaker/luma40/keymaps/wanderers/`)
as closely as a 42-key board allows. Approved 2026-10-07.

## Hardware

| Field | Value |
|---|---|
| Board | KeyClicks / PandaKB **W-Corne V4.1 MX**, 42 keys (3×6 + 3 thumbs per side) |
| Connection | 2.4 GHz dongle only. USB-C on the halves is charge-only. |
| USB dongle | `55d4:0461` "Pilot W-CORNE", serial `vial:f64c2b3c` (Vial magic) |
| Firmware | Closed nRF build with Vial. Halves update via nRF Connect DFU-over-BLE ("KCDFU", hold 4 keys at power-on); dongle via the Vial bootloader. |
| LEDs / OLED / encoders | none |
| Vendor docs | <https://docs.keyclicks.ca/w-keyboards/w-corne> |

Consequence: **everything lives in Vial's dynamic keymap**. No custom C, no
per-layer RGB, no QMK unicode map. Unicode glyphs are Vial macros that type
`Menu, <decimal codepoint>, Space`, resolved by the fleet `~/.XCompose`
(`/etc/nixos/home/xcompose/XCompose`, `compose:menu` on every desktop).

Stored scancodes are **QWERTY** exactly like the Luma40; the host's
`dvorak-alt-intl` layout does the remapping. Vial therefore displays QWERTY
names while the board types Dvorak. Diagrams below show what gets **typed**
on a Wanderers host.

## Layers

| # | Layer | Reached by | Role |
|---|-------|------------|------|
| 0 | Base | default | letters, thumb mods |
| 1 | Lower | hold left inner thumb | digits, dead keys, clipboard, page nav, volume |
| 2 | Raise | hold right inner thumb | symbols, F-keys, brackets, arrows |
| 3 | Adjust | Lower + Raise (explicit `MO(3)` on the opposite thumb, xiutik-style) | numpad, system and lock keys, layer toggles |
| 4 | Magic1 | `OSL(4)` on Raise + left outer thumb; `TG(4)` on Adjust | Greek + top math/typography glyphs |
| 5 | Magic2 | `OSL(5)` on Raise + left Space thumb; `TG(5)` on Adjust | second tier glyphs, uppercase Greek, logic/sets |
| 6 | Mouse | `TG(6)` on Adjust | mouse keys |

Thumb legend, left to right: `L1 L2 L3 | R1 R2 R3`. L3 and R1 are the 1.5u
inner keys.

### Base

```
GEsc  '  ,  .  p  y      f  g  c  r  l  Bspc
Tab   a  o  e  u  i      d  h  t  n  s  -
LSft  ;  q  j  k  x      b  m  w  v  z  RSft
         LGui Lower Ctrl/Spc   Alt/Ent Raise AltGr
```

- `GEsc` = Esc, Shift gives `~`, GUI gives `` ` `` (QK_GESC).
- `Ctrl/Spc` = `LCTL_T(KC_SPC)`, `Alt/Ent` = `LALT_T(KC_ENT)`. Permissive hold
  on, tapping term ~200 ms (Vial → QMK Settings → Tap-Hold).
- `AltGr` is a plain `KC_RALT`: direct `dvorak-alt-intl` level-3 letters
  (é à ô û î ç ß ä ö ü ë ï è ù â ê, € on 4).

### Lower (left inner thumb)

Rows 0–1 are the Luma40 verbatim, including the six dead keys on the vowel
each accent relates to. Row 2 right swaps media for page navigation so it sits
under the same fingers as the Raise arrows.

```
`      1  2  3  4  5      6    7     8     9     0    Del
___    ^  `  ´  ¨  ˘      Play PrtSc Menu  ~     F13  —
CapsW  Cp Ps Ct Un Rd     Mute Home  PgUp  PgDn  End  LSft
          ___ [held] ___      Vol-  Adjust  Vol+
```

Dead-key scancodes (AltGr chords into `dvorak-alt-intl` levels 3/4):

| Typed | Scancode | xkb |
|---|---|---|
| `^` on a | `RALT(KC_6)` | `<AE06>` L3 dead_circumflex |
| `` ` `` on o | `RALT(KC_GRV)` | `<TLDE>` L3 dead_grave |
| `´` on e | `RALT(KC_Q)` | `<AD01>` L3 dead_acute |
| `¨` on u | `RALT(S(KC_Q))` | `<AD01>` L4 dead_diaeresis |
| `˘` on i | `RALT(S(KC_9))` | `<AE09>` L4 dead_breve |
| `~` on n | `RALT(S(KC_GRV))` | `<TLDE>` L4 dead_tilde |

`Menu` is `S(KC_F10)` (context menu; plain Menu is the Compose key).
`Cp Ps Ct Un Rd` = `KC_COPY KC_PSTE KC_CUT KC_UNDO KC_AGIN`. `—` is a
Compose macro (U+2014). `CapsW` = `CW_TOGG` if the firmware has Caps Word,
else `KC_CAPS`.

### Raise (right inner thumb)

Luma40 scancodes kept, so the right home row types `/ = [ ] \` and
`? + { } |` with Shift. Shift on the top row gives digits via key overrides
(`ko_make_with_layers(MOD_MASK_SHIFT, KC_EXLM, KC_1, 1<<2)` …) when the
firmware has override slots. Arrows in the Luma40 order.

```
Esc  !  @  #  $  %       ^    &  *  (  )  Ctrl-Bspc
___  F1 F2 F3 F4 F5      F6   /  =  [  ]  \
___  F7 F8 F9 F10 F11    F12  ←  ↑  ↓  →  Ins
     OSL(Magic1) Adjust OSL(Magic2)     ___ [held] ___
```

### Adjust (Lower + Raise)

```
Boot    Sleep Bri-  Bri+   Pause     NumLk       ScrLk EEClr  7  8  9  /
CapsLk  Prev  Play  Next   Stop      Mute        Ins   Menu   4  5  6  *
___     Vol-  Vol+  TG(Ms) TG(Mag1)  TG(Mag2)    ___   ___    1  2  3  -
              ___ [held] ___                       0  [held]  .
```

Numpad keys are keypad usages (`KC_P7` …), hence `NumLk`: with Num Lock off
the host turns them into Home/PgUp/… . `Boot` = `QK_BOOT` (effect on the nRF
firmware unverified; DFU is a hardware key hold). `Bri±` are consumer
brightness usages, carried by the dongle's consumer-control interface.

### Magic1 (one glyph: Raise + L1; stretch: Adjust + TG(Mag1))

The board has only **16 macro slots**, so most glyphs are not macros. The 20
keys marked with a letter below send a spare scancode (F14–F24, the JIS and
Korean keys, non-US backslash, keypad =) that the host's xkb option
`wanderers:magic` maps to four levels: plain, Shift, AltGr, AltGr+Shift.
Greek therefore keeps its lower/upper Shift pair as on the Luma40. Keys
marked `*` are Compose macros. Thumbs transparent so Space/Enter/mods keep
working in toggle mode. `Exit` = `TG(4)`.

```
Exit   …*   “«   ”»   πΠ   θΘ      φΦ   γΓ   χΧ   ρΡ   λΛ   ·*
→*     αΑ   ≤*   εΕ   ≥*   ±*      δΔ   ηΗ   τΤ   νΝ   σΣ   –—
∞*     ¿¡   •*   °*   κ*   ×*      βΒ   μΜ   ≈*   √*   ∈*   ∅*
```

### Magic2 (one glyph: Raise + L3; stretch: Adjust + TG(Mag2))

The AltGr levels of the same 20 keys, sent as `RALT(scancode)`. Second
glyph with Shift. Also reachable without this layer as Magic1 + AltGr.
Macro positions are `KC_NO` here. `Exit` = `TG(5)`.

```
Exit   .    ⟨⟦   ⟩⟧   ∝‰   ∼≅      ∫∮   ⊤⊥   ⊂⊃   ℝℤ   ←↔   .
.      ∀∧   .    ∃∨   .    .       ∂∇   ⋯⋮   ⇒⇔   ℕℚ   ∑∏   ÷∓
.      ≠≡   .    .    .    .       ∪∩   𝔼ℙ   .    .    .    .
```

Host mapping (`xkb/symbols/wanderers`, generated):

| Pos | Scancode | xkb | L1 | L2 | L3 | L4 |
|---|---|---|---|---|---|---|
| p | KC_F14 | FK14 | π | Π | ∝ | ‰ |
| y | KC_F15 | FK15 | θ | Θ | ∼ | ≅ |
| f | KC_F16 | FK16 | φ | Φ | ∫ | ∮ |
| g | KC_F17 | FK17 | γ | Γ | ⊤ | ⊥ |
| c | KC_F18 | FK18 | χ | Χ | ⊂ | ⊃ |
| r | KC_F19 | FK19 | ρ | Ρ | ℝ | ℤ |
| l | KC_F20 | FK20 | λ | Λ | ← | ↔ |
| a | KC_F21 | FK21 | α | Α | ∀ | ∧ |
| e | KC_F22 | FK22 | ε | Ε | ∃ | ∨ |
| d | KC_F23 | FK23 | δ | Δ | ∂ | ∇ |
| h | KC_F24 | FK24 | η | Η | ⋯ | ⋮ |
| t | KC_RO (INT1) | AB11 | τ | Τ | ⇒ | ⇔ |
| n | KC_KANA (INT2) | HKTG | ν | Ν | ℕ | ℚ |
| s | KC_JYEN (INT3) | AE13 | σ | Σ | ∑ | ∏ |
| b | KC_HENK (INT4) | HENK | β | Β | ∪ | ∩ |
| m | KC_MHEN (INT5) | MUHE | μ | Μ | 𝔼 | ℙ |
| , | KC_LANG1 | HNGL | “ | « | ⟨ | ⟦ |
| . | KC_LANG2 | HJCV | ” | » | ⟩ | ⟧ |
| ; | KC_NONUS_BSLASH | LSGT | ¿ | ¡ | ≠ | ≡ |
| - | KC_KP_EQUAL | KPEQ | – | — | ÷ | ∓ |

F13 is excluded on purpose: the desktops bind it to `pbt practice`. The
option is merged after `inet(evdev)` (which would otherwise override
F14–F24 with XF86 keysyms); it is user-level xkb (`~/.config/xkb`), honoured
by KWin, Sway and Hyprland but not by X11/SDDM.

Compose macros (M0–M15): — … · → ≤ ≥ ± ∞ • ° × ≈ √ ∈ ∅ κ. All but · were
already in the fleet `~/.XCompose`; · is added by the same fleet commit.

### Mouse (Adjust + TG(Ms))

Cursor at the Raise arrow positions, wheel on the row above, speed on the left
home row, clicks on the thumbs. Unassigned keys are `KC_NO` (no base
bleed-through, Luma40 rule). `Exit` = `TG(6)`.

```
Exit  ___  ___  ___  ___  ___     ___  ___  ___  ___  ___  ___
___   Acl0 Acl1 Acl2 ___  ___     ___  WhL  WhU  WhD  WhR  ___
LSft  ___  ___  ___  ___  ___     ___  M←   M↑   M↓   M→   ___
          Btn3 Btn2 Btn1              Btn1 Btn2 Btn3
```

## Workflow

- **Letters and Shift**: Base, outer bottom keys. Caps Word: Lower + left Shift position.
- **Digits**: hold Lower, top row. **Symbols**: hold Raise, top row (Shift there gives digits if key overrides exist).
- **Brackets**: hold Raise, right home row.
- **Direct accents**: hold AltGr (R3), type the letter.
- **Dead-key accents**: hold Lower, tap the accent's vowel key, release, type the letter. `Lower+e, o → ó`; `Lower+n, n → ñ`; `Lower+a, c → ĉ`; `Lower+i, u → ŭ`.
- **Navigation**: Raise + right bottom row = arrows; Lower + same keys = Home PgUp PgDn End. Word jumps: hold Space (Ctrl), Raise, arrow.
- **Adjust**: both layer thumbs. Right hand numpad, left hand system keys.
- **One glyph**: hold Raise, tap L1 (Magic1) or L3 (Magic2), release both, press the glyph key. Back on Base automatically.
- **Many glyphs / mouse**: Adjust + TG key toggles the layer on; `Exit` top-left returns.

## Board budget (probed 2026-10-07)

| Item | Value |
|---|---|
| VIA / Vial protocol | 9 / 6 |
| Dynamic layers | 8 (7 used) |
| Macros | 16 slots, 6377-byte buffer (16 used) |
| Tap dance / combo / key override slots | 32 / 32 / 32 (10 overrides used) |
| Matrix | 4×12; rows 0–2 alphas, row 3 cols 3–8 thumbs; cols 0,1,9,10,11 of row 3 are optional keys not on this board |

**Dongle jam.** The dongle relays Vial requests over the radio. If any request
times out (halves asleep, two clients at once, write to a stale node) the
raw-HID interface NAKs every transfer, even control requests, until the
dongle is unplugged and replugged; the Vial GUI then dies with "failed to
communicate with the device". One client at a time; replug before opening
Vial if a probe ran.

## Files

- `README.md` — this spec (source of truth for intent).
- `layout.py` — layer tables + generator. Run `python3 layout.py` here; it rewrites everything below.
- `w-corne-wanderers.vil` — generated Vial layout. Vial → File → Load saved layout.
- `xkb/symbols/wanderers`, `xkb/rules/evdev` — generated host xkb option; copied to `/etc/nixos/home/xkb/`.
- `compose-missing.txt` — Compose sequences the fleet `~/.XCompose` still lacks (should be empty).
- `probe/vialq2.py` — retrying raw-HID probe (budgets + embedded definition). `probe/vialq.py` is the naive first version.
- `probe/wcorne-vial-def.json` — the board's embedded Vial definition.

## Loading and testing

1. Replug the dongle (clears any jam). Open Vial (`vial`, or `nix run nixpkgs#vial`).
2. File → Load saved layout → `w-corne-wanderers.vil`. Vial writes keys, macros and key overrides.
3. QMK Settings tab: Tapping Term ~200 ms, Permissive Hold on (thumb mod-taps).
4. Host side: the xkb option must be active in the session (`wanderers:magic`), see below.

## Host prerequisites

Fleet commit on `/etc/nixos` (`home/xkb/`, `home/files.nix`, the three session
configs, `home/xcompose/XCompose`): ships `~/.config/xkb/{symbols/wanderers,rules/evdev}`
through home-manager and adds `wanderers:magic` to the Plasma, Sway and Hyprland
xkb options. Saturn also needs `pkgs.vial` + the udev rule
`ATTRS{serial}=="*vial:f64c2b3c*"` (commit `7aee69ad`).

Until that deploys, the same files are copied by hand into `~/.config/xkb/`
and `~/.config/kxkbrc` carries the option. **Remove the hand copies before the
home-manager deploy** or it refuses to clobber them.
