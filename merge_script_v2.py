import os
import re

def get_mapping(content, slug):
    names = set()
    # Top level defs/classes
    names.update(re.findall(r'^(?:class|def)\s+(\w+)', content, re.MULTILINE))
    
    # Imports
    # import a as b, c
    for line in content.splitlines():
        trimmed = line.lstrip()
        if trimmed.startswith('import '):
            parts = trimmed[7:].split(',')
            for p in parts:
                p = p.strip()
                if ' as ' in p: names.add(p.split(' as ')[1].strip())
                else: names.add(p.split('.')[-1].strip() if '.' in p else p.strip())
        elif trimmed.startswith('from '):
            if ' import ' in trimmed:
                ents = trimmed.split(' import ', 1)[1].strip('() \n')
                for p in re.split(r'[,\s]+', ents):
                    p = p.strip()
                    if not p or p == 'as': continue
                    # This is rough but should catch most aliases
                    names.add(p)

    builtins = {'len', 'range', 'str', 'int', 'float', 'list', 'dict', 'set', 'bool', 'Exception', 'print', 'open', 'range', 'enumerate', 'zip', 'None', 'True', 'False', 'self', 'cls', 'args', 'kwargs', 'getattr', 'hasattr', 'setattr', 'isinstance', 'issubclass', 'iter', 'next', 'super', 'type', 'vars', 'ValueError', 'TypeError', 'RuntimeError', 'StopIteration', 'AttributeError', 'ImportError', 'KeyError', 'IndexError', 'NotImplementedError', 'property', 'staticmethod', 'classmethod', 'object', 'repr', 'hash'}
    mapping = {name: f"{name}{slug}" for name in names if name not in builtins and not name.startswith('__')}
    return mapping

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
            mapping = get_mapping(content, slug)
            sorted_names = sorted(mapping.items(), key=lambda x: len(x[0]), reverse=True)
            
            lines = content.splitlines()
            new_lines = []
            in_multiline_import = False
            for line in lines:
                line = line.replace('__file__', f"'{abs_path}'")
                trimmed = line.lstrip()
                
                if trimmed.startswith('import '):
                    prefix = line[:line.find('import ') + 7]
                    rest = line[line.find('import ') + 7:]
                    parts = rest.split(',')
                    new_parts = []
                    for p in parts:
                        p = p.strip()
                        if ' as ' in p:
                            base, alias = p.split(' as ')
                            new_parts.append(f"{base.strip()} as {alias.strip()}{slug}")
                        else:
                            if p in mapping: new_parts.append(f"{p} as {mapping[p]}")
                            else: new_parts.append(p)
                    new_lines.append(prefix + ", ".join(new_parts))
                elif trimmed.startswith('from '):
                    if ' import ' in line:
                        pre_idx = line.find(' import ')
                        pre = line[:pre_idx + 8]
                        post = line[pre_idx + 8:]
                        if '(' in post: in_multiline_import = True
                        if ')' in post: in_multiline_import = False
                        
                        entities = post.strip('() \n')
                        parts = entities.split(',')
                        new_entities = []
                        for p in parts:
                            p = p.strip()
                            if not p: continue
                            if ' as ' in p:
                                base, alias = p.split(' as ')
                                new_entities.append(f"{base.strip()} as {alias.strip()}{slug}")
                            else:
                                if p in mapping: new_entities.append(f"{p} as {mapping[p]}")
                                else: new_entities.append(p)
                        
                        wrapped = f"({', '.join(new_entities)})" if '(' in post else ", ".join(new_entities)
                        new_lines.append(pre + wrapped)
                    else:
                        new_lines.append(line)
                elif in_multiline_import:
                    if ')' in line: in_multiline_import = False
                    # This is still a bit rough for multiline
                    for name, new_name in sorted_names:
                        line = re.sub(r'\b' + re.escape(name) + r'\b(?!\s+as\b)', f"{name} as {new_name}", line)
                    new_lines.append(line)
                else:
                    for name, new_name in sorted_names:
                        line = re.sub(r'\b' + re.escape(name) + r'\b', new_name, line)
                    new_lines.append(line)
            
            header = f"\n\n# {'='*80}\n# FROM FILE: {f_path}\n# {'='*80}\n\n"
            out.write(header + "\n".join(new_lines) + "\n")
            print(f"Merged {f_path}")

if __name__ == "__main__":
    main()
