"""Vendor the OFL fonts used by DESING.md; never requested by the running app."""
from pathlib import Path
from urllib.request import urlopen

folder = Path(__file__).resolve().parents[1] / 'portal/static/portal/fonts'
folder.mkdir(parents=True, exist_ok=True)
files = {
    'Barlow-Regular.ttf': 'barlow/Barlow-Regular.ttf',
    'Barlow-Medium.ttf': 'barlow/Barlow-Medium.ttf',
    'BarlowSemiCondensed-SemiBold.ttf': 'barlowsemicondensed/BarlowSemiCondensed-SemiBold.ttf',
    'BarlowSemiCondensed-Bold.ttf': 'barlowsemicondensed/BarlowSemiCondensed-Bold.ttf',
    'JetBrainsMono.ttf': 'jetbrainsmono/JetBrainsMono%5Bwght%5D.ttf',
    'Barlow-OFL.txt': 'barlow/OFL.txt',
    'BarlowSemiCondensed-OFL.txt': 'barlowsemicondensed/OFL.txt',
    'JetBrainsMono-OFL.txt': 'jetbrainsmono/OFL.txt',
}
for name, relative in files.items():
    with urlopen('https://raw.githubusercontent.com/google/fonts/main/ofl/' + relative, timeout=30) as response:
        (folder / name).write_bytes(response.read())
    print(name)
