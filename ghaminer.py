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
             "subscribers_count", "pushed_at", "created_at", "updated_at"]

# tyto prvky tam muzou byt nezavisle na case:
# id full_name fork created_at
# tyto prvky budu muset omezit casem:
# stargazers_count forks_count watchers_count open_issues_count subscribers_count pushed_at


def get_repo_stats(gh, login, name):
    r = gh.repos(login)(name).get()

    values = [str(r[attr]) for attr in REPO_INFO]

    return values


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
            s = resp[0]

            stats = get_repo_stats(gh, s['owner']['login'], s['name'])

            f.write(" ".join(stats) + "\n")

            # dale:
            # repository events https://developer.github.com/v3/activity/events/#list-repository-events
            # repository issue events https://developer.github.com/v3/activity/events/#list-issue-events-for-a-repository
            # contributors statistics https://developer.github.com/v3/repos/statistics/#contributors
            # last year commit activity https://developer.github.com/v3/repos/statistics/#commit-activity
            # code frequency https://developer.github.com/v3/repos/statistics/#code-frequency
            # participation https://developer.github.com/v3/repos/statistics/#participation
            # punch card https://developer.github.com/v3/repos/statistics/#punch-card
            # contributors https://developer.github.com/v3/repos/#list-contributors and https://developer.github.com/v3/activity/events/#list-events-performed-by-a-user
            # git data?
            # issues for repository https://developer.github.com/v3/issues/#list-issues-for-a-repository
            # pozor na pull request
            # assignees? https://developer.github.com/v3/issues/assignees/
            # organizations bude asi jeste trochu problem
            # pull request https://developer.github.com/v3/pulls/ bude mozna dost spojenej s issues?
            # collaborators a jejich aktivita https://developer.github.com/v3/repos/collaborators/#list
            # commit comments collaboratoru? tohle prozkoumat jeste https://developer.github.com/v3/repos/comments/#list-commit-comments-for-a-repository
            # commity https://developer.github.com/v3/repos/commits/#list-commits-on-a-repository

            percentage += one_part
            print "\r%d %%" % percentage,

            remaining -= 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get Github repos dataset for GHAM project")
    parser.add_argument("-c", "--count", type=int, help="number of samples to download", default=100000)
    parser.add_argument("-o", "--output", help="name of the CSV output file", default="output.csv")
    args = parser.parse_args()

    main(args.count, args.output)
