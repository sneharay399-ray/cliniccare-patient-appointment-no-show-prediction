import os
import re

checked = set()
errors = []

def check_file(path):
    if path in checked:
        return
    if not os.path.exists(path):
        return
    checked.add(path)
    with open(path, encoding='utf-8', errors='ignore') as f:
        content = f.read()
    base = os.path.dirname(path)
    pattern = r"from\s+[\"'](\.\.?/[^\"']+)[\"']"
    for imp in re.findall(pattern, content):
        resolved = os.path.normpath(os.path.join(base, imp))
        found = False
        for ext in ['', '.jsx', '.js']:
            if os.path.exists(resolved + ext):
                found = True
                check_file(resolved + ext)
                break
        if not found:
            for ext in ['/index.jsx', '/index.js']:
                if os.path.exists(resolved + ext):
                    found = True
                    break
        if not found:
            errors.append('MISSING: {} in {}'.format(imp, os.path.relpath(path)))

check_file('healthcare-app/frontend/src/App.jsx')
check_file('healthcare-app/frontend/src/main.jsx')

if errors:
    for e in errors:
        print(e)
else:
    print('All imports resolved OK ({} files checked)'.format(len(checked)))
