import os
import re

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
    
    # Builtins and common names to avoid aliasing
    builtins = {'len', 'range', 'str', 'int', 'float', 'list', 'dict', 'set', 'bool', 'Exception', 'print', 'open', 'enumerate', 'zip', 'None', 'True', 'False', 'self', 'cls', 'args', 'kwargs', 'getattr', 'hasattr', 'setattr', 'isinstance', 'issubclass', 'iter', 'next', 'super', 'type', 'vars', 'ValueError', 'TypeError', 'RuntimeError', 'StopIteration', 'AttributeError', 'ImportError', 'KeyError', 'IndexError', 'NotImplementedError', 'property', 'staticmethod', 'classmethod', 'object', 'repr', 'hash'}

    with open(monolithic, 'a', encoding='utf-8') as out:
        for f_path, slug in files:
            if not os.path.exists(f_path):
                print(f"File not found: {f_path}")
                continue
                
            with open(f_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            abs_path = os.path.abspath(f_path).replace("\\", "/")
            
            # Identify names to alias
            top_names = re.findall(r'^(?:class|def)\s+(\w+)', content, re.MULTILINE)
            
            import_names = set()
            for line in content.splitlines():
                if line.lstrip().startswith('import '):
                    parts = line.lstrip()[7:].split(',')
                    for p in parts:
                        p = p.strip()
                        if ' as ' in p: import_names.add(p.split(' as ')[1].strip())
                        else: import_names.add(p.split('.')[-1].strip() if '.' in p else p.strip())
                elif line.lstrip().startswith('from '):
                    if ' import ' in line:
                         m = re.search(r'import\s+([^#\n]+)', line)
                         if m:
                             ents = m.group(1).strip('() ')
                             # Handle multi-line imports potentially
                             for p in re.split(r'[,\s]+', ents):
                                 p = p.strip()
                                 if not p or p == 'as': continue
                                 import_names.add(p)

            all_names = set(top_names) | import_names
            mapping = {n: f"{n}{slug}" for n in all_names if n not in builtins and not n.startswith('__')}
            sorted_names = sorted(mapping.items(), key=lambda x: len(x[0]), reverse=True)
            
            lines = content.splitlines()
            new_lines = []
            in_multiline_import = False
            for line in lines:
                # Handle __file__
                line = line.replace('__file__', f"'{abs_path}'")
                
                trimmed = line.lstrip()
                if trimmed.startswith('import ') or trimmed.startswith('from ') or in_multiline_import:
                    # Very rough multiline import detection
                    if '(' in line and ')' not in line: in_multiline_import = True
                    if ')' in line: in_multiline_import = False
                    
                    # For import/from lines, we only want to alias the entities, not the module path
                    if trimmed.startswith('from '):
                        # Split by ' import ' to separate module path from entities
                        if ' import ' in line:
                            path_part, entities_part = line.split(' import ', 1)
                            for name, new_name in sorted_names:
                                entities_part = re.sub(r'\b' + re.escape(name) + r'\b(?!\s+as\b)', f"{name} as {new_name}", entities_part)
                            line = path_part + ' import ' + entities_part
                    elif trimmed.startswith('import '):
                        # For 'import x, y as z'
                        # Skip the 'import ' prefix
                        prefix = line[:line.find('import ') + 7]
                        rest = line[line.find('import ') + 7:]
                        for name, new_name in sorted_names:
                            # Avoid replacing module path parts (like 'os' in 'os.path') if 'os' is aliased?
                            # Actually, 'import os' should become 'import os as os_slug'
                            rest = re.sub(r'\b' + re.escape(name) + r'\b(?!\s+as\b)', f"{name} as {new_name}", rest)
                        line = prefix + rest
                    else: # in multiline entities part
                        for name, new_name in sorted_names:
                            line = re.sub(r'\b' + re.escape(name) + r'\b(?!\s+as\b)', f"{name} as {new_name}", line)
                    
                    new_lines.append(line)
                else:
                    # Regular line
                    for name, new_name in sorted_names:
                        line = re.sub(r'\b' + re.escape(name) + r'\b', new_name, line)
                    new_lines.append(line)
            
            header = f"\n\n# {'='*80}\n# FROM FILE: {f_path}\n# {'='*80}\n\n"
            out.write(header + "\n".join(new_lines) + "\n")
            print(f"Merged {f_path}")

if __name__ == "__main__":
    main()
