gt_placeholders = {
    "our_record": "{our_rec}",
    "opp_record": "{opp_rec}",
    "date_and_time": "{date_time}",
    "playoff_series": "{playoff_series}",
    "playoff_teams": "{playoff_teams}"
}

pgt_placeholders = {
    "team": "***team***",
    "opponent": "***opponent***",
    "margin": "***margin***",
    "score": "***score***",
    "date": "***date***"
}

headlines = {
    "1": {
        "4": [
            "{0} win a close one over the {1} {2} | {3}",
            "{0} squeeze by the {1} {2} | {3}",
            "{0} narrowly edge out the {1} {2} | {3}"
        ],
        "15": [
            "{0} beat the {1} {2} | {3}",
            "{0} vanquish the {1} {2} | {3}",
            "{0} stymie the {1} {2} | {3}",
            "{0} defeat the {1} {2} | {3}",
            "{0} master the {1} {2} | {3}",
            "{0} humble the {1} {2} | {3}",
            "{0} overpower the {1} {2} | {3}",
            "{0} put the {1} in their place {2} | {3}"
        ],
        "100": [
            "{0} conquer the {1} {2} | {3}",
            "{0} run rings around the {1} {2} | {3}",
            "{0} bring the {1} to their knees {2} | {3}",
            "{0} clobber the {1} {2} | {3}",
            "{0} make mincemeat of the {1} {2} | {3}",
            "{0} wipe the floor with the {1} {2} | {3}",
            "{0} rout the {1} {2} | {3}"
        ]
    },
    "0": {
        "4": [
            "{0} drop a close one to the {1} {2} | {3}",
            "{0} fall short against the {1} {2} | {3}",
            "{0} let one slip away against the {1} {2} | {3}"
        ],
        "15": [
            "{0} fall to the {1} {2} | {3}",
            "{0} stuffed by the {1} {2} | {3}",
            "{0} lose one to the {1} {2} | {3}"
        ],
        "100": [
            "{0} humbled by the {1} {2} | {3}",
            "{0} clobbered by the {1} {2} | {3}",
            "{0} subdued by the {1} {2} | {3}"
        ]
    }
}

playoff_headlines = {
    'win': "PGT: {} WIN GAME #{}{} - {}",
    'lose': "PGT: {} DROP GAME #{} - {}",
    'leading': " | Lead series over the {} {}-{} | {}",
    'trailing': " | Trail series versus the {} {}-{} | {}",
    'tied': " | Series against the {} tied at {}-{} | {}",
    'clinch': " PGT: {} - {} ADVANCE!!! WIN SERIES OVER THE {} {}-{} | {}",
    'over': "PGT: The wild ride is over | {} | {} fall in {} to the {} | {}"
}
