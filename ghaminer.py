#!/usr/bin/env python

import os
import argparse
import random
import datetime

import github
from dateutil.parser import parse as parse_date
from dateutil.relativedelta import relativedelta
import pytz

MAX_ID = 30500000  # zjisteno experimentalne TODO: tohle zjistit nejak lip
ATTRS = ["id", "full_name", "fork", "created_at", "first_commit", "days_active", "last_commit", "commits_count",
         "freq_1w", "freq_1m", "freq_6m", "freq_1y", "freq_all",
         "freq_ratio", "percentage_remains", "future_freq_1w", "future_freq_1m", "future_freq_6m", "future_freq_1y"]
DIRECT_REPO_INFO = ["id", "full_name", "fork", "created_at"]
OTHER_REPO_INFO = ["stargazers_count", "forks_count", "watchers_count", "open_issues_count",
                   "subscribers_count", "updated_at", "pushed_at"]
one_day = datetime.timedelta(days=1)

# tyto prvky budu muset omezit casem:
# stargazers_count forks_count watchers_count open_issues_count subscribers_count pushed_at


class RepoNotValid(Exception):
    """Repozitar neni validni - neni vhodny pro dolovani (neobsahuje data...)"""


def is_old_enough(date, timespan=relativedelta(months=6), now=pytz.UTC.localize(datetime.datetime.now())):
    """Vraci, zda je repozitar dostatecne stary na to, aby mohl byt pouzit.

    :param datetime.datetime date: datum posledniho zaslani zmeny do repozitare
    :param relativedelta timespan: jak moc stary ma repozitar byt
    :return: informaci, zda je repozitar dostatecne stary
    :rtype: bool
    """
    # TODO: tohle musim obhajit. proc pulrok?
    # az ziskam nejaka data, musim vyzkouset, ze pulrok doopravdy staci
    return (date + timespan) < now


def compute_freq_for(commits, time_from, time_to):
    """Vraci frekvence zmen v repozitari v zadanem casovem rozpeti.

    f_comm(t) = C_comm(t)/(t - t_0)
    tudiz, frekvence commitu v case t je pocet commitu,
    co byly zaslany do casu t deleno dobou, jak dlouho
    byly zasilany
    [f_comm] = commit/den

    :param list[dict] commits: seznam vsech zmen v repozitari
    :param datetime.datetime time_from: cas od ktereho se ma frekvence pocitat
    :param datetime.datetime time_to: cas do ktereho se ma frekvence pocitat
    :return: frekvenci zmen v repozitari v zadanem casovem rozpeti
    :rtype: float
    """
    # pracuju ve "dnech"
    f_date = time_from.date()
    t_date = time_to.date()
    # ziskam seznam zmen v danem casovem rozmezi
    commits_in = [c for c in commits if f_date <= parse_date(c['commit']['committer']['date']).date() <= t_date]
    f_time = float(len(commits_in)) / ((time_to - time_from).days + 1)

    return f_time


def compute_perc_activity(commits, point_in_time):
    """Vraci procento projektu, ktere v zadanem case jeste zbyva.

    :param list[dict] commits: seznam vsech zmen v repozitari
    :param datetime.datetime point_in_time: cas ve kterem se ma procento pocitat
    :return: procento projektu, ktere zbyva v zadanem case
    :rtype: float
    """
    commits_after = [c for c in commits if point_in_time < parse_date(c['commit']['committer']['date'])]
    return float(len(commits_after)) / len(commits) * 100


def compute_freq_activity(commits, point_in_time):
    """Vraci miru aktivity spoctenou podle frekvenci

    :param list[dict] commits: seznam vsech zmen v repozitari
    :param datetime.datetime point_in_time: cas ve kterem se ma aktivita pocitat
    :return: mira aktivity dle frekvenci
    :rtype: float
    """
    # ziskam data prvniho a posledniho zaslani zmen do repozitare
    first_commit = min(commits, key=lambda commit: parse_date(commit['commit']['committer']['date']))
    last_commit = max(commits, key=lambda commit: parse_date(commit['commit']['committer']['date']))

    # ziskam informace o casech daneho repozitare
    time_created = parse_date(first_commit['commit']['committer']['date'])
    time_ended = parse_date(last_commit['commit']['committer']['date'])

    if is_old_enough(time_ended):
        # ziskam casove vzdalenosti
        begin_to_point = point_in_time - time_created

        # frekvence od zacatku je jednoduse frekvence commitu za den od prvniho commitu do aktualniho dne
        f_hist = compute_freq_for(commits, time_created, point_in_time)

        f_future = compute_freq_for(commits, point_in_time + one_day, point_in_time + one_day + begin_to_point)

        return f_future / f_hist
    else:
        # pokud se projekt stale vyviji, nemohu pouzit frekvence
        return -1


def compute_delta_freq_activity(commits, point_in_time, future_time_delta):
    """Vraci miru aktivity spoctenou podle budouci frekvence.

    :param list[dict] commits: seznam vsech zmen v repozitari
    :param datetime.datetime point_in_time: cas ve kterem se ma aktivita pocitat
    :param relativedelta future_time_delta: casove rozmezi, pro ktere se ma aktivita pocitat
    :return: mira aktivita dle budouci frekvence
    :rtype: float
    """
    if is_old_enough(point_in_time, future_time_delta):
        first_commit = min(commits, key=lambda commit: parse_date(commit['commit']['committer']['date']))
        time_created = parse_date(first_commit['commit']['committer']['date'])

        start = min(point_in_time, point_in_time + future_time_delta)
        start = max(start, time_created)
        end = max(point_in_time, point_in_time + future_time_delta)
        f = compute_freq_for(commits, start, end)
        return f
    else:
        return -1


def get_repo_stats(gh, login, name):
    ## Obecne informace
    # ziskej informace o repozitari
    r = gh.repos(login)(name).get()
    # vyberu to, co mohu ziskat primo, bez zapojeni casu
    values = [str(r[attr]) for attr in DIRECT_REPO_INFO]

    ## Informace o commitech
    # ziskam seznam vsech commitu
    page = 1
    commits = []
    while True:
        result = gh.repos(login)(name).commits().get(page=page)
        if len(result) > 0:
            commits.extend(result)
            page += 1
        else:
            break
    if len(commits) == 0:
        raise RepoNotValid  # prazdny repozitar je k nicemu

    # ziskam data prvniho a posledniho zaslani zmen do repozitare
    first_commit = min(commits, key=lambda commit: parse_date(commit['commit']['committer']['date']))
    last_commit = max(commits, key=lambda commit: parse_date(commit['commit']['committer']['date']))

    # ziskam informace o casech daneho repozitare
    time_created = parse_date(first_commit['commit']['committer']['date'])
    time_ended = parse_date(last_commit['commit']['committer']['date'])
    values.append(first_commit['commit']['committer']['date'])

    # ziskam nahodny bod v prubehu vyvoje projektu
    random_days = random.randint(0, (time_ended - time_created).days)  # TODO: forky brat az od forknuti?
    point_in_time = time_created + datetime.timedelta(days=random_days)
    duration = (point_in_time - time_created).days + 1
    values.append(str(duration))
    values.append(point_in_time.isoformat())

    # ziskam pocet commitu do daneho data
    commits_before = [c for c in commits if parse_date(c['commit']['committer']['date']) <= point_in_time]
    values.append(str(len(commits_before)))

    # ziskam frekvenci commitu za posledni tyden, mesic, pulrok, rok, celkovou dobu
    values.append(str(compute_delta_freq_activity(commits, point_in_time, relativedelta(weeks=-1))))
    values.append(str(compute_delta_freq_activity(commits, point_in_time, relativedelta(months=-1))))
    values.append(str(compute_delta_freq_activity(commits, point_in_time, relativedelta(months=-6))))
    values.append(str(compute_delta_freq_activity(commits, point_in_time, relativedelta(years=-1))))
    values.append(str(compute_freq_for(commits, time_created, point_in_time)))

    ## Informace o issues
    # ziskam seznam vsech issues a pull requestu
    page = 1
    issues_pulls = []
    while True:
        result = gh.repos(login)(name).issues(state="all", direction="asc").get(page=page)
        if len(result) > 0:
            issues_pulls.extend(result)
            page += 1
        else:
            break

    # roztridim na issues a pull requests
    issues = []
    pulls = []
    for i in issues_pulls:
        if 'pull_request' in i:
            pulls.append(i)
        else:
            issues.append(i)

    ## Hodnoty pro predikci:
    # ziskam aktivitu v bode podle frekvenci
    values.append(str(compute_freq_activity(commits, point_in_time)))

    # ziskam aktivitu v bode podle procent
    values.append(str(compute_perc_activity(commits, point_in_time)))

    # ziskam aktivitu podle frekvence v pristim tydnu
    values.append(str(compute_delta_freq_activity(commits, point_in_time + one_day, relativedelta(weeks=1))))

    # ziskam aktivitu podle frekvence v pristim mesici
    values.append(str(compute_delta_freq_activity(commits, point_in_time + one_day, relativedelta(months=1))))

    # ziskam aktivitu podle frekvence v pristim pulroce
    values.append(str(compute_delta_freq_activity(commits, point_in_time + one_day, relativedelta(months=6))))

    # ziskam aktivitu podle frekvence v pristim roce
    values.append(str(compute_delta_freq_activity(commits, point_in_time + one_day, relativedelta(years=1))))

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
            # ziskej nahodny repozitar, ktery jeste nebyl pouzity
            rindex = random.randint(0, MAX_ID)
            while used_ids.get(rindex, False):
                rindex = random.randint(0, MAX_ID)
            used_ids[rindex] = True

            resp = gh.repositories().get(since=rindex)
            s = resp[0]

            # ziskej z neho data. pokud nelze pouzit, pokracuj, ale nesnizuj zbyvajici pocet
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
