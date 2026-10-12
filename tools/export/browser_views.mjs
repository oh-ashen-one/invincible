// Browser reference captures of the SHOTLIST views (same camera as the UE view maps): ?shot=street&cam=x,y,z,tx,ty,tz
// usage: node tools/export/browser_views.mjs <out_dir> [ids...]
import { chromium } from 'playwright-core';
import fs from 'node:fs';
import path from 'node:path';
const out = process.argv[2]; const want = process.argv.slice(3);
const shots = JSON.parse(fs.readFileSync(new URL('../../unreal/WebHomage/Scripts/city_shots.json', import.meta.url)));
fs.mkdirSync(out, { recursive: true });
const SCRATCH = process.env.SM2_CITY_SCRATCH || '/Users/midir/sm2-n1/_scratch/city', PORT = process.env.SM2_CITY_PORT || '5202';
const ctx = await chromium.launchPersistentContext(path.join(SCRATCH, 'chrome-profile'), { channel: 'chrome', headless: true,
  viewport: { width: 1920, height: 1080 }, args: ['--use-angle=metal', '--enable-gpu', '--ignore-gpu-blocklist'] });
for (const s of shots) {
  if (want.length && !want.includes(s.id)) continue;
  const page = await ctx.newPage();
  await page.goto(`http://127.0.0.1:${PORT}/?shot=street&cam=${[...s.pos, ...s.target].join(',')}`);
  await page.waitForFunction(() => window.__shotReady === true, null, { timeout: 600000 });
  await page.evaluate(() => { const c = window.__ctx; if (c?.camera) { c.camera.fov = 75; c.camera.updateProjectionMatrix(); } });
  await page.waitForTimeout(3000);
  await page.screenshot({ path: path.join(out, `${s.id}_browser.png`) });
  console.log(s.id); await page.close();
}
await ctx.close();
