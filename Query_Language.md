# Monasca Query Language Definition

## Description
Monasca query language was designed to give more comprehensive tools to metric manipulation. It includes many advanced features beyond the basic API provided.

## Data Types
Monasca Query Language includes several data types: Vector, Range, Scalar.

### Vector
A vector data type includes multiple metric definitions (Ranges) in a list. Most operations will be performed between matching elements in the list.

### Range
A range represents a single time series. It includes the metric definition and a list of data points as (time, value) tuples. Most operations will be performed element-wise on the list of data points.

### Scalar
A scalar represents any single integer or float value.

## Query Format

### Basic Syntax
Queries follow basic mathematical syntax. For examples ```1 > 2``` will yield ```False```, ```1 + 1``` will yield ```2```, and so on.

#### Selecting a Metric
Generally, queries will contain a reference to metric data. A few simple examples might be:
* ```cpu.idle_perc```
* ```net.in_bytes_sec```

#### Selecting Dimensions
Metric definitions usually also contain dimensions, which can be selected alongside the metric name as follows
* ```cpu.idle_perc{hostname=test_host_01}```
* ```net.in_bytes_sec{hostname=juniper-01,device=eth0}```

Dimensions support the following comparisons  ```=, !=, =~, !~```, where ```~``` corresponds to a regular expression comparison.
* ```net.out_bytes_sec{device!=eth0}``` would find metrics for every device other than ```eth0```
* ```memory.used{hostname=~/juniper/``` will find every metric where the hostname include ```juniper```

The metric name can be referenced inside the dimensions with ```__name__```, which will allow the same comparisons as stated above
* ```{__name__=net.in_bytes_sec,hostname=juniper-01,device=eth0}```
* ```{__name__=~/^net/,hostname=~/juniper/``` will match any metric starting with ```net``` with ```juniper``` in the hostname

Additionally, the metric name may be excluded with a dimensions selection.
* ```{hostname=juniper-01}``` will return all metrics collected from the host ```juniper-01```

Each of these will return the latest value (within the last five minutes) of the specified series. If the selection corresponds to multiple series, a vector of the results will be returned instead. The general format is as follows:
* ```<metric_name>{<dimension_key><comparison_operator><dimension_value>,...}```

### Selecting Metrics over Time
#### Range
To retrieve historical data, metrics may be queried with time parameters. Adding a range to a query returns all data points within the time constraints.
Allowed time units are w (weeks), d (days), h (hours), m (minutes), s (seconds).
*  ```cpu.idle_perc [5m]``` will collect the last 5 minutes of cpu idle percentage data points.

#### Offset
To retrieve data stored farther in the past, add an offset clause. Offsets may be specified relative to the present or as an iso8601 formatted timestamp.
* ```cpu.idle_perc offset 5w``` returns data starting 5 weeks ago
* ```cpu.idle_perc offset 2016-01-01T00:00:00.000Z``` returns data starting at January 1st, 2016

Without a range clause, the above queries will return the most recent data point within five minutes before the specified time.

#### Grouping Data Points by Time
MQL supports grouping data by time, generally for use with aggregation functions. This is done inside the range clause, for example:
* ```cpu.idle_perc [5m over 30m]``` produces 6 groups of 5 minutes each
* ```cpu.idle_perc [5m over 22m]``` produces 4 groups of 5 minutes and one group of 2 minutes

### Functions
MQL supports a variety of functions including basic statistical functions (average, max, min, count, sum) and an additional utility function, 'rate'. These may be applied to any data type, but will behave slightly differently in each case.

Avg, max, min, count, sum will reduce a group of points down to a single data point. Rate will remove a single data point from the end of each group. All of these functions will not modify a scalar input.

Example usage:
* ```max(cpu.idle_perc [5m])``` gives the highest single point in the last five minutes
* ```avg(cpu.idle_perc [5m over 30m])``` gives 6 values, one for each 5 minute period
* ```max(1)``` returns ```1```

Functions may be nested for additional capabilities. Examples:
* ```avg(rate(cpu.idle_perc [1d over 1w]))``` gives the average cpu rate per day for the last week

### Metric Arithmetic
MQL allows simple arithmetic operations on metrics. The simplest case is modifying a range with a scalar.
* ```cpu.idle_perc [5m] + 5``` adds 5 to each data point for the last 5 minutes.
* ```cpu.idle_perc / 100``` reduces the cpu percentage to a decimal value

Multiple ranges may be modified together as well. In these cases, the ranges must have matching times (within a tolerance of 1 minute, timestamps will be averaged in the resulting range)
* ```memory.available - memory.free``` will add pairs of data points with matching times, resulting in a single range as the result.

### Comparisons
Metrics may be compared with simple boolean comparisons ```>=, >, <=, <```. The result will be a range of data points with a boolean value for each timestamp
* ```cpu.idle_perc [5m] > 10``` returns a range with ```True``` for each value above 10 and ```False``` for each value below 10

### Logical Operations
The ranges of boolean values may be combined with logical operations ```and, or``` to create a new range.
* ```cpu.idle_perc > 10 and cpu.idle_perc < 20``` would return ```True``` if the latest data point is between 10 and 20

## Notes
* Any empty groups in a grouped range (ex. ```cpu.idle_perc [5m over 15m]```) will be discarded. This can have an impact when attempting to combine metrics later
* Metrics must be in the same time range to perform arithmetic (each pair of points must be within one minute of each other)
* Any metrics combined via arithmetic will keep only shared elements of the definition and timestamps will be averaged in the result
* Boolean operations will maintain the definition and timestamps of the left operand
* Boolean operations require timestamps to be aligned (same requirements as metric arithmetic)
* Boolean constants are not allowed (i.e. ```net.in_bytes_sec > 100 and True``` is not a valid expression)
* Logical operations (and/or operations) will maintain the definition and timestamps of the left operand  
