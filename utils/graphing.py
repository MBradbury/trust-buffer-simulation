from __future__ import annotations

import subprocess

def check_fonts(path: str):
	# Not all papers like having type 3 fonts, 
	# so check if there are any

    r = subprocess.run(f"pdffonts {path}",
        shell=True,
        check=True,
        capture_output=True,
        universal_newlines=True,
        encoding="utf-8",
    )

    if "Type 3" in r.stdout:
        raise RuntimeError(f"Type 3 font in {path}")

def savefig(fig, target: str, crop=False):
    fig.savefig(target, bbox_inches='tight')

    if crop:
        subprocess.run(f"pdfcrop {target} {target}", shell=True)

    print("Produced:", target)
    check_fonts(target)
