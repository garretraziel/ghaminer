#!/usr/bin/env python

import os
import argparse
import random
import datetime

import github
from dateutil.parser import parse as dateparse
from dateutil.relativedelta import relativedelta
import pytz

MAX_ID = 30500000  # zjisteno experimentalne TODO: tohle zjistit nejak lip
ATTRS = ["id", "full_name", "fork", "created_at", "days_active", "last_push", "future_activity"]
DIRECT_REPO_INFO = ["id", "full_name", "fork", "created_at"]
OTHER_REPO_INFO = ["stargazers_count", "forks_count", "watchers_count", "open_issues_count",
                   "subscribers_count", "updated_at", "pushed_at"]

# tyto prvky tam muzou byt nezavisle na case:
# id full_name fork created_at
# tyto prvky budu muset omezit casem:
# stargazers_count forks_count watchers_count open_issues_count subscribers_count pushed_at


class RepoNotValid(Exception):
    """Repozitar neni validni - neni vhodny pro dolovani (neobsahuje data...)"""


def is_old_enough(date):
    # TODO: tohle musim obhajit. proc pulrok?
    # az ziskam nejaka data, musim vyzkouset, ze pulrok doopravdy staci
    return date < pytz.UTC.localize(datetime.datetime.now()) - relativedelta(months=6)


def compute_freq_for(commits, time_from, time_to):
    """Vraci frekvence zmen v repozitari - v zadanem case a maximalni

    f_comm(t) = C_comm(t)/(t - t_0)
    tudiz, frekvence commitu v case t je pocet commitu,
    co byly zaslany do casu t deleno dobou, jak dlouho
    byly zasilany
    [f_comm] = commit/mesic

    :param commits:
    :param time_from:
    :param time_to:
    :return:
    """
    f_date = time_from.date()
    t_date = time_to.date()
    commits_in = [c for c in commits if f_date <= dateparse(c['commit']['committer']['date']).date() <= t_date]
    f_time = float(len(commits_in)) / (((time_to - time_from).days + 1)/31)

    return f_time


def get_repo_stats(gh, login, name):
    r = gh.repos(login)(name).get()
    values = [str(r[attr]) for attr in DIRECT_REPO_INFO]  # vyberu to, co mohu ziskat primo, bez zapojeni casu

    commits = gh.repos(login)(name).commits().get()
    if len(commits) == 0:
        raise RepoNotValid

    first_commit = min(commits, key=lambda commit: dateparse(commit['commit']['committer']['date']))
    last_commit = max(commits, key=lambda commit: dateparse(commit['commit']['committer']['date']))

    # ziskam informace o casech daneho repozitare
    time_created = dateparse(first_commit['commit']['committer']['date'])
    time_ended = dateparse(last_commit['commit']['committer']['date'])
    if time_ended < time_created:
        raise RepoNotValid
    if is_old_enough(time_ended):
        random_days = random.randint(0, (time_ended - time_created).days)
        point_in_time = time_created + datetime.timedelta(days=random_days)
    else:
        raise RepoNotValid

    values.append(str((point_in_time - time_created).days + 1))
    values.append(point_in_time.isoformat())

    f_time = compute_freq_for(commits, point_in_time - datetime.timedelta(days=31), point_in_time)
    f_future = compute_freq_for(commits, point_in_time + datetime.timedelta(days=1), point_in_time + datetime.timedelta(days=32))

    values.append(str(f_future - f_time))

    return values


def main(sample_count, output):
    gh = github.GitHub(username=os.getenv("GH_USERNAME"), password=os.getenv("GH_PASSWORD"))

    used_ids = {}
    remaining = sample_count
    one_part = 100.0 / sample_count
    percentage = 0
    with open(output, "w") as f:
        f.write(", ".join(ATTRS) + "\n")

        while remaining > 0:
            rindex = random.randint(0, MAX_ID)
            while used_ids.get(rindex, False):
                rindex = random.randint(0, MAX_ID)
            used_ids[rindex] = True

            resp = gh.repositories().get(since=rindex)
            s = resp[0]

            try:
                stats = get_repo_stats(gh, s['owner']['login'], s['name'])

                f.write(", ".join(stats) + "\n")

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

            except (RepoNotValid, github.ApiError):
                pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get Github repos dataset for GHAM project")
    parser.add_argument("-c", "--count", type=int, help="number of samples to download", default=100000)
    parser.add_argument("-o", "--output", help="name of the CSV output file", default="output.csv")
    args = parser.parse_args()

    main(args.count, args.output)
