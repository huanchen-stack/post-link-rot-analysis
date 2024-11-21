import difflib

def compare_strings(str1, str2):
    lines1 = str1.splitlines()
    lines2 = str2.splitlines()

    differ = difflib.Differ()

    added_lines = []
    removed_lines = []
    diff = differ.compare(lines1, lines2)
    for line in diff:
        if line.startswith('+ '):
            added_lines.append(line[2:])
        elif line.startswith('- '):
            removed_lines.append(line[2:])

    return {'+': added_lines, '-': removed_lines}

string1 = """This is the first string.
It has multiple lines.
Some lines are the same."""

string2 = """This is the second string.
It has multiple lines.
Some lines are different."""

result = compare_strings(string1, string2)
print("Added lines:")
for line in result['+']:
    print(line)
print("\nRemoved lines:")
for line in result['-']:
    print(line)
