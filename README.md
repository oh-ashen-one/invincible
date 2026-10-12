# Spider-Man 2 — Spiderbench Enhanced & Unreal Engine Port

A non-commercial web-swinging homage built from **[Spiderbench](https://github.com/xikhar/spiderbench), originally created by Shikhar**. This fork extends the browser game and carries that work into **Unreal Engine 5.8**, with native traversal, richer environments, original suit work, and focused improvements to flips, catches, firing animations and camera framing.

**[Open the latest integrated enhancement branch →](https://github.com/oh-ashen-one/spider-man-2/tree/codex/round13-closeout-20261011)** · [Project history & proof](docs/PROJECT_HISTORY.md) · [Unreal setup](docs/UNREAL_PLAYTEST.md) · [Latest verified results](https://github.com/oh-ashen-one/spider-man-2/blob/9ad990d6ab482d5b1946b0bc9a60244eac8e320a/docs/night1/final/swing/round-13-four-fixes-final/RESULTS.md)

> **Which version should I use?** The current Unreal continuation is **`codex/round13-closeout-20261011`**. It includes the preserved Kimi starting point and the subsequent enhancements. The preservation branch is a historical backup, not a separate version you need to combine manually. `main` retains the browser code line; this overview is published on both branches.

![The enhanced Unreal traversal checkpoint, captured from the running game](https://raw.githubusercontent.com/oh-ashen-one/spider-man-2/9ad990d6ab482d5b1946b0bc9a60244eac8e320a/docs/night1/final/swing/round-13-four-fixes-reach-closeout/staged-smoke_00_t003.0.png)
*Actual Unreal gameplay capture from the October 12 checkpoint, using the Tessera suit.*

## Original creation and credit

The original game belongs to **Shikhar / [xikhar](https://github.com/xikhar)**. Upstream describes Spiderbench as a Claude-written browser game developed under human direction. Its city, original traversal systems, rendering pipeline and assets are the foundation of this project.

That origin is preserved in Git: [initial creation commit `9c223685`](https://github.com/oh-ashen-one/spider-man-2/commit/9c223685b5d3b6ddb2365e76284f193525c1f072), [upstream update `4361e159`](https://github.com/xikhar/spiderbench/commit/4361e15951d98519ba515da3ec31d3e537cb4a10), and the [original README at that starting point](https://github.com/xikhar/spiderbench/blob/4361e15951d98519ba515da3ec31d3e537cb4a10/README.md). The upstream update credits Claude Opus 5.5 as a co-author. Our [first attribution notice](https://github.com/oh-ashen-one/spider-man-2/commit/a0dbe98abe30581b3af11e547068fbc72960c4e8) explicitly identifies the fork and its original author.

**Our contribution is the enhancement and porting work described below.** We retain the original attribution and [LICENSE](LICENSE).

## What we added and enhanced

| Area | Work in this fork | Source or recorded proof |
|---|---|---|
| **Swinging and traversal** | Refined real-anchor swinging and facade interaction, then ported the custom traversal state machine and chase camera to native C++. | [Swing dynamics](https://github.com/oh-ashen-one/spider-man-2/commit/7a8927698bfbb4872d38459893252b48150ad848) · [C++ traversal port](https://github.com/oh-ashen-one/spider-man-2/commit/0f1c3874237f8bc74e5da01269740191436e644d) |
| **Unreal Engine 5.8 port** | Added the WebHomage C++ project, procedural-city export/import pipeline, Unreal materials and shaders, skeletal character animation, reproducible builders and gameplay captures. | [Port scaffold](https://github.com/oh-ashen-one/spider-man-2/commit/f65d4ea94698aad690c418a85bc5ce45624e03da) · [City/material pipeline](https://github.com/oh-ashen-one/spider-man-2/commit/11261555c0c05faf350878a05e7f7f4a6c2fb7f9) · [Native animation](https://github.com/oh-ashen-one/spider-man-2/commit/d5d6b82f3151c560715ab52693870164ef0293b0) |
| **City and visual presentation** | Expanded island/showcase assembly, foliage and terrain integration; translated the original author's facade and night-light models into Unreal and refined exposure, atmosphere and presentation. | [Island showcase](https://github.com/oh-ashen-one/spider-man-2/commit/3a7650b3ed5d09d1cccc1192212f8f4a2f643e90) · [Night-light port](https://github.com/oh-ashen-one/spider-man-2/commit/d2eee0a79714b482c9dbf1ba7991b330d5afd9d0) · [Facade shader port](https://github.com/oh-ashen-one/spider-man-2/commit/c10bcd5fd62bbb4c429d4bdbfb581c8e131eda55) |
| **Browser water and foliage** | Added water shading, waves, foam, wakes, splashes, underwater effects, caustics and lens droplets; improved procedural trees and grass. These are documented browser-stage additions, not a claim of identical feature parity in Unreal. | [Water implementation and audit](https://github.com/oh-ashen-one/spider-man-2/blob/9ad990d6ab482d5b1946b0bc9a60244eac8e320a/WATER-EFFECTS.md) · [Foliage/destruction work](https://github.com/oh-ashen-one/spider-man-2/blob/9ad990d6ab482d5b1946b0bc9a60244eac8e320a/PINATA-AND-TREES.md) |
| **Characters, suits and props** | Added custom suit concepts and models, a 20-citizen browser crowd, street props and animals, followed by an Unreal character/suit pipeline and original hero suit work. | [Browser asset integration](https://github.com/oh-ashen-one/spider-man-2/commit/2901735f74aed67293931f5ca60bc42847ac3372) · [Unreal suit integration](https://github.com/oh-ashen-one/spider-man-2/commit/8011219b6b9c1e22b4435de9fd44eec6fc0d91a7) |
| **Flips, catches and camera** | Developed multi-turn trick programs and readable open holds, diversified catch silhouettes, corrected rotation spikes, removed the reported off-screen camera losses, and synchronized the firing arm with the visible web. | [Final repair report](https://github.com/oh-ashen-one/spider-man-2/blob/9ad990d6ab482d5b1946b0bc9a60244eac8e320a/docs/night1/final/swing/round-13-four-fixes-final/RESULTS.md) · [Independent visual review](https://github.com/oh-ashen-one/spider-man-2/blob/9ad990d6ab482d5b1946b0bc9a60244eac8e320a/docs/night1/final/swing/round-13-four-fixes-final/FINAL_REACH.md) |
| **Verification and continuity** | Added repeatable scenario recordings, telemetry, image checks, independent review, mathematical checks, reproducible asset builders and explicit build/handoff records. | [Review protocol](https://github.com/oh-ashen-one/spider-man-2/blob/9ad990d6ab482d5b1946b0bc9a60244eac8e320a/docs/night1/final/swing/round-13-four-fixes-final/REVIEW_PROTOCOL.md) · [Rolling handoff](https://github.com/oh-ashen-one/spider-man-2/blob/9ad990d6ab482d5b1946b0bc9a60244eac8e320a/HANDOFF.md) |

## Before and after: browser stage to Unreal

<table>
<tr><th>Browser baseline before the Unreal port</th><th>Enhanced Unreal checkpoint</th></tr>
<tr><td><img src="https://raw.githubusercontent.com/oh-ashen-one/spider-man-2/9ad990d6ab482d5b1946b0bc9a60244eac8e320a/docs/night1/baseline/stills/swing.jpg" width="480" alt="Recorded browser-stage web swing"></td><td><img src="https://raw.githubusercontent.com/oh-ashen-one/spider-man-2/9ad990d6ab482d5b1946b0bc9a60244eac8e320a/docs/night1/final/swing/round-13-four-fixes-reach-closeout/staged-smoke_00_t003.0.png" width="480" alt="Recorded Unreal traversal with Tessera suit"></td></tr>
</table>

The browser image is the [documented pre-port baseline](https://github.com/oh-ashen-one/spider-man-2/blob/9ad990d6ab482d5b1946b0bc9a60244eac8e320a/docs/night1/baseline/README.md), which already includes our early browser enhancements. The Unreal image is a later native capture. These show the engine transition at different camera positions, not a matched performance benchmark or an untouched-upstream comparison.

### Browser water and foliage comparisons

| Earlier water | Enhanced water |
|---|---|
| ![Earlier East River water](https://raw.githubusercontent.com/oh-ashen-one/spider-man-2/9ad990d6ab482d5b1946b0bc9a60244eac8e320a/docs/water/before/eastRiver.jpg) | ![Enhanced East River shading and wakes](https://raw.githubusercontent.com/oh-ashen-one/spider-man-2/9ad990d6ab482d5b1946b0bc9a60244eac8e320a/docs/water/after/eastRiver.jpg) |

| Earlier park foliage | Enhanced park foliage |
|---|---|
| ![Earlier park trees](https://raw.githubusercontent.com/oh-ashen-one/spider-man-2/9ad990d6ab482d5b1946b0bc9a60244eac8e320a/docs/trees/parkHigh_before.jpg) | ![Enhanced park trees](https://raw.githubusercontent.com/oh-ashen-one/spider-man-2/9ad990d6ab482d5b1946b0bc9a60244eac8e320a/docs/trees/parkHigh_after.jpg) |

These are existing committed captures. Implementation details and third-party credits are in [WATER-EFFECTS.md](https://github.com/oh-ashen-one/spider-man-2/blob/9ad990d6ab482d5b1946b0bc9a60244eac8e320a/WATER-EFFECTS.md), [PINATA-AND-TREES.md](https://github.com/oh-ashen-one/spider-man-2/blob/9ad990d6ab482d5b1946b0bc9a60244eac8e320a/PINATA-AND-TREES.md) and [THIRD_PARTY.md](THIRD_PARTY.md).

## Before and after: the latest traversal repairs

| Problem | Before | What changed / evidence |
|---|---|---|
| **Camera losing the hero** | Off-screen escapes around rooftop starts, flip catches and collision recovery. | Full-body framing and collision-aware camera placement, plus a bounded startup guard. [Earlier press footage](https://github.com/oh-ashen-one/spider-man-2/blob/9ad990d6ab482d5b1946b0bc9a60244eac8e320a/docs/night1/final/swing/round-13-closeout/s2_press_variety.mp4) → [camera closeout footage](https://github.com/oh-ashen-one/spider-man-2/blob/9ad990d6ab482d5b1946b0bc9a60244eac8e320a/docs/night1/final/swing/round-13-four-fixes-camera-closeout/s2_press_variety.mp4). |
| **Abrupt firing arm** | A measured **131.6°** single-frame step in the roof-launch case. | A distributed reach with a **27.48°** largest measured step; the visible web follows the raised hand while original physical arrival/catch times remain. [Earlier launch](https://github.com/oh-ashen-one/spider-man-2/blob/9ad990d6ab482d5b1946b0bc9a60244eac8e320a/docs/night1/final/swing/round-13-closeout/s2_press_variety.mp4) → [final roof/re-press replay](https://github.com/oh-ashen-one/spider-man-2/blob/9ad990d6ab482d5b1946b0bc9a60244eac8e320a/docs/night1/final/swing/round-13-four-fixes-reach-closeout/s2_press_variety.mp4). |
| **Repetitive catch endings** | Endings repeatedly returned to similar narrow silhouettes. | At least **three distinct whole-body silhouettes across six inspected catches**: compact, extended and wide split. [Before](https://github.com/oh-ashen-one/spider-man-2/blob/9ad990d6ab482d5b1946b0bc9a60244eac8e320a/docs/night1/final/swing/round-13-closeout/s3b_flip_cases.mp4) → [after](https://github.com/oh-ashen-one/spider-man-2/blob/9ad990d6ab482d5b1946b0bc9a60244eac8e320a/docs/night1/final/swing/round-13-four-fixes-final/s3b_flip_cases.mp4) · [independent verdict](https://github.com/oh-ashen-one/spider-man-2/blob/9ad990d6ab482d5b1946b0bc9a60244eac8e320a/docs/night1/final/swing/round-13-four-fixes-final/CRITIC.md). |
| **Rotation spikes** | An intermediate front-double capture measured about **827°/s** in 3D on the existing finite-window check. | About **796°/s** after the curve/alignment correction, with turn counts and open holds retained. [Intermediate recording](https://github.com/oh-ashen-one/spider-man-2/blob/9ad990d6ab482d5b1946b0bc9a60244eac8e320a/docs/night1/final/swing/round-13-four-fixes/s3_flip_chain.mp4) → [corrected recording](https://github.com/oh-ashen-one/spider-man-2/blob/9ad990d6ab482d5b1946b0bc9a60244eac8e320a/docs/night1/final/swing/round-13-four-fixes-final/s3_flip_chain.mp4) · [measurement definitions](https://github.com/oh-ashen-one/spider-man-2/blob/9ad990d6ab482d5b1946b0bc9a60244eac8e320a/docs/night1/final/swing/round-13-four-fixes-final/MOTION_VERIFICATION.md). |

**Evidence boundaries matter.** The full 17-case suite is build `19521659`; the subsequent camera, launch and final reach patches have separately labeled targeted replays. The verified runtime source is **`2db14214`**, preserved with reports at **`9ad990d6`**. Read the [complete evidence index](docs/PROJECT_HISTORY.md#verification-records) for the build-by-build record.

The remaining limits are recorded too: brief partial lower-body occlusion behind a parapet, faster visible web extension in the final firing-arm fix, and broader quality checks that do not all pass. The videos include fixed-step capture; **60 Hz footage is not proof of real-time 60 FPS**. The final local checkpoint compiled, launched and rendered successfully, but the reports do not claim universal controller, performance or reference-quality acceptance.

## Run or inspect the project

### Browser version

Use Node.js 20.19+ or 22.12+ and a WebGL2-capable browser:

```bash
git clone https://github.com/oh-ashen-one/spider-man-2.git
cd spider-man-2
npm ci
npm run dev
```

`npm run build` creates the browser production build. Press **H** in-game for its controls.

### Latest Unreal continuation

```bash
git clone --branch codex/round13-closeout-20261011 https://github.com/oh-ashen-one/spider-man-2.git
```

Read [Unreal setup and playtest controls](docs/UNREAL_PLAYTEST.md). This is a source-and-builder project: generated Unreal content and compiled binaries are not bundled in the Git checkout. The verified owner checkpoint uses the installed Unreal Engine 5.8 runtime on a Mac Studio.

Core DualSense controls: **left stick** move, **right stick** camera, **R2** swing, **Cross** jump, **Square** air trick, **Triangle** zip, **Circle** drop, and **Options** pause/resume.

## Credits and license

- Original Spiderbench: **Shikhar / xikhar**, with the upstream AI-assisted creation credit preserved above.
- Enhancements and Unreal continuation: this `oh-ashen-one/spider-man-2` fork and its recorded contributors/history.
- Water, foliage and destruction adaptations include work by **Daniel Greenheck / DRG Software Solutions** and **Evan Wallace**; see [THIRD_PARTY.md](THIRD_PARTY.md) for the exact sources and licenses.

This is an **unofficial, non-commercial fan homage**. It is not affiliated with or endorsed by Marvel, Disney, Sony Interactive Entertainment or Insomniac Games. The original source-available restrictions remain in [LICENSE](LICENSE); see also [DISCLAIMER.md](DISCLAIMER.md).
