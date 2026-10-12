# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
# Shared strict-mode convention for the headless builders. build_manhattan.py sets SM2_STRICT=1 for every child.
#   * fail(): a required asset / actor / level / material was not produced. Strict: recorded and the build raises at finish(). Otherwise: a WARN line.
#   * warn(): purely cosmetic fallback (an optional property missing on this engine version). Always a WARN line.
#   * finish(): prints 'SM2_BUILD_FAILED: <script> <n> failures: <short list>' and raises, else prints 'SM2_BUILD_OK: <script>' (the last line a builder prints).
import os
import traceback

NIGHT_LIGHTS_LEVEL = '/Game/Look/Look_NightCity'   # the one night-lighting sublevel (the author's night mode port); every night map composes exactly this
LEGACY_NIGHT_LEVEL = '/Game/Look/Look_NightLights'   # the old night lights: must never be composed together with NIGHT_LIGHTS_LEVEL
TERRAIN_ROOT = '/Game/Terrain'   # build_terrain.py's root for the showcase; /Game/TerrainR5b is the preserved baseline and is never built
SHOWCASE_MAPS = {'golden': '/Game/Showcase/Maps/Manhattan_Showcase', 'midday': '/Game/Showcase/Maps/Manhattan_Showcase_Midday',
                 'night': '/Game/Showcase/Maps/Manhattan_Showcase_Night'}
SHOWCASE_COMMON_LEVELS = [TERRAIN_ROOT + '/City_Geo_T', '/Game/Look/Look_Boxes', '/Game/Maps/Manhattan_Actors', TERRAIN_ROOT + '/Terrain_Land',
                          '/Game/Water/Maps/Water_River', '/Game/Tests/Life/Life_Actors']
ISLAND_MAPS = {'golden': '/Game/Showcase/Maps/Manhattan_Island', 'midday': '/Game/Showcase/Maps/Manhattan_Island_Midday', 'night': '/Game/Showcase/Maps/Manhattan_Island_Night'}
ISLAND_WP_MAP = '/Game/Maps/Manhattan_WP'
PROPS_M3_LEVEL = '/Game/PropsM3/Maps/PropsM3_Island'   # the owner's supplied GLB props / animals (Scripts/build_props_m3.py; no collision HISMs)
ISLAND_COMMON_LEVELS = [TERRAIN_ROOT + '/Terrain_Land', '/Game/Water/Maps/Water_River', '/Game/Tests/Life/Life_Actors', PROPS_M3_LEVEL]   # level instances of the island maps (the WP map brings the city, its WHBox collision and the actors)
GAME_MODE_CLASS = '/Script/WebHomage.WebTravGameMode'
STRICT = os.environ.get('SM2_STRICT') == '1'


def island_levels(preset):
    """the level instances of an island showcase map (exactly these, no others)"""
    return ISLAND_COMMON_LEVELS + ['/Game/Look/Rigs/Look_Rig_' + preset] + ([NIGHT_LIGHTS_LEVEL] if preset == 'night' else [])


def showcase_levels(preset):
    """the always-loaded sublevels of a showcase map (exactly these, no others)"""
    return SHOWCASE_COMMON_LEVELS + ['/Game/Look/Rigs/Look_Rig_' + preset] + ([NIGHT_LIGHTS_LEVEL] if preset == 'night' else [])


class Build:
    def __init__(self, script):
        self.script = script
        self.failures = []

    def fail(self, msg, exc=None):
        text = '%s: %s' % (msg, str(exc).split('\n')[0][:160]) if exc is not None else str(msg)
        print('SM2_FAIL' if STRICT else 'WARN', self.script, text, flush=True)
        if exc is not None and STRICT:
            traceback.print_exc()
        if STRICT:
            self.failures.append(text)

    def warn(self, msg, exc=None):
        print('WARN', self.script, '%s: %s' % (msg, str(exc)[:160]) if exc is not None else msg, flush=True)

    def finish(self):
        if STRICT and self.failures:
            short = '; '.join(f[:100] for f in self.failures[:6]) + (' ...' if len(self.failures) > 6 else '')
            print('SM2_BUILD_FAILED: %s %d failures: %s' % (self.script, len(self.failures), short), flush=True)
            raise RuntimeError('SM2_BUILD_FAILED: %s %d failures' % (self.script, len(self.failures)))
        print('SM2_BUILD_OK: %s' % self.script, flush=True)
