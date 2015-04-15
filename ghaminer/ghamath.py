#!/usr/bin/env python

import datetime

import numpy as np
from dateutil.relativedelta import relativedelta
import pytz


def is_old_enough(date, timespan=relativedelta(months=6), now=pytz.UTC.localize(datetime.datetime.now())):
    """Vraci, zda je repozitar dostatecne stary na to, aby mohl byt pouzit.

    :param datetime.date date: datum posledniho zaslani zmeny do repozitare
    :param relativedelta timespan: jak moc stary ma repozitar byt
    :return: informaci, zda je repozitar dostatecne stary
    :rtype: bool
    """
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


def compute_delta_freq_func(values, get_date_func, time_created, point_in_time, time_delta):
    """Vraci frekvenci udalosti pro zadane casove rozpeti.

    :param [dict] values: seznam vsech udalosti
    :param function get_date_func: funkce pro ziskani data z hodnoty
    :param datetime.date time_created: cas ve kterem byl repozitar vytvoren
    :param datetime.date point_in_time: cas ve kterem se ma frekvence pocitat
    :param relativedelta time_delta: casove rozmezi, pro ktere se ma frekvence pocitat
    :return: frekvence udalosti v zadanem casovem rozmezi
    :rtype: float
    """
    if is_old_enough(point_in_time, time_delta):
        start = min(point_in_time, point_in_time + time_delta)
        start = max(start, time_created)
        end = max(point_in_time, point_in_time + time_delta)
        f = compute_freq_func(values, get_date_func, start, end)
        return f
    else:
        return np.NaN


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
        a = np.array(values_in)
        avg = a.mean()
    else:
        avg = np.NaN
    return avg


def compute_delta_avg_func(values, get_date_func, get_value_func, time_created, point_in_time, time_delta):
    """Vraci prumer hodnot pro zadane casove rozpeti.

    :param [dict] values: seznam vsech udalosti
    :param function get_date_func: funkce, ktera ziska casovy udaj z jedne udalosti
    :param function get_value_func: funkce, ktera ziska hodnotu udalosti
    :param datetime.date time_created: cas ve kterem byl repozitar vytvoren
    :param datetime.date point_in_time: cas ve kterem se ma prumer pocitat
    :param relativedelta time_delta: casove rozmezi, pro ktere se ma prumer pocitat
    :return: prumer hodnot v zadanem casovem rozmezi
    :rtype: float
    """
    if is_old_enough(point_in_time, time_delta):
        start = min(point_in_time, point_in_time + time_delta)
        start = max(start, time_created)
        end = max(point_in_time, point_in_time + time_delta)
        avg = compute_avg_func(values, get_date_func, get_value_func, start, end)
        return avg
    else:
        return np.NaN


def compute_contrib_count(contribs, percent, time_from, time_to):
    """Vraci kolika z nejaktivnejsich lidi bylo zaslano alespon "percent" zmen za dane casove obdobi.

    :param dict contribs: slovnik autor commitu: commity
    :param int percent: kolik procent museli udelat
    :param datetime.date time_from: cas od ktereho se pocet pocita
    :param datetime.date time_to: cas do ktereho se pocet pocita
    :return: pocet lidi, kteri spolu udelali aspon "percent" zmen
    :rtype: int
    """
    counts = []
    s = 0
    for c in contribs:
        l = len([v for v in contribs[c] if time_from <= v <= time_to])
        counts.append(l)
        s += l
    counts.sort(reverse=True)

    i = 1
    rat = percent/100.0
    while sum(counts[:i]) < rat*s:
        i += 1
    return i


def compute_delta_contrib_count(contribs, percent, time_created, point_in_time, time_delta):
    """Vraci kolika z nejaktivnejsich lidi bylo zaslano alespon "percent" zmen za dane casove rozpeti.

    :param dict contribs:
    :param int percent:
    :param datetime.date time_created:
    :param datetime.date point_in_time:
    :param relativedelta time_delta:
    :return:
    :rtype: int
    """
    if is_old_enough(point_in_time, time_delta):
        start = min(point_in_time, point_in_time + time_delta)
        start = max(start, time_created)
        end = max(point_in_time, point_in_time + time_delta)
        count = compute_contrib_count(contribs, percent, start, end)
        return count
    else:
        return np.NaN


def compute_contrib(contribs, percent, time_from, time_to):
    """Vraci nejaktivnejsi lidi, kteri zaslani alespon "percent" zmen za dane casove obdobi.

    :param dict contribs: slovnik autor commitu: commity
    :param int percent: kolik procent museli udelat
    :param datetime.date time_from: cas od ktereho se pocet pocita
    :param datetime.date time_to: cas do ktereho se pocet pocita
    :return: seznam lidi, kteri spolu udelali aspon "percent" zmen
    :rtype: [string]
    """
    counts = []
    s = 0
    for c in contribs:
        l = len([v for v in contribs[c] if time_from <= v <= time_to])
        counts.append((c, l))
        s += l
    counts.sort(key=lambda x: x[1], reverse=True)

    i = 1
    rat = percent/100.0
    while sum([x[1] for x in counts[:i]]) < rat*s:
        i += 1
    return [x[0] for x in counts[:i]]


def compute_delta_contrib(contribs, percent, time_created, point_in_time, time_delta):
    """Vraci nejaktivnejsi lidi, kteri zaslani alespon "percent" zmen za dane casove rozpeti.

    :param dict contribs: slovnik autor commitu: commity
    :param int percent: kolik procent museli udelat
    :param datetime.date time_created: cas kdy byl repozitar vytvoren
    :param datetime.date point_in_time: cas pro ktery se pocita
    :param relativedelta time_delta: casove rozpeti od point_in_time
    :return: seznam lidi, kteri spolu udelali aspon "percent" zmen
    :rtype: [string]
    """
    if is_old_enough(point_in_time, time_delta):
        start = min(point_in_time, point_in_time + time_delta)
        start = max(start, time_created)
        end = max(point_in_time, point_in_time + time_delta)
        contrib = compute_contrib(contribs, percent, start, end)
        return contrib
    else:
        return []
