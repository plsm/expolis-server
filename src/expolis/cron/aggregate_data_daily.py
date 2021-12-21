#!/usr/bin/env python3

import datetime
from typing import TextIO

import aggregation
import resolution

INTERPOLATION_RESOLUTION = resolution.FIFTY_METERS  # type: resolution.Resolution
INTERPOLATION_STATISTIC = aggregation.AVG  # type: aggregation.Statistic


def main (fd_log: TextIO):
    import data
    from database import Database
    from resolution import RESOLUTIONS
    from aggregation import STATISTICS
    from interpolation_period import PeriodDaily

    data.load_data ()
    db = Database ()
    now = datetime.datetime.now ()
    when = datetime.datetime (
        year=now.year,
        month=now.month,
        day=now.day
    ) - datetime.timedelta (days=1)
    time_period = PeriodDaily (when)
    fd_log.write ('{}:   aggregation period {}\n'.format (
        datetime.datetime.now ().isoformat (),
        time_period
    ))
    for s in STATISTICS:
        for r in RESOLUTIONS:
            for d in data.DATA:
                if not (d.mobile_app_flag or
                        (d.route_planner_flag and s == INTERPOLATION_STATISTIC and r == INTERPOLATION_RESOLUTION)):
                    continue
                fd_log.write ('{}:    {:10s} {:6s} {:30s}\n'.format (
                    datetime.datetime.now ().isoformat (),
                    s.description,
                    r.description,
                    d.description_en,
                ))
                function_name = 'aggregate_' + s.sql_function + '_' + time_period.sql_identifier + '_' + \
                                r.sql_identifier + '_' + d.sql_identifier
                db.cursor.callproc (
                    function_name,
                    {
                        'from_date': time_period.start,
                        'to_date': time_period.end,
                    }
                )


with open ('/var/log/expolis/aggregate-data-day', 'a') as fd:
    fd.write ('{}: start\n'.format (datetime.datetime.now ().isoformat ()))
    try:
        main (fd)
    except Exception as e:
        fd.write ('{}: error {}\n'.format (
            datetime.datetime.now ().isoformat (),
            e,
        ))
    fd.write ('{}: end\n'.format (datetime.datetime.now ().isoformat ()))
