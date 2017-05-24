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
        return '{' + ''.join(str(arg) for arg in self.args) + '}'

    def to_dict(self):
        return {"key": self.key,
                "operator": self.operator,
                "value": self.value}


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

    def __repr__(self):
        return "MetricSelector(name={},dimensions={})".format(
            self.name, self.dimensions)

    def to_dict(self):
        result = [{"key":"__name__", "value": self.name, "operator": "="}]
        for dim in self.dimensions:
            result.append({"key": dim.key,
                           "operator": dim.operator,
                           "value": dim.value})
        return result


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

    def __repr__(self):
        return "LogicalExpression(left={},operator='{}',right={})".format(self.left_operand, self.operator, self.right_operand)

    def __str__(self):
        return self.__repr__()

    def to_dict(self):
        result = {"left": self.left_operand.to_dict(),
                  "operator": self.normalized_operator,
                  "right": self.right_operand.to_dict(),
                  }
        return result
