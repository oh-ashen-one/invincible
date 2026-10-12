# Project history and evidence

This page records the original creation, our additions, and the verification behind the current Unreal continuation. Commit links are immutable; branch links identify where work continues.

## Original creation

The repository is a GitHub fork of [xikhar/spiderbench](https://github.com/xikhar/spiderbench), by Shikhar. The retained [initial commit](https://github.com/oh-ashen-one/spider-man-2/commit/9c223685b5d3b6ddb2365e76284f193525c1f072) and [upstream update](https://github.com/xikhar/spiderbench/commit/4361e15951d98519ba515da3ec31d3e537cb4a10) precede this fork's enhancements. The [original README](https://github.com/xikhar/spiderbench/blob/4361e15951d98519ba515da3ec31d3e537cb4a10/README.md) describes a Claude-written browser game under human direction; the update's commit message credits Claude Opus 5.5.

The original foundation already included web swinging, wall running, zipping, a procedural Manhattan-style city, traffic, pedestrians and a Three.js rendering pipeline. Those are upstream contributions. Our [attribution commit](https://github.com/oh-ashen-one/spider-man-2/commit/a0dbe98abe30581b3af11e547068fbc72960c4e8) records that distinction, and [LICENSE](../LICENSE) preserves the original author's terms.

## What this fork changed

| Stage | Concrete change | Commit proof |
|---|---|---|
| Browser traversal | Rigid-web velocity projection and artificial-tension swing; softer facade interaction | [7a892769](https://github.com/oh-ashen-one/spider-man-2/commit/7a8927698bfbb4872d38459893252b48150ad848) · [331e3fea](https://github.com/oh-ashen-one/spider-man-2/commit/331e3fea1a70e16759ac5d685e5e3f893ef88ac1) |
| Browser environments | Water shading, waves, foam, underwater effects, spray and caustics; trees/grass and destruction | [1524f7bc](https://github.com/oh-ashen-one/spider-man-2/commit/1524f7bcb9c0fca06d44670fb3406ff3dee79799) · [c38c3ced](https://github.com/oh-ashen-one/spider-man-2/commit/c38c3ced5a69fab001fa01f9f37c21de2f41e749) · [before/after water audit](https://github.com/oh-ashen-one/spider-man-2/commit/4a7f10dd92298eafa2b0a56228468900f1309ae9) |
| Custom assets | Hero suits, 20-citizen browser crowd, textured props and animals | [browser integration](https://github.com/oh-ashen-one/spider-man-2/commit/2901735f74aed67293931f5ca60bc42847ac3372) |
| Unreal foundation | UE 5.8 project and native C++ module | [f65d4ea9](https://github.com/oh-ashen-one/spider-man-2/commit/f65d4ea94698aad690c418a85bc5ce45624e03da) · [3aa5749d](https://github.com/oh-ashen-one/spider-man-2/commit/3aa5749d113ccf7e54a58e9e435bea7da80e9bab) |
| Unreal city and traversal | Geometry/material export and import; native traversal, chase camera and skeletal animation | [11261555](https://github.com/oh-ashen-one/spider-man-2/commit/11261555c0c05faf350878a05e7f7f4a6c2fb7f9) · [0f1c3874](https://github.com/oh-ashen-one/spider-man-2/commit/0f1c3874237f8bc74e5da01269740191436e644d) · [d5d6b82f](https://github.com/oh-ashen-one/spider-man-2/commit/d5d6b82f3151c560715ab52693870164ef0293b0) |
| Unreal presentation | Island showcase assembly and translation of the author's facade/night-light behavior | [3a7650b3](https://github.com/oh-ashen-one/spider-man-2/commit/3a7650b3ed5d09d1cccc1192212f8f4a2f643e90) · [c10bcd5f](https://github.com/oh-ashen-one/spider-man-2/commit/c10bcd5fd62bbb4c429d4bdbfb581c8e131eda55) · [d2eee0a7](https://github.com/oh-ashen-one/spider-man-2/commit/d2eee0a79714b482c9dbf1ba7991b330d5afd9d0) |
| Flip development | Multi-turn trick programs and held poses integrated into traversal | [2d9fc4af](https://github.com/oh-ashen-one/spider-man-2/commit/2d9fc4af132dd6c95a8e36ae96613e64deed074f) |
| Current repairs | Camera containment, firing-arm reach, catch variety, pose alignment and rotation-rate corrections | [final runtime](https://github.com/oh-ashen-one/spider-man-2/commit/2db142143bc60709a1db726a445d17aee2a57aca) · [completed handoff](https://github.com/oh-ashen-one/spider-man-2/commit/9ad990d6ab482d5b1946b0bc9a60244eac8e320a) |

## Kimi preservation and continuation

The interrupted Kimi session was preserved at [4f2a10da](https://github.com/oh-ashen-one/spider-man-2/commit/4f2a10daa1281db9c6816028544b104449bd9eb1). That commit is an ancestor of the enhanced checkpoint [9ad990d6](https://github.com/oh-ashen-one/spider-man-2/commit/9ad990d6ab482d5b1946b0bc9a60244eac8e320a); there are 44 subsequent commits in that continuation. The current branch contains the saved starting point and the later enhancements together. The separate preservation branch is an archive of the starting state.

- **Use this:** [integrated enhanced branch](https://github.com/oh-ashen-one/spider-man-2/tree/codex/round13-closeout-20261011).
- **Historical backup:** [Kimi preservation branch](https://github.com/oh-ashen-one/spider-man-2/tree/codex/preserve-kimi-spiderman-20261011).
- **Runtime code:** [2db14214](https://github.com/oh-ashen-one/spider-man-2/commit/2db142143bc60709a1db726a445d17aee2a57aca).
- **What was preserved:** [preservation record](https://github.com/oh-ashen-one/spider-man-2/blob/9ad990d6ab482d5b1946b0bc9a60244eac8e320a/docs/night1/final/swing/round-13/PRESERVATION.md).

## Verification records

| Record | Build / scope | Evidence |
|---|---|---|
| Browser before the port | Existing enhanced browser baseline; not untouched upstream | [capture method and index](https://github.com/oh-ashen-one/spider-man-2/blob/9ad990d6ab482d5b1946b0bc9a60244eac8e320a/docs/night1/baseline/README.md) |
| Earlier Unreal repair baseline | Round-13 closeout before the four requested fixes | [recordings and reports](https://github.com/oh-ashen-one/spider-man-2/blob/9ad990d6ab482d5b1946b0bc9a60244eac8e320a/docs/night1/final/swing/round-13-closeout/PRECHECK.md) |
| Full traversal suite | `19521659`: 17 cases, 5,246 frames across flips and web presses | [technical gate](https://github.com/oh-ashen-one/spider-man-2/blob/9ad990d6ab482d5b1946b0bc9a60244eac8e320a/docs/night1/final/swing/round-13-four-fixes-final/PRECRITIC_GATE.md) |
| Camera closeout | `4220b33b`: roof startup plus two difficult flip/catch cases | [verification](https://github.com/oh-ashen-one/spider-man-2/blob/9ad990d6ab482d5b1946b0bc9a60244eac8e320a/docs/night1/final/swing/round-13-four-fixes-camera-closeout/VERIFICATION.md) · [independent camera review](https://github.com/oh-ashen-one/spider-man-2/blob/9ad990d6ab482d5b1946b0bc9a60244eac8e320a/docs/night1/final/swing/round-13-four-fixes-final/CAMERA_DELTA.md) |
| Launch synchronization | `5b7b9074`: roof, cancel and re-press | [verification](https://github.com/oh-ashen-one/spider-man-2/blob/9ad990d6ab482d5b1946b0bc9a60244eac8e320a/docs/night1/final/swing/round-13-four-fixes-launch-closeout/VERIFICATION.md) |
| Final reach | `2db14214`: 526-row roof/re-press replay | [verification](https://github.com/oh-ashen-one/spider-man-2/blob/9ad990d6ab482d5b1946b0bc9a60244eac8e320a/docs/night1/final/swing/round-13-four-fixes-reach-closeout/VERIFICATION.md) · [independent final arm verdict](https://github.com/oh-ashen-one/spider-man-2/blob/9ad990d6ab482d5b1946b0bc9a60244eac8e320a/docs/night1/final/swing/round-13-four-fixes-final/FINAL_REACH.md) |
| Relocated local runtime | Final source launched, two 1080p screenshots inspected, clean exit, 51,169 manifest files verified | [machine-readable runtime record](https://github.com/oh-ashen-one/spider-man-2/blob/9ad990d6ab482d5b1946b0bc9a60244eac8e320a/docs/night1/final/swing/round-13-four-fixes-reach-closeout/OWNER_PLAYTEST.json) |
| Reproducible checks | 416 C++ flip variants and four measurement tests | [validation record](https://github.com/oh-ashen-one/spider-man-2/blob/9ad990d6ab482d5b1946b0bc9a60244eac8e320a/docs/night1/final/swing/round-13-four-fixes-final/VALIDATION.json) · [C++ harness](https://github.com/oh-ashen-one/spider-man-2/blob/9ad990d6ab482d5b1946b0bc9a60244eac8e320a/tools/final/swing/flip_math/run.py) |

The metrics use the definitions in the linked reports. For example, the front-double 796°/s result uses the existing finite-window 3D body-axis measurement; a single-frame reading reaches 801.8°/s. A later barani retains a projected-axis checker failure despite a lower 3D body-axis rate. These are disclosed in [motion verification](https://github.com/oh-ashen-one/spider-man-2/blob/9ad990d6ab482d5b1946b0bc9a60244eac8e320a/docs/night1/final/swing/round-13-four-fixes-final/MOTION_VERIFICATION.md).

The full suite predates the final two closing animation/camera refinements. It is not relabeled as a full final-binary rerun. Original independent reports remain unchanged, and later targeted reports show how their findings were addressed. Native recordings, source checks and local launch verification do not establish universal real-time performance or owner acceptance.

## Reusable sources, generated outputs and rights

The Unreal source, configuration, exporters and builders are committed. Generated `.uasset`/`.umap` content and compiled binaries are excluded; read [the content policy](https://github.com/oh-ashen-one/spider-man-2/blob/9ad990d6ab482d5b1946b0bc9a60244eac8e320a/unreal/WebHomage/CONTENT.md). The verified local owner copy is an installed-engine playtest, not a downloadable standalone release.

Private commercial-game reference footage is excluded. The images and gameplay videos linked in the README are captures of this repository's own browser/Unreal work. Original and third-party attribution remains in [LICENSE](../LICENSE), [DISCLAIMER.md](../DISCLAIMER.md) and [THIRD_PARTY.md](../THIRD_PARTY.md).
