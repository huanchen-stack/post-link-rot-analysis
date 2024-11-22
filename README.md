# post-link-rot-analysis

Results are too large to upload to github.

1. `parse_FSM.py`: read and parse ext dump; output is the first revision in 2019/2014 as well as revision meta (optional: `article_move_analysis.py`)
---
2. `extract_links.py`: read the first revisions and extract external links using `mwparserfromhell`

[logic-change] 3. `analysis_augment.py`: analysis the extracted external links, group them into [live-only, augmented, archive-only]
<!-- 3. `extract_live_links.py` filter out archived links -->
4. `merge_live_links_by_host.py`: prep probe for live links, group links by hostnames so that politeness is not performance bottleneck
5. `probe_scheduler.py`: randomize probe sequence to improve politeness
6. `probe_live.py`: GET requests to live links (for previous bug, probe_live_patch.py was used once)
7. `group_broken_links.py`: group broken links by DIR/article name; this is to help batched analysis

`probe_live_patch.py`
`probe_live_filter_broken.jq`

---
8. `last_revision_analysis.py`: efficiently extract all eventually-augmented/removed links (by only looking at grouped broken links and the last revision)
9. `iter_edit_history_FSM.py`: re-iterate through all edit histories, find date of 1st [augmentation, removal]
10. `removal_reason_filters.py`: 
11. `probe_archive_conf.py`

