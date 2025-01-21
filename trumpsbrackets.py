#! /home/robin/py/venv/bin/python
from dataclasses import dataclass
from collections import Counter
import random
import csv
import pandas as pd
import IPython
import argparse
import enum
from typing import Sequence, MutableSequence


class TeamResolution(enum.Enum):
  MAX = "max"
  SUM = "sum"
  MIN = "min"

_RESOLUTIONS = {
    TeamResolution.MAX: max,
    TeamResolution.SUM: sum,
    TeamResolution.MIN: min,
}

def sign(x: float) -> int:
    if x < 0:
        return -1
    if x > 0:
        return 1
    return 0


@dataclass
class Card:
    name: str
    skills: list[str]
    values: list[float]

    def __init__(self, name: str, skills: list[str], values: list[float]):
        if len(values) != len(skills):
            raise ValueError(
                f"Attributes for {name} dont align, "
                f"got {len(values)}, expected {len(skills)}"
            )
        self.name = name
        self.skills = skills
        self.values = values


@dataclass
class Team:
  cards: Sequence[Card]
  def __init__(self, cards: Sequence[Card]):
    if not cards:
      raise ValueError("Need at least one team member")
    self.cards = cards

  def values(self, resolution: TeamResolution) -> list[float]:
    resolve = _RESOLUTIONS[resolution]
    return [
        resolve([c.values[i] for c in self.cards])
        for i in range(len(self.cards[0].skills))
    ]


def read_cards(filename: str) -> tuple[list[Card], list[str]]:
    cards = []
    ordering = []
    with open(filename) as f:
        reader = csv.reader(f)
        header = next(reader)[1:]
        for col in header:
            ordering.append("-" if col.endswith("-") else "+")
        header = [h.removesuffix("-") for h in header]

        for line in reader:
            cards.append(Card(line[0], header, [float(x) for x in line[1:]]))

    return cards, ordering


def compare(
    a: Team,
    b: Team,
    ordering: list[str],
    resolution: TeamResolution
) -> tuple[Team, Team]:
    apoints = 0
    for av, bv, op in zip(a.values(resolution), b.values(resolution), ordering):
        av, bv = (av, bv) if op == "+" else (bv, av)
        apoints += sign(av - bv)
    if apoints == 0:
        apoints += random.choice([0, 1])
    if apoints > 0:
        return a, b
    return b, a


def make_teams(cards: MutableSequence[Card], size: int) -> list[Team]:
  n = len(cards)
  if n % size: 
    raise ValueError(f"Cannot make even sets of {size} from {len(cards)} cards")
  random.shuffle(cards)
  teams = []
  for i in range(n // size):
    teams.append(Team(cards[i * size:i * size + size]))
  return teams


def fight_roster(
    teams: list[Team],
    ordering: list[str],
    resolution: TeamResolution = TeamResolution.MAX,
) -> tuple[list[Team], list[Team]]:
    winners = []
    losers = []
    if len(teams) % 2:
        winners.append(teams.pop())
    while teams:
        a, b = teams.pop(), teams.pop()
        winner, loser = compare(a, b, ordering, resolution)
        winners.append(winner)
        losers.append(loser)

    return winners, losers


def one_round(
    cards: list[Card],
    ordering: list[str],
    teamsize: int = 1,
    resolution: TeamResolution = TeamResolution.MAX,
) -> list[Team]:
    """Returns teams in order of when they lost, winners last."""
    result: list[Team] = []
    cards = cards[:]
    teams = make_teams(cards, teamsize)
    while teams:
        winners, losers = fight_roster(teams, ordering, resolution)
        result.extend(losers)
        if len(winners) == 1:
            result.extend(winners)
            break
        teams = winners
    return result


def evaluate_result(ranks: list[Team]) -> dict[str, int]:
    return {
        card.name: len(ranks) - i
        for i, team in enumerate(ranks)
        for card in team.cards}


def n_rounds(
    cards: list[Card],
    n: int,
    ordering: list[str],
    teamsize: int = 1,
    resolution: TeamResolution = TeamResolution.MAX,
) -> dict[str, Counter]:
    ranks = {card.name: Counter() for card in cards}
    for i in range(n):
        if i and i % 1000 == 0:
            print(f"\r{i:,.0f}", end="", flush=True)
        results = evaluate_result(one_round(cards, ordering, teamsize, resolution))
        for card, rank in results.items():
            ranks[card][rank] += 1
    print("\r", end="")
    return ranks


def rounds_needed(participants: int) -> int:
  out = 0
  while participants > 1:
    out += 1
    participants = participants // 2 + participants % 2

  return out


def main():
    parser = argparse.ArgumentParser(
        "trumpsbrackets",
        description=(
            "Simulate head-to-head attribute comparisons. "
            "Two cards get compared and the one that wins more categories wins."
        ),
    )
    parser.add_argument(
        "file",
        type=str,
        help=(
            "Path to csv file. "
            "The first column is the header, headers with trailing - mean "
            "lower is better. "
            "The first column is the name of the card"
        ),
    )
    parser.add_argument(
        "--interactive",
        action=argparse.BooleanOptionalAction,
        default=True,
        help=(
          "Whether to throw you into an IPython REPL, pass `--no-interactive` "
          "to prevent"
        )
    )
    parser.add_argument(
        "-n", type=int, default=100_000, help="Number of simulations"
    )
    parser.add_argument(
        "-t", "--teamsize",
        type=int,
        default=1,
        help="How large teams are, by defaul everybody fights for themselves"
    )
    parser.add_argument(
        "-r", "--team_resolution",
        type=TeamResolution,
        default=TeamResolution.MAX,
        help="How multiple attributes get resolved, one of max, sum or min"
    )

    args = parser.parse_args()
    cards, ordering = read_cards(args.file)
    results = n_rounds(cards, args.n, ordering, args.teamsize)
    results = (
        pd.DataFrame(results)
        .fillna(0)
        .T.sort_values(1)
        .sort_index(axis=1)
        .astype(int)
    )

    nteams = len(cards) // args.teamsize
    for round in range(rounds_needed(nteams)):
      results[f"lost_{round + 1}"] = results.iloc[:, nteams // 2 + nteams % 2:nteams].sum(axis=1)
      nteams = nteams // 2 + nteams % 2
    results["won"] = results.loc[:, 1]
    results = results.drop(columns=range(1, len(cards) // args.teamsize + 1))
    print(results)

    if args.interactive:
      IPython.embed(banner1="")


if __name__ == "__main__":
    main()
