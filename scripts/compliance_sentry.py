import os
import sys
import hashlib
import json

# Break up the literal so it doesn't match itself
HEADER_MARKER = "This file is part of the " + "Polyglot FFI Contract Verifier ecosystem."

def get_comment_style(ext):
    if ext in ['.py', '.sh', '.yml', '.yaml']:
        return '# ', '#'
    elif ext in ['.c', '.h', '.cpp', '.hpp', '.js', '.ts', '.java', '.go', '.rs', '.css', '.md']:
        return '<!-- ' if ext == '.md' else '// ', ' -->' if ext == '.md' else '//'
    elif ext in ['.html', '.xml']:
        return '<!-- ', ' -->'
    return None, None

def load_template():
    template_path = os.path.join(os.path.dirname(__file__), 'header_template.txt')
    if not os.path.exists(template_path):
        print(f"Error: Could not find {template_path}")
        sys.exit(1)
    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()

def generate_header(body_hash, prefix, suffix, template):
    filled = template.replace("{file_hash}", body_hash)
    lines = []
    for line in filled.splitlines():
        if suffix != prefix and suffix != '' and not suffix.startswith('//') and not suffix.startswith('#'):
             lines.append(f"{prefix}{line}{suffix}")
        else:
             lines.append(f"{prefix}{line}".rstrip())
    return "\n".join(lines) + "\n\n"

def process_file(filepath, template, verify_only=False):
    # Prevent the script from modifying itself by skipping its own filename
    if os.path.basename(filepath) == 'compliance_sentry.py':
        return True

    ext = os.path.splitext(filepath)[1].lower()
    
    if ext == '.json':
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            data = json.loads(content)
            if not isinstance(data, dict): return True
            if '_gov_header' in data: del data['_gov_header']
            body_str = json.dumps(data, sort_keys=True)
            body_hash = hashlib.sha256(body_str.encode('utf-8')).hexdigest()[:16]
            header_text = template.replace("{file_hash}", body_hash)
            new_data = {"_gov_header": header_text.splitlines()}
            new_data.update(data)
            new_content = json.dumps(new_data, indent=2) + "\n"
            if content.strip() != new_content.strip():
                if verify_only: return False
                with open(filepath, 'w', encoding='utf-8') as f: f.write(new_content)
            return True
        except Exception as e:
            return True

    prefix, suffix = get_comment_style(ext)
    if not prefix: return True

    try:
        with open(filepath, 'r', encoding='utf-8') as f: content = f.read()
    except Exception: return True

    body = content
    # Check if the header marker is physically present at the beginning
    if content.startswith(prefix) and HEADER_MARKER in content[:2000]:
        lines = content.splitlines()
        header_end_idx = 0
        magic_identifier = "File Integrity " + "Identifier:"
        magic_equals = "===" + "===" + "==="
        for i, line in enumerate(lines[:50]):
            if magic_identifier in line or magic_equals in line:
                header_end_idx = i
                
        if header_end_idx > 0:
            while header_end_idx + 1 < len(lines) and (lines[header_end_idx+1].strip() == '' or prefix.strip() in lines[header_end_idx+1]):
                header_end_idx += 1
            body = "\n".join(lines[header_end_idx+1:]).lstrip()

    body_hash = hashlib.sha256(body.encode('utf-8')).hexdigest()[:16]
    new_header = generate_header(body_hash, prefix, suffix, template)
    new_content = new_header + body

    if content != new_content:
        if verify_only: return False
        with open(filepath, 'w', encoding='utf-8') as f: f.write(new_content)

    return True

def main():
    verify_only = '--verify' in sys.argv
    failed = False
    template = load_template()
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    
    for root, dirs, files in os.walk(repo_root):
        if any(skip in root for skip in ['.git', 'node_modules', 'venv', '__pycache__', 'governance']):
            continue
        for file in files:
            # Skip ASTPL root documents
            if file in ['LICENSE', 'LICENSE.md', 'TERMS.md', 'CONTRIBUTING.md', 'EULA.MD', 'TOS.MD', 'robots.txt', '.gitattributes']:
                continue
            filepath = os.path.join(root, file)
            if not process_file(filepath, template, verify_only):
                print(f"FAILED: {os.path.relpath(filepath, repo_root)} header missing or invalid.")
                failed = True
                
    if verify_only and failed:
        sys.exit(1)
    else:
        print("Compliance Sentry executed successfully.")

if __name__ == '__main__':
    main()