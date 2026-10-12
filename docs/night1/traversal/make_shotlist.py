#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Writes <round>/SHOTLIST.md from the replayed input scripts and the captured telemetry (neutral: what was pressed,
# camera settings, measured ranges; no assessment).  usage: make_shotlist.py <round dir> <round label> <commit>
import csv, glob, json, os, re, sys

ROUND, LABEL, COMMIT = sys.argv[1], sys.argv[2], sys.argv[3]
RN = int(re.search(r"(\d+)$", LABEL).group(1))  # round number
HERE = os.path.dirname(os.path.abspath(__file__))
SEQ = [
    ("a_swing_chain", "Swing chain up the avenue at speed (lit Manhattan map, golden)",
     "Airborne start 24 m over the north-south avenue (x 250 m) with 22 m/s forward velocity heading north (-Y); scripted swing chain "
     "(autoChain rule: release on the rising front, re-press after 0.8 s; a sky launch = jump-release + trick where the lower street "
     "wall ahead is within reach, at most every 2nd release)."),
    ("b_release_trick_dive_zip", "Release + trick + dive + zip to a rooftop",
     "Airborne start 30 m over the avenue (26 m/s north), one swing, release with a trick (frontPikeSwan) at 1.4 s, web-zip pressed as soon as the zip target reappears "
     "after the program (3.08 s, 0.27 s after its Reach; round 13: no web-less dive), zip to a roof point, perch."),
    ("c_wallrun_perch", "Swing into a facade -> wall-run up -> perch",
     "Airborne swing start 22 m over the avenue, the stick turns east into the 45 m loft facade (x 266 m), swing let go at 1.7 s, "
     "wall-run up, top-out onto the roof, camera turn, web-zip to the roof edge over the avenue, perch."),
    ("d_sprint_jump_first_swing", "Ground sprint -> jump -> first swing",
     "Street start on the avenue; run north, charged jump, first swing, then the round-10 chain rule (as a)."),
    ("f1_flow_backDouble", "Round 17 flow flips over the roofline: backDouble on every release",
     "Northern cross street (y -560), airborne start 30 m over the street at x -225 heading EAST (26 m/s); chain rule from 0.4 s; a trick at every "
     "release starts the flip program AT the release, its climb solved for an apex >= 4 m over the lower roofline within 30 m; program backDouble = "
     "tuck double + keyed kick-out, the next web in its final reach."),
    ("f2_flow_pikeSwan", "Round 17 flow flips over the roofline: frontPikeSwan on every release",
     "As f1 from x -200, program frontPikeSwan (pike, swan, tuck, reach)."),
    ("f3_flow_corkscrew", "Round 17 flow flips over the roofline: corkscrew on every release",
     "As f1 from x -250, program corkscrew (layout with a full twist, swan, tuck, reach)."),
    ("f4_chain_flips", "Round 17 chain: 12.2 s, a flip on every release",
     "As f1 from x -240; programs cycle backDouble, frontPikeSwan, corkscrew (4 flips; a 5th starts after the clip end)."),
    ("f5_canyon_backDouble", "Round 17: backDouble on every release from x -160 (name kept; no longer the Midtown canyon)",
     "As f1 from x -160 (rounds 13-16: the Midtown avenue x 250, flips inside a 140-250 m canyon)."),
]
FIELD = {"trick": "F trick", "move": "stick (x right, y fwd)", "swing": "RMB swing", "jump": "Space", "sprint": "Shift", "zip": "E zip",
         "drop": "C drop/dive", "quick": "Q boost", "look": "look (deg/s yaw, pitch-down)", "heading": "heading (world yaw deg)"}


def fmt_key(k):
    parts = []
    for f, v in k.items():
        if f == "t":
            continue
        if f == "heading" and v is False:
            parts.append("heading off")
        elif isinstance(v, bool):
            parts.append(f"{FIELD.get(f, f)} {'down' if v else 'up'}")
        else:
            parts.append(f"{FIELD.get(f, f)} = {v}")
    return ", ".join(parts)


def stats(path):
    if not os.path.exists(path):
        return None
    rows = list(csv.DictReader(open(path)))
    if not rows:
        return None
    f = lambda k: [float(r[k]) for r in rows]
    sp, hf, fov, cd = f("speed_mps"), f("height_above_floor_m"), f("cam_vfov_deg"), f("cam_dist_m")
    modes = []
    for r in rows:
        keep = {"trick", "dive", "release", "zipPull", "pointLaunch", "wallRun", "crawl", "zipFlight", "perchLand", "landRoll", "topOut", "landTopOut",
                "landHard", "landMedium", "jumpLaunch", "wallJump"}
        m = f"{r['mode']}/{r['sub']}" if r["sub"] in keep else r["mode"]
        if not modes or modes[-1][0] != m:
            modes.append([m, float(r["t"])])
    tricks = sorted({r["trick"] for r in rows if r["trick"]})
    chain = max(int(r["chain"]) for r in rows)
    x0, x1 = float(rows[0]["x_m"]), float(rows[-1]["x_m"])
    y0, y1 = float(rows[0]["y_m"]), float(rows[-1]["y_m"])
    return dict(n=len(rows), dur=float(rows[-1]["t"]), sp=(min(sp), max(sp)), hf=(min(hf), max(v for v in hf if v < 900)),
                fov=(min(fov), max(fov)), cd=(min(cd), max(cd)), modes=modes, tricks=tricks, chain=chain, dx=x1 - x0, dy=y1 - y0)


out = []
w = out.append
w(f"# Traversal (P3) — {LABEL} shot list")
w("")
w("> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. Nothing here is meant to infringe.")
w("")
MAPTXT = ("`/Game/Maps/Manhattan` (golden preset; the integrated lit city built in this worktree by `unreal/WebHomage/Scripts/build_manhattan.py`; "
          "hero = the `/Game/Traversal/HeroDev` dev proxy)") if RN >= 10 else ("`/Game/Tests/Traversal/Trav_Canyon` (generated by `unreal/WebHomage/Scripts/build_traversal.py`; "
          "layout in `docs/night1/traversal/trav_canyon_layout.json`)")
w(f"- Build: branch `night1/traversal`, commit `{COMMIT}`, UE 5.8.3, map {MAPTXT}.")
w("- Reproduce: `docs/night1/traversal/capture_round.sh <round dir>` (runs `unreal/WebHomage/Scripts/run_game.sh`, real `-game`, offscreen).")
if RN >= 4:
    w("- Game mode `AWebTravGameMode` -> pawn `AWebTravCharacter`. Hero: the browser build's GLB (`public/assets/spiderman.glb`, 58 bones, "
      "79 clips at 30 fps) imported by `build_traversal.py` into `/Game/Traversal/HeroDev` (dev proxy), animated by the C++ "
      "`UWebTravAnimInstance` (clip nodes with the browser's per-transition blend times, 3-way swing blend by arc phase, web-hand arm aimed "
      "at the anchor, air-phase clip timelines that differ from the previous cycle, procedural roll/pitch sway in the air, whole-body "
      "trick spins). Tricks happen only when the trick input is pressed. Web strands = chain of thin cylinders.")
    if RN >= 6:
        w("- Round 06 wall-run: body up along the wall, chest toward it, torso leaned back 0.16 rad; the hero's sprint clip plays at "
          "1.8-2.6 steps/s mapped from wall speed 6-14 m/s. Top-out: air sub-state `topOut` playing the `releaseFlip` clip, then the "
          "`landTopOut` landing (`perchLand` clip, 0.62 s) before idle. Hero textures are forced resident; `capture_round.sh` renders an "
          "unrecorded warm-up pass, then runs each sequence with a 0.8 s pre-roll (`-WHTravPreroll`: start pose rendered, simulation "
          "not stepped, camera state restored) that is cut from the video; video and still times are sequence times.")
    if RN >= 7:
        w("- Round 07 swings: virtual-pivot pendulum with a rope of 30-34 m (random per swing), at least 14 m + 0-5 m (random) below "
          "the entry height, pivot at most 30 m ahead. A web release keeps at most 8 m/s of upward speed (16 m/s within 12 m of the "
          "floor); the rest is added to forward speed. With the swing button held, the next anchor is searched 0.22 s after a "
          "release; a web found while rising faster than 5 m/s is attached (strand drawn) at once and its pendulum starts when "
          "the upward speed drops to 5 m/s or after 0.5 s. While a web is held, the hips are rotated so the hips->head line points "
          "at the anchor (weight 1.0 at the bottom of the arc, 0.6 at the ends). Scripts a and d: auto-chain rule (release after the "
          "swing has descended, at swing phase 0.7 while rising or at the forward apex; re-press 0.15 s after release; trick on "
          "every 3rd release), baked to plain keys. Script b: release + trick at 3.0 s (round 06: 3.2 s).")
    if RN >= 8:
        w("- Round 08 canyon keeping: 8 horizontal rays (every 0.05 s) find the facades beside the travel direction (wall normal "
          "within 60 deg of perpendicular to it); along each wall's normal the approach speed is limited to 2.5 m/s per metre "
          "above 3.5 m, and between two opposite walls the velocity along the normal is steered (rate 2.5 /s) toward 1.2 /s per "
          "metre off the centre line (<= 8 m/s). Active while swinging and in the air after a release. Web strands: 1.2 cm wide "
          "(at least ~1.2 px), grey, no emissive. Motion blur: amount 0.35 x smoothstep(speed, 28, 50 m/s) (diving x 1.3), none "
          "on foot / walls; max 1-3 %.")
    if RN >= 9:
        w("- Round 09: the arc depth alternates (odd swings 10.2 m, even swings 17.5 m below the entry, + 0-1.5 m; a high anchor "
          "lowers the virtual pivot instead). The anchor search heading is turned 30 deg toward the side opposite the previous web "
          "(the swing plane keeps the travel heading). While swinging, the canyon spring's target line sits 0.45 x the active "
          "anchor's offset from the centre (<= 6 m); in the air no centring inside +/-8 m. Pivot keeps 25 % of the anchor's side "
          "offset (was 10 %). Web: 1.6 cm (>= ~2 px), dark grey (0.09). Hero skeletal mesh: per-bone motion blur off. Perch / "
          "top-out landings start the perchLand clip at 0.22 s (its impact crouch). Dive: fast-fall / calm-fall blend "
          "oscillating with a 0.8 s period, plus the air sway. Scripts a and d re-baked from the same rule.")
    if RN >= 10:
        w("- Round 10 (Manhattan): a *sky launch* is a jump-release with a trick buffered; the launch speed is solved so the apex lands 3 m over the lower "
          "street wall's roofline ahead (peak clamped 38-58 m over the street, climb gravity x1.4, hang x0.55 under 7 m/s), followed by a long web "
          "(<= 50 m rope) built to bottom 5-9 m over the street; no web is searched on the way up. Script rule: a release is a sky launch when >= `skyEvery` "
          "releases have passed and the lower wall ahead is reachable (or 5.5 s after the last one); plain releases at phase 0.55; any swing is let go "
          "1.25-1.55 s in, a stale swing after 2.4 s. While swinging, touching a wide facade with the stick held into it lets go of the web and "
          "wall-runs up it. A new web never anchors below 3 m over the body or behind it. Hero mesh / clip paths are data (`HeroMeshPath`, `HeroClipRoot`, ...).")
    if RN >= 11:
        w("- Round 11 flips: a trick is a *flip program* = a timeline of held shapes (tuck, pike, layout, swan, pencil, straddle, throne, twist, "
          "reach) keyed in Blender on the hero rig (`docs/night1/traversal/blender/`); body rotation about the body centre follows one angular "
          "momentum per program with per-shape effective inertia (tuck 1 .. pencil / throne 9), solved to end upright; twist segments turn about "
          "the long axis; the upper body samples the timeline 0.04 s ahead and the legs 0.07 s behind; a cut program springs back to the body "
          "frame in ~0.07 s. The next web is searched only in the program's final reach (held up to 0.2 s). Wall-run top-out = program wallFront. "
          "Flip camera: orbit 40 deg off the travel axis toward the side with more space, 1.6 m under the hero, framing 0.42, look-up <= 18 deg.")
    if RN >= 12:
        w("- Round 12 (critic r11: tricks low in the canyon, facades behind the hero): a trick pressed at a web release is a sky launch; its "
          "speed is solved so the apex sits 6 m over the tallest roof within 30 m of the stretch of path the flip will cover (down-ray grid), "
          "peak <= 90 m over the street, launch <= 60 m/s; the program is armed on the climb, starts when the climb slows to 9 m/s and plays at "
          "0.32 g (it stays over the roofs). The chain rule only launches where that apex is reachable. Flip camera: every 0.15 s it scores "
          "orbit yaw offsets (-120..120 deg from behind) x look-up elevations (30-60 deg, camera below the hero) by the share of 16 rays around "
          "the hero (the hero box + 40 px at 1080p) that reach open sky within 900 m, preferring a 3/4 side view (55 deg) and the lowest "
          "clear look-up; springs 0.3 s, 3.4 m from the hero. backDouble = tuck 0.55 / layout 0.5 / tuck 0.55 / layout 0.5 / reach 0.2 s.")
    if RN >= 13:
        w("- Round 13 (critic r12: tricks were isolated set pieces, 1.7 s rise + trick + 1.3 s dive + a one-frame camera cut): a trick pressed at a web "
          "release is a *flow flip*: the program starts AT the release (no sky launch), the climb is solved so the catch window (the program's final "
          "Reach, 1.5 s in) opens ~2 m over the release height inside the canyon, and the next web attaches in that reach; a program keeps its "
          "shapes (no ballistic downgrade). backDouble = tuck double + a keyed Kickout (2 shapes). The chase camera's `too close: cut` rule is "
          "removed and the camera output is slew-limited per frame (3 deg pitch, 4 deg yaw, 1.2 m position at 60 fps); the flip camera blends out "
          "over >= 0.4 s. A hero-only fill light (5000 cd, 18000 cd in a flip) lifts the backlit silhouette. Camera hold: when the hero himself "
          "overlaps geometry (street-tree canopy at a swing bottom) the view is held RELATIVE to him (the first capture froze it absolutely: 20 m away).")
    if RN >= 14:
        w("- Round 14 (critic r13: the flip camera looked up from under the hero, so the rotation did not read, and stayed tilted up into the next swing): during a flip program the camera orbits to a SIDE view -- 70-115 deg off the travel-behind direction, one side for the whole trick, 4-28 deg below the hero, 3.3 m out, a spot with 1.5 m of free space beyond it and a clear path 0.5 s along the travel -- the flip look-up is capped at 27 deg and every non-wall view at 29 deg up; from 0.25 to 0.5 s after each web attach the pitch settles into 5.5-11.5 deg down. Flip rotation is eased: each segment's effective inertia rises toward its ends (tuck entries / exits ~40-60 % of the mid-tuck rate) and the keyed shapes' own hips->head lean is taken out of the root pitch, so the visible body axis follows the eased timeline. backDouble = Tuck 1.20 s + Kickout 0.60 s (<= ~100 deg/s), frontPikeSwan = Pike 0.40 / Swan 0.55 / Tuck 0.38 / Reach 0.26 s (no pencil), corkscrew = Layout 0.31 / Twist 0.42 / Swan 0.36 / Tuck 0.34 / Reach 0.24 s. f4 runs north from y 375 (11.6 s, 4 flips); b fires the zip from the flip's final Reach at 2.88 s.")
    if RN >= 15:
        w("- Round 15 (critic r14: the trick camera climbed to 20-27 deg up and looked into the sun, flaring out the flips): the side-on trick "
          "view is searched at elevations -3..6 deg around the hero's height (preferring 1 deg below), its look-up capped at 8 deg (every other "
          "non-wall view at 10 deg), and a view whose direction is closer than 100 deg to the sun (the level's atmosphere sun light: 8 deg up, "
          "due west in this map) is rejected (staged fallbacks keep the sun rule before any clearance rule); the flip camera blends in over 0.30 s. "
          "Wall-run camera: 1.3 m below and 3.1 m out from the hero, hero at 0.60 of the frame height, look-up capped at 30 deg. When the hero "
          "is inside a street-tree canopy the camera spot is lifted out of the foliage. A flow flip's rise targets 3 m over the lower street "
          "wall's roofline (buildings >= 16 m) when that needs <= 14 m of rise, else the round-13 3 m rise. While the trick camera frames a flip "
          "the zip reticle aims along the chase heading (b: zip fired from the final Reach at 2.88 s).")
    if RN >= 16:
        w("- Round 16 (director's TRICK_CAMERA_SPEC.md, replacing the r11-r15 sky search / side-on orbit): while a flip program plays the camera is a "
          "HELD 3/4-behind chase. At the release frame ONE yaw offset of 40-55 deg from the travel-behind direction is chosen (obstruction first: "
          "the spot must be sweep-reachable with 1.5 m free beyond it and a clear path 0.5 s along the travel; then the sun rule, view >= 100 deg "
          "from the level's sun; then open space) and is never re-searched; it is held on its WORLD azimuth. The camera sits 4.4 m from the hero "
          "(0.6 m closer while his shape is a tuck / pike; pulled in along the same axis by an obstruction, to 4.0 m, else blended to the plain chase), "
          "1.0 m under his body centre, hero framed at 0.36 of the frame height with a 3 deg lead-room yaw bias toward his travel; look-up capped at 7.5 deg; no roll, no attach yaw beat; "
          "FOV / kick / punch / shake untouched. Blend in: critically damped springs (0.35 s horizontal, 0.15 s height), blend out: smoothstep "
          "over 0.9 s from the web attach, the chase camera keeps running underneath (polar blend about the hero). No other flip or swing rule "
          "changed; scripts are the r15 ones.")
    if RN >= 17:
        w("- Round 17 (flips above the rooftops): the f-series runs EAST along the northern cross street (y -560): north side a park / 2-6 storey "
          "strip (10-30 m) with open sky and the far skyline behind it, south side 46-466 m blocks to web onto; the sun (due west) is behind every "
          "view. Arcs bottom >= 14 m over the street there (script tuning; over the 10-14 m street trees) and the hero keeps >= 9 m from the south "
          "facades. A flip on every release; each flow flip's climb is solved so its APEX puts the hips >= 4 m over the lower roofline within 30 m "
          "(highest top >= 16 m per street side, lower side; unreachable rooflines keep the round-13 climb), and a swing that ends in a flip is held on "
          "its rising front until that apex is reachable. Trick camera (round 16 held 3/4 view kept): the side is chosen sun-first (35-55 deg, view "
          ">= 100 deg from the sun), then by background sky share; the blend-in follows a minimum-time profile (<= 140 deg/s, k >= 0.9 at ~0.3 s). "
          "Asymmetric keyed shapes (tuck grab, pike with one arm swept back, stag swan, layout, scissor kick-out).")
else:
    w("- Game mode `AWebTravGameMode` -> pawn `AWebTravCharacter` (placeholder block figure; web strands = chain of thin cylinders).")
w("")
w("## Capture settings (all sequences)")
w("")
w("| | video | stills |")
w("|---|---|---|")
w("| output | 1920x1080, 60 fps, H.264 mp4 | 3840x2160, JPEG q92 (converted from PNG) |")
w("| internal resolution | 1920x1080 (`r.ScreenPercentage 100`) | 3840x2160 (`r.ScreenPercentage 100`) |")
w("| time step | fixed 1/60 s (`-benchmark -fps=60 -dumpmovie`) | fixed 1/60 s (`-benchmark -fps=60`) |")
w("| AA / GI | TSR, Lumen (project defaults) | same |")
w("")
w("The video frames are rendered offline at a fixed step; they say nothing about real-time frame rate.")
if not glob.glob(os.path.join(ROUND, "stills", "*.jpg")):
    w("No 4K stills were captured this round (the stills column above does not apply): only the 1920x1080 movies (internal = output, "
      "`r.ScreenPercentage 100`). Every run went through `gpu_slot.sh capture` on a GPU shared with other sessions (`contaminated`: no perf claim). " +
      ("Seven movies (f1-f5, a, b) were captured with the final build of this round (see Build above) in one GPU hold; c and d come from the first round-16 hold "
       "(wall camera / no trick camera: untouched by the later trick-camera edits); warm-up pass skipped (shader cache warm)." if RN >= 16 else
       "All nine movies were captured with the final build of this round (see Build above), in two GPU holds (f1-f5, then a-d); warm-up pass skipped "
       "(shader cache warm)."))
w("")
if RN >= 5:
    w("Camera (round 05 chase camera): 3.8 m behind the hero along the lagged heading yaw (horizontal spring 0.07 s, held 3.5-5.0 m), "
      "1.1 m above his centre (vertical spring 0.05 s, held 0.7-1.8 m), 0.3 m shoulder offset; yaw toward the hero; pitch places the hero "
      "at screen height 0.48 (arc bottom) .. 0.40 (arc ends), clamped 5-22 deg down. At each web attach (first 0.5 s) the view pitches up "
      "and, if needed, turns and widens (<= 26 deg of extra vertical FOV) so the anchor on the facade is inside the frame with the hero. "
      "Collision: sphere sweeps + clear-orbit search (see round 03). Vertical FOV 58 + 13 x smoothstep(speed, 12, 44 m/s) + 5 diving + "
      "kick / punch springs; vertical FOV converted to Unreal's horizontal FOV with the viewport aspect.")
    if RN >= 6:
        w("")
        w("Round 06 camera changes: on a wall (and while rising in the top-out) the camera blends (spring 0.16 s in, 0.22 s out) to a "
          "position 2.2 m below the hero's centre and 2.2 m out from the wall (at least 0.6 m over the street; further out when the street "
          "clamps it, keeping 3.2 m to the hero), yaw facing the wall, pitch up so the hero's centre sits at 0.68 of the frame height, "
          "vertical FOV +4 deg. Chase pitch may exceed 22 deg down when collision lifts the camera, so the hero's centre stays at or "
          "above 0.62 of the frame height. Script c: the camera-turn key looks up (pitch-down rate -10 deg/s) instead of down (+4).")
    if RN >= 7:
        w("")
        w("Round 07 camera changes: height over the hero 1.8 m (held 1.2-2.6 m; round 05-06: 1.1 m, 0.7-1.8 m), look-down at least "
          "10 deg (was 5). The attach look-up toward the anchor is scaled by 1 - (fall speed - 8) / 14 (clamped 0..1) and keeps the "
          "hero 12 deg inside the bottom edge (was 8); the attach yaw turn is capped at 25 deg with a 0.12 s spring (was 0.035 s). "
          "0.4 m closer while swinging / airborne.")
    if RN >= 8:
        w("")
        w("Round 08 camera change: sideways facade clearance measured from the camera along its right / left: a 0.15 s spring "
          "toward 3 m and a hard 1.5 m minimum, moved only as far as the line of sight to the hero stays clear.")
    if RN >= 9:
        w("")
        w("Round 09 camera changes: height over the hero 0.6 m (held 0.2-1.8 m), look-down floor -8 deg (looking up allowed), "
          "framing target 0.44 (arc bottom) .. 0.37 (arc ends); attach FOV widening <= 10 deg (round 08). During a swing chain "
          "the camera position slides 1.3 m toward the side of the active anchor (0.3 s spring; off after 0.8 s without a web, "
          "in a dive, and outside chains) and still turns toward the hero; roll toward that side up to 6 deg, weighted by "
          "smoothstep(|rope angle|, 0.55, 1.0) rad.")
    if RN >= 10:
        w("")
        w("Round 10 camera changes: the attach look-up stops where the hero centre reaches 0.64 of the frame height; attach springs 0.035 -> 0.12 s; "
          "the first composed frame starts at its framing / attach targets (no pop at t = 0); arc-bottom framing target 0.44 -> 0.50 (hero centre-Y "
          "spread); roll: yaw-rate lean 0.03 (cap 4 deg), bank 0.04, leans under 1 deg dropped. Sky launch: the camera sinks 1.2 m under the hero and frames "
          "him at 0.40, looking up <= 10 deg.")
elif LABEL.endswith("03") or LABEL.endswith("04"):
    w("Camera (round 03 chase camera): position 6.0 m behind the hero along the lagged heading yaw (browser auto-recenter behind "
      "the swing plane / travel direction), horizontal position spring 0.07 s then held 4.0-6.5 m away, height 2.4 m over the hero "
      "centre with a 0.05 s vertical spring, held 1.6-3.2 m above; 0.3 m right-shoulder offset. Orientation: yaw toward the hero; "
      "pitch set so the hero's screen centre sits at a framing target (0 top .. 1 bottom): while swinging 0.67 at the bottom of the "
      "arc to 0.36 at +-0.85 rad of rope angle; airborne 0.67 near the street to 0.36 at 40 m up; 0.22 s spring; pitch clamped 8-32 deg "
      "down. Collision: 0.22 m sphere sweeps from the hero's chest (or 1-2.6 m above it when the chest is against a surface); when "
      "the default spot is not clear, raised / rotated orbit spots are searched and eased in, with a cut when the camera would come "
      "within 4 m. Vertical FOV 58 + 13 x smoothstep(speed, 12, 44 m/s) + 5 diving, launch-kick / impact-punch springs, trauma shake, "
      "speed motion blur (browser values); vertical FOV converted to Unreal's horizontal FOV with the viewport aspect.")
else:
    w("Camera (port of `src/player/camera.js`): chase camera, critically damped springs on every framing value; base vertical FOV 58 deg, "
      "target FOV = 58 + 13 x smoothstep(speed, 12, 44 m/s) + 5 while diving, plus launch-kick and impact-punch springs.")
w("")
if os.path.exists(os.path.join(ROUND, "PX_CHECK.txt")):
    w("Pixel check: `PX_CHECK.txt` (`docs/night1/traversal/px_check.py`) — hero height in pixels at 1080p from a depth scene capture that "
      "renders only the hero meshes from the rendered camera (480x270 capture scaled to 1920x1080), and the web anchor projected through the "
      "engine's rendered camera at each attach.")
    w("")
if os.path.exists(os.path.join(ROUND, "ANIM_CHECK.txt")):
    w("Animation check (T-pose / no-clip frames; air silhouettes sampled at 6 fps, pose signature = head / hands / feet relative to the "
      "hips in camera right / up; consecutive air cycles compared by node sequence): `ANIM_CHECK.txt` (`docs/night1/traversal/anim_check.py`).")
    w("")
if os.path.exists(os.path.join(ROUND, "CAM_CHECK.txt")):
    w("Per-frame camera / framing check (hero screen bbox height and centre-Y, in-frame flag, camera-hero distance, camera-in-geometry "
      "flag, camera pitch / height; min / max per sequence and hero screen travel per swing): `CAM_CHECK.txt` (`docs/night1/traversal/cam_check.py`).")
    w("")
w("Inputs are replayed from JSON (`docs/night1/traversal/scripts/" + ("city/" if RN >= 10 else "") + "`, `-WHTravScript=`), sampled once per frame and fed to the same "
  "code path as the keyboard / pad. `heading` = the stick is set every frame to the world direction given (yaw deg), expressed "
  "relative to the current camera. "
  + ("Sequences a and d (round 10) run the `autoChain` rule live (rule-form keys in the JSON: release / re-press / sky-launch timing decided in "
     "the game tick from the physical state, seed 1234; the fixed 1/60 s replay is deterministic); b and c are hand-timed keys." if RN >= 10 else
     "Swing button edges in sequences a and d were generated by a timing rule (release on the rising front of the arc, re-press once the upward "
     "speed has dropped) and then written out as plain timed keys (`scripts/bake_keys.py`; the `*_auto.json` files hold the rule form)."))
w("")
if os.path.exists(os.path.join(ROUND, "SPEC_CHECK.txt")):
    w("TRAVERSAL-SPEC check: `SPEC_CHECK.txt` — `docs/night1/traversal/spec_cam_check.py` (lines T8-T14, T16, T19 from the "
      "telemetry: hero pixel box, the rendered camera's pitch / yaw / roll / horizontal FOV, occlusion) and the spec's own "
      "instruments run on the 1080p videos: `vp_cam.py` (roll / pitch / yaw / FOV from vanishing points) and `nearflow.py 8` "
      "(near-field coverage by optical flow; CSVs in `spec/`).")
    w("")
if os.path.exists(os.path.join(ROUND, "FACADE_CHECK.txt")):
    w("Facade check: `FACADE_CHECK.txt` (`docs/night1/traversal/facade_check.py`) — per frame of the rendered video, from a "
      "full-scene depth capture (480x270, same camera as the view, web strands hidden) and the hero-only depth capture: share of "
      "the frame covered by non-hero surfaces closer than 6 m to the camera, and share of the hero's pixels with geometry more "
      "than 0.3 m in front of him; plus hero / camera horizontal distance to the nearest building box of the layout.")
    w("")
if os.path.exists(os.path.join(ROUND, "CADENCE_CHECK.txt")):
    w("Swing cadence check: `CADENCE_CHECK.txt` (`docs/night1/traversal/cadence_check.py`) — over the first 12 s: web attaches, "
      "attach -> release time per swing, release -> next web stuck (web-less) time, drop per swing, frames with a web stuck and the "
      "hero inside the frame, body axis (hips -> head) vs the web (hips -> anchor) at each swing's low point.")
    w("")
if os.path.exists(os.path.join(ROUND, "WALL_CHECK.txt")):
    w("Wall-run check: `WALL_CHECK.txt` (`docs/night1/traversal/wall_check.py`) — on 6 fps samples of the wall-run: number of distinct "
      "hand / foot height arrangements relative to the hips (distinct = more than 0.12 m apart), head above the hips (world up), foot L/R "
      "height crossings per second, hero pixel box fully inside the frame from the wall-run start to the end of the top-out landing, "
      "camera pitch / height below the hero / distance on the wall.")
    w("")
if os.path.exists(os.path.join(ROUND, "DROP_TEST.txt")):
    w("Swing arc test output (per swing: height at the preceding release, low point, drop, rope length, duration, horizon travel on screen): `DROP_TEST.txt` "
      "(generated by `docs/night1/traversal/drop_test.py` from the telemetry CSVs of the videos).")
    w("")
w("Telemetry CSV columns (one row per rendered frame): frame, t, mode, sub, body position x/y/z (m, UE axes), velocity, speed, "
  "horizontal speed, height above the floor below, swing anchor x/y/z, rope length, web tension 0..1, momentum-chain level, "
  "trick, zip target present + position, camera position / yaw / pitch / vertical FOV / distance, motion-blur factor, input state"
  + ("; round 06 adds head_hip_dz (head minus hips height, m) and limb_z (hand L, hand R, foot L, foot R height minus hips, m)" if RN >= 6 else "")
  + ("; round 07 adds body_rope_deg (hips->head vs hips->anchor, deg, while swinging; -1 otherwise) and web_on (a web strand stuck)" if RN >= 7 else "")
  + ("; round 08 adds wall_frac and hero_occl (see the facade check)" if RN >= 8 else "")
  + ("; round 09 adds hero_cx (projected bone box centre x) and pcm_roll." if RN >= 9 else "."))
w("")
for name, title, desc in SEQ:
    if not os.path.exists(os.path.join(ROUND, name + ".mp4")):
        continue  # round 11: only the sequences captured in this round
    SCRDIR = os.path.join(HERE, "scripts", "city") if RN >= 10 else os.path.join(HERE, "scripts")
    js = json.load(open(os.path.join(SCRDIR, name + ".json")))
    st = stats(os.path.join(ROUND, name + "_telemetry.csv"))
    w(f"## {name} — {title}")
    w("")
    w(desc)
    w("")
    files = [f"`{name}.mp4`", f"`{name}_telemetry.csv`"] + [f"`stills/{os.path.basename(p)}`" for p in sorted(glob.glob(os.path.join(ROUND, "stills", name + "_*.jpg")))]
    w("Files: " + ", ".join(files))
    w("")
    sp = js["spawn"]
    w(f"Spawn: position {sp['pos']} m, yaw {sp.get('yaw', 0)} deg, camera pitch {sp.get('camPitch', 0.14)} rad"
      + (f", initial velocity {sp['vel']} m/s" if "vel" in sp else "") + f". Script: `scripts/{"city/" if RN >= 10 else ""}{name}.json`.")
    w("")
    w("| t (s) | input change |")
    w("|---|---|")
    for k in js["keys"]:
        w(f"| {float(k['t']):.3f} | {fmt_key(k)} |")
    w("")
    if st:
        w(f"Measured over the video ({st['n']} frames, {st['dur']:.2f} s): speed {st['sp'][0]:.1f}-{st['sp'][1]:.1f} m/s; height above the "
          f"floor {st['hf'][0]:.1f}-{st['hf'][1]:.1f} m; {'Y (north = -Y)' if RN >= 10 else 'X'} travelled {(st['dy'] if RN >= 10 else st['dx']):.0f} m; vertical FOV {st['fov'][0]:.1f}-{st['fov'][1]:.1f} deg; "
          f"camera distance {st['cd'][0]:.1f}-{st['cd'][1]:.1f} m; max momentum-chain level {st['chain']}; tricks: {', '.join(st['tricks']) or 'none'}.")
        w("")
        w("State sequence (mode/sub-state, start time s): " + " -> ".join(f"{m} {t:.2f}" for m, t in st["modes"]))
        w("")
open(os.path.join(ROUND, "SHOTLIST.md"), "w").write("\n".join(out) + "\n")
print("wrote", os.path.join(ROUND, "SHOTLIST.md"))
