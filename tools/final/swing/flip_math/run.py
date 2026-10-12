#!/usr/bin/env python3
"""Compile current real WebFlips code plus the actual PostAnimTick root composition."""
import argparse
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=Path(__file__).resolve().parents[4])
    parser.add_argument("--compiler", default=os.environ.get("CXX", "clang++"))
    args = parser.parse_args()
    fixture = Path(__file__).resolve().parent
    traversal = args.source_root / "unreal/WebHomage/Source/WebHomage/Traversal"
    flips = (traversal / "WebTravFlips.cpp").read_text()
    character = (traversal / "WebTravCharacter.cpp").read_text()
    pure = flips[flips.index("namespace WebFlips"):flips.index("// ---- Tricks C round 1: rendered-pose logger")]
    post = character[character.index("void AWebTravCharacter::PostAnimTick"):character.index("void AWebTravCharacter::EndAnimTick")]
    composition = re.search(r"const FQuat Q = .*?;", post)
    if composition is None:
        raise RuntimeError("PostAnimTick root composition changed; update the extraction deliberately")
    rendered = """#pragma once
#include "CoreMinimal.h"
inline FQuat RenderedRootComposition(const FQuat& FlipBodyFrame, const FQuat& FlipOffQ, const FQuat& SwayDeltaQ)
{
""" + composition.group(0) + "\nreturn Q;\n}\n"
    print("WebTravFlips.cpp sha256=" + hashlib.sha256(flips.encode()).hexdigest(), flush=True)
    print("PostAnimTick composition=" + composition.group(0), flush=True)
    with tempfile.TemporaryDirectory(prefix="sm2-flip-math-") as directory:
        build = Path(directory)
        (build / "program.cpp").write_text('#include "WebTravFlips.h"\n' + pure)
        (build / "rendered_root.hpp").write_text(rendered)
        shutil.copyfile(traversal / "WebTravFlips.h", build / "WebTravFlips.h")
        shutil.copyfile(fixture / "CoreMinimal.h", build / "CoreMinimal.h")
        subprocess.run([args.compiler, "-std=c++17", "-O2", "-I", str(build),
                        str(build / "program.cpp"), str(fixture / "check.cpp"),
                        "-o", str(build / "check")], check=True)
        subprocess.run([str(build / "check")], check=True)


if __name__ == "__main__":
    main()
