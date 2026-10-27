#!/usr/bin/env python3
"""
analytics.py

Aggregates Duffel logs (see app.py) into hit and unique-visitor counts.
Standard library only.

Usage:
    python analytics.py [--by day|week|month|year] [--resource recount3] LOG [LOG ...]

Logs may be .tsv or .tsv.gz. Output is TSV: period, resource, hits, uniques.
Pseudonyms rotate yearly, so uniques are meaningful at day/week/month/year
granularity but cannot be computed across years.
"""
import argparse
import datetime
import gzip
import sys
from collections import defaultdict

def period_key(date, by):
    if by == 'day':
        return date.isoformat()
    if by == 'week':
        year, week, _ = date.isocalendar()
        return '{}-W{:02d}'.format(year, week)
    if by == 'year':
        return date.strftime('%Y')
    return date.strftime('%Y-%m')

def main():
    parser = argparse.ArgumentParser(description=__doc__,
                formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('logs', nargs='+')
    parser.add_argument('--by', choices=['day', 'week', 'month', 'year'],
                        default='month')
    parser.add_argument('--resource', default=None,
                        help='only count this resource (e.g. recount3)')
    args = parser.parse_args()
    hits = defaultdict(int)
    uniques = defaultdict(set)
    malformed = 0
    for logfile in args.logs:
        opener = gzip.open if logfile.endswith('.gz') else open
        with opener(logfile, 'rt') as stream:
            for line in stream:
                fields = line.rstrip('\n').split('\t')
                if len(fields) != 4:
                    malformed += 1
                    continue
                date_str, pseud, resource, path = fields
                if resource == '-' or path == '-':
                    # unresolved (404) request; not a download
                    continue
                if args.resource and resource != args.resource:
                    continue
                try:
                    date = datetime.date.fromisoformat(date_str)
                except ValueError:
                    malformed += 1
                    continue
                key = (period_key(date, args.by), resource)
                hits[key] += 1
                uniques[key].add(pseud)
    print('\t'.join(['period', 'resource', 'hits', 'uniques']))
    for key in sorted(hits):
        print('\t'.join([key[0], key[1], str(hits[key]),
                         str(len(uniques[key]))]))
    if malformed:
        print('skipped {} malformed lines'.format(malformed), file=sys.stderr)

if __name__ == '__main__':
    main()
