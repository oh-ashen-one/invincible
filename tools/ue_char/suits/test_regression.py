#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Regression guard of the suit generator.
  1. LEGACY (round 08): design.py with relief.kind 'r8' (hero_suit_r8.py --legacy-r8) must reproduce the round-08 Tessera maps texel for texel
     (md5 of the 1024 px base colour / normal / ORM written by the ROUND-08 code, before design.py got a style argument).
  2. DEFAULT (round 15 = round 14 +; round 14: round 13 plus the lifted hood + baked face tone, piped sash ends, neck-base net stop, armpit stitch end, cheek panel seams; Tessera stays the default suit): raised piping, net / piping under the sash, torso-side cavity AO: the 1024 px maps.
     A deliberate design change updates EXPECT_R17 in the same commit (and says so in the round's HANDOFF).
  python3 tools/ue_char/suits/test_regression.py        (CPU, ~20 s)  -> exit 1 on a mismatch"""
import sys, os, hashlib, tempfile, subprocess
import cv2
HERE = os.path.dirname(os.path.abspath(__file__))
WT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
EXPECT_R8 = {'suit_basecolor_r8.png': '66e3b691813cc83cd9dc7bd20bdf0c59', 'suit_normal_r8.png': '09f0c6554c3a706529387e78ea4ff2e8', 'suit_orm_r8.png': 'ad1be27f39d2b4d5bb77f124125d5a8f'}
EXPECT_R12_ROUND12 = {'suit_basecolor_r8.png': '7b0905060f99c1e94c283208ee4b262c', 'suit_normal_r8.png': 'efa874d66249c9fd3c6c2601167c10e0', 'suit_orm_r8.png': '65e1bd9aeb876e3489777807abe22ad3'}   # history (round 12)
EXPECT_R13 = {'suit_basecolor_r8.png': '9055668912fbc29d852137f46be4a075', 'suit_normal_r8.png': 'c2e2b31393364aac92175bcf36d2ce3b', 'suit_orm_r8.png': '55bf7f082df45b5c768986564f382a5a'}   # history (round 13: raised face seam cord, satin hood (0.50), hood halfway to the crown colour, crown piping + brow flashes moved up, glyph on the sash in DEEP)
EXPECT_R14 = {'suit_basecolor_r8.png': '6df77485a86aef086d6acddd351f0513', 'suit_normal_r8.png': '9138e45913d0e22ea01a4070fd5d19fa', 'suit_orm_r8.png': 'a7eb0b1c0ca9eda7b39b6bf4a6e9d20d'}   # round 14: Tessera hood lifted to the body colour + the baked face tone of the sculpt field, two raised cheek panel seams per side, piped (straight, border + stitch rows + accent pipe) sash ends, torso net stops at the neck base, wedge pipe / stitch rows end below the armpit, lighter seam cord
EXPECT_R15_ROUND15 = {'suit_basecolor_r8.png': 'cee0654a14b2bb8223357a136cfd1b00', 'suit_normal_r8.png': '1f29a5bbcfcbb34854263563ab9cbf8b', 'suit_orm_r8.png': '804f424040a6c029553961edc1942edc'}   # history (round 15): sculpt field (brow 13.5, sockets -8.8 / -7.5: the baked face tone), the accent pipe ON the sash end line, the net panel as a yoke (hard edges, two seam cords, wedge side seam, hard limb ends), the shoulder cap 7.5 cm on the torso side (no ring cord over the armpit crease)
bad = 0
EXPECT_R16_ROUND16 = {'suit_basecolor_r8.png': '5b92fdc4c78f4d997cc309a05c3b4e6d', 'suit_normal_r8.png': '5b60ae0a7afd4ed48b6e48448d6e7657', 'suit_orm_r8.png': 'bb8b6990dbb16bf03aea7bdc432151fb'}   # round 16: the sash is a front panel (ends on the coronal plane, piped; its end finishing gated to the front), tone-on-tone back mark, seam-tone wedge pipe on the back, geometric limb net zones ending on ring cords (+ ring cords / yoke side seam on sleeveless suits, an inseam cord)
EXPECT_R17 = {'suit_basecolor_r8.png': '767613a808f1890fa1405a31274af896', 'suit_normal_r8.png': '1490b0d3423ac11e50cc968f4844bf23', 'suit_orm_r8.png': 'cdae53798376694a424cc29610f831ba'}   # round 17: the free (jaw) ends of the four cheek panel seams close in a rounded tip (circular cap over the last 6 / 4.8 mm) instead of a square cut; everything else identical to round 16
for tag, extra, expect in (('legacy r8', ['--legacy-r8'], EXPECT_R8), ('default r17', [], EXPECT_R17)):
    out = tempfile.mkdtemp()
    subprocess.run([sys.executable, os.path.join(WT, 'tools', 'ue_char', 'hero_suit_r8.py'), '--n', '1024', '--out', out] + extra, check=True, capture_output=True)
    for f, h in expect.items():
        got = hashlib.md5(cv2.imread(os.path.join(out, f)).tobytes()).hexdigest()
        ok = got == h; bad += not ok
        print('%-12s %-24s %s %s' % (tag, f, got, 'OK' if ok else 'MISMATCH (expected %s)' % h))
print('REGRESSION', 'PASS' if not bad else 'FAIL')
sys.exit(1 if bad else 0)
