# Four requested fixes — preserved checkpoint

Final runtime source: `2db142143bc60709a1db726a445d17aee2a57aca`. Branch: `codex/round13-closeout-20261011`. This bounded pass is complete; no unattended refinement continues.

- **Camera loss:** repaired the off-screen losses in the flip/catch routes and the separately discovered rooftop startup. The independent camera check confirms that the former complete escapes are removed. Two native frames (about 0.033 seconds) still partially hide the lower body behind a parapet while the upper body stays visible. Fast recovery and broader camera limits are documented separately.
- **Firing arm:** the original 131.6-degree single-frame snap becomes a distributed reach with a 27.48-degree largest measured step. The web follows the raised hand, originates at the current palm, and retains the original physical arrival and catch times. The independent [final arm review](FINAL_REACH.md) marks the actual firing arm FIXED visually in the inspected roof-launch window. The nonfiring arm still lifts quickly. Visible web flight is faster—about 45 ms in the roof case—so the older minimum-flight-duration target is not claimed passed.
- **Catch repetition:** at least three distinct whole-body endings appear across six inspected catches, including compact, extended and wide split silhouettes. The independent critic confirms the variety. Turn counts and open holds are preserved; all six primary catches pass the existing transition-motion limits.
- **Rotation:** corrected current-pose alignment and the actual front-double rate curve. All seven primary projected peaks are below 800 degrees/second on the existing finite-window check; front-double measures 773 projected and 796 in 3D. The late barani projected spike remains at 1136 while its 3D body-axis peak is 686; the raw checker failure is retained. A single-frame front-double measurement reaches 801.8, so the finite-window result is not an instantaneous bound at every sampling interval.

## Verification and build boundaries

The full 17-case, 5,246-frame suite in this folder belongs to runtime `19521659`. Its review exposed two further issues, which received narrow closing patches:

- Camera `4220b33b`: three targeted cases in [camera verification](../round-13-four-fixes-camera-closeout/VERIFICATION.md).
- Launch timing `5b7b9074`: roof launch, cancel and re-press checks.
- Final `2db14214`: smoother reach profile, with a 526-row roof/re-press replay in [final reach verification](../round-13-four-fixes-reach-closeout/VERIFICATION.md).

The closing replays confirm unchanged checked physics, input, flip-state and catch timing. The older full suite is not presented as a complete rerun of the final binary. The actual C++ flip harness passed 416 variants, and four focused measurement tests passed. All source changes built successfully. Original independent reports remain unchanged; later delta reports document the specific corrections.

## Preserved owner copy

Launch `/Users/midir/SpiderMan-FourFixes-OwnerPlaytest-20261012/Play.command` on this Mac with Unreal Engine 5.8 installed. The final copy launched, rendered two inspected native 1920×1080 screenshots and exited cleanly. All 51,169 runtime manifest entries matched after the run. See [final runtime verification](../round-13-four-fixes-reach-closeout/OWNER_PLAYTEST.json).

Physical controls, real-time FPS and owner acceptance remain unverified. The original Kimi checkout and earlier owner copy are preserved. Source, reports, native clips and review outcomes are on the task branch; private reference footage and comparison videos are excluded.
