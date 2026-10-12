// Player (hero) position and heading of the shots.js compositions of the author's night city (~/spiderbench @ 64d957f), one page at a time:
//   node tools/night/ref_players.mjs   -> ~/sm2-n1/_scratch/night/ref/ref_players.json  { shot_street: { pos: [x, y, z] browser m, dir: [dx, dy, dz] (object world forward), visible } ... }
// tools/showcase/gen_shot_cams.py turns it into hero_pos_m (UE axes, m) / hero_yaw_deg for -WHShotCam (UE (X, Y) = browser (x, z); yaw = atan2(dz, dx)).
import fs from 'node:fs';
import path from 'node:path';
import { SCRATCH, startServer, launchBrowser, openNight } from './common.mjs';

const OUT = process.env.OUT || path.join(SCRATCH, 'ref');
const res = {};
const { server, base } = await startServer({ inject: true });
try {
  const b = await launchBrowser();
  try {
    for (const shot of ['street', 'wall', 'swing', 'swingBack', 'climb']) {
      const { page } = await openNight(b, base, { shot });
      res['shot_' + shot] = await page.evaluate(() => {
        const o = window.__ctx.player.object, v = new o.position.constructor();
        o.getWorldDirection(v);
        return { pos: [o.position.x, o.position.y, o.position.z].map(x => Math.round(x * 100) / 100), dir: [v.x, v.y, v.z].map(x => Math.round(x * 1000) / 1000), visible: o.visible, heading: window.__ctx.player.heading ?? null, mode: window.__ctx.player.mode ?? null };
      });
      console.log(shot, JSON.stringify(res['shot_' + shot]));
      await page.close();
    }
  } finally { await b.close(); }
  fs.writeFileSync(path.join(OUT, 'ref_players.json'), JSON.stringify(res, null, 1));
} finally { await server.close(); }
