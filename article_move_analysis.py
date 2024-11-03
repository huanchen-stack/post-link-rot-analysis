import os
import json


for SHARD in range(4):
# SHARD = 1
    DIR = f"edit_history/edit_history_{SHARD+1}/"

    STATS = {}

    for filename in os.listdir(DIR):
        if filename.endswith("-2019.txt"):
            redir_2019 = False
            redir_last = False
            article_name = filename.split("-2019", 1)[0]
            with open(f"{DIR}{filename}", "r", encoding="utf-8") as file:
                text = file.read()
                if text.startswith("#REDIRECT"):
                    redir_2019 = True
            last_revision_filename = f"{article_name}-last.txt"
            with open(f"{DIR}{last_revision_filename}", "r", encoding="utf-8") as file:
                text = file.read()
                if text.startswith("#REDIRECT"):
                    redir_last = True

            if not redir_2019 and redir_last:
                print(article_name)
            elif redir_2019 and not redir_last:
                print(article_name)
            
            key = "0" if redir_2019 else "1"
            key += "0" if redir_last else "1"
            STATS[key] = STATS.get(key, 0) + 1
    print(STATS, sum(STATS.values()))