#!/usr/bin/env python3
"""Conta gli alert di Wazuh per regola, per agent e per intervallo di tempo.

Legge un file alerts.json (un alert JSON per riga) e stampa una tabella con
numero di alert, ID, livello e descrizione di ogni regola. Sul manager il file
è /var/ossec/logs/alerts/alerts.json e va letto con sudo.

Esempi:
  sudo python3 count-alerts.py /var/ossec/logs/alerts/alerts.json --agent win-01
  python3 count-alerts.py alerts-2026-10-18.json --agent win-01 \
      --from 2026-10-18T14:56 --to 2026-10-18T18:05
  python3 count-alerts.py alerts.json --rule 100010 100011 --min-level 8

Gli orari di --from e --to sono quelli locali del campo "timestamp" dell'alert
(ISO 8601, senza fuso: si confrontano come testo). Le righe che non sono JSON
valido si saltano e si contano alla fine.
"""
import argparse
import json
import sys
from collections import Counter


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("file", help="file alerts.json, un alert JSON per riga")
    p.add_argument("--agent", help="nome dell'agent (es. win-01)")
    p.add_argument("--from", dest="start", help="inizio, es. 2026-10-18T14:56")
    p.add_argument("--to", dest="end", help="fine, es. 2026-10-18T18:05")
    p.add_argument("--rule", nargs="+", help="solo queste regole (ID)")
    p.add_argument("--min-level", type=int, default=0, help="livello minimo")
    p.add_argument("--top", type=int, default=0, help="mostra solo le prime N regole")
    args = p.parse_args()

    counts = Counter()
    info = {}
    total = skipped = 0

    with open(args.file, "rb") as f:
        for line in f:
            try:
                a = json.loads(line)
            except ValueError:
                skipped += 1
                continue
            if args.agent and a.get("agent", {}).get("name") != args.agent:
                continue
            ts = a.get("timestamp", "")
            if args.start and ts < args.start:
                continue
            if args.end and ts > args.end:
                continue
            rule = a.get("rule", {})
            rid = rule.get("id", "?")
            level = int(rule.get("level", 0))
            if args.rule and rid not in args.rule:
                continue
            if level < args.min_level:
                continue
            counts[rid] += 1
            info[rid] = (level, rule.get("description", ""))
            total += 1

    rows = counts.most_common(args.top or None)
    print(f"{'alert':>6}  {'regola':>7}  {'liv':>3}  descrizione")
    for rid, n in rows:
        level, desc = info[rid]
        print(f"{n:>6}  {rid:>7}  {level:>3}  {desc[:90]}")
    print(f"\ntotale: {total} alert, {len(counts)} regole", end="")
    print(f", {skipped} righe non valide saltate" if skipped else "")


if __name__ == "__main__":
    sys.exit(main())
