#!/usr/bin/env python3
"""Build the Night 1 live progress page from docs/night1/progress.json.

Writes <out>/index.html plus <out>/media/* (copied from repo-relative or absolute
paths referenced in the JSON) and prints a JSON map of published path -> source
for the Artifact `files` parameter.

  python3 tools/night1/progress.py [out_dir]
"""
import html, json, os, shutil, sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = sys.argv[1] if len(sys.argv) > 1 else "/Users/midir/sm2-n1/_scratch/progress"
data = json.load(open(os.path.join(REPO, "docs/night1/progress.json")))
files = {}


def media(src):
    """Copy a media file next to the page and return its published relative path."""
    p = src if os.path.isabs(src) else os.path.join(REPO, src)
    if not os.path.exists(p):
        return None
    name = "media/" + src.strip("/").replace("/", "__").replace(" ", "_")
    os.makedirs(os.path.join(OUT, "media"), exist_ok=True)
    dst = os.path.join(OUT, name)
    if not os.path.exists(dst) or os.path.getmtime(dst) < os.path.getmtime(p):
        shutil.copy2(p, dst)
    files[name] = dst
    return name


e = html.escape
STATE = {"building": "Building", "critic": "With critic", "fixing": "Fixing gap",
         "queued": "Queued", "blocked": "Blocked", "meets": "Meets target",
         "approaches": "Approaches target", "fails": "Fails target", "done": "Done"}


def pill(state):
    return f'<span class="pill s-{e(state)}">{e(STATE.get(state, state))}</span>'


def fig(item):
    src = media(item["src"])
    if not src:
        return f'<figure class="missing"><div>missing: {e(item["src"])}</div><figcaption>{e(item.get("label", ""))}</figcaption></figure>'
    if src.endswith((".mp4", ".webm", ".mov")):
        body = f'<video src="{src}" controls muted loop playsinline preload="metadata"></video>'
    else:
        body = f'<a href="{src}" target="_blank" rel="noopener"><img src="{src}" alt="{e(item.get("label", ""))}" loading="lazy"></a>'
    return f'<figure>{body}<figcaption>{e(item.get("label", ""))}</figcaption></figure>'


rows = "".join(
    f'<tr><td class="id">{e(p["id"])}</td><td><b>{e(p["name"])}</b><div class="mono dim">{e(p["branch"])}</div></td>'
    f'<td>{pill(p["state"])}</td><td class="num">{p.get("round") or "–"}</td>'
    f'<td>{e(p.get("verdict") or "–")}</td><td class="gap">{e(p.get("gap") or "")}</td></tr>'
    for p in data["pieces"])

comps = "".join(
    f'<section class="comp"><h3>{e(c["title"])}</h3><p class="dim">{e(c.get("note", ""))}</p>'
    f'<div class="figs n{len(c["images"])}">{"".join(fig(i) for i in c["images"])}</div></section>'
    for c in data.get("comparisons", [])) or '<p class="empty">Before/after comparisons appear here after the first critic round.</p>'

clips = "".join(fig({"src": c["src"], "label": c["title"] + (" — " + c["caption"] if c.get("caption") else "")})
                for c in data.get("clips", [])) or '<p class="empty">Gameplay clips appear here once the baseline playtest and the first Unreal rounds finish.</p>'

critic = "".join(
    f'<li><div class="row"><span class="mono">{e(c["t"])}</span><b>{e(c["piece"])} · round {e(str(c["round"]))}</b>{pill(c["verdict"])}</div>'
    f'<p><b>Biggest gap:</b> {e(c["gap"])}</p>' + (f'<p class="dim">{e(c["notes"])}</p>' if c.get("notes") else "") + "</li>"
    for c in reversed(data.get("critic", []))) or '<li class="empty">No critic verdicts yet.</li>'

perf = "".join(
    f'<tr><td>{e(p["what"])}</td><td class="num">{e(p["output"])}</td><td class="num">{e(p["internal"])}</td>'
    f'<td class="num">{e(p["median"])}</td><td class="num">{e(p["p95"])}</td><td class="num">{e(p.get("p99", "–"))}</td>'
    f'<td class="num">{e(p.get("hitches", "–"))}</td><td class="dim">{e(p.get("notes", ""))}</td></tr>'
    for p in data.get("perf", [])) or '<tr><td colspan="8" class="empty">No gameplay measurements yet.</td></tr>'

gaps = "".join(f"<li>{e(g)}</li>" for g in data.get("gaps", []))
try:
    L = json.load(open(os.path.join(REPO, "docs/night1/model-ledger.json")))
    ledger = "".join(
        f'<tr><td>{e(r["piece"])}</td><td class="num">{r["round"]}</td><td>{e(r["model"])} <span class="dim">{e(r["effort"])}</span></td>'
        f'<td class="num">{" · ".join(str(x) for x in r["scores"])}</td><td class="num"><b>{sum(r["scores"])/len(r["scores"]):.1f}</b></td></tr>'
        for r in L["rounds"])
    ledger_note = e(L["note"])
except Exception:
    ledger, ledger_note = "", ""
log = "".join(f'<li><span class="mono">{e(l["t"])}</span> {e(l["text"])}</li>' for l in reversed(data.get("log", [])))

page = f"""<title>Night 1 Loop Board</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
/* Layout: a working board — status table first, then evidence (comparisons, clips), then critic log, perf and gaps. */
:root {{
  --bg: #eef0f3; --panel: #ffffff; --fg: #15191f; --dim: #5a6472; --line: #d5dae1; --accent: #1f4fd1;
  --good: #1d7a46; --warn: #a86400; --bad: #b3261e; --idle: #6b7280;
  --display: "Barlow Condensed", "Arial Narrow", sans-serif; --body: "IBM Plex Sans", system-ui, sans-serif; --mono: "IBM Plex Mono", ui-monospace, monospace;
}}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{
  --bg: #0f131a; --panel: #171c25; --fg: #e6e9ee; --dim: #9aa4b2; --line: #2a3140; --accent: #7fa2ff;
  --good: #5cc98b; --warn: #f0b04a; --bad: #ff8a80; --idle: #8b95a3; color-scheme: dark }} }}
:root[data-theme="dark"] {{
  --bg: #0f131a; --panel: #171c25; --fg: #e6e9ee; --dim: #9aa4b2; --line: #2a3140; --accent: #7fa2ff;
  --good: #5cc98b; --warn: #f0b04a; --bad: #ff8a80; --idle: #8b95a3; color-scheme: dark }}
body {{ background: var(--bg); color: var(--fg); font: 15px/1.55 var(--body); }}
.wrap {{ max-width: 1280px; margin: 0 auto; padding-inline: 20px; padding-block: 28px 64px; display: grid; gap: 36px; }}
h1, h2, h3 {{ font-family: var(--display); letter-spacing: .01em; text-wrap: balance; margin: 0; }}
h1 {{ font-size: clamp(2.2rem, 5vw, 3.4rem); line-height: 1; }}
h2 {{ font-size: 1.7rem; text-transform: uppercase; letter-spacing: .04em; border-bottom: 2px solid var(--fg); padding-bottom: 4px; }}
h3 {{ font-size: 1.3rem; }}
header {{ display: grid; gap: 10px; }}
.eyebrow {{ font: 500 .78rem var(--mono); letter-spacing: .08em; text-transform: uppercase; color: var(--accent); }}
.lede {{ max-width: 70ch; font-size: 1.05rem; margin: 0; }}
.meta {{ display: flex; flex-wrap: wrap; gap: 8px 22px; color: var(--dim); font: .82rem var(--mono); }}
.disclaimer {{ font-size: .8rem; color: var(--dim); max-width: 80ch; margin: 0; }}
section {{ display: grid; gap: 14px; min-width: 0; }}
.tablewrap {{ overflow-x: auto; background: var(--panel); border: 1px solid var(--line); }}
table {{ border-collapse: collapse; width: 100%; font-size: .9rem; }}
th, td {{ text-align: left; padding: 10px 12px; border-bottom: 1px solid var(--line); vertical-align: top; }}
th {{ font: 500 .72rem var(--mono); text-transform: uppercase; letter-spacing: .07em; color: var(--dim); }}
td.id {{ font: 600 .9rem var(--mono); }} td.num {{ font-variant-numeric: tabular-nums; white-space: nowrap; }}
td.gap {{ min-width: 220px; }}
.mono {{ font-family: var(--mono); font-size: .8rem; }} .dim {{ color: var(--dim); }}
.pill {{ display: inline-block; font: 500 .72rem var(--mono); text-transform: uppercase; letter-spacing: .05em; padding: 2px 8px; border: 1px solid currentColor; white-space: nowrap; }}
.s-meets, .s-done {{ color: var(--good); }} .s-approaches, .s-critic, .s-fixing {{ color: var(--warn); }}
.s-fails, .s-blocked {{ color: var(--bad); }} .s-building {{ color: var(--accent); }} .s-queued {{ color: var(--idle); }}
.figs {{ display: grid; gap: 10px; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); }}
figure {{ margin: 0; background: var(--panel); border: 1px solid var(--line); min-width: 0; }}
figure img, figure video {{ display: block; width: 100%; max-width: 100%; height: auto; background: #000; }}
figcaption {{ padding: 6px 10px; font-size: .82rem; color: var(--dim); }}
figure.missing div {{ padding: 30px 10px; font: .8rem var(--mono); color: var(--bad); }}
.comp {{ gap: 8px; }} .comp p {{ margin: 0; }}
ol.critic {{ list-style: none; padding: 0; margin: 0; display: grid; gap: 10px; }}
ol.critic li {{ background: var(--panel); border: 1px solid var(--line); padding: 12px 14px; }}
ol.critic .row {{ display: flex; flex-wrap: wrap; gap: 6px 14px; align-items: center; }}
ol.critic p {{ margin: 6px 0 0; max-width: 90ch; }}
ul.gaps, ul.log {{ margin: 0; padding-left: 1.2em; display: grid; gap: 6px; max-width: 95ch; }}
ul.log {{ list-style: none; padding: 0; }}
.empty {{ color: var(--dim); font-style: italic; }}
.two {{ display: grid; gap: 36px; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); }}
a {{ color: var(--accent); }} a:focus-visible, video:focus-visible {{ outline: 2px solid var(--accent); outline-offset: 2px; }}
</style>
<div class="wrap">
<header>
  <div class="eyebrow">Opus 5.5 Loop · Night 1 · {e(data["phase"])}</div>
  <h1>Night 1 Loop Board</h1>
  <p class="lede">{e(data["headline"])}</p>
  <div class="meta"><span>Updated {e(data["updated"])}</span><span>Branch Opus-5.5-Loop-Night-1</span><span>{e(data["target"])}</span></div>
  <p class="disclaimer">Homage fan project. Not an official Marvel, Sony or Insomniac game and not affiliated with them; nothing here is meant to infringe. Reference frames from the real game are used privately for critique only and are not shown on this page.</p>
</header>
<section><h2>Pieces</h2>
<div class="tablewrap"><table><thead><tr><th>ID</th><th>Piece</th><th>State</th><th>Round</th><th>Latest verdict</th><th>Current biggest gap</th></tr></thead><tbody>{rows}</tbody></table></div></section>
<section><h2>Before / after</h2>{comps}</section>
<section><h2>Gameplay clips</h2><div class="figs">{clips}</div></section>
<section><h2>Critic findings</h2><ol class="critic">{critic}</ol></section>
<section><h2>Performance in real gameplay</h2>
<div class="tablewrap"><table><thead><tr><th>Build / sequence</th><th>Output</th><th>Internal res</th><th>Median ms</th><th>p95 ms</th><th>p99 ms</th><th>Hitches &gt;33 ms</th><th>Notes</th></tr></thead><tbody>{perf}</tbody></table></div></section>
<section><h2>Model ledger</h2><p class="dim" style="margin:0;max-width:90ch">{ledger_note}</p>
<div class="tablewrap"><table><thead><tr><th>Piece</th><th>Round</th><th>Builder model</th><th>Critic axis scores</th><th>Avg</th></tr></thead><tbody>{ledger}</tbody></table></div></section>
<div class="two">
<section><h2>Remaining gaps</h2><ul class="gaps">{gaps}</ul></section>
<section><h2>Log</h2><ul class="log">{log}</ul></section>
</div>
</div>
"""
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, "index.html"), "w").write(page)
print(json.dumps(files))
