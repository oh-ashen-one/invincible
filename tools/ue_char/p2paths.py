# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""P2 Characters: where the tools read and write, relocatable (no worktree or user paths baked in).

  P2_WT       repo root (default: two levels above this file)
  P2_SCRATCH  derived, git-ignored build inputs + caches (default: <P2_WT>/unreal/WebHomage/Saved/P2Build)
  P2_RAW      the owner's raw Tripo people (default: ~/sm2-assets/raw; only the 'prep' of enemies needs it)
Import from any tool:  sys.path.insert(0, <tools/ue_char>); from p2paths import WT, SCRATCH, scr
"""
import os

WT = os.path.abspath(os.environ.get('P2_WT') or os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
SCRATCH = os.path.abspath(os.environ.get('P2_SCRATCH') or os.path.join(WT, 'unreal', 'WebHomage', 'Saved', 'P2Build'))
RAW = os.path.abspath(os.path.expanduser(os.environ.get('P2_RAW') or '~/sm2-assets/raw'))


def scr(*parts):
    """A path under the scratch root (not created)."""
    return os.path.join(SCRATCH, *parts)


if __name__ == '__main__':   # shell helper: eval "$(python3 tools/ue_char/p2paths.py)"
    print('export P2_WT=%s P2_SCRATCH=%s P2_RAW=%s' % tuple("'" + p + "'" for p in (WT, SCRATCH, RAW)))
