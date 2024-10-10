import os

DIR = "edit_history_4"
YEAR = 2019

def is_file_empty(file_path):
    return os.path.getsize(file_path) == 0

empty_files = [f for f in os.listdir(DIR) if f.endswith(f"-{YEAR}.txt") and is_file_empty(os.path.join(DIR, f))]
non_empty_files = [f for f in os.listdir(DIR) if f.endswith(f"-{YEAR}.txt") and not is_file_empty(os.path.join(DIR, f))]

print(f"'-{YEAR}.txt' non-empty: {len(non_empty_files)}; empty: {len(empty_files)}")
for i in range(5):
    print(empty_files[i])
