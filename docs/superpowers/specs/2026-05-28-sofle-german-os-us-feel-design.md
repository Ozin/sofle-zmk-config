# Sofle Wireless — German-OS / US-Feel Firmware Design

## 1. Goal

Deliver a single ZMK firmware configuration for the Keebart Sofle Wireless that:

- Runs cleanly against a **German (de) OS keyboard layout** on every machine the user touches (corporate Linux + Windows, personal machines).
- Preserves the user's **US-style typing experience** on the default layer — same letter positions, same number-row shifted symbols, same `` ` `` / `~`.
- Provides **first-class umlaut entry** via a `LGUI`/`RGUI` + `a/o/u/s` chord that emits `ä/ö/ü/ß`, mirroring the user's existing AutoHotkey muscle memory on Windows.
- Eliminates the user's previous problem: umlaut entry on Linux without OS-side tooling like `xkb` overrides, Compose key configuration, IBus shortcuts, or WinCompose-equivalents.

## 2. Non-goals

- Supporting a US OS layout. The firmware assumes OS = German.
- Supporting a Mac. (Possible later via a layer toggle, but out of scope here.)
- Touching the Raise or Adjust layers — those are BT/RGB/navigation, layout-agnostic.
- Replacing existing Lower-layer behavior with a different layout strategy; only the *target keycodes* on Lower change.

## 3. Constraints / accepted trade-offs

- **GUI shortcut collisions:** `LGUI`/`RGUI` + `a/o/u/s` is hijacked for umlauts. System shortcuts on those combinations (Windows: Win+A action center, Win+S search, Win+U accessibility, Win+O rotation lock; Linux: any Super+a/o/u/s window-manager binding) become unreachable from the keyboard. Confirmed acceptable.
- **`LGUI`/`RGUI` + other letters** remain plain GUI modifiers (Win+L locks, Win+E opens Explorer, etc.).
- The OS being set to German is a hard prerequisite. If a future machine resets to US, the firmware output is wrong everywhere. (User's environment is already German-default.)
- Dead-key handling for `` ` ``, `~`, `^` requires multi-step macros and inherits dead-key timing behavior from the OS; it's robust but not instantaneous.

## 4. High-level approach

ZMK firmware emits HID scancodes; the German-OS layout interprets them. The firmware is built on three mechanisms:

1. **Direct keycode swaps** — for keys where the desired US character is produced by a *different* HID scancode under the German layout (the position physically labeled `Y` on US needs the firmware to emit HID code `Z` so a German OS renders it as `y`).
2. **Mod-morph behaviors** — for keys whose Shift-form differs between US and German. The behavior says "if Shift is held, emit X; else emit Y."
3. **Macros** — for multi-keystroke sequences, primarily dead-key + Space to commit `` ` `` `~` `^`.

The umlaut chord is itself a **mod-morph**: when LGUI or RGUI is held, the `a`/`o`/`u`/`s` keys emit ä/ö/ü/ß (using ZMK's German-locale keycodes `DE_AE`, `DE_OE`, `DE_UE`, `DE_SS`), and the GUI mod is *consumed* for that press so the OS doesn't see GUI+letter.

## 5. Layer-by-layer changes

### 5.1 Default layer

**Keys that don't change behavior** (German-layout-position == US-layout-position): `1` `2` `3` `4` `5` `6` `7` `8` `9` `0` (unshifted), all letters except `Y` and `Z`, `,` and `.` (unshifted), `ESC`, `TAB`, `BSPC`, `RET`, `LSHFT`, `RSHFT`, `LCTRL`, `RCTRL`, `LALT`, `RALT`, `SPACE`, `MUTE`, `PLAY`, `Lower`, `Raise`.

**Direct keycode swaps:**

| Physical key | Emits HID code for | Result on German OS |
|---|---|---|
| Y | `Z` (US-Z position) | y |
| Z | `Y` (US-Y position) | z |

**Mod-morphs (Shift behavior):**

| Key position | Unshifted output | Shifted output | Shift implementation |
|---|---|---|---|
| 2 | 2 | `@` | AltGr+Q (RALT+Q) |
| 3 | 3 | `#` | NON_US_HASH (HID 0x32), no shift |
| 6 | 6 | `^` | macro: tap Shift+`=` (German dead `^`)… see §5.3 |
| 7 | 7 | `&` | German Shift+6 |
| 8 | 8 | `*` | German Shift+`+` (the `+/-/~` key) |
| 9 | 9 | `(` | German Shift+8 |
| 0 | 0 | `)` | German Shift+9 |
| `;` position | `;` (German Shift+`,`) | `:` (German Shift+`.`) | both via mod-morph; unshifted form is itself a Shift+something |
| `'` position | `'` (German Shift+NON_US_HASH) | `"` (German Shift+2) | both forms via mod-morph |
| `,` | `,` (passthrough) | `<` (German NON_US_BSLASH, HID 0x64) | shift form via mod-morph |
| `.` | `.` (passthrough) | `>` (German Shift+NON_US_BSLASH) | shift form via mod-morph |
| `/` position | `/` (German Shift+7) | `?` (German Shift+ß) | both forms via mod-morph |
| `` ` `` position | `` ` `` (dead-key macro, §5.3) | `~` (dead-key macro, §5.3) | both forms via mod-morph |

**Umlaut mod-morphs (GUI behavior):**

| Key position | Default output | LGUI/RGUI held → output | Implementation |
|---|---|---|---|
| A | `a` | `ä` | `DE_AE` (HID 0x34), GUI mod consumed |
| O | `o` | `ö` | `DE_OE` (HID 0x33), GUI mod consumed |
| U | `u` | `ü` | `DE_UE` (HID 0x2F), GUI mod consumed |
| S | `s` | `ß` | `DE_SS` (HID 0x2D), GUI mod consumed |

Shifted form behavior for umlauts: `GUI+Shift+a` → `Ä` (capital), via the same mod-morph + Shift propagating to the umlaut emit. To be confirmed in implementation: ZMK mod-morph's interaction with Shift on the morphed output is straightforward but the exact ZMK syntax for "consume GUI, keep Shift" needs to be verified.

### 5.2 Lower layer

The current Lower layer emits US scancodes for direct symbol keys. Each of these gets retargeted to its German equivalent so it produces the same character on a German OS. Numbers and F-keys are unchanged.

| Lower layer key | Current emit (US) | New emit (German-OS-compatible) |
|---|---|---|
| `!` | Shift+1 | Shift+1 (unchanged) |
| `@` | Shift+2 | AltGr+Q |
| `#` | Shift+3 | NON_US_HASH (HID 0x32) |
| `$` | Shift+4 | Shift+4 (unchanged) |
| `%` | Shift+5 | Shift+5 (unchanged) |
| `^` | Shift+6 | dead-key macro (§5.3) |
| `&` | Shift+7 | Shift+6 |
| `*` | Shift+8 | Shift+`+` |
| `(` | Shift+9 | Shift+8 |
| `)` | Shift+0 | Shift+9 |
| `=` | `=` | Shift+0 |
| `-` | `-` | `/` position HID (German `-` lives at US `/` position) |
| `+` | Shift+`=` | `+` (German `+` key, HID 0x30) |
| `{` | Shift+`[` | AltGr+7 |
| `}` | Shift+`]` | AltGr+0 |
| `[` | `[` | AltGr+8 |
| `]` | `]` | AltGr+9 |
| `;` | `;` | German Shift+`,` |
| `:` | Shift+`;` | German Shift+`.` |
| `\` | `\` | AltGr+ß |
| `\|` | Shift+`\` | AltGr+NON_US_BSLASH (HID 0x64) |
| `` ` `` | `` ` `` | dead-key macro (§5.3) |

### 5.3 Dead-key macros

ZMK macros that emit *dead-key + Space* to force the German OS to commit the standalone character:

- **Backtick `` ` ``** → tap Shift+`=` (German Shift+`=` is the `` ` `` dead key), then tap Space.
- **Tilde `~`** → tap AltGr+`+` (German AltGr+`+` is the `~` dead key), then tap Space. (Some German layouts emit `~` directly without a Space commit; to be verified during implementation.)
- **Circumflex `^`** → tap the German `^` key (HID 0x35, top-left, the dead `^` key), then tap Space.
- **Degree `°`** → tap Shift+(HID 0x35), no Space needed (not a dead key). Optional; only if user wants it.

Each macro is invoked from either the default layer (via the mod-morph for the `` ` ``/`~`/`^` keys) or directly from Lower.

### 5.4 Raise & Adjust layers

No changes. Both layers are layout-agnostic (Bluetooth profile switching, RGB control, media keys, navigation).

## 6. Architecture / file layout

The project will follow the ZMK config repo convention:

```
sofle-zmk-config/
├── config/
│   ├── sofle.keymap          # main keymap with all layers
│   ├── sofle.conf            # build-time config
│   ├── boards/               # any board-level overrides
│   └── west.yml              # ZMK module pointer
├── build.yaml                # GitHub Actions build matrix
├── docs/
│   └── superpowers/
│       └── specs/
│           └── 2026-05-28-sofle-german-os-us-feel-design.md  (this file)
└── README.md
```

Custom ZMK behaviors live inline in `sofle.keymap` under the `behaviors {}` node. Each mod-morph and macro is named with a clear, greppable identifier (`me_at`, `me_hash`, `me_caret`, `me_grave`, `me_tilde`, `me_ae`, `me_oe`, `me_ue`, `me_ss`, etc. — `me_` for "morph/macro emit").

## 7. Build & flash workflow

- Edits happen in `config/sofle.keymap` locally.
- Push to GitHub → GitHub Actions workflow (`build.yaml`) compiles `.uf2` firmware for both halves of the Sofle Wireless (nice!nano v2).
- Download both `.uf2` files from the Actions artifact, double-tap reset on each half to enter bootloader, drag-and-drop the file.
- Reconnect Bluetooth and verify.

## 8. Open questions / risks

1. **Mod-morph + Shift + GUI interaction.** ZMK's mod-morph is well-documented for `(MOD_LSFT|MOD_RSFT)` masks. The umlaut morph wants to consume `(MOD_LGUI|MOD_RGUI)` while *preserving* Shift to allow `Ä` capitals. Needs verification during implementation; if ZMK doesn't propagate Shift cleanly through a mod-morph, we add four extra morphs for Shift+GUI+letter → capital umlaut.
2. **Tilde dead-key.** Some German layouts (X11/Wayland on Linux) emit `~` immediately on AltGr+`+`, no Space commit needed; others require a commit. To be tested early; macros adjusted accordingly.
3. **OS resetting to a different layout.** If the user's machine ever defaults to US or another layout, every compensating key produces the wrong character. No graceful fallback in firmware; out of scope. Documented in README as a hard prerequisite.
4. **Bluetooth profile switching.** Unchanged from current keymap; flagged here only to confirm nothing in the design interferes.

## 9. Testing strategy

Manual verification on at least two machines (one Linux, one Windows), both OS-set to German layout. A test sheet enumerates:

- Every letter (verify `y` and `z` come out correctly).
- Every shifted number (verify `!@#$%^&*()`).
- Every right-side punctuation in shifted and unshifted form.
- `` ` `` and `~` produce the standalone characters (not dead-keys leaving the system in a dead-key state).
- Each of `LGUI+a/o/u/s`, `LGUI+Shift+a/o/u/s`, `RGUI+a/o/u/s`, `RGUI+Shift+a/o/u/s`.
- A control set of `LGUI+<other letter>` to confirm system shortcuts still work (Win+L locks, Win+E opens file manager, etc.).
- Every Lower-layer symbol.

## 10. Implementation phases (rough)

Detailed in a separate implementation plan (next step):

1. Bootstrap repo: copy current `.keymap`, set up `build.yaml`, verify CI build succeeds unmodified.
2. Add the locale include (`dt-bindings/zmk/keys_de.h`) and direct keycode swaps (Y/Z).
3. Add number-row mod-morphs.
4. Add right-side punctuation mod-morphs.
5. Add dead-key macros (`` ` ``, `~`, `^`).
6. Add umlaut mod-morphs (GUI+letter).
7. Rewrite Lower-layer symbol emissions.
8. Test sheet pass on Linux.
9. Test sheet pass on Windows.
