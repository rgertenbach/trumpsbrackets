#! /home/robin/py/venv/bin/python
from dataclasses import dataclass
from collections import Counter
import random
import csv
import pandas as pd
import IPython
import argparse


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


def compare(a: Card, b: Card, ordering: list[str]) -> tuple[Card, Card]:
    apoints = 0
    for av, bv, op in zip(a.values, b.values, ordering):
        av, bv = (av, bv) if op == "+" else (bv, av)
        apoints += sign(av - bv)
    if apoints == 0:
        apoints += random.choice([0, 1])
    if apoints > 0:
        return a, b
    return b, a


def fight_roster(
    cards: list[Card], ordering: list[str]
) -> tuple[list[Card], list[Card]]:
    winners = []
    losers = []
    random.shuffle(cards)
    if len(cards) % 2 == 1:
        winners.append(cards.pop())
    while cards:
        a, b = cards.pop(), cards.pop()
        winner, loser = compare(a, b, ordering)
        winners.append(winner)
        losers.append(loser)

    return winners, losers


def one_round(cards: list[Card], ordering: list[str]) -> list[Card]:
    result = []
    cards = cards[:]
    while cards:
        winners, losers = fight_roster(cards, ordering)
        result.extend(losers)
        if len(winners) == 1:
            result.extend(winners)
            break
        cards = winners
    return result


def evaluate_result(ranks: list[Card]) -> dict[str, int]:
    n = len(ranks)
    return {card.name: n - i for i, card in enumerate(ranks)}


def n_rounds(cards: list[Card], n: int, ordering: list[str]) -> dict[str, Counter]:
    ranks = {card.name: Counter() for card in cards}
    for i in range(n):
        if i % 1000 == 0:
            print(f"\r{i:,.0f}", end="", flush=True)
        results = evaluate_result(one_round(cards, ordering))
        for card, rank in results.items():
            ranks[card][rank] += 1
    print()
    return ranks

def rounds_needed(cards: int) -> int:
  out = 0
  while cards > 1:
    out += 1
    cards = cards // 2 + cards % 2

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
    parser.add_argument("-n", type=int, default=100_000, help="Number of simulations")

    args = parser.parse_args()
    cards, ordering = read_cards(args.file)
    results = n_rounds(cards, args.n, ordering)
    results = (
        pd.DataFrame(results)
        .fillna(0)
        .T.sort_values(1)
        .sort_index(axis=1)
        .astype(int)
    )
    ncards = len(cards)
    for round in range(rounds_needed(ncards)):
      results[f"lost_{round + 1}"] = results.iloc[:, ncards // 2 + ncards % 2:ncards].sum(axis=1)
      ncards = ncards // 2 + ncards % 2
    results["won"] = results.loc[:, 1]
    results = results.drop(columns=range(1, len(cards) + 1))
    print(results)

    if args.interactive:
      IPython.embed(banner1="")


if __name__ == "__main__":
    main()
