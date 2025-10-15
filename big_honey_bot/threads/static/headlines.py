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
            "{0} sneak past the {1} {2} | {3}",
            "{0} outlast the {1} {2} | {3}",
            "{0} narrowly defeat the {1} {2} | {3}",
            "{0} claim close win over the {1} {2} | {3}",
            "{0} get the better of the {1} {2} | {3}",
            "{0} slip by the {1} {2} | {3}",
        ],
        "15": [
            "{0} beat the {1} {2} | {3}",
            "{0} vanquish the {1} {2} | {3}",
            "{0} stymie the {1} {2} | {3}",
            "{0} defeat the {1} {2} | {3}",
            "{0} master the {1} {2} | {3}",
            "{0} humble the {1} {2} | {3}",
            "{0} overpower the {1} {2} | {3}",
            "{0} put the {1} in their place {2} | {3}",
            "{0} top the {1} {2} | {3}",
            "{0} take down the {1} {2} | {3}",
            "{0} prevail over the {1} {2} | {3}",
            "{0} handle the {1} {2} | {3}",
            "{0} outshine the {1} {2} | {3}",
            "{0} get it done against the {1} {2} | {3}",
        ],
        "100": [
            "{0} conquer the {1} {2} | {3}",
            "{0} run rings around the {1} {2} | {3}",
            "{0} bring the {1} to their knees {2} | {3}",
            "{0} clobber the {1} {2} | {3}",
            "{0} make mincemeat of the {1} {2} | {3}",
            "{0} wipe the floor with the {1} {2} | {3}",
            "{0} rout the {1} {2} | {3}",
            "{0} cruise past the {1} {2} | {3}",
            "{0} overpower the {1} {2} | {3}",
            "{0} rout the {1} {2} | {3}",
            "{0} dominate the {1} {2} | {3}",
            "{0} blow past the {1} {2} | {3}",
            "{0} roll over the {1} {2} | {3}",
            "{0} dismantle the {1} {2} | {3}",
            "{0} outclass the {1} {2} | {3}",
        ]
    },
    "0": {
        "4": [
            "{0} drop a close one to the {1} {2} | {3}",
            "{0} fall short against the {1} {2} | {3}",
            "{0} let one slip away against the {1} {2} | {3}",
            "{0} come up short against the {1} {2} | {3}",
            "{0} unable to top the {1} {2} | {3}",
            "{0} outlasted by the {1} {2} | {3}"
        ],
        "15": [
            "{0} fall to the {1} {2} | {3}",
            "{0} stuffed by the {1} {2} | {3}",
            "{0} lose one to the {1} {2} | {3}",
            "{0} outplayed by the {1} {2} | {3}",
            "{0} beaten by the {1} {2} | {3}",
            "{0} overpowered by the {1} {2} | {3}",
            "{0} lose to the {1} {2} | {3}",
            "{0} come up empty against the {1} {2} | {3}",
            "{0} can’t keep pace with the {1} {2} | {3}",
        ],
        "100": [
            "{0} humbled by the {1} {2} | {3}",
            "{0} clobbered by the {1} {2} | {3}",
            "{0} subdued by the {1} {2} | {3}",
            "{0} routed by the {1} {2} | {3}",
            "{0} crushed by the {1} {2} | {3}",
            "{0} dominated by the {1} {2} | {3}",
            "{0} blown out by the {1} {2} | {3}",
            "{0} outclassed by the {1} {2} | {3}",
            "{0} overwhelmed by the {1} {2} | {3}",
            "{0} overrun by the {1} {2} | {3}",
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
