import numpy

import utils


class VectorRange(object):
    supported_functions = {'avg', 'min', 'max', 'count', 'sum', 'rate'}

    def __init__(self, data):
        self.data = data

    def _basic_math(self, operation, other):
        if isinstance(other, VectorRange):
            if len(self.data) != len(other.data):
                raise Exception('Cannot add uneven Vectors')
            new_data = []
            for i in range(len(self.data)):
                if operation == 'add':
                    new_data.append(self.data[i] + other.data[i])
                elif operation == 'sub':
                    new_data.append(self.data[i] - other.data[i])
                elif operation == 'mul':
                    new_data.append(self.data[i] * other.data[i])
                elif operation == 'div':
                    new_data.append(self.data[i] / other.data[i])
            return VectorRange(new_data)
        elif isinstance(other, (int, float)):
            new_data = []
            for data in self.data:
                if operation == 'add':
                    new_data.append(data + other)
                elif operation == 'sub':
                    new_data.append(data - other)
                elif operation == 'mul':
                    new_data.append(data * other)
                elif operation == 'div':
                    new_data.append(data / other)
            return VectorRange(new_data)
        else:
            raise Exception('Not Implemented')

    def __add__(self, other):
        return self._basic_math('add', other)

    def __radd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        return self._basic_math('sub', other)

    def __mul__(self, other):
        return self._basic_math('mul', other)

    def __rmul__(self, other):
        return self.__mul__(other)

    def __div__(self, other):
        return self._basic_math('div', other)

    def _basic_comparison(self, operation, other):
        if isinstance(other, VectorRange):
            if len(self.data) != len(other.data):
                raise Exception('Cannot compare uneven Vectors')
            new_data = []
            for i in range(len(self.data)):
                if operation == 'gte':
                    new_data.append(self.data[i] >= other.data[i])
                elif operation == 'gt':
                    new_data.append(self.data[i] > other.data[i])
                elif operation == 'lte':
                    new_data.append(self.data[i] <= other.data[i])
                elif operation == 'lt':
                    new_data.append(self.data[i] < other.data[i])
            return BooleanVectorRange(new_data)
        elif isinstance(other, (int, float)):
            new_data = []
            for data in self.data:
                if operation == 'gte':
                    new_data.append(data >= other)
                elif operation == 'gt':
                    new_data.append(data > other)
                elif operation == 'lte':
                    new_data.append(data <= other)
                elif operation == 'lt':
                    new_data.append(data < other)
            return BooleanVectorRange(new_data)
        else:
            raise Exception('Not Implemented')

    def __ge__(self, other):
        return self._basic_comparison('gte', other)

    def __gt__(self, other):
        return self._basic_comparison('gt', other)

    def __le__(self, other):
        return self._basic_comparison('lte', other)

    def __lt__(self, other):
        return self._basic_comparison('lt', other)

    def apply_function(self, function, extra_args=None):
        new_data = []
        for data in self.data:
            if not isinstance(data, (int, float)):
                new_data.append(data.apply_function(function, extra_args))
            else:
                new_data.append(utils.apply_function_to_scalar(data, function, extra_args))
        return VectorRange(new_data)

    def __repr__(self):
        return '\n'.join([str(data) for data in self.data])


class BooleanVectorRange(object):
    def __init__(self, data):
        self.data = data

    def __and__(self, other):
        if isinstance(other, BooleanVectorRange):
            if len(self.data) != len(other.data):
                raise Exception('Cannot combine uneven Vectors')
            new_data = []
            for i in range(len(self.data)):
                new_data.append(self.data[i] & other.data[i])
            return BooleanVectorRange(new_data)
        else:
            raise Exception('Not Implemented')

    def __or__(self, other):
        if isinstance(other, BooleanVectorRange):
            if len(self.data) != len(other.data):
                raise Exception('Cannot combine uneven Vectors')
            new_data = []
            for i in range(len(self.data)):
                new_data.append(self.data[i] | other.data[i])
            return BooleanVectorRange(new_data)
        else:
            raise Exception('Not Implemented')

    def __repr__(self):
        return '\n'.join([str(data) for data in self.data])


class BinnedRange(object):
    supported_functions = {'avg', 'max', 'min', 'count', 'sum', 'rate'}

    def __init__(self, definition, bins, data):
        self.definition = definition
        self.bins = bins
        self.data = data

    def _basic_math(self, operation, other):
        if isinstance(other, BinnedRange):
            if len(self.data) != len(other.data):
                raise Exception('Cannot add uneven BinnedRanges')
            utils.validate_timestamp_matching(self.bins, other.bins)
            new_data = []
            for i in range(len(self.data)):
                result_data = utils.create_rec_array(len(self.data[i].f0))
                try:
                    result_data.f0 = (self.data[i].f0 + other.data[i].f0) / 2
                    if operation == 'add':
                        result_data.f1 = self.data[i].f1 + other.data[i].f1
                    elif operation == 'sub':
                        result_data.f1 = self.data[i].f1 - other.data[i].f1
                    elif operation == 'mul':
                        result_data.f1 = self.data[i].f1 * other.data[i].f1
                    elif operation == 'div':
                        result_data.f1 = self.data[i].f1 / other.data[i].f1
                    new_data.append(result_data)
                except ValueError:
                    raise Exception('Cannot add mismatched bins')
            new_definition = utils.reduce_definitions(self.definition, other.definition)
            new_bins = (self.bins + other.bins) / 2

            return BinnedRange(new_definition, new_bins, new_data)
        elif isinstance(other, (int, float)):
            new_data = []
            for data in self.data:
                result_data = utils.create_rec_array(len(self.data.f0))
                result_data.f0 = data.f0
                if operation == 'add':
                    result_data.f1 = data.f1 + other
                elif operation == 'sub':
                    result_data.f1 = data.f1 - other
                elif operation == 'mul':
                    result_data.f1 = data.f1 * other
                elif operation == 'div':
                    result_data.f1 = data.f1 / other
                new_data.append(result_data)
            return BinnedRange(self.definition, self.bins, new_data)
        else:
            raise Exception('Not Implemented')

    def __add__(self, other):
        return self._basic_math('add', other)

    def __radd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        return self._basic_math('sub', other)

    def __mul__(self, other):
        return self._basic_math('mul', other)

    def __rmul__(self, other):
        return self.__mul__(other)

    def __div__(self, other):
        return self._basic_math('div', other)

    def _basic_comparison(self, operation, other):
        if isinstance(other, BinnedRange):
            if len(self.data) != len(other.data):
                raise Exception('Cannot compare uneven BinnedRanges')
            utils.validate_timestamp_matching(self.bins, other.bins)
            new_data = []
            for i in range(len(self.data)):
                result_data = utils.create_bool_rec_array(len(self.data[i].f0))
                try:
                    result_data.f0 = self.data[i].f0
                    if operation == 'gte':
                        result_data.f1 = self.data[i].f1 >= other.data[i].f1
                    elif operation == 'gt':
                        result_data.f1 = self.data[i].f1 > other.data[i].f1
                    elif operation == 'lte':
                        result_data.f1 = self.data[i].f1 <= other.data[i].f1
                    elif operation == 'lt':
                        result_data.f1 = self.data[i].f1 < other.data[i].f1
                    new_data.append(result_data)
                except ValueError:
                    raise Exception('Cannot compare mismatched bins')
            return BooleanBinnedRange(self.definition, self.bins, new_data)
        elif isinstance(other, (int, float)):
            new_data = []
            for data in self.data:
                result_data = utils.create_bool_rec_array(len(data.f0))
                result_data.f0 = data.f0
                if operation == 'gte':
                    result_data.f1 = data.f1 >= other
                elif operation == 'gt':
                    result_data.f1 = data.f1 > other
                elif operation == 'lte':
                    result_data.f1 = data.f1 <= other
                elif operation == 'lt':
                    result_data.f1 = data.f1 < other
                new_data.append(result_data)
            return BooleanBinnedRange(self.definition, self.bins, new_data)
        else:
            raise Exception('Not Implemented')

    def __ge__(self, other):
        return self._basic_comparison('gte', other)

    def __gt__(self, other):
        return self._basic_comparison('gt', other)

    def __le__(self, other):
        return self._basic_comparison('lte', other)

    def __lt__(self, other):
        return self._basic_comparison('lt', other)

    def apply_function(self, function, extra_args=None):
        if function not in self.supported_functions:
            raise Exception('Unsupported input type grouped Range for function {}'.format(function))

        if function == 'avg':
            print(type(self.bins))
            data_result = []
            for data in self.data:
                data_result.append(numpy.mean(data.f1))
            result = utils.get_result_array(self.bins, data_result)
            return Range(self.definition, result)

        if function == 'max':
            data_result = []
            for data in self.data:
                data_result.append(numpy.amax(data.f1))
            result = utils.get_result_array(self.bins, data_result)
            return Range(self.definition, result)

        if function == 'min':
            data_result = []
            for data in self.data:
                data_result.append(numpy.amin(data.f1))
            result = utils.get_result_array(self.bins, data_result)
            return Range(self.definition, result)

        if function == 'count':
            data_result = []
            for data in self.data:
                data_result.append(len(data.f1))
            result = utils.get_result_array(self.bins, data_result)
            return Range(self.definition, result)

        if function == 'sum':
            data_result = []
            for data in self.data:
                data_result.append(numpy.sum(data.f1))
            result = utils.get_result_array(self.bins, data_result)
            return Range(self.definition, result)

        if function == 'rate':
            result = []
            for i in range(len(self.data)):
                data = self.data[i]
                new_times = data.f0[:-1]
                # if new_times is only one point, it will not be an array
                # if not isinstance(new_times)
                new_data = numpy.diff(data) / numpy.diff(data)
                # discard empty bins
                if len(new_data) > 0:
                    result.append(utils.get_result_array(new_times, new_data))
                else:
                    del self.bins[i]
            return BinnedRange(self.definition, self.bins, result)

    def __repr__(self):
        output = [self.data[i].tolist() for i in range(len(self.data)) if not isinstance(self.data[i], list)]
        return str(self.definition) + '\n' + '\n'.join(str(bin) for bin in output)

    def __str__(self):
        return self.__repr__()


class BooleanBinnedRange(object):
    def __init__(self, definition, bins, data):
        self.definition = definition
        self.bins = bins
        self.data = data

    def __and__(self, other):
        if isinstance(other, BooleanBinnedRange):
            if len(self.data) != len(other.data):
                raise Exception('Cannot compare uneven BinnedRanges')
            utils.validate_timestamp_matching(self.bins, other.bins)
            new_data = []
            for i in range(len(self.data)):
                result_data = utils.create_bool_rec_array(len(self.data[i].f0))
                try:
                    result_data.f0 = self.data[i].f0
                    result_data.f1 = numpy.logical_and(self.data[i].f1,  other.data[i].f1)
                    new_data.append(result_data)
                except ValueError:
                    raise Exception('Cannot compare mismatched bins')
            return BooleanBinnedRange(self.definition, self.bins, new_data)
        else:
            raise Exception('Not Implemented')

    def __or__(self, other):
        if isinstance(other, BooleanBinnedRange):
            if len(self.data) != len(other.data):
                raise Exception('Cannot compare uneven BinnedRanges')
            utils.validate_timestamp_matching(self.bins, other.bins)
            new_data = []
            for i in range(len(self.data)):
                result_data = utils.create_bool_rec_array(len(self.data[i].f0))
                try:
                    result_data.f0 = self.data[i].f0
                    result_data.f1 = numpy.logical_or(self.data[i].f1,  other.data[i].f1)
                    new_data.append(result_data)
                except ValueError:
                    raise Exception('Cannot compare mismatched bins')
            return BooleanBinnedRange(self.definition, self.bins, new_data)
        else:
            raise Exception('Not Implemented')

    def __repr__(self):
        output = [self.data[i].tolist() for i in range(len(self.data)) if not isinstance(self.data[i], list)]
        return str(self.definition) + '\n' + '\n'.join(str(bin) for bin in output)


class Range(object):
    supported_functions = {'avg', 'max', 'min', 'count', 'sum', 'rate'}

    def __init__(self, definition, data):
        self.definition = definition
        self.data = data

    def _basic_stat_function(self, function):
        available_functions = {'avg': numpy.mean,
                               'max': numpy.amax,
                               'min': numpy.amin,
                               'count': len,
                               'sum': numpy.sum}
        s_result = available_functions[function](self.data.f1)
        t_result = numpy.max(self.data.f0)
        range_result = numpy.rec.array([(t_result, s_result)])
        return Range(self.definition, range_result)

    def _basic_math(self, operation, other):
        if isinstance(other, Range):
            utils.validate_timestamp_matching(self.data.f0, other.data.f0)
            new_data = utils.create_rec_array(len(self.data.f0))
            try:
                new_data.f0 = (self.data.f0 + other.data.f0) / 2
                if operation == 'add':
                    new_data.f1 = self.data.f1 + other.data.f1
                elif operation == 'sub':
                    new_data.f1 = self.data.f1 - other.data.f1
                elif operation == 'mul':
                    new_data.f1 = self.data.f1 * other.data.f1
                elif operation == 'div':
                    new_data.f1 = self.data.f1 / other.data.f1
            except ValueError:
                raise Exception('Cannot add uneven ranges')
            new_definition = utils.reduce_definitions(self.definition, other.definition)
            return Range(new_definition, new_data)

        elif isinstance(other, (int, float)):
            new_data = utils.create_rec_array(len(self.data.f0))
            new_data.f0 = self.data.f0
            if operation == 'add':
                new_data.f1 = self.data.f1 + other
            elif operation == 'sub':
                new_data.f1 = self.data.f1 - other
            elif operation == 'mul':
                new_data.f1 = self.data.f1 * other
            elif operation == 'div':
                new_data.f1 = self.data.f1 / other
            return Range(self.definition, new_data)

        else:
            raise Exception('Not Implemented')

    def __add__(self, other):
        return self._basic_math('add', other)

    def __radd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        return self._basic_math('sub', other)

    def __mul__(self, other):
        return self._basic_math('mul', other)

    def __rmul__(self, other):
        return self.__mul__(other)

    def __div__(self, other):
        return self._basic_math('div', other)

    def _basic_comparison(self, operation, other):
        if isinstance(other, Range):
            utils.validate_timestamp_matching(self.data.f0, other.data.f0)
            new_data = utils.create_bool_rec_array(len(self.data.f0))
            try:
                new_data.f0 = self.data.f0
                if operation == 'gte':
                    new_data.f1 = self.data.f1 >= other.data.f1
                elif operation == 'gt':
                    new_data.f1 = self.data.f1 > other.data.f1
                elif operation == 'lte':
                    new_data.f1 = self.data.f1 <= other.data.f1
                elif operation == 'lt':
                    new_data.f1 = self.data.f1 < other.data.f1
            except ValueError:
                raise Exception('Cannot compare uneven ranges')
            return BooleanRange(self.definition, new_data)
        elif isinstance(other, (int, float)):
            new_data = utils.create_bool_rec_array(len(self.data.f0))
            new_data.f0 = self.data.f0
            if operation == 'gte':
                new_data.f1 = self.data.f1 >= other
            elif operation == 'gt':
                new_data.f1 = self.data.f1 > other
            elif operation == 'lte':
                new_data.f1 = self.data.f1 <= other
            elif operation == 'lt':
                new_data.f1 = self.data.f1 < other
            return BooleanRange(self.definition, new_data)
        else:
            raise Exception('Not Implemented')

    def __ge__(self, other):
        return self._basic_comparison('gte', other)

    def __gt__(self, other):
        return self._basic_comparison('gt', other)

    def __le__(self, other):
        return self._basic_comparison('lte', other)

    def __lt__(self, other):
        return self._basic_comparison('lt', other)

    def apply_function(self, function, extra_args=None):
        if function not in self.supported_functions:
            raise Exception('Unsupported input type Range for function {}'.format(function))

        if function == 'avg':
            data_result = numpy.mean(self.data.f1)
            result = utils.get_result_array(self.data.f0[:1], data_result)
            return Range(self.definition, result)

        if function == 'max':
            data_result = numpy.amax(self.data.f1)
            result = utils.get_result_array(self.data.f0[:1], data_result)
            return Range(self.definition, result)

        if function == 'min':
            data_result = numpy.amin(self.data.f1)
            result = utils.get_result_array(self.data.f0[:1], data_result)
            return Range(self.definition, result)

        if function == 'count':
            data_result = len(self.data.f1)
            result = utils.get_result_array(self.data.f0[:1], data_result)
            return Range(self.definition, result)

        if function == 'sum':
            data_result = numpy.sum(self.data.f1)
            result = utils.get_result_array(self.data.f0[:1], data_result)
            return Range(self.definition, result)

        if function == 'rate':
            new_time = self.data.f0[:-1]
            new_data = numpy.diff(self.data.f1) / numpy.diff(self.data.f0)
            result = utils.get_result_array(new_time, new_data)
            return Range(self.definition, result)

    def __repr__(self):
        return str(self.definition) + '\n' + str(self.data.tolist())

    def __str__(self):
        return self.__repr__()


class BooleanRange(object):
    def __init__(self, definition, data):
        self.definition = definition
        self.data = data

    def __and__(self, other):
        if isinstance(other, BooleanRange):
            utils.validate_timestamp_matching(self.data.f0, other.data.f0)
            new_data = utils.create_bool_rec_array(len(self.data.f0))
            try:
                new_data.f0 = self.data.f0
                new_data.f1 = numpy.logical_and(self.data.f1, other.data.f1)
            except ValueError:
                raise Exception('Cannot combine uneven ranges')
            return BooleanRange(self.definition, new_data)
        else:
            raise Exception('Not Implemented')

    def __or__(self, other):
        if isinstance(other, BooleanRange):
            utils.validate_timestamp_matching(self.data.f0, other.data.f0)
            new_data = utils.create_bool_rec_array(len(self.data.f0))
            try:
                new_data.f0 = self.data.f0
                new_data.f1 = numpy.logical_or(self.data.f1, other.data.f1)
            except ValueError:
                raise Exception('Cannot combine uneven ranges')
            return BooleanRange(self.definition, new_data)
        else:
            raise Exception('Not Implemented')

    def __repr__(self):
        return str(self.definition) + '\n' + str(self.data.tolist())
