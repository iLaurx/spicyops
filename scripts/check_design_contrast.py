"""Check the actual text, focus and essential control tokens from app.css."""
import json
from pathlib import Path
import re

root = Path(__file__).resolve().parents[1]
css = (root/'portal/static/portal/app.css').read_text(encoding='utf-8-sig')
themes = {}
for name, selector in [('light', r':root\s*\{([^}]+)\}'), ('dark', r':root\[data-theme="dark"\]\s*\{([^}]+)\}')]:
    block = re.search(selector, css).group(1)
    themes[name] = dict(re.findall(r'--([\w-]+):\s*(#[0-9a-fA-F]{6})', block))

def luminance(color):
    values = [int(color[i:i+2], 16)/255 for i in (1, 3, 5)]
    linear = [v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4 for v in values]
    return sum(a*b for a, b in zip(linear, [.2126, .7152, .0722]))

def ratio(a, b):
    low, high = sorted([luminance(tokens[a]), luminance(tokens[b])])
    return (high+.05)/(low+.05)

pairs = [(a, b, 4.5) for a, b in [('ink', 'bg'), ('heading', 'paper'), ('muted', 'paper'),
         ('muted', 'sidebar'), ('on-action', 'action'), ('success', 'success-bg'),
         ('warning', 'warning-bg'), ('danger', 'danger-bg'), ('neutral', 'neutral-bg'),
         ('info', 'info-bg'), ('on-danger', 'danger-action'), ('on-action', 'action-hover')]]
pairs += [('control-border', 'surface-soft', 3), ('focus', 'paper', 3), ('brand', 'surface-deep', 3)]
report = {}
for name, tokens in themes.items():
    report[name] = {f'{a}/{b}': round(ratio(a, b), 2) for a, b, _ in pairs}
    for a, b, minimum in pairs:
        assert ratio(a, b) >= minimum, (name, a, b, ratio(a, b), minimum)
folder = root/'build/redesign'
folder.mkdir(parents=True, exist_ok=True)
(folder/'contrast.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print('OK: text >= 4.5:1; essential controls, icons and focus >= 3:1.', report)
