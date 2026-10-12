"""Machine / worktree specific locations of the P1 city pipeline, in ONE place. Every value can be overridden from the environment so that another worktree
(other dev port, other scratch folder, other MCP port) can build the city without editing files; the defaults are the values of the P1 worktree.
  SM2_CITY_SCRATCH   scratch root (export/, tex/, uejobs/, chrome-profile/)       default /Users/midir/sm2-n1/_scratch/city
  SM2_CITY_PORT      dev server port that serves the browser city (exporter)      default 5202
  SM2_CITY_EXPORT / SM2_CITY_TEX / SM2_CITY_JOBS   override the derived folders
  SM2_CITY_MCP_PORT  Unreal MCP port of launch_editor.sh                          default 8771"""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
SCRATCH = os.environ.get('SM2_CITY_SCRATCH', '/Users/midir/sm2-n1/_scratch/city')
PORT = os.environ.get('SM2_CITY_PORT', '5202')
EXPORT = os.environ.get('SM2_CITY_EXPORT', os.path.join(SCRATCH, 'export', 'midtown3x3'))
TEX = os.environ.get('SM2_CITY_TEX', os.path.join(SCRATCH, 'tex'))
JOBS = os.environ.get('SM2_CITY_JOBS', os.path.join(SCRATCH, 'uejobs'))
MCP_PORT = os.environ.get('SM2_CITY_MCP_PORT', '8771')
def asset_rel(url):
    """'http://127.0.0.1:<any port>/assets/city/tex/x.webp?v=1' -> 'assets/city/tex/x.webp' (manifest map URLs; the port depends on who exported)"""
    import re
    return re.sub(r'^https?://[^/]+/', '', url).split('?')[0]
