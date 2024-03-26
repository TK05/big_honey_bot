import pprint

from big_honey_bot.games.helpers import get_espn_schedule_dict, get_nba_com_schedule_dict
from big_honey_bot.helpers import write_dict_to_json_file, get_dict_from_json_file


FILE_NAME = 'schedule_scrape_output.json'
DEBUG = False


def get_espn_schedule():
        
    espn_data = get_espn_schedule_dict()
    write_dict_to_json_file(FILE_NAME, espn_data)

    if DEBUG:
        pprint.pprint(espn_data)


def update_with_nba_com_schedule():
    
    nbacom_data = get_nba_com_schedule_dict()
    sch_dict = get_dict_from_json_file(FILE_NAME)

    # update json file using utc_key as key
    for utc_key, game_dict in nbacom_data.items():
        for data_key, data in game_dict.items():
            try:
                sch_dict[utc_key][data_key] = data
            except KeyError:
                # 2020 catch for scrimmage games not on both sites
                pass

    write_dict_to_json_file(FILE_NAME, sch_dict)

    if DEBUG:
        pprint.pprint(nbacom_data)


if __name__ == '__main__':
    # get base schedule from espn, then add nba_com data to it
    get_espn_schedule()
    update_with_nba_com_schedule()
