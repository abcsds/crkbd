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

Greek on its Latin letter as on the Luma40. Zero-frequency Greek
(ο υ ι ξ ς ζ ω ψ) gave their keys to the top math symbols from
`docs/luma40-designer/freq-study/symbols.md`, several at their old Magic-Hi
positions (≤ on o, ± on i). Thumbs transparent so Space/Enter/mods keep
working in toggle mode. `Exit` = `TG(4)`.

```
Exit  …  “  ”  π  θ      φ  γ  χ  ρ  λ  ·
→     α  ≤  ε  ≥  ±      Δ  η  τ  ν  σ  –
∞     ¿  ¡  °  κ  ×      β  μ  ≈  √  ∈  ↔
          ___ ___ ___        ___ ___ ___
```

### Magic2 (one glyph: Raise + L3; stretch: Adjust + TG(Mag2))

Next tier from the study plus the Luma40 Magic-Hi logic/set symbols.
Mnemonics: ∀ a, ∃ e, ∪ u, ∂ d, ⊤ t, ⊥ b, ∇ n, Σ s, ∧ w (wedge), ∨ v (vee),
𝔼 m (mean). `Exit` = `TG(5)`.

```
Exit  ∑  ∫  ⋯  Π  Θ      Φ  Γ  ∠  ℝ  Λ  •
⇒     ∀  Ω  ∃  ∪  ∩      ∂  ∼  ⊤  ∇  Σ  ≠
←     δ  ∅  Ψ  ⊂  ∉      ⊥  𝔼  ∧  ∨  ∝  ÷
          ___ ___ ___        ___ ___ ___
```

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

## Macro budget

Compose macros needed: Magic1 36 + em dash on Lower = 37, Magic2 36, total 73.
Vial firmware commonly ships 16 or 32 macro slots. Fill order follows the
frequency study, Magic1 first:

1. (16) — × α σ Δ μ β · ρ → ± τ ≤ ≈ ¿ ¡
2. (32) + – ε ≥ θ ∈ √ λ ↔ χ π ∞ ν η φ … “
3. (37) + ” κ ° ∑ ∫ … then Magic2 in row order.

Keys whose macro did not fit are left `KC_NO` on the Magic layers.

## Files

- `README.md` — this spec (source of truth for intent).
- `layout.py` — layer spec as data + generator for the `.vil` file.
- `w-corne-wanderers.vil` — generated Vial layout; load via Vial → File → Load saved layout.
- `probe/vialq.py` — raw-HID probe: layer/macro/override counts, embedded keyboard definition.
- `probe/wcorne-vial-def.json` — the board's embedded Vial definition (matrix, layout).

## Host prerequisites

Saturn: `pkgs.vial` + a udev rule matching `ATTRS{serial}=="*vial:f64c2b3c*"`
(`/etc/nixos/devices/saturn/default.nix`). Without it hidraw is root-only and
Vial sees no keyboard.
