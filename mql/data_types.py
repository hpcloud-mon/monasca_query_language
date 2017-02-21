import numpy

import utils


class VectorRange(object):
    def __init__(self, data):
        self.data = data

    def __add__(self, other):
        if isinstance(other, VectorRange):
            if len(self.data) != len(other.data):
                raise Exception('Cannot add uneven Vectors')
            new_data = []
            for i in range(len(self.data)):
                new_data.append(self.data[i] + other.data[i])
            return VectorRange(new_data)
        elif isinstance(other, (int, float)):
            new_data = []
            for data in self.data:
                new_data.append(data + other)
            return VectorRange(new_data)
        else:
            raise Exception('Not Implemented')

    def __radd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        if isinstance(other, VectorRange):
            if len(self.data) != len(other.data):
                raise Exception('Cannot subtract uneven Vectors')
            new_data = []
            for i in range(len(self.data)):
                new_data.append(self.data[i] - other.data[i])
            return VectorRange(new_data)
        elif isinstance(other, (int, float)):
            new_data = []
            for data in self.data:
                new_data.append(data - other)
            return VectorRange(new_data)
        else:
            raise Exception('Not Implemented')

    def __mul__(self, other):
        if isinstance(other, VectorRange):
            if len(self.data) != len(other.data):
                raise Exception('Cannot multiply uneven Vectors')
            new_data = []
            for i in range(len(self.data)):
                new_data.append(self.data[i] * other.data[i])
            return VectorRange(new_data)
        elif isinstance(other, (int, float)):
            new_data = []
            for data in self.data:
                new_data.append(data * other)
            return VectorRange(new_data)
        else:
            raise Exception('Not Implemented')

    def __rmul__(self, other):
        return self.__mul__(other)

    def __div__(self, other):
        if isinstance(other, VectorRange):
            if len(self.data) != len(other.data):
                raise Exception('Cannot divide uneven Vectors')
            new_data = []
            for i in range(len(self.data)):
                new_data.append(self.data[i] / other.data[i])
            return VectorRange(new_data)
        elif isinstance(other, (int, float)):
            new_data = []
            for data in self.data:
                new_data.append(data / other)
            return VectorRange(new_data)
        else:
            raise Exception('Not Implemented')

    def __ge__(self, other):
        if isinstance(other, VectorRange):
            if len(self.data) != len(other.data):
                raise Exception('Cannot compare uneven Vectors')
            new_data = []
            for i in range(len(self.data)):
                new_data.append(self.data[i] >= other.data[i])
            return BooleanVectorRange(new_data)
        elif isinstance(other, (int, float)):
            new_data = []
            for data in self.data:
                new_data.append(data >= other)
            return BooleanVectorRange(new_data)
        else:
            raise Exception('Not Implemented')

    def __gt__(self, other):
        if isinstance(other, VectorRange):
            if len(self.data) != len(other.data):
                raise Exception('Cannot compare uneven Vectors')
            new_data = []
            for i in range(len(self.data)):
                new_data.append(self.data[i] > other.data[i])
            return BooleanVectorRange(new_data)
        elif isinstance(other, (int, float)):
            new_data = []
            for data in self.data:
                new_data.append(data > other)
            return BooleanVectorRange(new_data)
        else:
            raise Exception('Not Implemented')

    def __le__(self, other):
        if isinstance(other, VectorRange):
            if len(self.data) != len(other.data):
                raise Exception('Cannot compare uneven Vectors')
            new_data = []
            for i in range(len(self.data)):
                new_data.append(self.data[i] <= other.data[i])
            return BooleanVectorRange(new_data)
        elif isinstance(other, (int, float)):
            new_data = []
            for data in self.data:
                new_data.append(data <= other)
            return BooleanVectorRange(new_data)
        else:
            raise Exception('Not Implemented')

    def __lt__(self, other):
        if isinstance(other, VectorRange):
            if len(self.data) != len(other.data):
                raise Exception('Cannot compare uneven Vectors')
            new_data = []
            for i in range(len(self.data)):
                new_data.append(self.data[i] < other.data[i])
            return BooleanVectorRange(new_data)
        elif isinstance(other, (int, float)):
            new_data = []
            for data in self.data:
                new_data.append(data < other)
            return BooleanVectorRange(new_data)
        else:
            raise Exception('Not Implemented')

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
    def __init__(self, definition, bins, data):
        self.definition = definition
        self.bins = bins
        self.data = data

    def __add__(self, other):
        if isinstance(other, BinnedRange):
            if len(self.data) != len(other.data):
                raise Exception('Cannot add uneven BinnedRanges')
            utils.validate_timestamp_matching(self.bins, other.bins)
            new_data = []
            for i in range(len(self.data)):
                result_data = utils.create_rec_array(len(self.data[i].f0))
                try:
                    result_data.f0 = (self.data[i].f0 + other.data[i].f0) / 2
                    result_data.f1 = self.data[i].f1 + other.data[i].f1
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
                result_data.f1 = data.f1 + other
                new_data.append(result_data)
            return BinnedRange(self.definition, self.bins, new_data)
        else:
            raise Exception('Not Implemented')

    def __radd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        if isinstance(other, BinnedRange):
            if len(self.data) != len(other.data):
                raise Exception('Cannot subtract uneven BinnedRanges')
            utils.validate_timestamp_matching(self.bins, other.bins)
            new_data = []
            for i in range(len(self.data)):
                result_data = utils.create_rec_array(len(self.data[i].f0))
                try:
                    result_data.f0 = (self.data[i].f0 + other.data[i].f0) / 2
                    result_data.f1 = self.data[i].f1 - other.data[i].f1
                    new_data.append(result_data)
                except ValueError:
                    raise Exception('Cannot subtract mismatched bins')
            new_definition = utils.reduce_definitions(self.definition, other.definition)
            new_bins = (self.bins + other.bins) / 2

            return BinnedRange(new_definition, new_bins, new_data)
        elif isinstance(other, (int, float)):
            new_data = []
            for data in self.data:
                result_data = utils.create_rec_array(len(self.data.f0))
                result_data.f0 = data.f0
                result_data.f1 = data.f1 - other
                new_data.append(result_data)
            return BinnedRange(self.definition, self.bins, new_data)
        else:
            raise Exception('Not Implemented')

    def __mul__(self, other):
        if isinstance(other, BinnedRange):
            if len(self.data) != len(other.data):
                raise Exception('Cannot multiply uneven BinnedRanges')
            utils.validate_timestamp_matching(self.bins, other.bins)
            new_data = []
            for i in range(len(self.data)):
                result_data = utils.create_rec_array(len(self.data[i].f0))
                try:
                    result_data.f0 = (self.data[i].f0 + other.data[i].f0) / 2
                    result_data.f1 = self.data[i].f1 * other.data[i].f1
                    new_data.append(result_data)
                except ValueError:
                    raise Exception('Cannot multiply mismatched bins')
            new_definition = utils.reduce_definitions(self.definition, other.definition)
            new_bins = (self.bins + other.bins) / 2

            return BinnedRange(new_definition, new_bins, new_data)
        elif isinstance(other, (int, float)):
            new_data = []
            for data in self.data:
                result_data = utils.create_rec_array(len(self.data.f0))
                result_data.f0 = data.f0
                result_data.f1 = data.f1 * other
                new_data.append(result_data)
            return BinnedRange(self.definition, self.bins, new_data)
        else:
            raise Exception('Not Implemented')

    def __rmul__(self, other):
        return self.__mul__(other)

    def __div__(self, other):
        if isinstance(other, BinnedRange):
            if len(self.data) != len(other.data):
                raise Exception('Cannot divide uneven BinnedRanges')
            utils.validate_timestamp_matching(self.bins, other.bins)
            new_data = []
            for i in range(len(self.data)):
                result_data = utils.create_rec_array(len(self.data[i].f0))
                try:
                    result_data.f0 = (self.data[i].f0 + other.data[i].f0) / 2
                    result_data.f1 = self.data[i].f1 / other.data[i].f1
                    new_data.append(result_data)
                except ValueError:
                    raise Exception('Cannot divide mismatched bins')
            new_definition = utils.reduce_definitions(self.definition, other.definition)
            new_bins = (self.bins + other.bins) / 2

            return BinnedRange(new_definition, new_bins, new_data)
        elif isinstance(other, (int, float)):
            new_data = []
            for data in self.data:
                result_data = utils.create_rec_array(len(self.data.f0))
                result_data.f0 = data.f0
                result_data.f1 = data.f1 / other
                new_data.append(result_data)
            return BinnedRange(self.definition, self.bins, new_data)
        else:
            raise Exception('Not Implemented')

    def __ge__(self, other):
        if isinstance(other, BinnedRange):
            if len(self.data) != len(other.data):
                raise Exception('Cannot compare uneven BinnedRanges')
            utils.validate_timestamp_matching(self.bins, other.bins)
            new_data = []
            for i in range(len(self.data)):
                result_data = utils.create_bool_rec_array(len(self.data[i].f0))
                try:
                    result_data.f0 = self.data[i].f0
                    result_data.f1 = self.data[i].f1 >= other.data[i].f1
                    new_data.append(result_data)
                except ValueError:
                    raise Exception('Cannot compare mismatched bins')
            return BooleanBinnedRange(self.definition, self.bins, new_data)
        elif isinstance(other, (int, float)):
            new_data = []
            for data in self.data:
                result_data = utils.create_bool_rec_array(len(data.f0))
                result_data.f0 = data.f0
                result_data.f1 = data.f1 >= other
                new_data.append(result_data)
            return BooleanBinnedRange(self.definition, self.bins, new_data)
        else:
            raise Exception('Not Implemented')

    def __gt__(self, other):
        if isinstance(other, BinnedRange):
            if len(self.data) != len(other.data):
                raise Exception('Cannot compare uneven BinnedRanges')
            utils.validate_timestamp_matching(self.bins, other.bins)
            new_data = []
            for i in range(len(self.data)):
                result_data = utils.create_bool_rec_array(len(self.data[i].f0))
                try:
                    result_data.f0 = self.data[i].f0
                    result_data.f1 = self.data[i].f1 > other.data[i].f1
                    new_data.append(result_data)
                except ValueError:
                    raise Exception('Cannot compare mismatched bins')
            return BooleanBinnedRange(self.definition, self.bins, new_data)
        elif isinstance(other, (int, float)):
            new_data = []
            for data in self.data:
                result_data = utils.create_bool_rec_array(len(data.f0))
                result_data.f0 = data.f0
                result_data.f1 = data.f1 > other
                new_data.append(result_data)
            return BooleanBinnedRange(self.definition, self.bins, new_data)
        else:
            raise Exception('Not Implemented')

    def __le__(self, other):
        if isinstance(other, BinnedRange):
            if len(self.data) != len(other.data):
                raise Exception('Cannot compare uneven BinnedRanges')
            utils.validate_timestamp_matching(self.bins, other.bins)
            new_data = []
            for i in range(len(self.data)):
                result_data = utils.create_bool_rec_array(len(self.data[i].f0))
                try:
                    result_data.f0 = self.data[i].f0
                    result_data.f1 = self.data[i].f1 <= other.data[i].f1
                    new_data.append(result_data)
                except ValueError:
                    raise Exception('Cannot compare mismatched bins')
            return BooleanBinnedRange(self.definition, self.bins, new_data)
        elif isinstance(other, (int, float)):
            new_data = []
            for data in self.data:
                result_data = utils.create_bool_rec_array(len(data.f0))
                result_data.f0 = data.f0
                result_data.f1 = data.f1 <= other
                new_data.append(result_data)
            return BooleanBinnedRange(self.definition, self.bins, new_data)
        else:
            raise Exception('Not Implemented')

    def __lt__(self, other):
        if isinstance(other, BinnedRange):
            if len(self.data) != len(other.data):
                raise Exception('Cannot compare uneven BinnedRanges')
            utils.validate_timestamp_matching(self.bins, other.bins)
            new_data = []
            for i in range(len(self.data)):
                result_data = utils.create_bool_rec_array(len(self.data[i].f0))
                try:
                    result_data.f0 = self.data[i].f0
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
                result_data.f1 = data.f1 < other
                new_data.append(result_data)
            return BooleanBinnedRange(self.definition, self.bins, new_data)
        else:
            raise Exception('Not Implemented')

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
    def __init__(self, definition, data):
        self.definition = definition
        self.data = data

    def __add__(self, other):
        if isinstance(other, Range):
            utils.validate_timestamp_matching(self.data.f0, other.data.f0)
            new_data = utils.create_rec_array(len(self.data.f0))
            try:
                new_data.f0 = (self.data.f0 + other.data.f0) / 2
                new_data.f1 = self.data.f1 + other.data.f1
            except ValueError:
                raise Exception('Cannot add uneven ranges')
            new_definition = utils.reduce_definitions(self.definition, other.definition)

            return Range(new_definition, new_data)
        elif isinstance(other, (int, float)):
            new_data = utils.create_rec_array(len(self.data.f0))
            new_data.f0 = self.data.f0
            new_data.f1 = self.data.f1 + other
            return Range(self.definition, new_data)
        else:
            raise Exception('Not Implemented')

    def __radd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        if isinstance(other, Range):
            utils.validate_timestamp_matching(self.data.f0, other.data.f0)
            new_data = utils.create_rec_array(len(self.data.f0))
            try:
                new_data.f0 = (self.data.f0 + other.data.f0) / 2
                new_data.f1 = self.data.f1 - other.data.f1
            except ValueError:
                raise Exception('Cannot subtract uneven ranges')
            new_definition = utils.reduce_definitions(self.definition, other.definition)

            return Range(new_definition, new_data)
        elif isinstance(other, (int, float)):
            new_data = utils.create_rec_array(len(self.data.f0))
            new_data.f0 = self.data.f0
            new_data.f1 = self.data.f1 - other
            return Range(self.definition, new_data)
        else:
            raise Exception('Not Implemented')

    def __mul__(self, other):
        if isinstance(other, Range):
            utils.validate_timestamp_matching(self.data.f0, other.data.f0)
            new_data = utils.create_rec_array(len(self.data.f0))
            try:
                new_data.f0 = (self.data.f0 + other.data.f0) / 2
                new_data.f1 = self.data.f1 * other.data.f1
            except ValueError:
                raise Exception('Cannot multiply uneven ranges')
            new_definition = utils.reduce_definitions(self.definition, other.definition)

            return Range(new_definition, new_data)
        elif isinstance(other, (int, float)):
            new_data = utils.create_rec_array(len(self.data.f0))
            new_data.f0 = self.data.f0
            new_data.f1 = self.data.f1 * other
            return Range(self.definition, new_data)
        else:
            raise Exception('Not Implemented')

    def __rmul__(self, other):
        return self.__mul__(other)

    def __div__(self, other):
        if isinstance(other, Range):
            utils.validate_timestamp_matching(self.data.f0, other.data.f0)
            new_data = utils.create_rec_array(len(self.data.f0))
            try:
                new_data.f0 = (self.data.f0 + other.data.f0) / 2
                new_data.f1 = self.data.f1 / other.data.f1
            except ValueError:
                raise Exception('Cannot divide uneven ranges')
            new_definition = utils.reduce_definitions(self.definition, other.definition)

            return Range(new_definition, new_data)
        elif isinstance(other, (int, float)):
            new_data = utils.create_rec_array(len(self.data.f0))
            new_data.f0 = self.data.f0
            new_data.f1 = self.data.f1 / other
            return Range(self.definition, new_data)
        else:
            raise Exception('Not Implemented')

    def __ge__(self, other):
        if isinstance(other, Range):
            utils.validate_timestamp_matching(self.data.f0, other.data.f0)
            new_data = utils.create_bool_rec_array(len(self.data.f0))
            try:
                new_data.f0 = self.data.f0
                new_data.f1 = self.data.f1 >= other.data.f1
            except ValueError:
                raise Exception('Cannot compare uneven ranges')
            return BooleanRange(self.definition, new_data)
        elif isinstance(other, (int, float)):
            new_data = utils.create_bool_rec_array(len(self.data.f0))
            new_data.f0 = self.data.f0
            new_data.f1 = self.data.f1 >= other
            return BooleanRange(self.definition, new_data)
        else:
            raise Exception('Not Implemented')

    def __gt__(self, other):
        if isinstance(other, Range):
            utils.validate_timestamp_matching(self.data.f0, other.data.f0)
            new_data = utils.create_bool_rec_array(len(self.data.f0))
            try:
                new_data.f0 = self.data.f0
                new_data.f1 = self.data.f1 > other.data.f1
            except ValueError:
                raise Exception('Cannot compare uneven ranges')
            return BooleanRange(self.definition, new_data)
        elif isinstance(other, (int, float)):
            new_data = utils.create_bool_rec_array(len(self.data.f0))
            new_data.f0 = self.data.f0
            new_data.f1 = self.data.f1 > other
            return BooleanRange(self.definition, new_data)
        else:
            raise Exception('Not Implemented')

    def __le__(self, other):
        if isinstance(other, Range):
            utils.validate_timestamp_matching(self.data.f0, other.data.f0)
            new_data = utils.create_bool_rec_array(len(self.data.f0))
            try:
                new_data.f0 = self.data.f0
                new_data.f1 = self.data.f1 <= other.data.f1
            except ValueError:
                raise Exception('Cannot compare uneven ranges')
            return BooleanRange(self.definition, new_data)
        elif isinstance(other, (int, float)):
            new_data = utils.create_bool_rec_array(len(self.data.f0))
            new_data.f0 = self.data.f0
            new_data.f1 = self.data.f1 <= other
            return BooleanRange(self.definition, new_data)
        else:
            raise Exception('Not Implemented')

    def __lt__(self, other):
        if isinstance(other, Range):
            utils.validate_timestamp_matching(self.data.f0, other.data.f0)
            new_data = utils.create_bool_rec_array(len(self.data.f0))
            try:
                new_data.f0 = self.data.f0
                new_data.f1 = self.data.f1 < other.data.f1
            except ValueError:
                raise Exception('Cannot compare uneven ranges')
            return BooleanRange(self.definition, new_data)
        elif isinstance(other, (int, float)):
            new_data = utils.create_bool_rec_array(len(self.data.f0))
            new_data.f0 = self.data.f0
            new_data.f1 = self.data.f1 < other
            return BooleanRange(self.definition, new_data)
        else:
            raise Exception('Not Implemented')

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
