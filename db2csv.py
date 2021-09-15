#!/usr/bin/env python3

import argparse
import csv
import sqlite3
import sys


# Pulled out of imco.session because we don't want to depend on the session
# state or config.
def export_to_csv(db_path, fh, coder):
    writer = csv.writer(fh, lineterminator='\n')
    for i, row in enumerate(iterate_image_rows(db_path)):
        if i == 0:
            writer.writerow(['Coder'] + list(row.keys()))
        row = [coder] + list(row)
        writer.writerow(row)


# Pulled out of imco.db because we don't want to depend on the "codes" config,
# which we don't need in order to export from the db because the db schema
# already has the code names as column names.
def iterate_image_rows(db_path):
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    curs = connection.cursor()
    q = '''
        SELECT * FROM `codes`
        ORDER BY Dir ASC, Image ASC
        '''
    curs.execute(q)
    return curs


parser = argparse.ArgumentParser()
parser.add_argument('db_path', help="path to state.db to export")
parser.add_argument('coder', help="name of coder")
parser.add_argument('-o', '--outfile', default='state.csv')
args = parser.parse_args()

try:
    with open(args.outfile, 'w') as fh:
        export_to_csv(args.db_path, fh, args.coder)
except IOError as e:
    print(e, file=sys.stderr)
