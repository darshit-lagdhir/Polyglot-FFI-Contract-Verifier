import os

def fix_file_robust(path):
    print(f"Fixing {path}")
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    iters = 0
    while iters < 5000:
        try:
            compile("".join(lines), path, 'exec')
            break
        except (IndentationError, SyntaxError) as e:
            iters += 1
            ln = getattr(e, 'lineno', None)
            if ln is None: break
            idx = ln - 1
            if idx >= len(lines): break
            
            line = lines[idx]
            stripped = line.lstrip()
            if not stripped:
                lines[idx] = "\n"
                continue
                
            curr_indent = len(line) - len(stripped)
            msg = str(e)
            
            # Find candidate levels from previous lines
            levels = []
            for i in range(max(0, idx-200), idx):
                if lines[i].strip():
                    levels.append(len(lines[i]) - len(lines[i].lstrip()))
            
            target = None
            if "unindent does not match" in msg:
                # Try to match an existing level
                if levels:
                    # Pick the one closest to current, but preferably smaller
                    candidates = sorted(list(set(levels)), reverse=True)
                    for c in candidates:
                        if c <= curr_indent:
                            target = c
                            break
                    if target is None: target = candidates[-1]
            
            if target is None:
                # Fallback: based on previous line
                for pi in range(idx-1, -1, -1):
                    if lines[pi].strip():
                        prev = lines[pi]
                        p_ind = len(prev) - len(prev.lstrip())
                        target = p_ind
                        if prev.strip().endswith(':'): target += 4
                        if stripped.startswith(('else:', 'elif ', 'except', 'finally:')):
                            target -= 4
                        break
            
            if target is None: target = 0
            
            lines[idx] = " " * max(0, target) + stripped + ("" if stripped.endswith("\n") else "\n")
            
    with open(path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print(f"  Done {path} in {iters} iters")

targets = [
    r'modules\module_01_ffi_verifier\system_architecture.py',
    r'modules\module_02_verification_pipeline\verification_pipeline.py',
    r'modules\module_03_build_process\build_process.py',
    r'modules\module_04_native_interface_ingestion\native_interface_ingestion.py'
]

for t in targets:
    if os.path.exists(t):
        fix_file_robust(t)
