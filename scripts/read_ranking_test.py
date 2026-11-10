with open(r'c:\Users\nuyan\Downloads\du an python\quiz-app-v2\backend\tests\test_play.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    for i, line in enumerate(lines[93:150], 94):
        print(f'{i}: {line.rstrip()}')