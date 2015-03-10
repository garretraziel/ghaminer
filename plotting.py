# coding: utf-8

import matplotlib.pyplot as plt
import github
import ghaminer
from dateutil.parser import parse as parse_date
from dateutil.relativedelta import relativedelta
import datetime

gh = github.GitHub(username="garretraziel", password="Boloomka0951")

print "getting information..."
page = 1
commits = []
while True:
    print "Page: %d" % page
    result = gh.repos("sgala")("gajim").commits().get(page=page)
    #result = gh.repos("garretraziel")("icp").commits().get(page=page)
    if len(result) > 0:
        commits.extend(result)
        page += 1
    else:
        break

print "\nsorting commits..."
commits.sort(key=lambda x: parse_date(x['commit']['committer']['date']))
times = [parse_date(c['commit']['committer']['date']) for c in commits]
timespan = (times[-1] - times[0]).days + 1
first = times[0]
last = times[-1]

print "getting freq ratio"
freqs = [ghaminer.compute_commit_freq_activity(commits, (first + datetime.timedelta(days=r))) for r in range(timespan)]
print "getting percentage"
percs = [ghaminer.compute_perc_activity(commits, (first + datetime.timedelta(days=r))) for r in range(timespan)]
print "getting 1w freq"
freq1w = [ghaminer.compute_delta_freq_activity(commits, (first + datetime.timedelta(days=r)), relativedelta(weeks=1)) for r in range(timespan)]
print "getting 1m freq"
freq1m = [ghaminer.compute_delta_freq_activity(commits, (first + datetime.timedelta(days=r)), relativedelta(months=1)) for r in range(timespan)]
print "getting 6m freq"
freq6m = [ghaminer.compute_delta_freq_activity(commits, (first + datetime.timedelta(days=r)), relativedelta(months=6)) for r in range(timespan)]
print "getting 1y freq"
freq1y = [ghaminer.compute_delta_freq_activity(commits, (first + datetime.timedelta(days=r)), relativedelta(years=1)) for r in range(timespan)]

dates = [t.date() for t in times]
counts = [dates.count(first.date() + datetime.timedelta(days=r)) for r in range(timespan)]
text_dates = [(first.date() + datetime.timedelta(days=r)).strftime("%d %b") for r in range(timespan)]

print "plotting..."
plt.subplot(321)
plt.title("Aktivita dle miry frekvence")
plt.plot(freqs, 'b-')
bx = plt.twinx()
bx.plot(counts, 'r-')
plt.xlim(xmax=timespan)
plt.xticks(range(2, timespan, timespan/5), text_dates[2::timespan/5], rotation='vertical')

plt.subplot(322)
plt.title("Aktivita dle zbyvajici casti zmen")
plt.plot(percs, 'b-')
bx = plt.twinx()
bx.plot(counts, 'r-')
plt.xlim(xmax=timespan)
plt.xticks(range(2, timespan, timespan/5), text_dates[2::timespan/5], rotation='vertical')

plt.subplot(323)
plt.title("Aktivita dle frekvence budouciho tydne")
plt.plot(freq1w, 'b-')
bx = plt.twinx()
bx.plot(counts, 'r-')
plt.xlim(xmax=timespan)
plt.xticks(range(2, timespan, timespan/5), text_dates[2::timespan/5], rotation='vertical')

plt.subplot(324)
plt.title("Aktivita dle frekvence budouciho mesice")
plt.plot(freq1m, 'b-')
bx = plt.twinx()
bx.plot(counts, 'r-')
plt.xlim(xmax=timespan)
plt.xticks(range(2, timespan, timespan/5), text_dates[2::timespan/5], rotation='vertical')

plt.subplot(325)
plt.title("Aktivita dle frekvence budouciho pul roku")
plt.plot(freq6m, 'b-')
bx = plt.twinx()
bx.plot(counts, 'r-')
plt.xlim(xmax=timespan)
plt.xticks(range(2, timespan, timespan/5), text_dates[2::timespan/5], rotation='vertical')

plt.subplot(326)
plt.title("Aktivita dle frekvence budouciho roku")
plt.plot(freq1y, 'b-')
bx = plt.twinx()
bx.plot(counts, 'r-')
plt.xlim(xmax=timespan)
plt.xticks(range(2, timespan, timespan/5), text_dates[2::timespan/5], rotation='vertical')

plt.show()
