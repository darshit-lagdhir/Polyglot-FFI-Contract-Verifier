import py_compile
import os

targets = [
    r"modules\module_01_ffi_verifier\system_architecture.py",
    r"modules\module_02_verification_pipeline\verification_pipeline.py",
    r"modules\module_03_build_process\build_process.py",
    r"modules\module_04_native_interface_ingestion\native_interface_ingestion.py",
]

for t in targets:
    if os.path.exists(t):
        try:
            py_compile.compile(t, doraise=True)
            print(f"{t}: OK")
        except py_compile.PyCompileError as e:
            print(f"{t}: {e}")
