"""Compile the per-user Windows installer with an available Inno Setup 7 compiler."""

import argparse
import subprocess
from pathlib import Path

from build_windows import ROOT, main


def build():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iscc", required=True, type=Path, help="Path to official ISCC.exe")
    args = parser.parse_args()
    from scenescout import __version__

    stage = main()
    (stage / ".installed").write_text("per-user\n", encoding="utf-8")
    subprocess.run(
        [
            str(args.iscc.resolve()),
            f"/DAppVersion={__version__}",
            f"/DStageDir={stage}",
            f"/DOutputDir={ROOT / 'dist'}",
            str(ROOT / "scripts" / "windows.iss"),
        ],
        check=True,
    )


if __name__ == "__main__":
    build()
