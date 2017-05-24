import datetime
import sys
import time

import pyparsing

from query_structures import (Dimension,
                              # RangeSelector,
                              # OffsetSelector,
                              MetricSelector,
                              # FuncStmt,
                              # Expression,
                              # BooleanExpression,
                              LogicalExpression,
                              )

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
metric.addParseAction(MetricSelector)

logical_and = pyparsing.oneOf("and &&", caseless=True)
logical_or = pyparsing.oneOf("or ||", caseless=True)

logical_expression = pyparsing.infixNotation(metric,
                                             [(logical_and, 2, pyparsing.opAssoc.LEFT, LogicalExpression),
                                              (logical_or, 2, pyparsing.opAssoc.LEFT, LogicalExpression)])

grammar = logical_expression


class MQLParser(object):
    def __init__(self, expr):
        self._expr = expr

    def parse(self):
        parse_result = grammar.parseString(self._expr, parseAll=True)
        return parse_result


def main():

    expression_list = [
        "metric_name",
        "metric_name{}",
        "metric_name{test_key=test_value,key!=value}",
        "metric_one and metric_two",
        "metric_one{one=two} or metric_two{three!=four}",
    ]

    negative_expression_list = [
    ]

    start_time = time.time()

    for expr in expression_list:
        print(expr)
        result = MQLParser(expr).parse()
        # uncomment below to show details of parsing
        print(result)
        print("Accepted")
        print(result[0].to_dict())
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


if __name__ == "__main__":
    sys.exit(main())

