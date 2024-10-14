# post-link-rot-analysis

1. `parse_FSM.py`: read and parse ext dump; output is the first revision in 2019/2014 as well as revision meta (optional: find number of empty 2019 revisions with `count_empty_articles.py`)
2. `extract_links.py`: read the first revisions and extract external links using `mwparserfromhell`
[logic-change] 3. `analysis_augment.py`: analysis the extracted external links, group them into [live-only, augmented, archive-only]
<!-- 3. `extract_live_links.py` filter out archived links -->
4. `merge_live_links_by_host.py`: prep probe for live links, group links by hostnames so that politeness is not performance bottleneck
5. `probe_scheduler.py`: randomize probe sequence to improve politeness
6. `probe_live.py`: GET requests to live links (for previous bug, probe_live_patch.py was used once)
7. `group_broken_links.py`: group broken links by DIR/article name; this is to help batched analysis
8. `iter_edit_history_FSM.py`: re-iterate through all edit histories, find date of 1st [augmentation, removal]
9. `probe_hisory.py`
