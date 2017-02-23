import datetime
import sys

import numpy
from influxdb import client

import mql_parser

influxdb_client = client.InfluxDBClient(
    "192.168.10.6", "8086",
    "", "",
    "mon")



functions_for_repo = {
    'avg': 'mean',
    'max': 'max',
    'min': 'min',
    'count': 'count',
    'sum': 'sum',
    'rate': 'derivative'
}

# class Range(object):
#     def __init__(self, name, dimensions, values):
#         self.name = name
#         self.dimensions = dimensions
#         self.values = values
#
#
# class Vector(object):
#     def __init__(self):
#         pass


def get_function(function):
    if function in functions_for_repo:
        return functions_for_repo[function]
    else:
        return None


def _double_quote(string):
    return '"' + string + '"'


def _single_quote(string):
    return "'" + string + "'"


def query(name, dimensions, function=None, start_time=None, end_time=None, group_by=None,
          bucket_size=None):
    base_query = "Select {value} from \"{metric_name}\" " \
                 "{where_clause} " \
                 "{group_by} {limit}"

    # handle name is missing (if name is in dimensions, this will be overwritten below)
    if name is not None:
        metric_name = name
    else:
        metric_name = '/.*/'

    # create where clauses
    where_clauses = []

    if dimensions is not None:
        for dim in dimensions:
            clause = _double_quote(dim.key) + dim.operator
            if '~' in dim.operator:
                clause += dim.value
            else:
                clause += _single_quote(dim.value)
            where_clauses.append(clause)

    # if there is no range on a metric, we will collect only the last value
    limit = None
    if function == 'last_force':
        function = 'last'
        bucket_size = None
        limit = 1

    # add bucket size to group_by if exists
    if function is not None and bucket_size is not None:
        time_str = 'time(' + str(bucket_size) + 's)'
        if isinstance(group_by, list):
            group_by.append(time_str)
        else:
            group_by = [time_str]

    if start_time is not None:
        where_clauses.append('time >= \'' + start_time.isoformat() + 'Z\'')
    if end_time is not None:
        where_clauses.append('time <= \'' + end_time.isoformat() + 'Z\'')

    final_query = base_query.format(
        value=function + '(value) as value' if function is not None else 'value',
        metric_name=metric_name,
        where_clause=' where ' + " and ".join(where_clauses) if where_clauses else "",
        group_by=' group by ' + ','.join(group_by) if group_by is not None else "",
        limit=" limit " + str(limit) if limit is not None else ""
    )

    print(final_query)

    return parse_influx_results(influxdb_client.query(final_query, epoch='ms'))


def parse_influx_results(influx_data):
    # print(influx_data)
    results = []
    definitions = {}
    for key, series in influx_data.items():
        key_str = str(key)
        definitions[key_str] = key
        time_series = []
        for point in influx_data[key]:
            if point['value'] is None:
                continue
            time_series.append((point['time'], point['value']))
        results.append((key, numpy.rec.array(time_series)))
    return results


def main():
    data_start_time = datetime.datetime.strptime("2017-01-23T16:00:00.000Z", '%Y-%m-%dT%H:%M:%S.%fZ')
    query("cpu.idle_perc", None)
    query(None, [mql_parser.Dimension(['hostname', '=', 'devstack'])])
    query("cpu.idle_perc", None,
          start_time=data_start_time,
          end_time=data_start_time + datetime.timedelta(minutes=5))
    query("cpu.idle_perc", None,
          function='last',
          start_time=data_start_time,
          end_time=data_start_time + datetime.timedelta(minutes=5),
          bucket_size='60s')

if __name__ == '__main__':
    sys.exit(main())
