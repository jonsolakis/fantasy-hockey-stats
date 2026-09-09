from app.nhl import NhlClient


def test_normalize_skater_uses_last_team():
    player = NhlClient._normalize_skater(
        {
            "playerId": 1,
            "lastName": "Player",
            "skaterFullName": "Jane Player",
            "positionCode": "C",
            "teamAbbrevs": "TOR,MTL",
        }
    )

    assert player.team_abbreviation == "MTL"
    assert player.first_name == "Jane"


def test_normalize_skater_merges_realtime_and_special_teams_stats():
    player = NhlClient._normalize_skater(
        {
            "playerId": 1,
            "lastName": "Player",
            "skaterFullName": "Jane Player",
            "positionCode": "C",
            "ppGoals": 3,
            "ppPoints": 8,
            "shGoals": 1,
            "shPoints": 4,
        },
        {"hits": 22, "blockedShots": 13},
    )

    assert player.hits == 22
    assert player.blocked_shots == 13
    assert player.power_play_goals == 3
    assert player.power_play_assists == 5
    assert player.shorthanded_goals == 1
    assert player.shorthanded_assists == 3
