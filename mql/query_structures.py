import datetime
import numpy

import influx_repo
from data_types import (VectorRange,
                        BinnedRange,
                        Range)
import utils


class Dimension(object):
    def __init__(self, tokens):
        self.args = tokens
        self.key = tokens[0]
        self.operator = tokens[1]
        self.value = tokens[2]

    def __repr__(self):
        return "Dimension(key={},operator='{}',value={})".format(self.key, self.operator, self.value)

    def __str__(self):
        return '{' + ''.join(str(arg) for arg in self.args) + '}'


class RangeSelector(object):
    def __init__(self, tokens):
        self.args = tokens
        self.range_value = None
        self.range_unit = None
        self.bucket_value = None
        self.bucket_unit = None

        if len(tokens) > 1:
            bucket_str = tokens[0]
            range_str = tokens[2]
        else:
            range_str = tokens[0]
            bucket_str = None

        self.range_value = int(range_str[:-1])
        self.range_unit = range_str[-1]
        if bucket_str is not None:
            self.bucket_value = int(bucket_str[:-1])
            self.bucket_unit = bucket_str[-1]

    @property
    def range_sec(self):
        return _convert_to_seconds(self.range_value, self.range_unit)

    @property
    def bucket_sec(self):
        return _convert_to_seconds(self.bucket_value, self.bucket_unit)

    def __repr__(self):
        _range = str(self.range_value) + self.range_unit
        _bucket = 'None'
        if self.bucket_value is not None:
            _bucket = str(self.bucket_value) + self.bucket_unit
        return "RangeSelector(range={},bucket={})".format(_range, _bucket)

    def __str__(self):
        return '[' + ' '.join(str(arg) for arg in self.args) + ']'


class OffsetSelector(object):
    def __init__(self, tokens):
        self.args = tokens
        self.offset = tokens[1]
        if isinstance(self.offset, datetime.datetime):
            self.normalized_offset = self.offset
        else:
            time_diff_sec = _convert_to_seconds(int(self.offset[:-1]), self.offset[-1])
            self.normalized_offset = datetime.datetime.utcnow() - datetime.timedelta(
                seconds=time_diff_sec)

    def __repr__(self):
        return "Offset({})".format(self.offset)

    def __str__(self):
        return ' '.join(str(arg) for arg in self.args)


class MetricSelector(object):
    def __init__(self, tokens):
        self.args = tokens
        self.name = None
        self.dimensions = []
        self.range_selector = None
        self.offset = None
        _dimensions = []
        for token in tokens:
            if isinstance(token, basestring):
                self.name = token
            elif isinstance(token, list):
                _dimensions = token
            elif isinstance(token, RangeSelector):
                self.range_selector = token
            elif isinstance(token, OffsetSelector):
                self.offset = token.normalized_offset
        # if there is no offset, default to now
        if self.offset is None:
            self.offset = datetime.datetime.utcnow()
        # remove __name__ from dimension, apply to self.name if not supplied
        for dim in _dimensions:
            if dim.key == '__name__':
                if self.name is None:
                    self.name = dim.value
            else:
                self.dimensions.append(dim)

    def evaluate(self, function=None):
        end_time = self.offset

        if self.range_selector is not None:
            start_time = end_time - datetime.timedelta(seconds=self.range_selector.range_sec)
            bucket_size_sec = self.range_selector.bucket_sec

            # cannot group in influx with derivative
            if function == 'derivative' and bucket_size_sec is not None:
                bucket_size_sec = None
        else:
            function = 'last_force'
            start_time = end_time - datetime.timedelta(minutes=5)
            bucket_size_sec = None

        influx_result = influx_repo.query(self.name, self.dimensions,
                                          function=function,
                                          start_time=start_time,
                                          end_time=end_time,
                                          bucket_size=bucket_size_sec,
                                          group_by=['*'])

        # if we did a derivative, do binning here
        if function == 'derivative':
            function = None
            bucket_size_sec = self.range_selector.bucket_sec

        result = []
        # Change into a binned series if necessary
        if function is None and bucket_size_sec is not None:
            unix_start = int((start_time - datetime.datetime(1970, 01, 01)).total_seconds() * 1000)
            unix_end = int((end_time - datetime.datetime(1970, 01, 01)).total_seconds() * 1000)
            bins = [i for i in range(unix_start, unix_end, bucket_size_sec * 1000)]

            # do not include start time in bin edges
            bins_inner_edges = bins[1:]
            output = [[] for _ in range(len(bins_inner_edges) + 1)]
            for range_tuple in influx_result:
                bin_indexes = numpy.digitize(range_tuple[1].f0, bins_inner_edges)

                for i in range(len(bin_indexes)):
                    output[bin_indexes[i]].append((range_tuple[1][i].f0, range_tuple[1][i].f1))
                for i in range(len(output)):
                    if output[i]:
                        output[i] = numpy.rec.array(output[i])
                result.append(BinnedRange(range_tuple[0], numpy.array(bins), output))
        else:
            for range_tuple in influx_result:
                result.append(Range(range_tuple[0], range_tuple[1]))

        return VectorRange(result)

    def __repr__(self):
        return "MetricSelector(name={},dimensions={},range={},offset={})".format(
            self.name, self.dimensions, self.range_selector, self.offset)

    # def __str__(self):
    #     return ' '.join(str(arg) for arg in self.args)


class FuncStmt(object):
    functions_for_repo = {
        'avg': 'mean',
        'max': 'max',
        'min': 'min',
        'count': 'count',
        'sum': 'sum',
        'rate': 'derivative'
    }
    functions_downsize_return_type = {
        'avg': numpy.mean,
        'max': numpy.amax,
        'min': numpy.amin,
        'count': len,
        'sum': numpy.sum,
    }
    functions_same_return_type = {
        'rate': numpy.diff
    }

    def __init__(self, tokens):
        self.args = tokens
        self.function = tokens[0]
        self.operand = tokens[1]
        # TODO add ability to specify extra arguments
        # self.extra_args = tokens[2:]

    def evaluate(self):
        if hasattr(self.operand, 'evaluate'):

            # if metric selector try to pass in function
            if isinstance(self.operand, MetricSelector):
                if self.function in self.functions_for_repo:
                    result = self.operand.evaluate(
                        self.functions_for_repo[self.function])
                    # format data if necessary
                    # bail out here, since there is no more to do
                    return result

            inner_result = self.operand.evaluate()
        else:
            inner_result = self.operand

        # if this is not a list, we shouldn't operate on it
        if not isinstance(inner_result, VectorRange):
            return inner_result

        if self.function in self.functions_downsize_return_type:
            outer_result = []
            for item in inner_result.data:
                if isinstance(item, BinnedRange):
                    s_result = []
                    t_result = []
                    for i in range(len(item.data)):
                        # drop any empty bins from the results
                        if not isinstance(item.data[i], list):
                            s_result.append(self.functions_downsize_return_type[self.function](item.data[i].f1))
                            t_result.append(item.bins[i])

                    bin_result = utils.get_result_array(t_result, s_result)

                    outer_result.append(Range(item.definition, bin_result))

                elif isinstance(item, Range):
                    s_result = self.functions_downsize_return_type[self.function](item.data.f1)
                    t_result = numpy.max(item.data.f0)
                    range_result = numpy.rec.array([(t_result, s_result)])
                    outer_result.append(Range(item.definition, range_result))

                elif isinstance(item, (int, float)):
                    outer_result.append(item)

                else:
                    raise utils.EvalException('Unknown input type {} for function {}'.format(
                        type(item), self.function))

        elif self.function in self.functions_same_return_type:
            outer_result = []
            for item in inner_result:
                if isinstance(item, BinnedRange):
                    resulting_bins = []
                    for i in range(len(item.data)):
                        # drop any empty bins from the results
                        if not isinstance(item.data[i], list):
                            s_result = self.functions_same_return_type[self.function](item.data[i].f1)
                            t_result = item.data[i].f0[:-1]
                            bin_result = utils.get_result_array(t_result, s_result)
                            resulting_bins.append(bin_result)

                    outer_result.append(BinnedRange(item.definition,
                                                    item.bins,
                                                    resulting_bins))
                elif isinstance(item, Range):
                    s_result = self.functions_same_return_type[self.function](item.data.f1)
                    t_result = item.data.f0[:-1]
                    range_result = utils.get_result_array(t_result, s_result)
                    outer_result.append(Range(item.definition, range_result))

                elif isinstance(item, (int, float)):
                    outer_result.append(item)

                else:
                    raise utils.EvalException('Unknown input type {} for function {}'.format(
                        type(item), self.function))
        else:
            raise utils.EvalException('Function not implemented')

        return outer_result

    def __repr__(self):
        return "FuncStmt(function={},operand={})".format(self.function, self.operand)

    # def __str__(self):
    #     return ' '.join(str(arg) for arg in self.args)


class Expression(object):
    def __init__(self, tokens):
        self.args = tokens[0]
        self.left_operand = self.args[0]
        self.operator = None
        self.right_operand = None
        if len(self.args) > 1:
            self.operator = self.args[1]
        if len(self.args) > 2:
            self.right_operand = self.args[2]

    def _apply_operator(self, left, right):
        if self.operator == '+':
            return left + right
        elif self.operator == '-':
            return left - right
        elif self.operator == '*':
            return left * right
        elif self.operator == '/':
            return left / right
        else:
            raise utils.EvalException('Unknown operator \'{}\''.format(self.operator))

    def evaluate(self):
        if hasattr(self.left_operand, 'evaluate'):
            left = self.left_operand.evaluate()
        else:
            left = self.left_operand

        if hasattr(self.right_operand, 'evaluate'):
            right = self.right_operand.evaluate()
        else:
            right = self.right_operand

        if left is None:
            raise Exception('Failed to evaluate ' + str(self))
        elif self.operator is None or right is None:
            outer_result = left
        else:
            outer_result = self._apply_operator(left, right)

        return outer_result

    def __repr__(self):
        return "Expression(left={},operator='{}',right={})".format(self.left_operand, self.operator, self.right_operand)

    def __str__(self):
        return ' '.join(str(arg) for arg in self.args)


class BooleanExpression(object):
    def __init__(self, tokens):
        self.args = tokens
        self.left_operand = tokens[0]
        self.operator = None
        self.right_operand = None
        if len(tokens) > 1:
            self.operator = tokens[1]
        if len(tokens) > 2:
            self.right_operand = tokens[2]

    def _apply_operator(self, left, right):
        op = self.normalized_operator
        if op == '>=':
            return left >= right
        elif op == '>':
            return left > right
        elif op == '<=':
            return left <= right
        elif op == '<':
            return left < right
        else:
            raise Exception('Unknown operator')

    @property
    def normalized_operator(self):
        norm_ops = {'gte': '>=',
                    'gt': '>',
                    'lte': '<=',
                    'lt': '<'}
        if self.operator in norm_ops:
            return norm_ops[self.operator]
        else:
            return self.operator

    def evaluate(self):
        if hasattr(self.left_operand, 'evaluate'):
            left = self.left_operand.evaluate()
        else:
            left = self.left_operand

        if hasattr(self.right_operand, 'evaluate'):
            right = self.right_operand.evaluate()
        else:
            right = self.right_operand

        if left is None:
            raise utils.EvalException('Failed to evaluate ' + str(self))
        elif self.operator is None or right is None:
            result = left
        else:
            result = self._apply_operator(left, right)

        return result

    def __repr__(self):
        return "BooleanExpression(left={},operator='{}',right={})".format(self.left_operand, self.operator, self.right_operand)

    def __str__(self):
        return self.__repr__()


class LogicalExpression(object):
    def __init__(self, tokens):
        self.args = tokens
        self.left_operand = tokens[0][0]
        self.operator = None
        self.right_operand = None
        if len(tokens[0]) > 1:
            self.operator = tokens[0][1]
        if len(tokens[0]) > 2:
            self.right_operand = tokens[0][2]

    def _apply_operator(self, left, right):
        op = self.normalized_operator
        if op == 'and':
            return left & right
        elif op == 'or':
            return left | right
        else:
            raise utils.EvalException('Unknown operator')

    def evaluate(self):
        if hasattr(self.left_operand, 'evaluate'):
            left = self.left_operand.evaluate()
        else:
            left = self.left_operand

        if hasattr(self.right_operand, 'evaluate'):
            right = self.right_operand.evaluate()
        else:
            right = self.right_operand

        if left is None:
            raise utils.EvalException('Failed to evaluate ' + str(self))
        elif self.operator is None or right is None:
            result = left
        else:
            result = self._apply_operator(left, right)

        return result

    @property
    def normalized_operator(self):
        if self.operator == '&&':
            result = 'and'
        elif self.operator == '||':
            result = 'or'
        else:
            result = self.operator
        return result

    def __repr__(self):
        return "LogicalExpression(left={},operator='{}',right={})".format(self.left_operand, self.operator, self.right_operand)

    def __str__(self):
        return self.__repr__()


def _convert_to_seconds(value, unit):
    if value is None or unit is None:
        return None
    result = value
    if unit == 's':
        return result
    result *= 60

    if unit == 'm':
        return result
    result *= 60

    if unit == 'h':
        return result
    result *= 24

    if unit == 'd':
        return result
    result *= 7

    return result
