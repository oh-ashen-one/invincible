# Director plan — Night 2 wave (Fable 5.1 high, 2026-10-01 01:40 EDT)

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.

Evidence read: HANDOFF.md, NIGHT1.md, model-ledger.json (47 rounds), progress.json (48 critic rows), latest critic per piece on its branch (traversal r17, perf r6, characters r10, city r9, life r2, combat r3, look r3), the seven piece HANDOFFs (in-flight r18/r7/r11/r10/r3/r4/r4). Owner plays the merged build ~09:30–10:30; last new round launches **07:30**, last critic done **08:30**, merge + headless rebuild 08:30–09:30. GPU cap 2, one UnrealEditor running now, no PAUSED.

## 1. Model per piece (next rounds) — 9 Opus / 6 Sonnet rounds = 60 % Opus

| Piece | Running | Next round(s) → model | Ledger evidence (one line) |
|---|---|---|---|
| P3 Traversal | r18 Opus | **r19 Opus 5.5 high** (only if r18 flips < 7) | Opus r11/r14/r15/r17 all avg 6.17; the one Sonnet engineering round (r16) regressed flips and sky (79 % → 2 %, not merged); Sonnet r13 was fine only as render/verify on Opus code. |
| F Perf | r7 Opus | **r8 Opus 5.5 high** (only if r7 passes the look gate) | Sonnet r1–r3 5.8/5.5/5.4 with voided look; Opus r4 7.2 APPROACHES; r5/r6 5.2 because the critic voided foliage loss — the remaining p95 problem is a CPU/RT-sync diagnosis, not content. |
| P5 Combat | r4 Opus (capture queued) | **r5 Opus 5.5 high** | Opus-only piece, monotonic 3.2 → 4.2 → 4.6; every gap is C++ FX/animation/camera. Ledger is missing the r2/r3 rows — orchestrator records them (Opus, [4,4,5,4,4], [5,5,5,4,4]). |
| P2 Characters | r11 Opus | **r12 Sonnet 5.5 xhigh** (hair assets in Blender, collar wedge; mechanical) | Sonnet r8–r10 flat at 5.0 ×3 with IQ 4 twice; the fight choreography (Opus r11) is the judgment work, the hair/collar is asset work Sonnet has done well (r6 seams 1035 → 0). |
| P1 City | r10 Sonnet | **r11 Sonnet 5.5 xhigh** (multi-gap: S8 glass, S6 curb/steps clipping, white roof props, car clearcoat) | Sonnet r4–r9 steady 4.2 → 4.8 with one spec line fixed per round and no regressions; Opus r1–r3 2.8–3.8 on the harder early layers. Keep the converging builder. |
| P4 Look | r4 Opus | **r5 Sonnet 5.5 xhigh** (preset sweep with its own capture_tour/sweep_report tools) | Sonnet r1–r3 3.3 → 4.3 → 4.7, built the live-tuning tools; r4 (Opus) only needs to stop the golden over-correction (§3d). |
| P6 Life | r3 Sonnet (renders) | **r4 Sonnet 5.5 xhigh** (if GPU time remains) | Sonnet r1 → r2 3.2 → 4.6 (peds 2 → 5), detector-driven population tuning; no engineering gap left in its own files. |
| Integration | — | **Morning regression playtest: Opus 5.5 high** | Cross-piece judgment (G in PLAN-wave2, never run yet). |

Critics: every round, fresh blind Opus 5.5 high, never skipped. No Fable builds.

## 2. Priority order and rounds before the cut-off

GPU FIFO priority when holds queue (20–60 min per hold tonight): **traversal > perf > combat > characters > city > look > life**. Iteration captures at 1080p; 4K only for the final pack. Perf exclusive sessions only when the FIFO is empty of traversal work.

1. **Traversal**: r18 + r19 (2). Owner's top priority; it takes the first slot every time.
2. **Perf**: r7 + r8 (2). r8 only if r7 is look-gated clean; otherwise r7 ends by naming the preset that ships (§4).
3. **Combat**: r4 + r5 (2). r5 = combat-cam opening (pitch 15–25° down, ≤15 % dark pixels), finisher cut + 0.3× slow-mo, snap @14.42.
4. **Characters**: r11 + r12 (2). r12 only if r11 leaves a mechanical hair/collar item.
5. **City**: r10 + r11 (2).
6. **Look**: r4 + r5 (2).
7. **Life**: r3 + r4 (1–2). r4 is dropped first if the FIFO is behind at 06:00.

Nothing launches after 07:30. A round whose critic cannot finish by 08:30 is not merged; its branch is pushed and left for day 3.

## 3. Stalls and oscillations, one directive each

- **a) Traversal flips (r15 7 → r16 6 → r17 6, camera 5 → 6)**. Each round fixes one trick property and loses another (r16 lost sky, r17 froze the split). Directive: **TC-A..TC-K are frozen as pass/keep; r18/r19 touch pose curves only.** Pass = `pose.py` 0 slow samples on f1–f5 AND flips ≥ 7 AND no TC line regresses. No camera edits in these rounds.
- **b) Perf vs look (r4 7.2 → r5 5.2 → r6 5.2)**. The builder trades foliage for p95; the critic voids it; the fps number is then void too. Directive: **`look_gate.py` PASS (S1 SSIM ≥ 0.97, S2/S7 foliage restored) is a precondition for recording any perf number**; the p95 work follows the critic's instrument (RHI/render-thread wait stats in the CSV, no Insights) at the frame-time-minus-GPU gap, not further GPU cuts. r7's finding that the gap also appears on static S2 is consistent with that: find the sync, don't cut content.
- **c) Characters image-quality plateau (5.0 × 3 rounds, IQ 4 in r9 and r10)**. Each patch adds a new 4K defect (r10's beard "dark card" became the critic's flat card). Directive: **one hair asset per head, authored in Blender, no patch cards; the builder runs the critic's 4K crop checks (seam ≤ 40 px, no card ≥ 20 px, no skin blob ≥ 15×15) before packing.**
- **d) Look golden over-correction (r2 "sepia, no cool fill" → r3 "lifted, flat, no sun/shade split")** and a **cross-piece conflict on the S4 far band**: city r10 is darkening the far strip (`FarGain`, C13 now −42.4) while look r3 asks for it to rise to 15–32 Y below the sky. Two owners move the same pixels. Directive: **look owns far-band luma (fog/aerial perspective); city owns albedo ≤ 0.5 and silhouette (T1/T2) only, and C13 is measured after look's preset, not tuned with FarGain.** Golden must satisfy both spec sides at once: p5 Y ≤ 12 AND B−R ≥ −55 (dark but cool shadows), sun/shade pair ratio ≥ 3 on S1/S5/S6.
- **e) Life**: the r2 critic's "lower the camera / cars 28 px" is P3's camera, not P6's. Directive: life is scored only on counts at the r17 traversal camera as is; no camera edits in `/Game/Life`.
- Combat is not oscillating (monotonic; each FX fix overshoots once, r4 already uses an additive burst with the Sobel ≥ 60 % test). Keep going.

## 4. Morning acceptance checklist (orchestrator, 08:30–09:30; nothing to `main`, no window, no publish)

1. **Merge decisions (only with its critic on the branch; no axis below the merged round's):** traversal r17 now (no axis < 6, all TC lines pass; r15's camera was 5), then r18/r19 on top only if flips ≥ 7 and no TC regression · perf: ship the r5 preset unless r7/r8 passes `look_gate.py` AND life-on p50 ≥ 60 fps · characters r11 if IQ ≥ 5 with the r10 fight kept, else r10 minus the beard card · combat r4 if impact ≥ 6 and the Tessera suit shows (no copied emblem) · city r10 if T1 ≥ 12 px, T2 ≤ 10 % and C11–C15 pass · look r4 if no axis drops below r3 · life r3 if swing samples reach ≥ 15 near-sidewalk pedestrians and traffic ≥ 5.
2. `record_round.py` for every judged round (incl. the missing combat r2/r3 rows); regenerate and republish the progress page.
3. Headless rebuild under `gpu_slot.sh` from the integration branch: `build_manhattan.py` → `build_water.py` → `build_life.py` → `build_combat.py --steps combat` (if combat merged). Zero build errors in the logs.
4. Verify on the rebuilt map: (a) 30 s scripted route: 0 fall-through / T-pose / stuck; (b) one exclusive perf session, 4K output, life ON, honest internal res disclosed in HANDOFF (p50/p95 reported whatever they are); (c) `look_gate.py` on S1/S2/S7 PASS; (d) OCR brand scan of the final stills: no spider emblem, no "NYC TAXI", no "…ON BURGER" / "POP THE SUMM…" billboards (critic r17 flagged these; P4 owns ad textures); (e) `wh.MouseSensitivity` default lowered (owner's showcase note).
5. Stop every loop engine (`stop_ue.sh`), `ps` shows 0 UnrealEditor from this loop, no `PAUSED`, health monitor running at cap 2; all piece branches and integration pushed; HANDOFF table updated with "launch for the owner" = standalone `-game -windowed -ResX=1920 -ResY=1080` and the one-line disclosure of the shipped preset's internal resolution.
6. Launch only when the owner says so.
