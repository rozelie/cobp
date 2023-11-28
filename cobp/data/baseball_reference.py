import logging
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import pandas as pd
from fuzzywuzzy import process
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

from cobp import paths
from cobp.ui.selectors import FIRST_AVAILABLE_YEAR, LAST_AVAILABLE_YEAR

logger = logging.getLogger(__name__)


@dataclass
class PlayerSeasonalStats:
    player_name: str
    player_id: str
    baseball_reference_team_id: str
    rbis: int
    runs: int


@dataclass
class BaseballReferenceClient:
    base_url: str = "https://www.baseball-reference.com"

    def get_players_seasonal_stats(self, year: int) -> list[PlayerSeasonalStats]:
        logger.info(f"Loading players' seasonal stats from Baseball Reference for {year=}")
        driver = webdriver.Firefox()
        driver.get(f"{self.base_url}/leagues/majors/{year}-standard-batting.shtml")
        wait_seconds_until_table_loads = 10
        batting_table = WebDriverWait(driver, wait_seconds_until_table_loads).until(
            expected_conditions.presence_of_element_located((By.ID, "players_standard_batting"))
        )
        rows = batting_table.find_elements(By.TAG_NAME, "tr")
        players_stats = []
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if not cells:
                continue

            player_name = cells[0].text
            # remove metadata characters in the player's name if present
            for char in ["*", "#", "?"]:
                player_name = player_name.replace(char, "")

            try:
                # href example: 'https://www.baseball-reference.com/players/a/abramcj01.shtml'
                player_href = cells[0].find_element(By.TAG_NAME, "a").get_attribute("href")
                player_id = player_href.split("/")[5].replace(".shtml", "")  # type: ignore
            except NoSuchElementException:
                # skip non-player rows
                continue

            player_stats = PlayerSeasonalStats(
                player_name=player_name,
                player_id=player_id,
                baseball_reference_team_id=cells[2].text,
                rbis=int(cells[12].text),
                runs=int(cells[7].text),
            )
            logger.info(f"Loaded player seasonal stats: {player_stats}")
            players_stats.append(player_stats)

        driver.close()
        return players_stats


def dump_players_seasonal_stats(year: int) -> None:
    baseball_reference_client = BaseballReferenceClient()
    players_seasonal_stats = baseball_reference_client.get_players_seasonal_stats(year)
    lines = ["player_name,player_id,baseball_reference_team_id,rbis,runs"]
    for player_stats in players_seasonal_stats:
        lines.append(
            ",".join(
                [
                    player_stats.player_name,
                    player_stats.player_id,
                    player_stats.baseball_reference_team_id,
                    str(player_stats.rbis),
                    str(player_stats.runs),
                ]
            )
        )

    data_path = _get_players_seasonal_stats_data_path(year)
    data_path.write_text("\n".join(lines))
    logger.info(f"Wrote baseball reference seasonal players rbis to {data_path.as_posix()}")


@lru_cache(maxsize=None)
def get_seasonal_players_stats(year: int) -> pd.DataFrame:
    data_path = _get_players_seasonal_stats_data_path(year)
    if data_path.exists():
        return pd.read_csv(data_path)

    dump_players_seasonal_stats(year)
    return pd.read_csv(data_path)


def lookup_player(df: pd.DataFrame, player_name: str, team_id: str) -> pd.Series | None:
    def fuzzy_lookup(query: str, choices: list[str], threshold: int = 50) -> str:
        """
        Note that the threshold is relatively low due to some players playing under different names.
        e.g. Clint Frazier has also played under the name of Jackson Frazier
             https://www.baseball-reference.com/players/f/frazicl01.shtml
        """
        result, score = process.extractOne(query, choices)
        if score >= threshold:
            return result  # type: ignore

        raise ValueError(f"Unable to perform a fuzzy lookup of {player_name=} | {team_id=} | {result=} | {score=}")

    team_players = df.loc[df["baseball_reference_team_id"] == team_id]
    # some players have accented names in Baseball Reference data but not in Retrosheet so
    # we perform a fuzzy lookup
    player_name_match = fuzzy_lookup(player_name, team_players["player_name"].tolist())
    return team_players.loc[df["player_name"] == player_name_match]


def dump_all_seasons():
    for year in range(FIRST_AVAILABLE_YEAR, LAST_AVAILABLE_YEAR + 1):
        dump_players_seasonal_stats(year)


def _get_players_seasonal_stats_data_path(year: int) -> Path:
    return paths.DATA_DIR / str(year) / "baseball_reference.csv"


# 2023-11-27 15:57:42,536 INFO cross_reference:42 - Unable to find baseball reference player rbis:
# year=2022 | player_name='Noah Syndergaard' | player_id='syndn001' | team_id='LAA'
# a = get_seasonal_players_rbis(2022)
# b = a[a["baseball_reference_team_id"] == "LAA"]
# print(a)
