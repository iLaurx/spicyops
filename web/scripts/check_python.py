"""Syntax and read-only contract checks; never imports librouteros or connects."""
import ast
import json
import re
from pathlib import Path

chapters = json.loads(Path('src/content/guide.json').read_text(encoding='utf-8'))
count = 0
for chapter in chapters:
    for lang, code in re.findall(r'```(python|bash)\n(.*?)\n```', chapter['body'], re.S):
        if lang == 'python':
            ast.parse(code)
            count += 1
        elif "<<'PY'" in code:
            ast.parse(code.split("<<'PY'\n", 1)[1].rsplit('\nPY', 1)[0])
            count += 1
script = Path('public/downloads/spicyops-check-api.py').read_text(encoding='utf-8')
paths = re.findall(r'\("(/[^\"]+)"', script)
assert set(paths) == {'/system/identity/print', '/system/resource/print', '/queue/simple/print', '/ip/firewall/address-list/print'}
assert 'CERT_NONE' not in script and 'check_hostname = False' not in script
assert 'sys.stdin.isatty()' in script and 'getpass(' in script
print(f'{count} Python blocks parsed; download limited to four /print paths with TLS validation.')
