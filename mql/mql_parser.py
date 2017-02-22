import datetime
import sys
import time

import pyparsing

from query_structures import (Dimension,
                              RangeSelector,
                              OffsetSelector,
                              MetricSelector,
                              FuncStmt,
                              Expression,
                              BooleanExpression,
                              LogicalExpression)

COMMA = pyparsing.Suppress(pyparsing.Literal(","))
LPAREN = pyparsing.Suppress(pyparsing.Literal("("))
RPAREN = pyparsing.Suppress(pyparsing.Literal(")"))
LBRACE = pyparsing.Suppress(pyparsing.Literal("{"))
RBRACE = pyparsing.Suppress(pyparsing.Literal("}"))
LBRACKET = pyparsing.Suppress(pyparsing.Literal("["))
RBRACKET = pyparsing.Suppress(pyparsing.Literal("]"))

MINUS = pyparsing.Literal("-")

integer_number = pyparsing.Word(pyparsing.nums)
decimal_number = (pyparsing.Optional(MINUS) + integer_number +
                  pyparsing.Optional("." + integer_number))
decimal_number.setParseAction(lambda tokens: float("".join(tokens)))

# Initialize non-ascii unicode code points in the Basic Multilingual Plane.
unicode_printables = u''.join(
    unichr(c) for c in range(128, 65536) if not unichr(c).isspace())

# Does not like comma. No Literals from above allowed.
valid_identifier_chars = (
    (unicode_printables + pyparsing.alphanums + ".-_#$%&'*+/:;?@[\\]^`|"))

metric_name = (
    pyparsing.Word(pyparsing.alphas, valid_identifier_chars, min=1, max=255)("metric_name"))
dimension_name = pyparsing.Word(valid_identifier_chars + ' ', min=1, max=255)
dimension_value = pyparsing.Word(valid_identifier_chars + ' ', min=1, max=255)

dim_comparison_op = pyparsing.oneOf("= != =~ !~")

dimension = dimension_name + dim_comparison_op + dimension_value
dimension.setParseAction(Dimension)

dimension_list = pyparsing.Group((LBRACE + pyparsing.Optional(
    pyparsing.delimitedList(dimension)) +
                                  RBRACE))

metric = (metric_name + pyparsing.Optional(dimension_list) |
          pyparsing.Optional(metric_name) + dimension_list)

time_unit = pyparsing.oneOf("s m h d w")

over = pyparsing.Keyword("over", caseless=True)

time_selector = integer_number + time_unit
time_selector.setParseAction(lambda tokens: "".join(tokens))

range_selector = (LBRACKET + time_selector + pyparsing.Optional(over + time_selector) + RBRACKET)
range_selector.setParseAction(RangeSelector)

offset = pyparsing.Keyword("offset", caseless=True)


def validate_iso_timestamp(tokens):
    return datetime.datetime.strptime(str(tokens[0]), '%Y-%m-%dT%H:%M:%S.%fZ')
# include three digits below decimal and 'Z'
iso_time_stamp = pyparsing.Word(pyparsing.nums + "TZ-:.", exact=24)
iso_time_stamp.setParseAction(validate_iso_timestamp)  # validate timestamp

offset_selector = offset + (time_selector | iso_time_stamp)
offset_selector.setParseAction(OffsetSelector)

metric_selector = metric + pyparsing.Optional(range_selector) + pyparsing.Optional(offset_selector)
metric_selector.setParseAction(MetricSelector)

func = pyparsing.oneOf("max min avg count sum last rate", caseless=True)

expression = pyparsing.Forward()

func_stmt = func + LPAREN + expression + RPAREN
func_stmt.setParseAction(FuncStmt)

sub_expression = (func_stmt |
                  metric_selector |
                  decimal_number)

arithmetic_operator_high_precedence = pyparsing.oneOf("* /")
arithmetic_operator_low_precedence = pyparsing.oneOf("+ -")

expression << pyparsing.infixNotation(sub_expression,
                                      [(arithmetic_operator_high_precedence, 2, pyparsing.opAssoc.LEFT, Expression),
                                       (arithmetic_operator_low_precedence, 2, pyparsing.opAssoc.LEFT, Expression)])

relational_op = pyparsing.oneOf("< lt <= lte > gt >= gte", caseless=True)

boolean_expression = expression + relational_op + expression
boolean_expression.setParseAction(BooleanExpression)

logical_and = pyparsing.oneOf("and &&", caseless=True)
logical_or = pyparsing.oneOf("or ||", caseless=True)

logical_expression = pyparsing.infixNotation(boolean_expression,
                                             [(logical_and, 2, pyparsing.opAssoc.LEFT, LogicalExpression),
                                              (logical_or, 2, pyparsing.opAssoc.LEFT, LogicalExpression)])

# creating a separate rule for boolean functions makes the parsing significantly faster
#  (over 10x on average)
boolean_functions = pyparsing.oneOf("any all", caseless=True)

boolean_function_stmt = pyparsing.Forward()
boolean_function_stmt << boolean_functions + LPAREN + logical_expression + RPAREN
boolean_function_stmt.setParseAction(FuncStmt)

# order matters, put longer first
grammar = (boolean_function_stmt | logical_expression | expression)


class MQLParser(object):
    def __init__(self, expr):
        self._expr = expr

    def parse(self):
        parse_result = grammar.parseString(self._expr, parseAll=True)
        return parse_result


def main():

    expression_list = [
        # test metric parsing
        "net.in_bytes_sec",
        "net.in_bytes_sec{}",
        "net.in_bytes_sec{hostname=dev}",
        "net.in_bytes_sec{hostname=~dev, testing=testing}",
        "{hostname!~testing, testing!=hostname}",
        "{hostname=dev, testing!=testing}",
        "{host name=testing}",
        "{22=34, 45!=1}",

        # test function parsing
        "max(2)",
        "avg(net.in_bytes_sec)",
        "max(net.in_bytes_sec{})",
        "count(min(2.1))",
        "max(avg(net.in_bytes_sec))",
        "(avg(latency) - latency_threshold) + 22",

        # test range
        "net.in_bytes_sec [5m]",
        "avg(net.out_bytes_sec [2w])",
        "max(avg(test_metric [1s]))",

        # test range with offset
        "net.in_bytes_sec offset 1w",
        "net.in_bytes_sec offset 2017-01-01T13:10:12.001Z",
        "net.in_bytes_sec [5m] offset 1w",
        "net.in_bytes_sec [5m] offset 2017-01-01T13:10:12.001Z",

        # test range with grouping
        "net.in_bytes_sec [1m over 15m]",
        "avg(net.out_bytes_sec [10m over 1h])",
        "net.in_bytes_sec [5m over 1d] + net.out_bytes_sec [5m over 1d]",

        # test range with grouping and offset
        "net.in_bytes_sec [1m over 15m] offset 1w",
        "avg(net.out_bytes_sec [10m over 1h] offset 2017-01-01T13:13:13.102Z)",
        "net.in_bytes_sec [5m over 1d] offset 2016-01-01T01:01:01.001Z + net.out_bytes_sec [5m over 1d] offset 1w",

        # test multiple statements
        "net.in_bytes_sec + net.out_bytes_sec",
        "avg(net.in_bytes_sec) / max(net.out_bytes_sec)",
        "net.in_bytes_sec [5m] * net.out_bytes_sec [5s]",
        "avg(net.in_bytes_sec [5m]) / avg(net.out_bytes_sec [5m over 1h])",
        "min(net.in_bytes_sec) + avg(net.in_bytes_sec) + max(net.in_bytes_sec)",

        # test statements nested inside functions
        "avg(net.in_bytes_sec - net.out_bytes_sec)",
        "avg(net.in_bytes_sec - net.out_bytes_sec) - count(test_metric)",
        "sum(avg(net.out_bytes_sec) - avg(net.in_bytes_sec) / count(net.total_bytes_sec))",

        # test boolean expressions
        "net.in_bytes_sec > 5000",
        "net.in_bytes_sec > net.out_bytes_sec",
        "avg(net.in_bytes_sec) <= avg(net.out_bytes_sec)",
        "max(net.in_bytes_sec [5m]) >= max(net.out_bytes_sec [5m] offset 1d)",
        "5 lt 10",
        "net.out_bytes_sec gte test_metric",

        # test logical expressions
        "net.in_bytes_sec > net.out_bytes_sec or net.in_bytes_sec < net.out_bytes_sec",
        "avg(net.in_bytes_sec [17m]) >= test_metric || min(net.out_bytes_sec [1h over 2d]) < test_metric",
        "test_metric > 1 and test_metric < 2 && avg(test_metric [5m]) < test_metric offset 2016-01-01T01:01:01.001Z",  # Failing to parse completely
        "(test_metric > 1 or test_metric < 1) and test_metric >= 1",
        "test_metric > 1 or (test_metric < 1 and test_metric >= 1)",
        "test_metric > 1 or test_metric < 1 and test_metric < 2",

        # test boolean expression functions
        "any(test_metric > 1)",
        "all(test_metric < 10)",

        # test logical expression functions
        "any(test_metric > 1 and test_metric < 10)",
    ]

    negative_expression_list = [
        # test invalid metric names
        "22{hostname=test-01}",
        "2a3{hostname=test-02}",

        # test invalid symbol/operator use
        "test_metric // 22",
        "test_metric >> 22",
        "test_metric > and test_metric < 2",
        "14 < net.in_bytes < 25",

        # test timestamp parsing/validation
        "test_metric offset 2017-01-01",
        "test_metric offset 2017-01-57T01:01:01.001Z",
    ]

    start_time = time.time()

    for expr in expression_list:
        print(expr)
        result = MQLParser(expr).parse()
        # uncomment below to show details of parsing
        print(result)
        print("Accepted")
        print

    print("--Negative Testing--")

    for expr in negative_expression_list:
        try:
            print(expr)
            result = MQLParser(expr).parse()
            assert False, "Expression did not fail"
        except (pyparsing.ParseBaseException, ValueError) as ex:
            # print(ex)
            print("Rejected")
            pass
        print

    total_time = time.time() - start_time
    total_queries = len(expression_list) + len(negative_expression_list)
    print("Complete {} in {} seconds".format(total_queries, total_time))

    data_start_time = datetime.datetime.strptime("2017-01-23T16:00:00.000Z", '%Y-%m-%dT%H:%M:%S.%fZ')
    eval_expr_list = [
        # check basic metric results
        'cpu.idle_perc offset ' + data_start_time.isoformat() + '.000Z',
        'cpu.idle_perc [5m] offset ' + data_start_time.isoformat() + '.000Z',

        # check single depth function results
        'avg(cpu.idle_perc offset ' + data_start_time.isoformat() + '.000Z)',
        'avg(cpu.idle_perc [1d] offset ' + data_start_time.isoformat() + '.000Z)',
        'avg(cpu.idle_perc [5m over 1h] offset ' + data_start_time.isoformat() + '.000Z)',
        'avg(avg(cpu.idle_perc [5m over 1h] offset ' + data_start_time.isoformat() + '.000Z))',
        'rate(cpu.idle_perc [5m over 1h] offset ' + data_start_time.isoformat() + '.000Z)',
        'avg(rate(cpu.idle_perc [5m over 1h] offset ' + data_start_time.isoformat() + '.000Z))',
        'rate(avg(rate(cpu.idle_perc [5m over 1h] offset ' + data_start_time.isoformat() + '.000Z)))',
        'rate(1)',

        # arith expressions
        '1 + 1',
        'avg(1) + min(1)',
        'cpu.idle_perc [5m] offset ' + data_start_time.isoformat() + '.000Z + ' + \
            'cpu.idle_perc [5m] offset ' + data_start_time.isoformat() + '.000Z',
        'cpu.idle_perc [5m] offset ' + data_start_time.isoformat() + '.000Z * 2 ',
        # 'cpu.idle_perc [5m] offset ' + data_start_time.isoformat() + '.000Z + ' + \
        #     'cpu.idle_perc [5m] offset ' + (data_start_time + datetime.timedelta(minutes=5)).isoformat() + '.000Z',
        'cpu.idle_perc [5m over 15m] offset ' + data_start_time.isoformat() + '.000Z',
        'cpu.idle_perc [5m over 15m] offset ' + data_start_time.isoformat() + '.000Z + ' + \
            'cpu.idle_perc [5m over 15m] offset ' + data_start_time.isoformat() + '.000Z',
        'avg(cpu.idle_perc [5m over 15m] offset ' + data_start_time.isoformat() + '.000Z)',
        'avg(cpu.idle_perc [5m over 15m] offset ' + data_start_time.isoformat() + '.000Z) + ' + \
            'avg(cpu.idle_perc [5m over 15m] offset ' + data_start_time.isoformat() + '.000Z)',

        # boolean expressions
        '1 < 2',
        '2 < 1',
        'cpu.idle_perc [5m] offset ' + data_start_time.isoformat() + '.000Z',
        'cpu.idle_perc [5m] offset ' + data_start_time.isoformat() + '.000Z >= 93.3 ',
        'cpu.idle_perc [5m over 15m] offset ' + data_start_time.isoformat() + '.000Z',
        'cpu.idle_perc [5m over 15m] offset ' + data_start_time.isoformat() + '.000Z > 93.3',
        'cpu.idle_perc [5m] offset ' + data_start_time.isoformat() + '.000Z >= '
            'cpu.idle_perc [5m] offset ' + data_start_time.isoformat() + '.000Z',
        'cpu.idle_perc [5m] offset ' + data_start_time.isoformat() + '.000Z < 94.0',
        'cpu.idle_perc [5m] offset ' + data_start_time.isoformat() + '.000Z >= 93.3 and '
             'cpu.idle_perc [5m] offset ' + data_start_time.isoformat() + '.000Z < 94.0',
        'any(cpu.idle_perc [5m] offset ' + data_start_time.isoformat() + '.000Z < 94.0)',
        'all(cpu.idle_perc [5m] offset ' + data_start_time.isoformat() + '.000Z < 94.0)',
    ]

    # print("Live data tests")
    # for expr in eval_expr_list:
    #     print
    #     print(expr)
    #     result = MQLParser(expr).parse()
    #     print(result)
    #     print(result[0].evaluate())


if __name__ == "__main__":
    sys.exit(main())
