// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
// Dumps the browser city's land polygons (Manhattan LAND_POLY + far shores FAR_LANDS) for the UE water shore map.
// usage: node tools/water/dump_shores.mjs <out.json>
import fs from 'node:fs';
globalThis.location = { search: '' }; globalThis.window = globalThis;
const { LAND_POLY, G } = await import('../../src/world/layout.js');
const { FAR_LANDS } = await import('../../src/world/farshore.js');
const out = { WATER_Y: G.WATER_Y, lands: [{ name: 'manhattan', pts: LAND_POLY }, ...FAR_LANDS.map(l => ({ name: l.name, pts: l.pts }))] };
fs.writeFileSync(process.argv[2], JSON.stringify(out));
console.log('lands', out.lands.map(l => `${l.name}:${l.pts.length}`).join(' '));
