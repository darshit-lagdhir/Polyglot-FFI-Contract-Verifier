
try:
    import polyglot_ffi_verifier
    print('✓ Package imports')
except ImportError as e:
    print(f'Fail Package: {e}')

try:
    from polyglot_ffi_verifier import ExecutionContext
    print('✓ Context imports')
except ImportError as e:
    print(f'Fail Context: {e}')

try:
    from polyglot_ffi_verifier.ingestion import NativeInterfaceAnalyzer
    print('✓ Ingestion imports')
except ImportError as e:
    print(f'Fail Ingestion: {e}')
