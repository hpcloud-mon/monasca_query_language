import numpy


class EvalException(Exception):
    pass


def create_rec_array(rows):
    return numpy.recarray((int(rows)), dtype=[('f0', numpy.uint64), ('f1', numpy.float64)])


def create_bool_rec_array(rows):
    return numpy.recarray((int(rows)), dtype=[('f0', numpy.uint64), ('f1', numpy.bool_)])


def validate_timestamp_matching(left, right):
    diff = left - right
    abs_diff = numpy.absolute(diff)
    bool_diff = abs_diff > 60000
    if numpy.any(bool_diff):
        raise Exception('Timestamp mismatch is too large')


def validate_matching_list_sizes(left, right):
    if len(left) != len(right):
        raise Exception('Inputs differ in size')


def reduce_definitions(left, right):
    result_name = None
    if left[0] == right[0]:
        result_name = left[0]
    reduced_dimensions = {}
    shared_keys = set(left[1].keys()).intersection(right[1].keys())
    for key in shared_keys:
        if left[1][key] == right[1][key]:
            reduced_dimensions[key] = left[1][key]

    return tuple((result_name, reduced_dimensions))


def get_result_array(timestamps, values):
    result = create_rec_array(len(timestamps))
    result.f0 = timestamps
    result.f1 = values
    return result


def get_boolean_result_array(timestamps, values):
    result = create_bool_rec_array(len(timestamps))
    result.f0 = timestamps
    result.f1 = values
    return result


def apply_function_to_scalar(scalar, function, extra_args=None):
    return scalar
