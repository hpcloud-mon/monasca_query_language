import pyparsing


class Dimension(object):
    def __init__(self, tokens):
        self.args = tokens
        self.key = tokens[0]
        self.operator = tokens[1]
        self.value = tokens[2]

    def __repr__(self):
        return "Dimension(key={},operator='{}',value={})".format(self.key, self.operator, self.value)

    def __str__(self):
        return self.__repr__()


class MetricSelector(object):
    def __init__(self, tokens):
        self.args = tokens
        self.name = None
        self.dimensions = []
        _dimensions = []
        for token in tokens:
            if isinstance(token, basestring):
                self.name = token
            elif isinstance(token, pyparsing.ParseResults):
                _dimensions = token
        # remove __name__ from dimension, apply to self.name if not supplied
        for dim in _dimensions:
            if dim.key == '__name__':
                if self.name is None:
                    self.name = dim.value
            else:
                self.dimensions.append(dim)

    def get_filters(self):
        result = {}
        for dim in self.dimensions:
            if dim.key in result and result[key] != dim.value:
                raise Exception("Duplicate keys specified in single selector '{}' ".format(dim.key))
            result[dim.key] = dim.value
        return result

    def __repr__(self):
        return "MetricSelector(name={},dimensions={})".format(
            self.name, self.dimensions)

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

    @property
    def normalized_operator(self):
        if self.operator == '&&':
            result = 'and'
        elif self.operator == '||':
            result = 'or'
        else:
            result = self.operator
        return result

    def get_filters(self):
        left_filters = self.left_operand.get_filters()
        right_filters = self.right_operand.get_filters()
        for key, value in right_filters:
            if key in left_filters and left_filters[key] != value:
                raise Exception("Duplicate keys specified ".format(key))
            left_filters[key] = value
        return left_filters

    def __repr__(self):
        return "LogicalExpression(left={},operator='{}',right={})".format(self.left_operand, self.operator, self.right_operand)

    def __str__(self):
        return self.__repr__()


class TargetsExpression(object):
    def __init__(self, tokens):
        self.args = tokens
        self.target = tokens[1]

    def get_filters(self):
        return self.target.get_filters()

    def __repr__(self):
        return "TargetExpression(target={})".format(self.target)

    def __str__(self):
        return self.__repr__()


class ExcludesExpression(object):
    def __init__(self, tokens):
        self.args = tokens
        self.exclude = tokens[1]

    def get_filters(self):
        return self.target.get_filters()

    def __repr__(self):
        return "ExcludesExpression(exclude={})".format(self.exclude)

    def __str__(self):
        return self.__repr__()


class GroupByExpression(object):
    def __init__(self, tokens):
        self.args = tokens
        self.group_keys = tokens[1:]

    def get_filters(self):
        return self.target.get_filters()

    def __repr__(self):
        return "GroupByExpression({})".format(self.group_keys)

    def __str__(self):
        return self.__repr__()


class Rule(object):
    def __init__(self, tokens):
        self.source = tokens[0]
        self.target = None
        self.excludes = None
        self.group_by = None
        for token in tokens[1:]:
            if isinstance(token, TargetsExpression):
                self.target = token
            elif isinstance(token, ExcludesExpression):
                self.excludes = token
            elif isinstance(token, GroupByExpression):
                self.group_by = token

    def get_struct(self):
        result = {}
        if self.source is not None:
            if self.target is None:
                result['matchers'] = self.source.get_filters()
            else:
                result['source_match'] = self.source.get_filters()
        if self.target is not None:
            result['target_match'] = self.target.get_filters()
        if self.excludes is not None:
            result['exclusions'] = self.excludes.get_filters()

        # check how to return group by keys
        if self.group_by is not None:
            result['group by'] = self.excludes.get_filters()

    def __repr__(self):
        return "Rule(source={},target={},excludes={},group_by={})".format(self.source, self.target, self.excludes, self.group_by)

    def __str__(self):
        return self.__repr__()
