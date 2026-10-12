# Build and test status (browser game, before)

Worktree `~/sm2-n1/browser-baseline`, branch `night1/browser-baseline`, base commit `847565a` (includes `Opus-5.5-Loop-Night-1` at `da1a83f`). Game code (`src/`, `public/`, `index.html`, `vite.config.js`, `package*.json`) is byte-identical to the integration branch; only `docs/night1/baseline/` was added. Node v26.8.2, npm 11.19.1, Vite 8.3.0, three 0.186.0, macOS on Mac Studio M3 Ultra. Raw logs: `logs/build/`.

| step | result | notes |
|---|---|---|
| `npm ci` | **OK** (0.9 s, 21 packages, 0 vulnerabilities) | npm warns that `fsevents@2.3.3` has an install script not covered by `allowScripts` (`npm install-scripts approve`); harmless here. |
| `npm test` | **OK, 15 / 15 pass** (0.2 s) | `node --test test/*.test.mjs`: destruction fracture (3 tests), tree skeleton / bark / wind patch (5), web-swing physics (7: projection, tension formula, arc length, energy conservation, pendulum period, loop). Nothing tests rendering, streaming, animation, combat or any system under `src/game/`; a green run says little about the game working. |
| `npx vite build` | **OK** (0.66 s, 184 modules) | Largest chunks: `index` 1.20 MB (462 kB gzip), `fonts` 877 kB, `preload-helper` 395 kB, `three.core` 377 kB, `systems` 214 kB, `fracture.worker` 174 kB. `dist/` = 182 MB (public assets copied). No build warnings. |
| game boots in headless Chrome | **OK** | `?playtest=1` reaches `__cmb` + `__sys` + `__ctx.player` in about 25 s at 1920x1080 (cold profile, dev server); `?shot=<name>` reaches `__shotReady` in 21-50 s per shot at 3840x2160. |

Not run: `vite preview` / production bundle playthrough (all captures use the dev server on port 5201).
