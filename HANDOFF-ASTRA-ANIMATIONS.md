> **SUPERSEDED 2026-09-28:** The owner cancelled the crowd/animal work and selected main-character animations with automatic AND button-triggered tricks. Follow [the hero plan](docs/anim/hero/PLAN.md). The prior brief below is historical, not the active task.

# Handoff: animate the city's people and animals in Blender (Astra)

> This is a homage game. It does not use anything copyrighted, and it is not an official Marvel game. See [DISCLAIMER.md](DISCLAIMER.md).

**Branch:** `3d-animations-astra`, cut from `main` on 2026-09-28 at `2901735`. That `main` already has the custom hero skins, the 20-citizen crowd, and the textured street props and animals.

**Lead:** Astra (`gpt-6-astra`, high reasoning) in Codex on the Mac Studio. All animation is authored in Blender through the Blender MCP.

The owner chose Astra for this task. That overrides the default in `~/.agents-md` that the running model is the builder.

---

## 0. Paste this into a new Codex session on the Studio

```
You are Astra (gpt-6-astra, high reasoning). Repo: oh-ashen-one/spider-man-2, branch 3d-animations-astra.
Read HANDOFF-ASTRA-ANIMATIONS.md in full and follow it. Your job is to animate the game's existing 3D people and
animals in Blender through the Blender MCP, then bake them into the game and verify them in-engine on this Mac Studio.
Start with section 2 (setup + MCP connection proof), then work through section 4 in order, one character group at a
time, committing and pushing to 3d-animations-astra after every group. Never touch main or other branches.
```

Before your first action, write down the actual model, reasoning setting and MCP server you are running with. Record them in the log at the bottom of this file. Never claim a setting or a connection you have not verified.

---

## 1. What you are animating

### People: the crowd

There are 20 textured citizens plus an accessory kit: caps, hats, beanie, headphones, sunglasses, backpack and bag.

- **Meshes:** `public/assets/city/npc/citizens.{json,bin}` and `citizens_atlas.webp`, built by `tools/crowdfit/crowdfit.py`. Read `tools/crowdfit/README.md`.
- **Skeleton:** every citizen is skinned (4 weights per vertex) to the crowd's shared 18-bone skeleton, in its rest pose: arms down, 1.70 m tall, facing +Z, +Y up. The bones and their rest heads are in `public/assets/city/npc/people.json` under `bones`:
  `hips, spine, chest, neck, head, upperArmL, forearmL, handL, upperArmR, forearmR, handR, thighL, shinL, footL, thighR, shinR, footR, prop` (the prop is parented to handR and holds phones and bags).
- **Animation:** 27 clips baked into one float texture, inside `people.bin`.
  - `people.json` holds `anim` (byte offset), `frames` (2185 rows total), `nb` (18) and `clips {name: {row, len, fps: 30, loop, stride?}}`.
  - Texel layout: the texture is `nb*3` texels wide and one row per frame. Each bone takes 3 RGBA float texels, which are the rows of its 3x4 skinning matrix: `r0 = (m00 m01 m02 m03)`, `r1 = (m10 …)`, `r2 = (m20 …)`. The matrix is the bone's posed matrix times the inverse of its rest matrix, in model space.
  - The runtime is `src/world/npc/crowd.js`. It samples at `clipBone()` and blends clip A/B with `iA`/`iB`. It adds procedural head and neck look-at (`lookRot`) on top, so authored clips should leave the head fairly neutral where a look-at is expected.
  - `stride` is metres per loop cycle. The runtime uses it to match the playback rate to ground speed, so it must be measured from your clip, or the feet slide.
- **Clips today:** walk, run, idle, talk, phone, photo, wave, cheer, point, lookUp, cower, sit, clap, flee, walkF, walkCarry, idlePockets, idleCrossed, idleHip, walkPhone, walkBrisk, walkStroll, walkOld, idleOld, idleShift, listen and talk2.
  - They came baked from the upstream spiderbench build, and they're stiff. **The Blender source that baked them is not in this repo.** Rebuilding that authoring path is part of the job (see 4.1).
- **How the crowd uses the clips** (grep `crowd.js`):
  - `lookUp` and `point`: bystanders craning at, and pointing at, Spider-Man overhead.
  - `talk`, `talk2` and `listen`: conversation groups.
  - `flee`, `run` and `cower`: danger.
  - `photo`, `cheer` and `wave`: fans.
  - Keep every existing clip name working. The runtime refers to them by name. You may add clips.

### Animals

The animals live in `public/assets/city/npc/fauna.{json,bin}` and `fauna_atlas.webp`, built by `tools/critterfit/critterfit.py`. Read `tools/critterfit/README.md`.

| Item | Used by | Today |
|---|---|---|
| `golden`, `bulldog` | Dog walkers (`crowd.js` → `npc/fauna.js` `createDogsHQ`) | Rigid-part vertex shader: legs swing, tail wags, head sways |
| `cat`, `rat`, `squirrel` | Street critters (`npc/fauna.js` `createCritters`) | Same rigid parts: skitter, sniff, flee |
| `pigeon`, `gull` (standing), `pigeonfly`, `gullfly` (flying) | Flocks (`npc/pigeons.js`) | Standing models peck; flying models flap two rigid wings |

- Every fauna vertex has a part id and a weight (`aRig`), and the pivots are in the JSON. That's the fallback: it's cheap, but it looks robotic.
- **Raw sources** (textured Tripo GLBs) live on the Studio in `~/sm2-assets/raw2/` (animals and props) and `~/sm2-assets/raw/` (citizens and accessories). The owner's originals are in the laptop's iCloud `Documents/3d assets spiderman/`.
- `pigeon_in_flight.glb` has no texture. The preferred fix is to give the standing pigeon (and the gull) wings on one skeleton, which retires the separate flight mesh. Otherwise, rig the flight mesh and colour it from the standing pigeon.

### Out of scope

The hero and the five suit skins already use the 58-bone hero skeleton with 79 clips (`src/game/systems/skinswap.js`). Don't touch them unless the owner asks.

---

## 2. Setup and rules

1. **Workspace:**
   - Work on the Studio in a checkout of **your own**: `git clone git@github.com:oh-ashen-one/spider-man-2.git ~/sm2-astra-anim && cd ~/sm2-astra-anim && git checkout 3d-animations-astra && npm install`.
   - Commit and push to `3d-animations-astra` after every character group. Nothing stays local-only.
   - Never commit to `main`, and never merge into it. The owner merges.
2. **Other sessions are off-limits:**
   - Don't touch `~/spider-man-2-claude`, `~/spider-man-2`, or any other worktree or branch (`flight-dynamics`, `water-effects` and others).
   - Don't touch the `Infected_Blender` MCP server or its Blender on port **19876**; it belongs to another project.
   - Never broad-`pkill`, and never touch Blender or Godot processes you didn't start.
3. **Your own Blender plus Blender MCP** (running several instances is explicitly allowed):
   - Launch your own Blender GUI on the Studio desktop (`open -na /Applications/Blender.app --args ~/sm2-astra-anim/art/anim/<file>.blend`). Enable the blender-mcp add-on and start its server on a **new port, for example 19891**.
   - Register a separate Codex MCP entry for it, for example in `~/.codex/config.toml`:
     ```toml
     [mcp_servers.SM2_Anim_Blender]
     command = "/opt/homebrew/bin/uvx"
     args = ["--from", "blender-mcp==1.9.1", "blender-mcp"]
     [mcp_servers.SM2_Anim_Blender.env]
     BLENDER_HOST = "127.0.0.1"
     BLENDER_PORT = "19891"
     ```
   - **Prove the connection before any work:** the tool catalog must be non-empty, `get_addon_status` must report the Blender version, `get_scene_info` must show *your* file, and one `execute_blender_code` round trip must work. A saved config or an open window is not proof.
   - If the MCP won't connect, write up a bounded diagnosis in the log. Headless `blender -b -P` scripts can carry on with non-interactive work, but the owner asked for MCP authoring, so keep that gate open.
4. **Blender MCP code hygiene:**
   - Look up shader nodes by `type`, never by name.
   - Read enum identifiers from RNA instead of hard-coding them.
   - After every visible change, confirm it with `get_viewport_screenshot`.
5. **Heavy work stays on the Studio:** Blender, bakes, Vite and Chrome. That includes all animation authoring and QA.
6. **Assets:** hand-key the animation in Blender. Study real-motion reference for timing (walk cycles, pigeon head bob, squirrel bounding gait, dog trot). **No downloaded mocap or animation packs** (Mixamo and similar) unless the owner says yes. External meshes are off-limits too, since the models already exist.
7. **Text:** the disclaimer above goes in any new README or doc. If you ever generate images (you shouldn't need to), never put the words "Spider-Man" in a prompt.
8. **Game playbook:** read `~/gaming-ralph-loops` first, especially `MODELING.md`, `FAILURES.md`, `OPS.md` and `TOOLING.md`. Don't re-derive what it already records.

---

## 3. Integration contract (how the animation gets into the game)

- **People:** write `tools/crowdanim/`, a Blender-side toolkit that:
  1. rebuilds the 18-bone armature from `people.json` `bones` (heads, parents; rest pose facing −Y in Blender, which is +Z in glTF);
  2. imports the citizens from `citizens.bin` (skinned, with the atlas) plus a few accessories, for preview. Use several body types (the runtime also reshapes girth per instance, see `bodyShape()` in `crowd.js`);
  3. keeps one Blender **Action per clip** under the existing names;
  4. **bakes** the actions into the texel layout from section 1, rewrites the `anim` block of `people.bin`, and updates `people.json` (`frames`, `clips` with `row/len/fps/loop/stride`).
  - **Keep the `.blend` and the scripts in the repo** (`art/anim/crowd.blend`, `tools/crowdanim/*.py`). The next person has to be able to re-bake.
  - **Don't change the skeleton:** no new bones and no reordering. `citizens.bin` weights and the shader's bone indices depend on it.
- **Animals:** add real skeletons.
  - For each species, rig it in Blender: a spine chain, legs with feet, tail chain, neck and head, ears if cheap, wings for birds.
  - Skin the critterfit meshes, keeping the same UVs and atlas, and author the clips.
  - Bake each species into a bone animation texture with the same texel layout as the crowd.
  - Add a GPU-skinned instanced path in `npc/fauna.js` and `npc/pigeons.js`: weights and bone indices per vertex, clip per instance, blend when the state changes. The shapes of `RigPool` and `crowd.js skinningGLSL` are the models to follow.
  - Extend `tools/critterfit` (or add `tools/faunaanim/`) so the pack can be rebuilt with weights.
  - Keep the rigid-part path as the fallback whenever the new data is missing.
- **Performance:** hundreds of people and pigeons can be on screen at once. Everything stays instanced and GPU-skinned with one texture per group, and each character group adds no more than a few draw calls. The target is 60 fps on the Mac Studio (M3 Ultra).

---

## 4. The work, in order

Each group ends with QA (section 5), a commit and a push.

### 4.1 People: rebuild the authoring path and re-author the core clips

Start by proving the round trip:
1. Import the current baked clips into Blender (decode the texture back into keyframes).
2. Re-bake them unchanged.
3. Check the game looks identical.

Only then re-author. Clips in priority order, each loopable, root in place, with a measured `stride` for locomotion:

1. **Walking:** `walk` (neutral), `walkF` (feminine), `walkBrisk`, `walkStroll`, `walkOld`. The details that matter:
   - heel strike and toe-off
   - pelvis tilt and rotation, with the counter-rotation of the chest
   - arm swing from the shoulder with a forearm lag
   - a little head stabilisation
   - `walkPhone` and `walkCarry` keep their held-arm poses.
2. **Running:** `run` (jog) and `flee`. Flee is a panicked sprint: arms flailing, torso leaning forward, glances back.
3. **Looking up:** `lookUp`. Stop, crane the neck and upper back, shade the eyes with a hand, sway the weight. The runtime adds its own head look-at, so keep the authored head moderate.
4. **Pointing:** `point`. Arm raised to point upward and out, with an excited bounce. Consider adding `pointUp` and `pointShout` variants.
5. **Talking:** `talk`, `talk2`, `listen`. These are conversation loops:
   - hand gestures, weight shifts, head nods
   - an occasional laugh in one of them
   - `listen` gets nods and crossed or relaxed arms.
   - Make `talk` and `listen` read as a pair when two people face each other.
6. Optional polish if time allows: `idle*` variety, `wave`, `cheer`, `photo`, `cower`, `sit`, `clap`.

### 4.2 Dogs: golden retriever and French bulldog

`walk`, `trot` and `run`, plus `idle` (breathing, looking around), `sit`, `sniff` (nose down, tracking), and tail wag as a separate layer or folded into the clips. The dog follows its owner at the owner's speed: choose the clip from speed and match `stride`. The bulldog's gait is choppier and wider.

### 4.3 Street critters

- **Rat:** `scurry` (low, fast gallop with body undulation), `sniff` (rearing up, whiskering), `idle`, and `flee` (fastest scurry).
- **Squirrel:** `bound` (the real squirrel gait, with hind feet landing ahead of the front), `run`, `sitUp` (upright, nibbling), `freeze`, and tail flicks.
- **Cat:** `walk`, `trot`, `sit`, `idle` (tail flick, ear twitch), and optionally `groom`. When it moves away from the player it walks off indifferently rather than bolting.

### 4.4 Birds: pigeon and gull

`walk` (**the pigeon head bob is essential**), `peck`, `idle`, `takeoff` (wing clap and burst), `flap`, `glide`, `land`, and `bank`, which is optional. The flock logic in `pigeons.js` already has the states ground → burst → circle → landing, so map the clips onto them. Gulls flap slower and glide more.

---

## 5. QA gates (for every group)

1. **Blender:**
   - Render a side and a three-quarter playblast of every clip. Save them under `docs/anim/<group>/`, with a contact sheet or a short MP4.
   - Check for foot sliding against the ground grid, with the ground speed = `stride` × cycles per second.
   - Check no mesh tears on **all 20 citizens**, including the accessories: hats stay on heads, and backpacks follow the chest.
2. **In-engine (Studio):**
   - Dev server: `npx vite --port 5192 --host 127.0.0.1`. Pick a port nobody else uses; 5191 may belong to another session.
   - Headless Chrome: `"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --remote-debugging-port=9334 --user-data-dir=/tmp/astra-chrome --use-angle=metal --ignore-gpu-blocklist about:blank`.
   - Framed captures: `tools/qa/pool_views.mjs`. Edit its port and targets for your pools. It drives `ctx.manualStep`, `ctx.stepFrame(1/60)` and `world.life.debugCam = [cx,cy,cz, tx,ty,tz]`; `world.life.stats()` reports the counts.
   - Capture each clip in context: a walking crowd, a conversation group, people looking up at and pointing at Spider-Man overhead, dogs on leashes, a rat bolting, a squirrel bounding, and a pigeon flock taking off and landing.
   - Compare the captures with the Blender playblasts.
3. **Performance:**
   - Measure frame time in a **real desktop session** on the Studio, not over SSH, because an SSH-launched browser fakes about 16 fps. Use the busiest street view and a park view.
   - Report the average, the 1% lows and the hitches before and after. The 60 fps budget (16.67 ms) stays part of the brief.
4. **Honesty:**
   - Separate what was verified in Blender, what was verified in-engine, and what was measured, from what is left for the owner to judge.
   - Record anything unresolved.

---

## 6. Done means

- New clips are baked for every group in section 4.
- The `.blend` files and bake scripts are committed.
- Playblasts, in-game captures and perf numbers are committed under `docs/anim/`.
- The rigid-part and old-clip fallbacks still work.
- `BACKLOG.md` and `concepts/CREATURES.md` are updated.
- Everything is pushed to `3d-animations-astra`.
- A summary is added to the log below.

---

## Log (Astra appends here)

| Date | Session / model / settings | Done | Evidence | Next |
|---|---|---|---|---|
| 2026-09-28 | Claude (handoff author) | Branch cut from `main` at `2901735`, handoff written, `tools/qa/pool_views.mjs` added | — | Astra: section 2 |
