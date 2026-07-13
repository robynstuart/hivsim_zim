"""Plotting utilities: shared font + style setup."""

from pathlib import Path

import sciris as sc

REPO = Path(__file__).resolve().parent


def set_font(size=14, font='Libertinus Sans'):
    """Register Libertinus Sans and set as the matplotlib default.

    Default font size 14 targets slide-readable figures at 10 x 5 inches.
    """
    fontfile = REPO / 'assets' / 'LibertinusSans-Regular.otf'
    if fontfile.exists():
        sc.fonts(add=fontfile)
        sc.options(font=font, fontsize=size)
    else:
        sc.options(fontsize=size)
