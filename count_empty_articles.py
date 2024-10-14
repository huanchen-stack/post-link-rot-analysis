import os

DIR = "edit_history/edit_history_4"
YEAR = 2019

def is_file_empty(file_path):
    return os.path.getsize(file_path) == 0

total_non_empty = [f for f in os.listdir(DIR) if f.endswith(f"-{YEAR}.txt") and not is_file_empty(os.path.join(DIR, f))]
total_article_count = sum([1 for f in os.listdir(DIR) if f.endswith(f"-meta.json")])

print(f"Total non-empty articles: {len(total_non_empty)}")
print(f"Total article count: {total_article_count}")
