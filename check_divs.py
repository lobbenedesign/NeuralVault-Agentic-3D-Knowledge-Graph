
with open('/Users/giuseppelobbene/Downloads/DATABASE VETTORIALE/dashboard/index.html', 'r') as f:
    lines = f.readlines()

depth = 0
for i, line in enumerate(lines):
    line_num = i + 1
    opens = line.count('<div')
    closes = line.count('</div>')
    
    for _ in range(opens):
        depth += 1
        # print(f"L{line_num}: Open -> {depth}")
    
    for _ in range(closes):
        depth -= 1
        # print(f"L{line_num}: Close -> {depth}")
        if depth < 0:
            print(f"ERROR: EXTRA CLOSING DIV AT LINE {line_num}")
            depth = 0 # reset to keep finding others
print(f"Final depth: {depth}")
