# coding: utf-8

import matplotlib.pyplot as plt
import github
import ghaminer
import ghamath
from dateutil.relativedelta import relativedelta
import datetime

gh = github.GitHub(username="garretraziel", password="Boloomka0951")

print "getting information..."
commits, first, last = ghaminer.get_all_commits(gh, "os-autoinst", "os-autoinst")

print "sorting commits..."
commits.sort(key=ghaminer.get_commit_date)
times = [ghaminer.get_commit_date(c) for c in commits]
timespan = (last - first).days + 1

print "getting freq ratio"
freqs = [ghaminer.compute_commit_freq_activity(commits, (first + datetime.timedelta(days=r))) for r in range(timespan)]
print "getting percentage"
percs = [ghaminer.compute_perc_activity(commits, (first + datetime.timedelta(days=r))) for r in range(timespan)]
print "getting 1w freq"
freq1w = [
    ghamath.compute_delta_freq_func(commits, ghaminer.get_commit_date, first, (first + datetime.timedelta(days=r)),
                                    relativedelta(weeks=1)) for r in range(timespan)]
print "getting 1m freq"
freq1m = [
    ghamath.compute_delta_freq_func(commits, ghaminer.get_commit_date, first, (first + datetime.timedelta(days=r)),
                                    relativedelta(months=1)) for r in range(timespan)]
print "getting 6m freq"
freq6m = [
    ghamath.compute_delta_freq_func(commits, ghaminer.get_commit_date, first, (first + datetime.timedelta(days=r)),
                                    relativedelta(months=6)) for r in range(timespan)]
print "getting 1y freq"
freq1y = [
    ghamath.compute_delta_freq_func(commits, ghaminer.get_commit_date, first, (first + datetime.timedelta(days=r)),
                                    relativedelta(years=1)) for r in range(timespan)]

dates = times
counts = [dates.count(first + datetime.timedelta(days=r)) for r in range(timespan)]
text_dates = [(first + datetime.timedelta(days=r)).strftime("%d %b") for r in range(timespan)]

print "plotting..."
plt.subplot(321)
plt.title("Aktivita dle miry frekvence")
plt.plot(freqs, 'b-')
bx = plt.twinx()
bx.plot(counts, 'r-')
plt.xlim(xmax=timespan)
plt.xticks(range(2, timespan, timespan / 5), text_dates[2::timespan / 5], rotation='vertical')

plt.subplot(322)
plt.title("Aktivita dle zbyvajici casti zmen")
plt.plot(percs, 'b-')
bx = plt.twinx()
bx.plot(counts, 'r-')
plt.xlim(xmax=timespan)
plt.xticks(range(2, timespan, timespan / 5), text_dates[2::timespan / 5], rotation='vertical')

plt.subplot(323)
plt.title("Aktivita dle frekvence budouciho tydne")
plt.plot(freq1w, 'b-')
bx = plt.twinx()
bx.plot(counts, 'r-')
plt.xlim(xmax=timespan)
plt.xticks(range(2, timespan, timespan / 5), text_dates[2::timespan / 5], rotation='vertical')

plt.subplot(324)
plt.title("Aktivita dle frekvence budouciho mesice")
plt.plot(freq1m, 'b-')
bx = plt.twinx()
bx.plot(counts, 'r-')
plt.xlim(xmax=timespan)
plt.xticks(range(2, timespan, timespan / 5), text_dates[2::timespan / 5], rotation='vertical')

plt.subplot(325)
plt.title("Aktivita dle frekvence budouciho pul roku")
plt.plot(freq6m, 'b-')
bx = plt.twinx()
bx.plot(counts, 'r-')
plt.xlim(xmax=timespan)
plt.xticks(range(2, timespan, timespan / 5), text_dates[2::timespan / 5], rotation='vertical')

plt.subplot(326)
plt.title("Aktivita dle frekvence budouciho roku")
plt.plot(freq1y, 'b-')
bx = plt.twinx()
bx.plot(counts, 'r-')
plt.xlim(xmax=timespan)
plt.xticks(range(2, timespan, timespan / 5), text_dates[2::timespan / 5], rotation='vertical')

plt.show()
