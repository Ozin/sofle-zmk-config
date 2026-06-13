# Sofle German-OS / US-Feel Firmware — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reprogram the Keebart Sofle Wireless (board `sofle_choc_pro`) so it types the user's familiar US-style characters while the OS keyboard layout is set to **German**, and add the spec's extras (umlaut chord, Raise nav tweaks, Adjust numpad).

**Architecture:** Bootstrap a buildable ZMK config from the upstream `Keebart/zmk-config` (which bundles the custom `sofle_choc_pro` board, the `nice_view_disp` display shield, `build.yaml`, and ZMK-Studio support). Vendor the German locale header `keys_de.h` (from `joelspadin/zmk-locales`, MIT) directly into `config/` so every key can emit the HID scancode-plus-modifier that a **German OS** renders as the intended US character. Keys whose US output differs between shifted and unshifted forms (number row, right-side punctuation, the `` ` ``/`~` key) use `zmk,behavior-mod-morph`; the umlaut chord (GUI + a/o/u/s) is a mod-morph keyed on GUI; `` ` `` `~` `^` use macros that tap a German dead key then Space.

**Tech Stack:** ZMK firmware (pinned `v0.3` via `config/west.yml`), Devicetree keymap, GitHub Actions build matrix, nice!nano-class controller, UF2 drag-and-drop flashing.

---

## Why this mechanism (vs. the spec's §4 hand-built approach)

The spec (§4) predates the discovery of the `zmk-locales` German header. That header defines a `DE_*` macro for every character, each pre-encoded as the exact scancode+modifier a German OS turns back into that character — verified examples: `DE_Y`=HID-Z and `DE_Z`=HID-Y (Y/Z swap is automatic), `DE_AT`=`RA(Q)`, `DE_HASH`, `DE_CARET`, `DE_TILDE`, `DE_LBRC`/`DE_RBRC`, `DE_A_UMLAUT`/`DE_O_UMLAUT`/`DE_U_UMLAUT`/`DE_SZ`, plus capitals `DE_CAPITAL_SZ`. Using these as the *targets* of the (still required) mod-morphs makes the keymap readable and correct, and collapses the entire single-function Lower layer to plain `&kp DE_*` one-liners.

**Spec open questions resolved during research:**
- **§8.1 (mod-morph + Shift + GUI):** Solved cleanly. The umlaut morph's trigger set is GUI only; Shift is *not* in the trigger set, so it passes through to the morphed output automatically → `GUI+Shift+a` → `Ä`. For `ß` specifically, Shift on the German `ß`-key would yield `?`, so a nested Shift-morph emits `DE_CAPITAL_SZ` (`ẞ`) instead. `keep-mods` exists in ZMK `v0.3` if ever needed, but is not required here.
- **§8.2 (tilde dead-key):** Still must be confirmed on hardware (Task 8). The macro taps `DE_TILDE` then `SPACE`; if your OS emits `~` directly (no dead-key), drop the trailing `SPACE` — noted inline in Task 3.

## File Structure

After Task 1 the repo mirrors `Keebart/zmk-config` (board definition bundled so CI can build), plus our docs:

```
sofle-zmk-config/
├── .github/workflows/build.yml        # GitHub Actions: runs the build.yaml matrix
├── build.yaml                          # board+shield matrix (sofle_choc_pro_left/right)
├── boards/arm/sofle_choc_pro/          # custom board definition (REQUIRED for CI build)
├── boards/shields/nice_view_disp/      # nice!view display shield
├── config/
│   ├── west.yml                        # ZMK module pointer (revision v0.3) — unchanged
│   ├── sofle_choc_pro.conf             # build-time config — unchanged
│   ├── sofle_choc_pro.json             # ZMK Studio physical layout — unchanged
│   ├── keys_de.h                       # VENDORED German locale header (new)
│   └── sofle_choc_pro.keymap           # THE FILE WE EDIT — all layers + behaviors
└── docs/superpowers/                   # spec + this plan
```

Only **two** files are authored/changed by this plan: `config/keys_de.h` (new, vendored once) and `config/sofle_choc_pro.keymap` (rewritten layer by layer). Everything else is copied in unmodified at Task 1.

## Testing approach (read before starting)

ZMK firmware has no practical local unit-test loop for a personal config. "Verify" in this plan means:
1. **CI build green** — push the branch; the GitHub Actions "Build" workflow must finish with all matrix jobs ✅ and produce `.uf2` artifacts. This is the per-task gate.
2. **Manual hardware test sheet** — Tasks 8–9, flashing real firmware and typing on a German-OS machine.

You can optionally flash any intermediate build to spot-check, but the required gate after each layer task is a green CI build.

---

### Task 1: Bootstrap the buildable repo from Keebart/zmk-config

**Files:**
- Create: everything under `boards/`, `config/` (except docs), `build.yaml`, `.github/workflows/build.yml`
- Keep: existing `docs/` untouched

- [ ] **Step 1: Vendor the upstream repo content into a temp dir**

```bash
cd /tmp
rm -rf keebart-src
git clone --depth 1 https://github.com/Keebart/zmk-config.git keebart-src
ls keebart-src   # expect: boards  config  build.yaml  .github  ...
```

- [ ] **Step 2: Copy the buildable scaffolding into our repo (do NOT overwrite docs/)**

```bash
cd /home/michi/projects/private/sofle-zmk-config
cp -r /tmp/keebart-src/boards .
cp -r /tmp/keebart-src/config .
cp /tmp/keebart-src/build.yaml .
mkdir -p .github
cp -r /tmp/keebart-src/.github/workflows .github/
cp /tmp/keebart-src/.gitignore . 2>/dev/null || true
```

- [ ] **Step 3: Trim the build matrix to only the Sofle (optional but faster CI)**

Edit `build.yaml` and delete the `corne_choc_pro_*` and `piantor_pro_bt_*` `include:` entries, keeping only the four `sofle_choc_pro_*` entries (the two `nice_view_disp` builds and the two `settings_reset` builds). Final `build.yaml`:

```yaml
---
include:
  - board: sofle_choc_pro_left
    snippet: studio-rpc-usb-uart
    shield: nice_view_disp
    cmake-args: -DCONFIG_ZMK_STUDIO=y
  - board: sofle_choc_pro_right
    shield: nice_view_disp
    snippet: studio-rpc-usb-uart
  - board: sofle_choc_pro_left
    shield: settings_reset
    snippet: studio-rpc-usb-uart
  - board: sofle_choc_pro_right
    shield: settings_reset
    snippet: studio-rpc-usb-uart
```

- [ ] **Step 4: Commit the unmodified baseline**

```bash
git add boards config build.yaml .github .gitignore
git commit -m "Bootstrap buildable sofle_choc_pro config from Keebart/zmk-config"
```

- [ ] **Step 5: Create the GitHub repo and push (enables Actions builds)**

```bash
gh repo create sofle-zmk-config --private --source=. --remote=origin --push
```

Expected: repo created, branch pushed, GitHub Actions "Build" workflow auto-triggers.

- [ ] **Step 6: Verify the BASELINE build is green BEFORE any change**

```bash
gh run watch --exit-status   # or: gh run list --limit 1
```

Expected: all four matrix jobs ✅. This proves the toolchain/board build works before we touch the keymap. If red here, the problem is the bootstrap, not our edits. Do not proceed until green.

---

### Task 2: Vendor the German locale header and include it

**Files:**
- Create: `config/keys_de.h`
- Modify: `config/sofle_choc_pro.keymap` (add one `#include`)

- [ ] **Step 1: Vendor the header (preserve its MIT license block)**

```bash
cd /home/michi/projects/private/sofle-zmk-config
curl -fsSL https://raw.githubusercontent.com/joelspadin/zmk-locales/main/include/locale/keys_de.h -o config/keys_de.h
head -20 config/keys_de.h   # confirm the SPDX/MIT license header is intact
grep -c '#define DE_' config/keys_de.h   # expect a large count (>200)
```

- [ ] **Step 2: Include it in the keymap, after the standard ZMK includes**

In `config/sofle_choc_pro.keymap`, the include block currently ends with `#include <dt-bindings/zmk/ext_power.h>`. Add immediately below it:

```c
#include "keys_de.h"
```

- [ ] **Step 3: Commit and verify the build still passes (header present but unused)**

```bash
git add config/keys_de.h config/sofle_choc_pro.keymap
git commit -m "Vendor German locale header (keys_de.h) and include it"
git push
gh run watch --exit-status
```

Expected: green. An included-but-unused header must not break the build. If the build fails with "locale/... not found" it means the header references an include path — re-check Step 1 copied the file to `config/keys_de.h` and the include uses quotes `"keys_de.h"` (same dir as the keymap), not angle brackets.

---

### Task 3: Define all custom behaviors (umlaut morphs, dead-key macros, symbol morphs)

**Files:**
- Modify: `config/sofle_choc_pro.keymap` — add a `behaviors { }` and `macros { }` node inside the root `/ { ... }`, above the existing `conditional_layers` node.

- [ ] **Step 1: Add the macros node (dead-key committers)**

Insert directly after the opening `/ {` line (and its comment), before `conditional_layers`:

```c
    macros {
        // Tap the German dead-grave (Shift+=) then Space to commit a standalone `
        grave_dk: grave_dk {
            compatible = "zmk,behavior-macro";
            #binding-cells = <0>;
            bindings = <&macro_tap &kp DE_GRAVE &kp SPACE>;
        };
        // Tap AltGr+'+' (German tilde) then Space. If your OS emits ~ directly
        // (no dead key), remove the "&kp SPACE" below — verified in Task 8.
        tilde_dk: tilde_dk {
            compatible = "zmk,behavior-macro";
            #binding-cells = <0>;
            bindings = <&macro_tap &kp DE_TILDE &kp SPACE>;
        };
        // Tap the German dead-circumflex (^ key, top-left) then Space.
        caret_dk: caret_dk {
            compatible = "zmk,behavior-macro";
            #binding-cells = <0>;
            bindings = <&macro_tap &kp DE_CARET &kp SPACE>;
        };
    };
```

- [ ] **Step 2: Add the behaviors node (mod-morphs)**

Insert directly after the `macros { }` node:

```c
    behaviors {
        // --- Umlaut chord: hold LGUI/RGUI + letter -> umlaut. GUI is consumed
        //     (not sent to OS); Shift passes through, so GUI+Shift -> capital. ---
        umlaut_a: umlaut_a {
            compatible = "zmk,behavior-mod-morph";
            #binding-cells = <0>;
            bindings = <&kp A>, <&kp DE_A_UMLAUT>;
            mods = <(MOD_LGUI|MOD_RGUI)>;
        };
        umlaut_o: umlaut_o {
            compatible = "zmk,behavior-mod-morph";
            #binding-cells = <0>;
            bindings = <&kp O>, <&kp DE_O_UMLAUT>;
            mods = <(MOD_LGUI|MOD_RGUI)>;
        };
        umlaut_u: umlaut_u {
            compatible = "zmk,behavior-mod-morph";
            #binding-cells = <0>;
            bindings = <&kp U>, <&kp DE_U_UMLAUT>;
            mods = <(MOD_LGUI|MOD_RGUI)>;
        };
        // ß: GUI+s -> ß ; GUI+Shift+s -> ẞ (capital eszett) via nested Shift-morph
        ss_case: ss_case {
            compatible = "zmk,behavior-mod-morph";
            #binding-cells = <0>;
            bindings = <&kp DE_SZ>, <&kp DE_CAPITAL_SZ>;
            mods = <(MOD_LSFT|MOD_RSFT)>;
        };
        umlaut_s: umlaut_s {
            compatible = "zmk,behavior-mod-morph";
            #binding-cells = <0>;
            bindings = <&kp S>, <&ss_case>;
            mods = <(MOD_LGUI|MOD_RGUI)>;
        };

        // --- Number row: digit unshifted, US symbol shifted ---
        n2_morph: n2_morph {
            compatible = "zmk,behavior-mod-morph";
            #binding-cells = <0>;
            bindings = <&kp N2>, <&kp DE_AT>;
            mods = <(MOD_LSFT|MOD_RSFT)>;
        };
        n3_morph: n3_morph {
            compatible = "zmk,behavior-mod-morph";
            #binding-cells = <0>;
            bindings = <&kp N3>, <&kp DE_HASH>;
            mods = <(MOD_LSFT|MOD_RSFT)>;
        };
        n6_morph: n6_morph {
            compatible = "zmk,behavior-mod-morph";
            #binding-cells = <0>;
            bindings = <&kp N6>, <&caret_dk>;
            mods = <(MOD_LSFT|MOD_RSFT)>;
        };
        n7_morph: n7_morph {
            compatible = "zmk,behavior-mod-morph";
            #binding-cells = <0>;
            bindings = <&kp N7>, <&kp DE_AMPS>;
            mods = <(MOD_LSFT|MOD_RSFT)>;
        };
        n8_morph: n8_morph {
            compatible = "zmk,behavior-mod-morph";
            #binding-cells = <0>;
            bindings = <&kp N8>, <&kp DE_ASTRK>;
            mods = <(MOD_LSFT|MOD_RSFT)>;
        };
        n9_morph: n9_morph {
            compatible = "zmk,behavior-mod-morph";
            #binding-cells = <0>;
            bindings = <&kp N9>, <&kp DE_LPAR>;
            mods = <(MOD_LSFT|MOD_RSFT)>;
        };
        n0_morph: n0_morph {
            compatible = "zmk,behavior-mod-morph";
            #binding-cells = <0>;
            bindings = <&kp N0>, <&kp DE_RPAR>;
            mods = <(MOD_LSFT|MOD_RSFT)>;
        };

        // --- Right-side punctuation: US unshifted/shifted pairs ---
        semi_morph: semi_morph {
            compatible = "zmk,behavior-mod-morph";
            #binding-cells = <0>;
            bindings = <&kp DE_SEMI>, <&kp DE_COLON>;   // ; / :
            mods = <(MOD_LSFT|MOD_RSFT)>;
        };
        quote_morph: quote_morph {
            compatible = "zmk,behavior-mod-morph";
            #binding-cells = <0>;
            bindings = <&kp DE_SQT>, <&kp DE_DQT>;      // ' / "
            mods = <(MOD_LSFT|MOD_RSFT)>;
        };
        comma_morph: comma_morph {
            compatible = "zmk,behavior-mod-morph";
            #binding-cells = <0>;
            bindings = <&kp DE_COMMA>, <&kp DE_LT>;     // , / <
            mods = <(MOD_LSFT|MOD_RSFT)>;
        };
        dot_morph: dot_morph {
            compatible = "zmk,behavior-mod-morph";
            #binding-cells = <0>;
            bindings = <&kp DE_DOT>, <&kp DE_GT>;       // . / >
            mods = <(MOD_LSFT|MOD_RSFT)>;
        };
        slash_morph: slash_morph {
            compatible = "zmk,behavior-mod-morph";
            #binding-cells = <0>;
            bindings = <&kp DE_SLASH>, <&kp DE_QUESTION>; // / / ?
            mods = <(MOD_LSFT|MOD_RSFT)>;
        };
        // ` unshifted (dead-grave macro) / ~ shifted (dead-tilde macro)
        grave_morph: grave_morph {
            compatible = "zmk,behavior-mod-morph";
            #binding-cells = <0>;
            bindings = <&grave_dk>, <&tilde_dk>;
            mods = <(MOD_LSFT|MOD_RSFT)>;
        };
    };
```

- [ ] **Step 2 note — DE_* names used above must exist in `keys_de.h`.** Confirm before building:

```bash
grep -E 'define (DE_GRAVE|DE_TILDE|DE_CARET|DE_A_UMLAUT|DE_O_UMLAUT|DE_U_UMLAUT|DE_SZ|DE_CAPITAL_SZ|DE_AT|DE_HASH|DE_AMPS|DE_ASTRK|DE_LPAR|DE_RPAR|DE_SEMI|DE_COLON|DE_SQT|DE_DQT|DE_COMMA|DE_LT|DE_DOT|DE_GT|DE_SLASH|DE_QUESTION) ' config/keys_de.h | wc -l
```

Expected: `24` (all present). If any is missing, open `config/keys_de.h` and find its alias (e.g. `DE_QMARK` for `DE_QUESTION`) and adjust the binding.

- [ ] **Step 3: Commit and verify build (behaviors defined but not yet referenced by layers)**

```bash
git add config/sofle_choc_pro.keymap
git commit -m "Add umlaut morphs, dead-key macros, and symbol mod-morphs"
git push
gh run watch --exit-status
```

Expected: green. Unused behaviors compile fine. A failure here is almost always a typo in a `DE_*` name or a missing `#binding-cells` — read the Actions log's devicetree error, it names the offending node.

---

### Task 4: Rewrite the Default layer

**Files:**
- Modify: `config/sofle_choc_pro.keymap` — replace the `default_layer` `bindings = < ... >;` block only. Leave `display-name`, the comment art, and `sensor-bindings` as-is.

- [ ] **Step 1: Replace the default_layer bindings**

```c
            bindings = <
&grave_morph &kp N1   &n2_morph &n3_morph &kp N4    &kp N5                              &n6_morph &n7_morph &n8_morph  &n9_morph &n0_morph &grave_morph
&kp ESC      &kp Q    &kp W     &kp E     &kp R     &kp T                               &kp DE_Y  &umlaut_u &kp I      &umlaut_o &kp P     &kp BSPC
&kp TAB      &umlaut_a &umlaut_s &kp D    &kp F     &kp G                               &kp H     &kp J     &kp K      &kp L     &semi_morph &quote_morph
&kp LSHFT    &kp DE_Z &kp X     &kp C     &kp V     &kp B   &kp C_MUTE  &kp C_PLAY       &kp N     &kp M     &comma_morph &dot_morph &slash_morph &kp RSHFT
                      &kp LGUI  &kp LALT  &kp LCTRL &mo LOWER &kp RET   &kp SPACE        &mo RAISE &kp RCTRL &kp RALT   &kp RGUI
            >;
```

What changed vs. baseline (everything else is intentionally unchanged):
- `` ` `` (both corners) → `&grave_morph` (` / ~ dead-key macros)
- `2 3 6 7 8 9 0` → number-row morphs (US shifted symbols)
- `Y`→`&kp DE_Y`, `Z`→`&kp DE_Z` (automatic Y/Z swap)
- `A O U S` → umlaut morphs (normal letters; GUI → ä ö ü ß)
- `;` `'` `,` `.` `/` → punctuation morphs
- `1 4 5` stay plain `&kp N1/N4/N5` (German Shift gives `! $ %`, already correct)

- [ ] **Step 2: Commit and verify build green**

```bash
git add config/sofle_choc_pro.keymap
git commit -m "Rewrite default layer for German-OS US-feel + umlaut chord"
git push
gh run watch --exit-status
```

Expected: green. (Optional spot-check: flash and confirm `qwerty`, `y`, `z`, `@`, `Ä` via GUI+Shift+a.)

---

### Task 5: Rewrite the Lower layer

**Files:**
- Modify: `config/sofle_choc_pro.keymap` — replace the `lower_layer` `bindings` block only.

- [ ] **Step 1: Replace the lower_layer bindings**

```c
            bindings = <
&trans     &kp F1      &kp F2      &kp F3      &kp F4     &kp F5                          &kp F6      &kp F7      &kp F8      &kp F9      &kp F10     &kp F11
&grave_dk  &kp N1      &kp N2      &kp N3      &kp N4     &kp N5                          &kp N6      &kp N7      &kp N8      &kp N9      &kp N0      &kp F12
&trans     &kp DE_EXCL &kp DE_AT   &kp DE_HASH &kp DE_DLLR &kp DE_PRCNT                   &caret_dk   &kp DE_AMPS &kp DE_ASTRK &kp DE_LPAR &kp DE_RPAR &kp DE_PIPE
&trans     &kp DE_EQUAL &kp DE_MINUS &kp DE_PLUS &kp DE_LBRC &kp DE_RBRC  &trans &trans   &kp DE_LBKT &kp DE_RBKT &kp DE_SEMI &kp DE_COLON &kp DE_BSLH &trans
                       &trans      &trans      &trans     &trans          &trans &trans   &trans      &trans      &trans      &trans
            >;
```

Every symbol now emits its German-OS-correct scancode via `DE_*`. `` ` `` and `^` use the dead-key macros. Numbers/F-keys unchanged. (`DE_EXCL` == German `Shift+1` == `!`, already correct — using the explicit name keeps the row readable.)

- [ ] **Step 2: Confirm the DE_* names used here exist**

```bash
grep -E 'define (DE_EXCL|DE_DLLR|DE_PRCNT|DE_PIPE|DE_EQUAL|DE_MINUS|DE_PLUS|DE_LBRC|DE_RBRC|DE_LBKT|DE_RBKT|DE_BSLH) ' config/keys_de.h | wc -l
```

Expected: `12`. If `DE_EXCL` is absent, its alias is `DE_EXCLAMATION` (and `DE_DLLR`→`DE_DOLLAR`, `DE_PRCNT`→`DE_PERCENT`).

- [ ] **Step 3: Commit and verify build green**

```bash
git add config/sofle_choc_pro.keymap
git commit -m "Rewrite lower layer symbols for German OS"
git push
gh run watch --exit-status
```

Expected: green.

---

### Task 6: Apply Raise-layer nav tweaks

**Files:**
- Modify: `config/sofle_choc_pro.keymap` — change two keys in the `raise_layer` bindings (right-half row 2): `U` `&trans`→`&kp HOME`, `O` `&trans`→`&kp END`.

- [ ] **Step 1: Replace the raise_layer bindings**

```c
            bindings = <
&bt BT_CLR &bt BT_SEL 0 &bt BT_SEL 1 &bt BT_SEL 2 &bt BT_SEL 3 &bt BT_SEL 4                      &trans    &trans    &trans    &trans     &trans   &trans
&trans     &kp INS      &kp PSCRN    &kp K_CMENU  &trans       &trans                            &kp PG_UP &kp HOME  &kp UP    &kp END    &trans   &trans
&trans     &kp LALT     &kp LCTRL    &kp LSHFT    &trans       &kp CLCK                          &kp PG_DN &kp LEFT  &kp DOWN  &kp RIGHT  &kp DEL  &kp BSPC
&trans     &kp K_UNDO   &kp K_CUT    &kp K_COPY   &kp K_PASTE  &studio_unlock  &trans  &trans    &trans    &trans    &trans    &trans     &trans   &trans
                        &trans       &trans       &trans       &trans          &trans  &trans    &trans    &trans    &trans    &trans
            >;
```

Result (right half): `HOME` now sits above `LEFT`, `END` above `RIGHT`, alongside the existing `PG_UP`/`PG_DN`/arrow cluster. `HOME`/`END` are layout-agnostic HID codes — no `DE_*` needed.

- [ ] **Step 2: Commit and verify build green**

```bash
git add config/sofle_choc_pro.keymap
git commit -m "Add Home/End to Raise-layer nav cluster"
git push
gh run watch --exit-status
```

Expected: green.

---

### Task 7: Add the Adjust-layer numpad (right half)

**Files:**
- Modify: `config/sofle_choc_pro.keymap` — replace the `adjust_layer` bindings. Left half (BT/RGB/ext_power) stays exactly as-is; right-half `&none`s become the numpad.

- [ ] **Step 1: Replace the adjust_layer bindings**

```c
            bindings = <
&bt BT_CLR        &bt BT_SEL 0    &bt BT_SEL 1    &bt BT_SEL 2    &bt BT_SEL 3    &bt BT_SEL 4                            &none      &kp KP_SLASH &kp KP_ASTERISK &kp KP_MINUS &none        &none
&ext_power EP_TOG &rgb_ug RGB_HUD &rgb_ug RGB_HUI &rgb_ug RGB_SAD &rgb_ug RGB_SAI &rgb_ug RGB_EFF                         &none      &kp KP_N7    &kp KP_N8       &kp KP_N9    &kp KP_PLUS  &none
&none             &rgb_ug RGB_BRD &rgb_ug RGB_BRI &none           &none           &none                                   &none      &kp KP_N4    &kp KP_N5       &kp KP_N6    &kp KP_DOT   &none
&none             &none           &none           &none           &none           &none            &rgb_ug RGB_TOG &none  &kp KP_N0  &kp KP_N1    &kp KP_N2       &kp KP_N3    &kp KP_ENTER &none
                                  &none           &none           &none           &none            &none           &none  &none      &none        &none           &none
            >;
```

Numpad anchored on `K`=`KP_N5`; `KP_N0` at the `N` position (most reachable empty slot). All `KP_*` are HID numpad codes — layout-agnostic.

- [ ] **Step 2: Commit and verify build green**

```bash
git add config/sofle_choc_pro.keymap
git commit -m "Add numpad to Adjust-layer right half"
git push
gh run watch --exit-status
```

Expected: green. This is the last code task — all four matrix jobs should still produce `.uf2` artifacts.

---

### Task 8: Flash and run the test sheet on Linux (German OS)

**Files:** none (hardware verification).

- [ ] **Step 1: Set the OS keyboard layout to German**

Confirm the Linux machine's keyboard layout is **German (de)**. This is a hard prerequisite (spec §3) — every compensation assumes it.

- [ ] **Step 2: Download and flash both halves**

From the latest green Actions run, download the artifact and flash:

```bash
gh run download --name "firmware" --dir /tmp/fw   # name may differ; gh run view shows artifacts
ls /tmp/fw   # expect sofle_choc_pro_left-*.uf2 and sofle_choc_pro_right-*.uf2
```

For each half: double-tap reset → a `NICENANO`-style USB drive mounts → drag the matching `.uf2` onto it → it reboots. Flash left and right with their respective files. Reconnect Bluetooth.

- [ ] **Step 3: Run the test sheet (spec §9). Type each, confirm the on-screen result:**

```
Letters:     the quick brown fox … y z Y Z           -> y and z correct, not swapped
Shift+nums:  ! @ # $ % ^ & * ( )                       -> exactly these (^ standalone)
Punctuation: ; : ' " , < . > / ?                       -> each, unshifted & shifted
Grave/Tilde: ` ~                                        -> standalone chars, no leftover dead-key
Umlauts:     LGUI+a/o/u/s -> ä ö ü ß
             LGUI+Shift+a/o/u/s -> Ä Ö Ü ẞ
             RGUI+a/o/u/s -> ä ö ü ß
GUI control: LGUI+l (lock), LGUI+e (files)             -> system shortcuts still fire
Lower layer: ! @ # $ % ^ & * ( ) = - + { } [ ] ; : \ | ` and digits/F-keys
Raise layer: Home/End/arrows/PgUp/PgDn/Del
Adjust:      hold Lower+Raise -> numpad digits, / * - + . Enter
```

- [ ] **Step 4: Tilde decision (spec §8.2).** If `~` produced `~ ` (trailing space) or a lingering dead-key, edit `tilde_dk` in the keymap: remove `&kp SPACE` so it reads `bindings = <&macro_tap &kp DE_TILDE>;`. Re-commit, push, rebuild, reflash, retest. If `~` was correct, leave as-is.

- [ ] **Step 5: Record results.** Note any key that produced the wrong character; each is a one-line fix (swap the `DE_*` target on that key/morph). Re-run Tasks 3–7's relevant step, rebuild, reflash. Commit when the sheet passes clean.

---

### Task 9: Run the test sheet on Windows (German OS)

**Files:** none (hardware verification).

- [ ] **Step 1:** On a Windows machine set to the **German** keyboard layout, connect the keyboard via a free Bluetooth profile (Raise layer `BT1`–`BT5`).

- [ ] **Step 2:** Re-run the entire Task 8 Step 3 test sheet. Pay special attention to the dead keys (`` ` `` `~` `^`) — Windows German dead-key commit timing can differ from Linux.

- [ ] **Step 3:** Confirm `LGUI+a/o/u/s` umlauts match the user's prior AutoHotkey muscle memory, and that `Win+L`/`Win+E` still work (GUI not hijacked for non-umlaut letters).

- [ ] **Step 4:** If any character differs from Linux, it's almost always a dead-key timing/commit difference — adjust the relevant macro and reflash. Commit the final working keymap.

```bash
git add -A && git commit -m "Finalize keymap after Linux + Windows test-sheet pass"
git push
```

---

## Self-review (spec coverage)

- §5.1 Default layer — Y/Z swap (Task 4, `DE_Y`/`DE_Z`); number-row US symbols (Task 3 morphs + Task 4); right-punctuation morphs (Task 3 + 4); `` ` ``/`~` (Task 3 macros + `grave_morph`); umlaut GUI morphs incl. capitals (Task 3). ✅
- §5.2 Lower layer — all symbols retargeted to `DE_*` (Task 5). ✅
- §5.3 Dead-key macros — `grave_dk`, `tilde_dk`, `caret_dk` (Task 3); tilde-commit verified (Task 8 Step 4). ✅
- §5.4 Raise nav — Home/End added (Task 6). ✅
- §5.5 Adjust numpad — right-half numpad, `KP_DOT` per latest commit (Task 7). ✅
- §6 Architecture / §7 build-flash — Task 1 (bootstrap + CI) and Task 8 (flash). ✅
- §8 open questions — §8.1 resolved (Task 3 design note); §8.2 resolved at runtime (Task 8 Step 4). ✅
- §9 testing — Tasks 8–9. ✅
- §10 phases — map 1:1 onto Tasks 1–9. ✅

**Deviation from spec, on purpose:** the spec's §4 hand-built mod-morphs/raw-HID are replaced by vendored `DE_*` keycodes as morph targets (simpler, identical result). Number-row and punctuation still require mod-morphs (dual-function keys) — unavoidable in any approach.
