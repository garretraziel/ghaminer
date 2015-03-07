# coding: utf-8

import matplotlib.pyplot as plt
import github
import ghaminer
from dateutil.parser import parse as parse_date
import datetime

gh = github.GitHub(username="garretraziel", password="Boloomka0951")

page = 1
commits = []
while True:
    result = gh.repos("sgala")("gajim").commits().get(page=page)
    #result = gh.repos("garretraziel")("icp").commits().get(page=page)
    if len(result) > 0:
        commits.extend(result)
        page += 1
    else:
        break

commits.sort(key=lambda x: parse_date(x['commit']['committer']['date']))
times = [parse_date(c['commit']['committer']['date']) for c in commits]
timespan = (times[-1] - times[0]).days + 1
first = times[0]
last = times[-1]
freqs = [ghaminer.compute_freq_activity(commits, first, last, (first + datetime.timedelta(days=r))) for r in range(timespan)]
percs = [ghaminer.compute_perc_activity(commits, (first + datetime.timedelta(days=r))) for r in range(timespan)]
dates = [t.date() for t in times]
counts = [dates.count(first.date() + datetime.timedelta(days=r)) for r in range(timespan)]
f, axarr = plt.subplots(2, sharex=True)
axarr[0].plot(freqs, 'b-')
bx = axarr[0].twinx()
bx.plot(counts, 'r-')
axarr[1].plot(percs, 'b-')
bx = axarr[1].twinx()
bx.plot(counts, 'r-')
textdates = [(first.date() + datetime.timedelta(days=r)).strftime("%d %b") for r in range(timespan)]
plt.xticks(range(2, timespan, timespan/5), textdates[2::timespan/5], rotation='vertical')
axarr[0].set_title("Aktivita projektu dle frekvence a mnozstvi zbyvajici prace", y=1.08)
plt.show()
