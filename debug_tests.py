import sys
import os
import traceback

sys.path.insert(0, os.getcwd())

try:
    import tests.tests
    print("Import successful")
except Exception:
    traceback.print_exc()
