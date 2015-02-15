#!/usr/bin/env python

# Co bude umet tento program:
# ---------------------------
# 1. zadam mu cislo, to vyjadruje pocet repozitaru
# 2. on z githubarchive zvoli danej pocet projektu pomoci nejake heuristiky,
# tim ale asi vyuziti githubarchive konci. pouzivat vubec githubarchive? mozna staci timeline
# 3. k danemu projektu vzdy ziska informace, co se budou pro dolovani pouzivat

import os
import argparse
import random

import github


MAX_ID = 30500000  # zjisteno experimentalne
REPO_INFO = ["id", "full_name", "fork", "stargazers_count", "forks_count", "watchers_count", "open_issues_count",
             "subscribers_count", "size", "pushed_at", "created_at", "updated_at"]


def main(sample_count, output):
    gh = github.GitHub(username=os.getenv("GH_USERNAME"), password=os.getenv("GH_PASSWORD"))

    used_ids = {}
    remaining = sample_count
    one_part = 100.0 / sample_count
    percentage = 0
    with open(output, "w") as f:
        f.write(" ".join(REPO_INFO) + "\n")

        while remaining > 0:
            rindex = random.randint(0, MAX_ID)
            while used_ids.get(rindex, False):
                rindex = random.randint(0, MAX_ID)
            used_ids[rindex] = True

            resp = gh.repositories().get(since=rindex)

            k = random.randint(1, min(remaining, len(resp)))
            rsample = random.sample(resp, k)

            for s in rsample:
                r = gh.repos(s['owner']['login'])(s['name']).get()

                values = [str(r[attr]) for attr in REPO_INFO]
                f.write(" ".join(values) + "\n")
                percentage += one_part
                print "\r%d %%" % percentage,

            remaining -= len(rsample)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get Github repos dataset for GHAM project")
    parser.add_argument("-c", "--count", type=int, help="number of samples to download", default=100000)
    parser.add_argument("-o", "--output", help="name of the CSV output file", default="output.csv")
    args = parser.parse_args()

    main(args.count, args.output)
