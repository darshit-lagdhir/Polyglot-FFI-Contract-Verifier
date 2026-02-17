
try:
    with open('test_logs.txt', 'r', encoding='utf-16-le') as f:
        print(f.read())
except Exception as e:
    print(f"Error reading utf-16: {e}")
