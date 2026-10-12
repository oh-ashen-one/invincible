# GPU lock + perf protocol (Night 1, Unreal port)

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See `../../../DISCLAIMER.md`.

One M3 Ultra GPU is shared by up to 3 Unreal instances plus other sessions' Chrome/Blender; before this tool every
perf number was taken at 40-100 % GPU busy. The rules below are mandatory.

## Usage (copy these lines)

Stable path, available now without merging: `G=/Users/midir/sm2-n1/_scratch/gpu/bin` (in-repo copy: `tools/gpu/`).
```
# every -game / -RenderOffScreen capture, movie or screenshot run (2 may run at once, a 3rd waits)
$G/gpu_slot.sh capture --label <piece> -- Scripts/run_game.sh <out_dir> -res 3840x2160 -shots 20,30,40 ...
# every perf / frame-time measurement: EXCLUSIVE, waits for an idle GPU
$G/gpu_slot.sh perf --label <piece> --json <round>/perf_gpu.json -- Scripts/run_game.sh <out_dir> -perf 22:52 ...
$G/gpu_slot.sh summary <round>/perf_gpu.json    # one line to paste next to the numbers
$G/gpu_status.sh                                # holders, waiters, GPU util, Unreal processes
```
Wrap the command that RUNS the game (run_game.sh, your capture_round.sh / run_perf.py), directly launched,
never `open -n` (the wrapper must outlive the game). Exit code = the command's. Wrapper-only codes: 75 = wait
timed out, command NOT run (retry later); 124 = max hold hit, command killed; 2 = usage or perf nested in a capture.
Nesting a capture inside a held capture/perf passes through, so wrapping twice is harmless.
## Semantics

- `capture`: one of 2 shared slots (`GPU_SLOT_CAPTURE_SLOTS`); no util requirement; blocked while a perf run holds
  the lock or is settling. Max hold 40 min (command killed). Wait timeout 60 min.
- `perf`: takes the exclusive lock, then waits until (1) no capture slot is held, (2) no Unreal `-game` /
  `-WHShotDir` / `-WHPerfFrom` process exists that is not yours (including UNWRAPPED ones from agents who have not
  adopted this yet), and (3) `ioreg -r -d 1 -c IOAccelerator` Device Utilization stays < 15 % for 10 consecutive
  seconds (any sample >= 15 or a foreign capture resets the streak). Then runs the command, max hold 15 min from
  command start, wait timeout 30 min. Waiting for calm blocks new captures (they would ruin the calm), so run
  `gpu_status.sh` first and do not queue a perf run while unwrapped captures are known to be running.
- Builder editors (`-RenderOffScreen` editors driven over MCP) are not capture processes; they count in the instance
  total (hard cap 3, RULES.md) and their GPU load is caught by the utilization gate.
- Fairness: strict FIFO ticket queue. Locks are kernel `flock`s: a killed holder frees its lock instantly; dead or
  PID-reused queue/holder records are logged `stale-recovered` and removed by the next waiter.
- Log (enqueue/wait/acquire/run/release, timestamps + GPU util): `/Users/midir/sm2-n1/_scratch/gpu/gpu_slot.log`
  (state dir = same folder). Knobs: env `GPU_SLOT_*`, see the header of `tools/gpu/gpu_slot.py`.
## What every perf result must record (from the `--json` sidecar, keep the file next to the perf json)

| field | meaning |
|---|---|
| `util_before`, `util_after`, `util_during.{avg,max}` | GPU Device Utilization % just before / after / sampled during the run |
| `wait_s` | seconds spent queued + draining + settling before the command started |
| `instances_before`, `instances_max_during` | Unreal instances (all editors + games) running, so a reader sees the load |
| `settle.{samples,min,max}` | utilization samples of the final calm streak (must all be < 15) |
| `exclusive`, `contaminated`, `contaminated_reasons`, `perf_valid` | verdict |

Put the `gpu_slot.sh summary` line and the disclosed internal resolution next to every perf table.
## Contaminated

A perf number is **`contaminated`** and must be labelled so (never compared with locked numbers, never used by a
critic or director as evidence of a pass/fail on fps) when ANY of: it was not run under `gpu_slot.sh perf`;
`exclusive` is false; `util_before` >= 15 %; a foreign capture process appeared during the run
(`foreign_capture_during`); the max hold killed it. `perf_valid: true` in the sidecar is the only clean state.
All perf numbers recorded before this lock existed are void (GPU 40-100 % busy); re-baseline once.

Tests (no Unreal launched): `tools/gpu/test_gpu_slot.sh --save <dir>`; results in `docs/night1/gpu/test-results/`.
