import os
import re

builtins = {'len', 'range', 'str', 'int', 'float', 'list', 'dict', 'set', 'bool', 'Exception', 'print', 'open', 'range', 'enumerate', 'zip', 'None', 'True', 'False', 'self', 'cls', 'args', 'kwargs', 'getattr', 'hasattr', 'setattr', 'isinstance', 'issubclass', 'iter', 'next', 'super', 'type', 'vars', 'ValueError', 'TypeError', 'RuntimeError', 'StopIteration', 'AttributeError', 'ImportError', 'KeyError', 'IndexError', 'NotImplementedError', 'property', 'staticmethod', 'classmethod', 'object', 'repr', 'hash', 'Any', 'List', 'Dict', 'Optional', 'tuple', 'callable'}

def get_mapping(content, slug):
    names = set()
    names.update(re.findall(r'^(?:class|def)\s+(\w+)', content, re.MULTILINE))
    
    lines = content.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        trimmed = line.lstrip()
        if trimmed.startswith('import '):
            rest = trimmed[7:]
            parts = rest.split(',')
            for p in parts:
                p = p.strip()
                if ' as ' in p: names.add(p.split(' as ')[1].strip())
                else: names.add(p.split('.')[-1].strip() if '.' in p else p.strip())
        elif trimmed.startswith('from '):
            if ' import ' in trimmed:
                post = trimmed.split(' import ', 1)[1]
                if '(' in post and ')' not in post:
                    j = i + 1
                    while j < len(lines) and ')' not in lines[j]:
                        post += " " + lines[j]
                        j += 1
                    if j < len(lines): post += " " + lines[j]
                    i = j
                ents = post.strip('() \n')
                for p in re.split(r'[,\s]+', ents):
                    p = p.strip()
                    if not p or p == 'as': continue
                    names.add(p)
        i += 1
    
    mapping = {name: f"{name}{slug}" for name in names if name not in builtins and not name.startswith('__')}
    return mapping

def transform_content(content, slug, abs_path):
    mapping = get_mapping(content, slug)
    sorted_names = sorted(mapping.items(), key=lambda x: len(x[0]), reverse=True)
    
    new_lines = []
    lines = content.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        line = line.replace('__file__', f"'{abs_path}'")
        trimmed = line.lstrip()
        
        if trimmed.startswith('import '):
             prefix_idx = line.find('import ')
             prefix = line[:prefix_idx + 7]
             rest = line[prefix_idx + 7:]
             parts = rest.split(',')
             new_parts = []
             for p in parts:
                 p = p.strip()
                 if not p: continue
                 if ' as ' in p:
                     base, alias = p.split(' as ')
                     new_parts.append(f"{base.strip()} as {alias.strip()}{slug}")
                 else:
                     if p in mapping: new_parts.append(f"{p} as {mapping[p]}")
                     else: new_parts.append(p)
             new_lines.append(prefix + ", ".join(new_parts))
        elif trimmed.startswith('from '):
             import_idx = line.find(' import ')
             pre = line[:import_idx + 8]
             post = line[import_idx + 8:]
             
             entities_str = post
             if '(' in post and ')' not in post:
                 j = i + 1
                 while j < len(lines) and ')' not in lines[j]:
                     entities_str += "\n" + lines[j]
                     j += 1
                 if j < len(lines):
                     entities_str += "\n" + lines[j]
                 i = j
             
             for name, new_name in sorted_names:
                 entities_str = re.sub(r'\b' + re.escape(name) + r'\b(?!\s+as\b)', f"{name} as {new_name}", entities_str)
             new_lines.append(pre + entities_str)
        else:
             for name, new_name in sorted_names:
                 line = re.sub(r'\b' + re.escape(name) + r'\b', new_name, line)
             new_lines.append(line)
        i += 1
    return "\n".join(new_lines)

def main():
    files = [
        ("tests/test_stress.py", "_test_stress"),
        ("tests/unit/test_synthesis_bridges.py", "_test_synthesis_bridges"),
        ("tests/unit/test_synthesis_cli.py", "_test_synthesis_cli"),
        ("tests/unit/test_synthesis_completion.py", "_test_synthesis_completion"),
        ("tests/unit/test_synthesis_engine_advanced.py", "_test_synthesis_engine_advanced"),
        ("tests/unit/test_synthesis_engine_contextual.py", "_test_synthesis_engine_contextual"),
        ("tests/unit/test_synthesis_packaging.py", "_test_synthesis_packaging"),
        ("tests/unit/test_synthesis_performance.py", "_test_synthesis_performance"),
        ("tests/unit/test_synthesis_versioning.py", "_test_synthesis_versioning"),
    ]

    monolithic = "tests/tests.py"
    with open(monolithic, 'a', encoding='utf-8') as out:
        for f_path, slug in files:
            if not os.path.exists(f_path):
                print(f"File not found: {f_path}")
                continue
                
            with open(f_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            abs_path = os.path.abspath(f_path).replace("\\", "/")
            transformed = transform_content(content, slug, abs_path)
            
            header = f"\n\n# {'='*80}\n# FROM FILE: {f_path}\n# {'='*80}\n\n"
            out.write(header + transformed + "\n")
            print(f"Merged {f_path}")

if __name__ == "__main__":
    main()
