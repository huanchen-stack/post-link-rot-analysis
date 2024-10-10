jq -s 'reduce .[] as $item ({"total": 0, "augmented": 0, "augmented_by_bot": 0, "removed": 0, "removed_by_bot": 0}; 
    {
        "total": (.total + ($item.stats.total // 0)),
        "augmented": (.augmented + ($item.stats.augmented // 0)),
        "augmented_by_bot": (.augmented_by_bot + ($item.stats.augmented_by_bot // 0)),
        "removed": (.removed + ($item.stats.removed // 0)),
        "removed_by_bot": (.removed_by_bot + ($item.stats.removed_by_bot // 0))
    })' iter_edit_history_results_4.json
