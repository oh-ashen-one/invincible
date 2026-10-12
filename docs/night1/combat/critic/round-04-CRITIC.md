# P5 Combat r04: critic (pixels only)

> Homage fan game. It is not an official Marvel, Sony or Insomniac game and has no affiliation with them.

Ours: `round-04/fight30_1080p60.mp4`, with contacts aligned to the event log (movie frame = rt*60-53, checked against burst onsets). Diffs are mean gray at 480x270.

## Scores (vs r3 [5,5,5,4,4])
1. **Impact: 6** (+1). The disc is gone. Each blow shows an additive burst of about 8 streaks, with fill 0.02-0.30 and a median core of 3.3% of frame width. It lasts 7-8 frames while the world keeps moving (hold diff 1.0-3.5, frozen 0.27%). But it shuts off in one frame with no decay, it is the same shape on every blow, and @14.32 it covers the victim for 10 frames.
2. **Move set: 5** (=). The launch, air hits, slam and finisher are unchanged. The finisher has no cut, only a slow-mo of 0.45 s at x0.55.
3. **Enemies: 5** (=). Every blow moves the victim: 0.46-2.66 m in 0.3 s, and knockdowns travel 3.4-6.9 m in 1 s. But light blows move it only 43-60 px on a body about 310 px tall. The finisher victim @26.63 barely changes over 24 frames, and the armored brute @29.78 shows no flinch.
4. **Camera: 4** (=). The backlit opening remains (20.5% dark pixels at 0-4 s, vs 15.2% later). There is a snap of 29.2 @15.3 s, over the limit of 25. The median hero height is 27.4% of frame, vs about 40% in the refs.
5. **Spectacle: 4** (=). The street is still flat and untextured, with no environment hits and no blur. New regression: at 0-4 s the hero is a blown-out white glow, with 40-57k near-white pixels vs 10-20k mid-fight.

## A/B
I chose the reference in all 11 ref pairs. It has environment slams, blur, swirl FX and cuts. In prev-vs-now and prev-vs-now-hit I chose **B**, which has starbursts with readable victims where A has opaque discs. I guess B is r04.

## Biggest gap
**Build the combat camera and lighting.**
- At contacts, the median hero box is at least 35% of frame height.
- At 0-4 s, 15% or fewer pixels are below gray 30, and the shot is not backlit.
- Outside burst frames, 2% or fewer of the hero box's pixels have V≥250 and S<60.
- No 60 fps diff is above 25 unless it is a deliberate cut.

## Secondary
1. The burst decays over frames 6-10 and varies by blow type.
2. A light blow moves the victim at least 25% of its body height within 0.3 s.
3. Add a finisher close-up cut of 1 s or more at 0.3x.
4. **Brand:** the copied white spider emblem on the chest and back is still visible (@14.32, @26.63). Remove it.

## Verdict: **FAILS TARGET** [6,5,5,4,4]
