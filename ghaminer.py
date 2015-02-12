#!/usr/bin/env python

# Co bude umet tento program:
# ---------------------------
# 1. zadam mu cislo, to vyjadruje pocet repozitaru
# 2. on z githubarchive zvoli danej pocet projektu pomoci nejake heuristiky,
# tim ale asi vyuziti githubarchive konci. pouzivat vubec githubarchive? mozna staci timeline
# 3. k danemu projektu vzdy ziska informace, co se budou pro dolovani pouzivat

import os
import argparse

import github


def main(sample_count, output):
    gh = github.GitHub(username=os.getenv("GH_USERNAME"), password=os.getenv("GH_PASSWORD"))

    print gh.repositories().get(since=40400)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get Github repos dataset for GHAM project")
    parser.add_argument("-c", "--count", type=int, help="number of samples to download", default=100000)
    parser.add_argument("-o", "--output", help="name of the CSV output file", default="output.csv")
    args = parser.parse_args()

    main(args.count, args.output)
