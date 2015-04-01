#!/usr/bin/env python

import os
import sys
import argparse
import random
import datetime

import github
import pause
from dateutil.parser import parse as parse_date
from dateutil.relativedelta import relativedelta

import ghamath as gm

MAX_ID = 30500000  # zjisteno experimentalne TODO: tohle zjistit nejak lip
ATTRS = [
    # zakladni informace
    "id", "full_name", "fork", "created_at", "first_commit", "days_active", "last_commit",

    # commits
    # informace o frekvencich commitu
    "commits_count", "commits_f_1w", "commits_f_1m", "commits_f_6m", "commits_f_1y", "commits_f_all",

    # issues
    # informace o frekvencich issues
    "issues_count", "issues_f_1w", "issues_f_1m", "issues_f_6m", "issues_f_1y", "issues_f_all",
    # informace o frekvencich zavrenych issues
    "closed_issues_count", "closed_issues_f_1w", "closed_issues_f_1m", "closed_issues_f_6m", "closed_issues_f_1y",
    "closed_issues_f_all",
    # informace o prumernych casech k zavreni issues
    "closed_issues_time_1w", "closed_issues_time_1m", "closed_issues_time_6m", "closed_issues_time_1y",
    "closed_issues_time_all",
    # informace o frekvencich komentaru
    "comments_count", "comments_f_1w", "comments_f_1m", "comments_f_6m", "comments_f_1y", "comments_f_all",

    # pull requests
    # informace o frekvencich pull requestu
    "pulls_count", "pulls_f_1w", "pulls_f_1m", "pulls_f_6m", "pulls_f_1y", "pulls_f_all",
    # informace o frekvencich zavrenych pull requestu
    "closed_pulls_count", "closed_pulls_f_1w", "closed_pulls_f_1m", "closed_pulls_f_6m", "closed_pulls_f_1y",
    "closed_pulls_f_all",
    # informace o prumernych casech k zavreni pull requestu
    "closed_pulls_time_1w", "closed_pulls_time_1m", "closed_pulls_time_6m", "closed_pulls_time_1y",
    "closed_pulls_time_all",
    # informace o frekvencich komentaru k pull requestu
    "pulls_comments_count", "pulls_comments_f_1w", "pulls_comments_f_1m", "pulls_comments_f_6m", "pulls_comments_f_1y",
    "pulls_comments_f_all",

    # events
    # informace o frekvencich vsech udalosti
    "events_count", "events_f_1w", "events_f_1m", "events_f_6m", "events_f_1y", "events_f_all",

    # contributors
    # informace o lidech, co nekdy zaslali commit
    "contrib_count", "contrib_others", "contrib_p25_1w", "contrib_p50_1w", "contrib_p75_1w",
    "contrib_p25_1m", "contrib_p50_1m", "contrib_p75_1m", "contrib_p25_6m", "contrib_p50_6m", "contrib_p75_6m",
    "contrib_p25_1y", "contrib_p50_1y", "contrib_p75_1y", "contrib_p25_all", "contrib_p50_all", "contrib_p75_all",
    # # aktivita lidi, co za poslednich X mesicu napsali aspon 75%
    # "contrib_1w_avgact_1w", "contrib_1w_avgact_1m", "contrib_1w_avgact_6m", "contrib_1w_avgact_1y",
    # "contrib_1m_avgact_1w", "contrib_1m_avgact_1m", "contrib_1m_avgact_6m", "contrib_1m_avgact_1y",
    # "contrib_6m_avgact_1w", "contrib_6m_avgact_1m", "contrib_6m_avgact_6m", "contrib_6m_avgact_1y",
    # "contrib_1y_avgact_1w", "contrib_1y_avgact_1m", "contrib_1y_avgact_6m", "contrib_1y_avgact_1y"

    # commit comments
    # informace o frekvencich komentaru commitu
    "ccomments_count", "ccomments_f_1w", "ccomments_f_1m", "ccomments_f_6m", "ccomments_f_1y", "ccomments_f_all",

    # forks
    # informace o frekvencich forkovani
    "forks_count", "forks_f_1w", "forks_f_1m", "forks_f_6m", "forks_f_1y", "forks_f_all",

    # hodnoty pro predikci
    "freq_ratio", "percentage_remains", "future_freq_1w", "future_freq_1m", "future_freq_6m", "future_freq_1y"]
DIRECT_REPO_INFO = ["id", "full_name", "fork", "created_at"]
OTHER_REPO_INFO = ["stargazers_count", "forks_count", "watchers_count", "open_issues_count",
                   "subscribers_count", "updated_at", "pushed_at"]
one_day = datetime.timedelta(days=1)
get_commit_date = lambda x: parse_date(x['commit']['committer']['date']).date()
get_issues_date = lambda x: parse_date(x['created_at']).date()
get_time_to_close = lambda x: (parse_date(x['closed_at']).date() - parse_date(x['created_at']).date()).days


class RepoNotValid(Exception):
    """Repozitar neni validni - neni vhodny pro dolovani (neobsahuje data...)"""


def download(gh, download_obj, **kwargs):
    """Zavola prikaz pro stahnuti, popripade pocka na rate limit, je-li treba.

    :param github.GitHub gh: instance objektu GitHub
    :param download_obj: objekt, ktery se ma pouzit pro ziskani dat
    :return: ziskana data
    """
    while True:
        try:
            result = download_obj.get(**kwargs)
            return result
        except github.ApiError as e:
            if gh.x_ratelimit_remaining == 0:
                pause.until(gh.x_ratelimit_reset)
            else:
                print "Got GitHub API error:", e
                raise


def download_all(gh, download_obj, **kwargs):
    """Vola prikaz pro ziskani dat opakovane se zvysujicim se argumentem page.

    :param github.GitHub gh: instance objektu GitHub
    :param download_obj: objekt, ktery se ma pouzit pro ziskani dat
    :return: ziskana data
    """
    page = 1
    values = []
    while True:
        result = download(gh, download_obj, page=page, **kwargs)
        if len(result) > 0:
            values.extend(result)
            page += 1
        else:
            break
    return values


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

    if gm.is_old_enough(time_ended):
        # ziskam casove vzdalenosti
        begin_to_point = point_in_time - time_created

        # frekvence od zacatku je jednoduse frekvence commitu za den od prvniho commitu do aktualniho dne
        f_hist = gm.compute_freq_func(commits, get_commit_date, time_created, point_in_time)
        f_future = gm.compute_freq_func(commits, get_commit_date, point_in_time + one_day,
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
    commits = download_all(gh, gh.repos(login)(name).commits())
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
    issues_pulls = download_all(gh, gh.repos(login)(name).issues(), state="all", direction="asc")

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
        comments = download_all(gh, gh.repos(login)(name).issues()(i['number']).comments())
        issues_comm.append((i, comments))
    for p in pulls:
        comments = download_all(gh, gh.repos(login)(name).issues()(p['number']).comments())
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
    values.append(
        str(gm.compute_delta_freq_func(commits, get_commit_date, time_created, point_in_time, relativedelta(weeks=-1))))
    values.append(
        str(gm.compute_delta_freq_func(commits, get_commit_date, time_created, point_in_time,
                                       relativedelta(months=-1))))
    values.append(
        str(gm.compute_delta_freq_func(commits, get_commit_date, time_created, point_in_time,
                                       relativedelta(months=-6))))
    values.append(
        str(gm.compute_delta_freq_func(commits, get_commit_date, time_created, point_in_time, relativedelta(years=-1))))
    values.append(str(gm.compute_freq_func(commits, get_commit_date, time_created, point_in_time)))

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
    values.append(str(
        gm.compute_delta_freq_func(issues_before, get_issues_date, time_created, point_in_time,
                                   relativedelta(weeks=-1))))
    values.append(str(
        gm.compute_delta_freq_func(issues_before, get_issues_date, time_created, point_in_time,
                                   relativedelta(months=-1))))
    values.append(str(
        gm.compute_delta_freq_func(issues_before, get_issues_date, time_created, point_in_time,
                                   relativedelta(months=-6))))
    values.append(str(
        gm.compute_delta_freq_func(issues_before, get_issues_date, time_created, point_in_time,
                                   relativedelta(years=-1))))
    values.append(str(gm.compute_freq_func(issues_before, get_issues_date, time_created, point_in_time)))

    # informace o zavrenych issues
    values.append(str(len(closed_issues)))

    values.append(str(
        gm.compute_delta_freq_func(closed_issues, get_issues_date, time_created, point_in_time,
                                   relativedelta(weeks=-1))))
    values.append(str(
        gm.compute_delta_freq_func(closed_issues, get_issues_date, time_created, point_in_time,
                                   relativedelta(months=-1))))
    values.append(str(
        gm.compute_delta_freq_func(closed_issues, get_issues_date, time_created, point_in_time,
                                   relativedelta(months=-6))))
    values.append(str(
        gm.compute_delta_freq_func(closed_issues, get_issues_date, time_created, point_in_time,
                                   relativedelta(years=-1))))
    values.append(str(gm.compute_freq_func(closed_issues, get_issues_date, time_created, point_in_time)))

    # cas, jak dlouho trvalo zavrit issue
    values.append(
        str(gm.compute_delta_avg_func(closed_issues, get_issues_date, get_time_to_close, time_created, point_in_time,
                                      relativedelta(weeks=-1))))
    values.append(
        str(gm.compute_delta_avg_func(closed_issues, get_issues_date, get_time_to_close, time_created, point_in_time,
                                      relativedelta(months=-1))))
    values.append(
        str(gm.compute_delta_avg_func(closed_issues, get_issues_date, get_time_to_close, time_created, point_in_time,
                                      relativedelta(months=-6))))
    values.append(
        str(gm.compute_delta_avg_func(closed_issues, get_issues_date, get_time_to_close, time_created, point_in_time,
                                      relativedelta(years=-1))))
    values.append(
        str(gm.compute_avg_func(closed_issues, get_issues_date, get_time_to_close, time_created, point_in_time)))

    # ziskam frekvenci komentaru za posledni tyden, mesic, pulrok, rok, celkovou dobu
    values.append(str(len(flattened_comments)))
    values.append(
        str(gm.compute_delta_freq_func(flattened_comments, get_issues_date, time_created, point_in_time,
                                       relativedelta(weeks=-1))))
    values.append(
        str(gm.compute_delta_freq_func(flattened_comments, get_issues_date, time_created, point_in_time,
                                       relativedelta(months=-1))))
    values.append(
        str(gm.compute_delta_freq_func(flattened_comments, get_issues_date, time_created, point_in_time,
                                       relativedelta(months=-6))))
    values.append(
        str(gm.compute_delta_freq_func(flattened_comments, get_issues_date, time_created, point_in_time,
                                       relativedelta(years=-1))))
    values.append(str(gm.compute_freq_func(flattened_comments, get_issues_date, time_created, point_in_time)))

    return values


def get_all_events(gh, login, name):
    """Ziska seznam uplne vsech udalosti zadaneho repozitare.

    :param github.GitHub gh: instance objektu GitHub
    :param string login: login vlastnika repozitare
    :param string name: nazev repozitare
    :return: seznam vsech udalosti repozitare
    :rtype: list
    """
    events = download_all(gh, gh.repos(login)(name).events())
    return events


def get_events_stats(events, time_created, point_in_time):
    """Ziska informace o udalostech v zadany cas.

    :param [dict] events: pole vsech udalosti repozitare
    :param datetime.datetime time_created: cas vytvoreni repozitare
    :param datetime.datetime point_in_time: chvile, pro kterou se maji statistiky pocitat
    :return: pole hodnot, ktere se maji pridat k atributum objektu
    :rtype: list
    """
    events_before = [e for e in events if get_issues_date(e) <= point_in_time]
    values = [str(len(events_before)),
              str(gm.compute_delta_freq_func(events_before, get_issues_date, time_created, point_in_time,
                                             relativedelta(weeks=-1))),
              str(gm.compute_delta_freq_func(events_before, get_issues_date, time_created, point_in_time,
                                             relativedelta(months=-1))),
              str(gm.compute_delta_freq_func(events_before, get_issues_date, time_created, point_in_time,
                                             relativedelta(months=-6))),
              str(gm.compute_delta_freq_func(events_before, get_issues_date, time_created, point_in_time,
                                             relativedelta(years=-1))),
              str(gm.compute_freq_func(events_before, get_issues_date, time_created, point_in_time))]
    return values


def get_contributors_stats(commits, time_created, point_in_time):
    """Ziska informace o aktivite autoru commitu v zadany cas.

    :param [dict] commits: pole vsech commitu
    :param datetime.datetime time_created: cas vytvoreni repozitare
    :param datetime.datetime point_in_time: chvile, pro kterou se maji statistiky pocitat
    :return: pole hodnot, ktere se maji pridat k atributum objektu
    :rtype: list
    """
    values = []
    contrib_times = {}
    others = []

    # ziskam slovnik {autor: seznam dat commitu}
    for c in commits:
        commit_date = get_commit_date(c)
        if point_in_time < commit_date:
            continue
        if c['author'] is None or 'login' not in c['author'] or c['author']['login'] is None:
            others.append(commit_date)
        else:
            author = c['author']['login']
            if author in contrib_times:
                contrib_times[author].append(commit_date)
            else:
                contrib_times[author] = [commit_date]

    values.append(str(len(contrib_times)))
    values.append(str(len(others)))

    for td in [relativedelta(weeks=-1), relativedelta(months=-1), relativedelta(months=-6), relativedelta(years=-1)]:
        values.append(str(gm.compute_delta_contrib_count(contrib_times, 25, time_created, point_in_time, td)))
        values.append(str(gm.compute_delta_contrib_count(contrib_times, 50, time_created, point_in_time, td)))
        values.append(str(gm.compute_delta_contrib_count(contrib_times, 75, time_created, point_in_time, td)))

    values.append(str(gm.compute_contrib_count(contrib_times, 25, time_created, point_in_time)))
    values.append(str(gm.compute_contrib_count(contrib_times, 50, time_created, point_in_time)))
    values.append(str(gm.compute_contrib_count(contrib_times, 75, time_created, point_in_time)))

    # bohuzel nemohu pouzit pro data mining, protoze udalosti se ukladaji jenom 90 dni zpet
    # activity = {}
    # for td in [relativedelta(weeks=-1), relativedelta(months=-1), relativedelta(months=-6), relativedelta(years=-1)]:
    #     # ziskam X nejaktivnejsich lidi, kteri dohromady zaslali aspon 75 % zmen
    #     # dle https://developer.github.com/v3/activity/events/ je zahrnuto max 300 udalosti za max poslednich 90 dni
    #     most_active = gm.compute_delta_contrib(contrib_times, 75, time_created, point_in_time, td)
    #     for user in most_active:
    #         if user not in activity:
    #             events = download_all(gh.users()(user).events())
    #             activity[user] = events
    #
    #     for atd in [relativedelta(weeks=-1), relativedelta(months=-1), relativedelta(months=-6),
    #                 relativedelta(years=-1)]:
    #         avg = 0.0
    #         for user in activity:
    #             avg += gm.compute_delta_freq_func(activity[user], get_issues_date, time_created, point_in_time, atd)
    #         avg /= len(activity)
    #
    #         values.append(str(avg))

    return values


def get_all_commit_comments(gh, login, name):
    """Ziska seznam vsech komentaru ke commitum

    :param github.GitHub gh: instance objektu GitHub
    :param string login: login vlastnika repozitare
    :param string name: nazev repozitare
    :return: seznam vsech commit komentaru
    :rtype: list
    """
    comments = download_all(gh, gh.repos(login)(name).comments())
    return comments


def get_commit_comments_stats(ccomments, time_created, point_in_time):
    """Ziska informace o komentarich v zadany cas.

    :param [dict] ccomments: pole vsech komentaru
    :param datetime.datetime time_created: cas vytvoreni repozitare
    :param datetime.datetime point_in_time: chvile, pro kterou se maji statistiky pocitat
    :return: pole hodnot, ktere se maji pridat k atributum objektu
    :rtype: list
    """
    comments_before = [e for e in ccomments if get_issues_date(e) <= point_in_time]
    values = [str(len(comments_before)),
              str(gm.compute_delta_freq_func(comments_before, get_issues_date, time_created, point_in_time,
                                             relativedelta(weeks=-1))),
              str(gm.compute_delta_freq_func(comments_before, get_issues_date, time_created, point_in_time,
                                             relativedelta(months=-1))),
              str(gm.compute_delta_freq_func(comments_before, get_issues_date, time_created, point_in_time,
                                             relativedelta(months=-6))),
              str(gm.compute_delta_freq_func(comments_before, get_issues_date, time_created, point_in_time,
                                             relativedelta(years=-1))),
              str(gm.compute_freq_func(comments_before, get_issues_date, time_created, point_in_time))]
    return values


def get_all_forks(gh, login, name):
    """Ziska seznam vsech forku.

    :param github.GitHub gh: instance objektu GitHub
    :param string login: login vlastnika repozitare
    :param string name: nazev repozitare
    :return: seznam vsech forku
    :rtype: list
    """
    forks = download_all(gh, gh.repos(login)(name).forks())
    return forks


def get_forks_stats(forks, time_created, point_in_time):
    """Ziska informace o komentarich v zadany cas.

    :param [dict] forks: pole vsech forku
    :param datetime.datetime time_created: cas vytvoreni repozitare
    :param datetime.datetime point_in_time: chvile, pro kterou se maji statistiky pocitat
    :return: pole hodnot, ktere se maji pridat k atributum objektu
    :rtype: list
    """
    forks_before = [e for e in forks if get_issues_date(e) <= point_in_time]
    values = [str(len(forks_before)),
              str(gm.compute_delta_freq_func(forks_before, get_issues_date, time_created, point_in_time,
                                             relativedelta(weeks=-1))),
              str(gm.compute_delta_freq_func(forks_before, get_issues_date, time_created, point_in_time,
                                             relativedelta(months=-1))),
              str(gm.compute_delta_freq_func(forks_before, get_issues_date, time_created, point_in_time,
                                             relativedelta(months=-6))),
              str(gm.compute_delta_freq_func(forks_before, get_issues_date, time_created, point_in_time,
                                             relativedelta(years=-1))),
              str(gm.compute_freq_func(forks_before, get_issues_date, time_created, point_in_time))]
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
    r = download(gh, gh.repos(login)(name))
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

    # Informace o udalostech
    events = get_all_events(gh, login, name)
    values.extend(get_events_stats(events, time_created, point_in_time))

    # Informace o contributors
    values.extend(get_contributors_stats(commits, time_created, point_in_time))

    # Informace o commit comments
    ccomments = get_all_commit_comments(gh, login, name)
    values.extend(get_commit_comments_stats(ccomments, time_created, point_in_time))

    # Informace o forcich repozitare
    forks = get_all_forks(gh, login, name)
    values.extend(get_forks_stats(forks, time_created, point_in_time))

    # Hodnoty pro predikci:
    # ziskam aktivitu v bode podle frekvenci
    values.append(str(compute_commit_freq_activity(commits, point_in_time)))
    # ziskam aktivitu v bode podle procent
    values.append(str(compute_perc_activity(commits, point_in_time)))
    # ziskam aktivitu podle frekvence v pristim tydnu
    values.append(str(gm.compute_delta_freq_func(commits, get_commit_date, time_created, point_in_time + one_day,
                                                 relativedelta(weeks=1))))
    # ziskam aktivitu podle frekvence v pristim mesici
    values.append(str(gm.compute_delta_freq_func(commits, get_commit_date, time_created, point_in_time + one_day,
                                                 relativedelta(months=1))))
    # ziskam aktivitu podle frekvence v pristim pulroce
    values.append(str(gm.compute_delta_freq_func(commits, get_commit_date, time_created, point_in_time + one_day,
                                                 relativedelta(months=6))))
    # ziskam aktivitu podle frekvence v pristim roce
    values.append(str(gm.compute_delta_freq_func(commits, get_commit_date, time_created, point_in_time + one_day,
                                                 relativedelta(years=1))))

    return values


def main(sample_count, output):
    """Hlavni funkce programu. Do vystupu zapise statistky o `sample_count` nahodnych repozitaru.

    :param int sample_count: pocet nahodnych repozitaru, ktere ma program najit
    :param string output: nazev vystupniho souboru
    """
    gh = github.GitHub(username=os.getenv("GH_USERNAME"), password=os.getenv("GH_PASSWORD"))

    remaining = sample_count
    one_part = 100.0 / sample_count
    percentage = 0
    with open(output, "w", 1) as f:
        f.write(", ".join(ATTRS) + "\n")

        while remaining > 0:
            # ziskej nahodny repozitar (klidne uz i pouzity)
            rindex = random.randint(0, MAX_ID)
            resp = download(gh, gh.repositories(), since=rindex)
            s = resp[0]

            # ziskej z neho data. pokud nelze pouzit, pokracuj, ale nesnizuj zbyvajici pocet
            try:
                stats = get_repo_stats(gh, s['owner']['login'], s['name'])

                f.write(", ".join(stats) + "\n")

                # TODO: participation? jak se zmenila frekvence nejvlivnejsich lidi?
                # TODO: watchers https://developer.github.com/v3/activity/watching/

                percentage += one_part
                print "\r%d %%" % percentage,

                remaining -= 1

            except (RepoNotValid, github.ApiError, KeyError):
                pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get Github repos dataset for GHAM project")
    parser.add_argument("-c", "--count", type=int, help="number of samples to download", default=100000)
    parser.add_argument("-o", "--output", help="name of the CSV output file", default="output.csv")
    args = parser.parse_args()

    main(args.count, args.output)
