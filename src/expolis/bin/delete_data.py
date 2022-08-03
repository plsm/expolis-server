#!/usr/bin/env python3

import argparse
import datetime
import sys
import time

import psycopg2

import aggregation
import data
import interpolation_method
import period
import resolution
from database import Database
from interpolation import INTERPOLATION_PERIOD, INTERPOLATION_RESOLUTION, INTERPOLATION_STATISTIC


__DATETIME_FORMAT_ARG__ = '%Y-%m-%dT%H:%M:%S'
__DATETIME_FORMAT_SQL__ = '%Y-%m-%d %H:%M:%S.%f'


class Args:
    def __init__ (self):
        parser = argparse.ArgumentParser (
            description='Delete data between a time period'
        )
        parser.add_argument (
            '--from',
            metavar='DATE',
            dest='from_date',
            default=None,
            type=str,
            help='Time period starting date. If omitted starts from the earliest sensor data.'
        )
        parser.add_argument (
            '--to',
            metavar='DATE',
            default=None,
            type=str,
            help='Time period end date. If omitted goes to the latest sensor data.'
        )
        parser.add_argument (
            '--YeS',
            action='store_true',
            help='Supply this option in scripts, to skip the confirmation prompt.'
        )
        parser.add_argument (
            '--verbose',
            action='store_true',
            help='Be verbose on which table is being processed.'
        )
        args = parser.parse_args ()
        self.from_date = args.from_date  # type: str
        self.to_date = args.to           # type: str
        self.confirm = args.YeS          # type: bool
        self.verbose = args.verbose      # type: bool


def main ():
    args = Args ()
    if args.confirm or confirm ():
        delete_data (args.from_date, args.to_date, args.verbose)


def delete_data (from_date, to_date, verbose):
    if from_date is None and to_date is None:
        date_filter = ''
        sql_arguments = []
    elif from_date is None and to_date is not None:
        date_filter = ' WHERE _when <= CAST (%s AS TIMESTAMP)'
        sql_arguments = [
            datetime.datetime.strptime (to_date, __DATETIME_FORMAT_ARG__).strftime (__DATETIME_FORMAT_SQL__)
        ]
    elif to_date is None:
        date_filter = ' WHERE _when >= CAST (%s AS TIMESTAMP)'
        sql_arguments = [
            datetime.datetime.strptime (from_date, __DATETIME_FORMAT_ARG__).strftime (__DATETIME_FORMAT_SQL__),
        ]
    else:
        date_filter = ' WHERE _when >= CAST (%s AS TIMESTAMP) AND _when <= CAST (%s AS TIMESTAMP)'
        sql_arguments = [
            datetime.datetime.strptime (from_date, __DATETIME_FORMAT_ARG__).strftime (__DATETIME_FORMAT_SQL__),
            datetime.datetime.strptime (to_date, __DATETIME_FORMAT_ARG__).strftime (__DATETIME_FORMAT_SQL__),
        ]
    data.load_data ()
    db = Database ()

    def run_delete (table_name):
        sql_command = 'DELETE FROM {}{}'.format (
            table_name,
            date_filter)
        db.cursor.execute (sql_command, sql_arguments)
        if db.cursor.rowcount == 0:
            if verbose:
                print ('Nothing to delete from {}'.format (table_name))
        elif db.cursor.rowcount == 1:
            print ('Deleted one row from {}'.format (table_name))
        else:
            print ('Deleted {} rows from {}'.format (db.cursor.rowcount, table_name))

    print ('Deleting measurement_properties and measurement_data_D tables...')
    run_delete ('measurement_properties')
    print ('Deleting aggregation_S_P_R_D tables...')
    for a_data in data.DATA:
        if a_data.mobile_app_flag or a_data.route_planner_flag:
            for s in aggregation.STATISTICS:
                if not a_data.mobile_app_flag and (not a_data.route_planner_flag or s != INTERPOLATION_STATISTIC):
                    continue
                for p in period.PERIODS:
                    if not a_data.mobile_app_flag and (not a_data.route_planner_flag or p != INTERPOLATION_PERIOD):
                        continue
                    for r in resolution.RESOLUTIONS:
                        if not a_data.mobile_app_flag and (not a_data.route_planner_flag or r != INTERPOLATION_RESOLUTION):
                            continue
                        run_delete (a_data.table_aggregation_name (s, p, r))
    print ('Deleting interpolation_M_P_D tables...')
    for a_data in data.DATA:
        if a_data.mobile_app_flag or a_data.route_planner_flag:
            for m in interpolation_method.METHODS:
                for p in period.PERIODS:
                    if not a_data.mobile_app_flag and a_data.route_planner_flag and p != INTERPOLATION_PERIOD:
                        continue
                    run_delete (a_data.table_interpolation_name (m, p))


def confirm ():
    answer = input ('Are you sure you want to continue? (yes/no) ')
    while True:
        answer = answer.lower ()
        if answer == 'y':
            answer = input ('Pleaser enter yes: ')
        elif answer == 'yes':
            count = 3
            while count > 0:
                print ('\rStarting in {} seconds...'.format (count), end='')
                sys.stdout.flush ()
                time.sleep (1)
                count += -1
            return True
        else:
            return False


if __name__ == '__main__':
    main ()
