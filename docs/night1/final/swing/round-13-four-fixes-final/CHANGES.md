# Four requested traversal repairs

Runtime source: `195216591f5cd597467d097954f18b0a89c686e9`. Continued the existing round13 branch from `ecb68aad`; original Kimi checkout and earlier owner copy were preserved. No city, lighting, suit, material or feature work was added.

- **Camera loss:** fit the evaluated body rather than a single point; separate real occlusion from framing loss; account for roof lift in collision probes; anticipate a blocked held view; retain protection through the catch; couple camera placement to the already-limited angle so collision correction cannot carry the hero off-screen while yaw catches up. Collision and angle limits remain active.
- **Firing arm:** blend the complete aim direction once from a stable launch direction over the actual short strand-flight window. Evaluate arm aim once per animation update. Predict the same local pose coordinates used by the final flip correction, preventing a catch from rotating an already-aimed arm away from its anchor.
- **Catch repetition:** retain three authored terminal families (seated Throne, wide Straddle, extended Reach), hold outgoing samples while they fade, and ease the seated transition into the swing. Hand choice alone is not counted as pose variety.
- **Rotation:** align the root against the current evaluated body axis, preserve existing sway composition, settle entry before the fast tuck, and cap/integrate the first frontDouble burst with the existing angle/time budget. Counts, durations and mid-chain holds are preserved. The rate is changed in the actual integrated curve, not only in telemetry.

The corrected measurement path records final post-animation axes on the same row. Legacy comparisons are shifted only within the same case, avoiding a false cross-case spike. Raw projected checks remain published alongside true 3D axis measurements; no acceptance threshold was weakened.

## Verification boundary

The final core evidence is this folder's seven-case flips, nine-case web presses and continuous flip-chain MP4/CSV sets, captured at native1920x1080/fixed60Hz from one fingerprinted binary. See PRECRITIC_GATE.md for completion and exact failures; CAMERA_VERIFICATION.md and MOTION_VERIFICATION.md record targeted evidence. The previous folder `round-13-four-fixes` contains the initial candidate and its regression findings. Its ordinary-swing replay is prior-build regression evidence, not a final same-build capture.

The actual C++ flip harness passes416variants (including rate/angle parity, endpoints, counts, holds and pose families); four focused measurement tests pass. The local owner artifact requires this Mac's installed Unreal Engine5.8. Scripted offscreen verification does not establish manual controls, realtime FPS or owner acceptance. Native visual critique and relocated artifact smoke are recorded separately when complete.
