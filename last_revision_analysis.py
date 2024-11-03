import os
import json
import re
import fuzzy_match
from tqdm import tqdm


for SHARD in range(4):
    DIRS = [f"edit_history/edit_history_{i}" for i in range(1, 5)]
    ITER_DIR = "edit_history/iter/"

    with open(os.path.join(ITER_DIR, "probe_live_broken_links.json"), "r", encoding="utf-8") as file:
        ALL_BROKEN_LINKS = json.load(file)

    ALL_AUG_BIASED = 0
    ALL_REMOVED = 0
    ALL_NO_ACTION = 0

    def process_dir(dir_path):
        global ALL_AUG_BIASED, ALL_REMOVED, ALL_NO_ACTION

        print(dir_path)
        for filename in tqdm(os.listdir(dir_path)):
            if not filename.endswith(f"-last.txt"):
                continue
            article_name = filename.replace(f"-last.txt", "")
            if article_name not in ALL_BROKEN_LINKS[dir_path]:
                continue

            revision_last = open(f"{dir_path}/{filename}", 'r').read()
            arn = {}

            # first check augmentation; elif check removal
            for link in ALL_BROKEN_LINKS[dir_path][article_name]["list_of_links"]:
                link_url = link["url"]

                aug_match = fuzzy_match.check_if_augmented(link_url, revision_last, {})
                removed = fuzzy_match.check_if_removed(link_url, revision_last)
                if aug_match:
                    link["last_revision_AUG_REM"] = {
                        "type": "augmented",
                        "match": aug_match
                    }
                    ALL_AUG_BIASED += 1
                elif removed:
                    link["last_revision_AUG_REM"] = { "type": "removed" }
                    ALL_REMOVED += 1
                else:
                    link["last_revision_AUG_REM"] = { "type": "no_action"}
                    ALL_NO_ACTION += 1

                arn[link["url"]] = link
            with open(f"{dir_path}/{article_name}-arn.json", "w", encoding="utf-8") as file:
                json.dump(arn, file, indent=4)

    # if __name__ == "__main__":
    process_dir(DIRS[SHARD])
    print(ALL_AUG_BIASED, ALL_REMOVED, ALL_NO_ACTION, 
        ALL_AUG_BIASED + ALL_REMOVED + ALL_NO_ACTION)