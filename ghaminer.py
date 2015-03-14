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
ATTRS = [
    # zakladni informace
    "id", "full_name", "fork", "created_at", "first_commit", "days_active", "last_commit",

    ## commits
    # informace o frekvencich commitu
    "commits_count", "commits_f_1w", "commits_f_1m", "commits_f_6m", "commits_f_1y", "commits_f_all",

    ## issues
    # informace o frekvencich issues
    "issues_count", "issues_f_1w", "issues_f_1m", "issues_f_6m", "issues_f_1y", "issues_f_all",
    # informace o frekvencich zavrenych issues
    "closed_issues_count", "closed_issues_f_1w", "closed_issues_f_1m", "closed_issues_f_6m", "closed_issues_f_1y", "closed_issues_f_all",
    # informace o prumernych casech k zavreni issues
    "closed_issues_time_1w", "closed_issues_time_1m", "closed_issues_time_6m", "closed_issues_time_1y", "closed_issues_time_all",
    # informace o frekvencich komentaru
    "comments_count", "comments_f_1w", "comments_f_1m", "comments_f_6m", "comments_f_1y", "comments_f_all",

    ## pull requests
    # informace o frekvencich pull requestu
    "pulls_count", "pulls_f_1w", "pulls_f_1m", "pulls_f_6m", "pulls_f_1y", "pulls_f_all",
    # informace o frekvencich zavrenych pull requestu
    "closed_pulls_count", "closed_pulls_f_1w", "closed_pulls_f_1m", "closed_pulls_f_6m", "closed_pulls_f_1y", "closed_pulls_f_all",
    # informace o prumernych casech k zavreni pull requestu
    "closed_pulls_time_1w", "closed_pulls_time_1m", "closed_pulls_time_6m", "closed_pulls_time_1y", "closed_pulls_time_all",
    # informace o frekvencich komentaru k pull requestu
    "pulls_comments_count", "pulls_comments_f_1w", "pulls_comments_f_1m", "pulls_comments_f_6m", "pulls_comments_f_1y", "pulls_comments_f_all",

    ## hodnoty pro predikci
    "freq_ratio", "percentage_remains", "future_freq_1w", "future_freq_1m", "future_freq_6m", "future_freq_1y"]
DIRECT_REPO_INFO = ["id", "full_name", "fork", "created_at"]
OTHER_REPO_INFO = ["stargazers_count", "forks_count", "watchers_count", "open_issues_count",
                   "subscribers_count", "updated_at", "pushed_at"]
one_day = datetime.timedelta(days=1)
get_commit_date = lambda x: parse_date(x['commit']['committer']['date']).date()
get_issues_date = lambda x: parse_date(x['created_at']).date()
get_time_to_close = lambda x: (parse_date(x['closed_at']).date() - parse_date(x['created_at']).date()).days

# tyto prvky budu muset omezit casem:
# stargazers_count forks_count watchers_count open_issues_count subscribers_count pushed_at


class RepoNotValid(Exception):
    """Repozitar neni validni - neni vhodny pro dolovani (neobsahuje data...)"""


def download_all(download_obj, **kwargs):
    """Vola prikaz pro ziskani dat opakovane se zvysujicim se argumentem page.

    :param download_obj: objekt, ktery se ma pouzit pro ziskani dat
    :return: ziskana data
    """
    page = 1
    values = []
    while True:
        result = download_obj.get(page=page, **kwargs)
        if len(result) > 0:
            values.extend(result)
            page += 1
        else:
            break
    return values


def is_old_enough(date, timespan=relativedelta(months=6), now=pytz.UTC.localize(datetime.datetime.now())):
    """Vraci, zda je repozitar dostatecne stary na to, aby mohl byt pouzit.

    :param datetime.date date: datum posledniho zaslani zmeny do repozitare
    :param relativedelta timespan: jak moc stary ma repozitar byt
    :return: informaci, zda je repozitar dostatecne stary
    :rtype: bool
    """
    # TODO: tohle musim obhajit. proc pulrok?
    # az ziskam nejaka data, musim vyzkouset, ze pulrok doopravdy staci
    return (date + timespan) < now.date()


def compute_freq_func(values, get_date_func, time_from, time_to):
    """Vraci frekvence udalosti, ktere muze ziskat dle zadane funkce

    :param [dict] values: seznam vsech udalosti
    :param function get_date_func: funkce, ktera ziska casovy udaj z jedne udalosti
    :param datetime.date time_from: cas od ktereho se ma frekvence pocitat
    :param datetime.date time_to: cas do ktereho se ma frekvence pocitat
    :return: frekvenci udalosti v repozitari v zadanem casovem rozpeti
    :rtype: float
    """
    # ziskam seznam udalosti v danem casovem rozmezi
    values_in = [v for v in values if time_from <= get_date_func(v) <= time_to]
    f_time = float(len(values_in)) / ((time_to - time_from).days + 1)

    return f_time


def compute_delta_freq_func(values, get_date_func, point_in_time, time_delta):
    """Vraci frekvenci udalosti pro zadane casove rozpeti.

    :param [dict] values: seznam vsech udalosti
    :param function get_date_func: funkce pro ziskani data z hodnoty
    :param datetime.date point_in_time: cas ve kterem se ma frekvence pocitat
    :param relativedelta time_delta: casove rozmezi, pro ktere se ma frekvence pocitat
    :return: frekvence udalosti v zadanem casovem rozmezi
    :rtype: float
    """
    if is_old_enough(point_in_time, time_delta):
        if len(values) == 0:
            return 0.0
        else:
            first_value = min(values, key=get_date_func)
            time_created = get_date_func(first_value)

            start = min(point_in_time, point_in_time + time_delta)
            start = max(start, time_created)
            end = max(point_in_time, point_in_time + time_delta)
            f = compute_freq_func(values, get_date_func, start, end)
            return f
    else:
        return -1


def compute_avg_func(values, get_date_func, get_value_func, time_from, time_to):
    """Vraci prumer hodnot, ktere lze ziskat danou funkci, za dane casove obdobi.

    :param [dict] values: seznam vsech udalosti
    :param function get_date_func: funkce, ktera ziska casovy udaj z jedne udalosti
    :param function get_value_func: funkce, ktera ziska hodnotu udalosti
    :param datetime.date time_from: cas od ktereho se ma prumer pocitat
    :param datetime.date time_to: cas do ktereho se ma prumer pocitat
    :return: prumer hodnot
    :rtype: float
    """
    values_in = [get_value_func(v) for v in values if time_from <= get_date_func(v) <= time_to]
    if len(values_in) > 0:
        avg = float(sum(values_in)) / len(values_in)
    else:
        avg = -1
    return avg


def compute_delta_avg_func(values, get_date_func, get_value_func, point_in_time, time_delta):
    """Vraci prumer hodnot pro zadane casove rozpeti.

    :param [dict] values: seznam vsech udalosti
    :param function get_date_func: funkce, ktera ziska casovy udaj z jedne udalosti
    :param function get_value_func: funkce, ktera ziska hodnotu udalosti
    :param datetime.date point_in_time: cas ve kterem se ma prumer pocitat
    :param relativedelta time_delta: casove rozmezi, pro ktere se ma prumer pocitat
    :return: prumer hodnot v zadanem casovem rozmezi
    :rtype: float
    """
    if is_old_enough(point_in_time, time_delta):
        if len(values) == 0:
            return -1
        first_value = min(values, key=get_date_func)
        time_created = get_date_func(first_value)

        start = min(point_in_time, point_in_time + time_delta)
        start = max(start, time_created)
        end = max(point_in_time, point_in_time + time_delta)
        avg = compute_avg_func(values, get_date_func, get_value_func, start, end)
        return avg
    else:
        return -1


def compute_perc_activity(commits, point_in_time):
    """Vraci procento projektu, ktere v zadanem case jeste zbyva.

    :param [dict] commits: seznam vsech zmen v repozitari
    :param datetime.date point_in_time: cas ve kterem se ma procento pocitat
    :return: procento projektu, ktere zbyva v zadanem case
    :rtype: float
    """
    commits_after = [c for c in commits if point_in_time < get_commit_date(c)]
    return float(len(commits_after)) / len(commits) * 100


def compute_commit_freq_activity(commits, point_in_time):
    """Vraci miru aktivity spoctenou podle frekvenci

    :param [dict] commits: seznam vsech zmen v repozitari
    :param datetime.date point_in_time: cas ve kterem se ma aktivita pocitat
    :return: mira aktivity dle frekvenci
    :rtype: float
    """
    # ziskam data prvniho a posledniho zaslani zmen do repozitare
    first_commit = min(commits, key=get_commit_date)
    last_commit = max(commits, key=get_commit_date)

    # ziskam informace o casech daneho repozitare
    time_created = get_commit_date(first_commit)
    time_ended = get_commit_date(last_commit)

    if is_old_enough(time_ended):
        # ziskam casove vzdalenosti
        begin_to_point = point_in_time - time_created

        # frekvence od zacatku je jednoduse frekvence commitu za den od prvniho commitu do aktualniho dne
        f_hist = compute_freq_func(commits, get_commit_date, time_created, point_in_time)
        f_future = compute_freq_func(commits, get_commit_date, point_in_time + one_day,
                                     point_in_time + one_day + begin_to_point)

        return f_future / f_hist
    else:
        # pokud se projekt stale vyviji, nemohu pouzit frekvence
        return -1


def get_all_commits(gh, login, name):
    """Vrati pole vsech commitu a informace o vytvoreni zadaneho repozitare.

    :param github.GitHub gh: instance objektu GitHub
    :param string login: login vlastnika repozitare
    :param string name: nazev repozitare
    :return: pole vsech commitu, udaje o trvani repozitare
    :rtype: [dict], datetime.datetime, datetime.datetime
    """
    commits = download_all(gh.repos(login)(name).commits())
    if len(commits) == 0:
        raise RepoNotValid  # prazdny repozitar je k nicemu

    # ziskam data prvniho a posledniho zaslani zmen do repozitare
    first_commit = min(commits, key=get_commit_date)
    last_commit = max(commits, key=get_commit_date)

    # ziskam informace o casech daneho repozitare
    time_created = get_commit_date(first_commit)
    time_ended = get_commit_date(last_commit)

    return commits, time_created, time_ended


def get_all_issues_pulls(gh, login, name):
    """Vrati vsechy issues a pull requesty zadaneho repozitare a jejich patricne komentare.

    :param github.GitHub gh: instance objektu GitHub
    :param string login: login vlastnika repozitare
    :param string name: nazev repozitare
    :return: issues a pull requesty spolu s jejich komentari
    :rtype: ([(dict, [dict])], [(dict, [dict])])
    """
    # ziskam seznam vsech issues a pull requestu
    issues_pulls = download_all(gh.repos(login)(name).issues(), state="all", direction="asc")

    # roztridim na issues a pull requests
    issues = []
    pulls = []
    for p in issues_pulls:
        if 'pull_request' in p:
            pulls.append(p)
        else:
            issues.append(p)

    issues_comm = []
    pulls_comm = []
    for i in issues:
        comments = download_all(gh.repos(login)(name).issues()(i['number']).comments())
        issues_comm.append((i, comments))
    for p in pulls:
        comments = download_all(gh.repos(login)(name).issues()(p['number']).comments())
        pulls_comm.append((p, comments))
    return issues_comm, pulls_comm


def get_commits_stats(commits, time_created, point_in_time):
    """Ziska mozne statistiky o commitech k repozitari v zadany cas.

    :param [dict] commits: pole vsech commitu do repozitare
    :param datetime.datetime time_created: cas vytvoreni repozitare
    :param datetime.datetime point_in_time: chvile, pro kterou se maji statistiky pocitat
    :return: pole hodnot, ktere se maji pridat k atributum objektu
    :rtype: list
    """
    values = []
    # ziskam pocet commitu do daneho data
    commits_before = [c for c in commits if get_commit_date(c) <= point_in_time]
    values.append(str(len(commits_before)))

    # ziskam frekvenci commitu za posledni tyden, mesic, pulrok, rok, celkovou dobu
    values.append(str(compute_delta_freq_func(commits, get_commit_date, point_in_time, relativedelta(weeks=-1))))
    values.append(str(compute_delta_freq_func(commits, get_commit_date, point_in_time, relativedelta(months=-1))))
    values.append(str(compute_delta_freq_func(commits, get_commit_date, point_in_time, relativedelta(months=-6))))
    values.append(str(compute_delta_freq_func(commits, get_commit_date, point_in_time, relativedelta(years=-1))))
    values.append(str(compute_freq_func(commits, get_commit_date, time_created, point_in_time)))

    # TODO: jeste rozlozeni podle autora
    return values


def get_issues_stats(issues, time_created, point_in_time):
    """Ziska mozne statistiky o issues nebo pull requestech k repozitari v zadany cas.

    :param [(dict, [dict])] issues: slovnik issues nebo pull requestu
    :param datetime.datetime time_created: cas vytvoreni repozitare
    :param datetime.datetime point_in_time: chvile, pro kterou se maji statistiky pocitat
    :return: pole hodnot, ktere se maji pridat k atributum objektu
    :rtype: list
    """
    values = []
    issues_before = []
    comments_dict = {}
    flattened_comments = []
    closed_issues = []
    for issue, comments in issues:
        if get_issues_date(issue) > point_in_time:
            continue
        comments_for = [c for c in comments if get_issues_date(c) <= point_in_time]
        comments_dict[issue['number']] = comments_for
        flattened_comments.extend(comments_for)
        issues_before.append(issue)

        if issue['state'] == 'closed':
            closed_issues.append(issue)

    # ziskam frekvenci issues za posledni tyden, mesic, pulrok, rok, celkovou dobu
    values.append(str(len(issues_before)))
    values.append(str(compute_delta_freq_func(issues_before, get_issues_date, point_in_time, relativedelta(weeks=-1))))
    values.append(str(compute_delta_freq_func(issues_before, get_issues_date, point_in_time, relativedelta(months=-1))))
    values.append(str(compute_delta_freq_func(issues_before, get_issues_date, point_in_time, relativedelta(months=-6))))
    values.append(str(compute_delta_freq_func(issues_before, get_issues_date, point_in_time, relativedelta(years=-1))))
    values.append(str(compute_freq_func(issues_before, get_issues_date, time_created, point_in_time)))

    # informace o zavrenych issues
    values.append(str(len(closed_issues)))

    values.append(str(compute_delta_freq_func(closed_issues, get_issues_date, point_in_time, relativedelta(weeks=-1))))
    values.append(str(compute_delta_freq_func(closed_issues, get_issues_date, point_in_time, relativedelta(months=-1))))
    values.append(str(compute_delta_freq_func(closed_issues, get_issues_date, point_in_time, relativedelta(months=-6))))
    values.append(str(compute_delta_freq_func(closed_issues, get_issues_date, point_in_time, relativedelta(years=-1))))
    values.append(str(compute_freq_func(closed_issues, get_issues_date, time_created, point_in_time)))

    # cas, jak dlouho trvalo zavrit issue
    values.append(str(compute_delta_avg_func(closed_issues, get_issues_date, get_time_to_close, point_in_time,
                                             relativedelta(weeks=-1))))
    values.append(str(compute_delta_avg_func(closed_issues, get_issues_date, get_time_to_close, point_in_time,
                                             relativedelta(months=-1))))
    values.append(str(compute_delta_avg_func(closed_issues, get_issues_date, get_time_to_close, point_in_time,
                                             relativedelta(months=-6))))
    values.append(str(compute_delta_avg_func(closed_issues, get_issues_date, get_time_to_close, point_in_time,
                                             relativedelta(years=-1))))
    values.append(str(compute_avg_func(closed_issues, get_issues_date, get_time_to_close, time_created, point_in_time)))

    # ziskam frekvenci komentaru za posledni tyden, mesic, pulrok, rok, celkovou dobu
    values.append(str(len(flattened_comments)))
    values.append(
        str(compute_delta_freq_func(flattened_comments, get_issues_date, point_in_time, relativedelta(weeks=-1))))
    values.append(
        str(compute_delta_freq_func(flattened_comments, get_issues_date, point_in_time, relativedelta(months=-1))))
    values.append(
        str(compute_delta_freq_func(flattened_comments, get_issues_date, point_in_time, relativedelta(months=-6))))
    values.append(
        str(compute_delta_freq_func(flattened_comments, get_issues_date, point_in_time, relativedelta(years=-1))))
    values.append(str(compute_freq_func(flattened_comments, get_issues_date, time_created, point_in_time)))

    return values


def get_repo_stats(gh, login, name):
    """Ziska veskere statistiky k zadanemu repozitari.

    :param github.GitHub gh: instance objektu GitHub
    :param string login: login vlastnika repozitare
    :param string name: nazev repozitare
    :return: seznam vsech atributu repozitare
    :rtype: list
    """
    # Obecne informace
    r = gh.repos(login)(name).get()
    # vyberu to, co mohu ziskat primo, bez zapojeni casu
    values = [str(r[attr]) for attr in DIRECT_REPO_INFO]

    # Informace o commitech
    # ziskam seznam vsech commitu
    commits, time_created, time_ended = get_all_commits(gh, login, name)
    values.append(time_created.isoformat())

    # ziskam nahodny bod v prubehu vyvoje projektu
    random_days = random.randint(0, (time_ended - time_created).days)  # TODO: forky brat az od forknuti?
    point_in_time = time_created + datetime.timedelta(days=random_days)
    duration = (point_in_time - time_created).days + 1
    values.append(str(duration))
    values.append(point_in_time.isoformat())

    # ziskam dalsi statistiky o commitech
    values.extend(get_commits_stats(commits, time_created, point_in_time))

    # Informace o issues
    issues, pulls = get_all_issues_pulls(gh, login, name)
    values.extend(get_issues_stats(issues, time_created, point_in_time))
    values.extend(get_issues_stats(pulls, time_created, point_in_time))

    ## Hodnoty pro predikci:
    # ziskam aktivitu v bode podle frekvenci
    values.append(str(compute_commit_freq_activity(commits, point_in_time)))
    # ziskam aktivitu v bode podle procent
    values.append(str(compute_perc_activity(commits, point_in_time)))
    # ziskam aktivitu podle frekvence v pristim tydnu
    values.append(str(compute_delta_freq_func(commits, get_commit_date, point_in_time + one_day,
                                              relativedelta(weeks=1))))
    # ziskam aktivitu podle frekvence v pristim mesici
    values.append(str(compute_delta_freq_func(commits, get_commit_date, point_in_time + one_day,
                                              relativedelta(months=1))))
    # ziskam aktivitu podle frekvence v pristim pulroce
    values.append(str(compute_delta_freq_func(commits, get_commit_date, point_in_time + one_day,
                                              relativedelta(months=6))))
    # ziskam aktivitu podle frekvence v pristim roce
    values.append(str(compute_delta_freq_func(commits, get_commit_date, point_in_time + one_day,
                                              relativedelta(years=1))))

    return values


def main(sample_count, output):
    """Hlavni funkce programu. Do vystupu zapise statistky o `sample_count` nahodnych repozitaru.

    :param int sample_count: pocet nahodnych repozitaru, ktere ma program najit
    :param string output: nazev vystupniho souboru
    """
    gh = github.GitHub(username=os.getenv("GH_USERNAME"), password=os.getenv("GH_PASSWORD"))

    used_ids = {}
    remaining = sample_count
    one_part = 100.0 / sample_count
    percentage = 0
    with open(output, "w", 1) as f:
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
