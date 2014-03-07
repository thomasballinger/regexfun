import itertools

def indent(s, n):
    return '\n'.join([' '*n + line for line in s.split('\n')])

class Regex(object):
    def __init__(self, *operands):
        self.operands = [Literal(op) if isinstance(op, basestring) else op for op in operands]
    def _match(self, s):
        raise NotImplemented
    def __repr__(self):
        return '%s(%s)' % (type(self).__name__, ', '.join(repr(op) for op in self.operands))
    def __str__(self):
        return '%s(\n%s)' % (type(self).__name__, '\n'.join(indent(str(op), len(type(self).__name__)+1) for op in self.operands))
    def __call__(self, s):
        if isinstance(s, basestring):
            return self._match(list(s))
        else:
            return self._match(s)
    def __eq__(self, other):
        """
        >>> And("a", "b") == And("a", "b")
        True
        >>> And("a", And("b", "c")) == And("a", And("b", "c"))
        True
        """
        return self.operands == other.operands

class And(Regex):
    def _match(self, s):
        """
        >>> l = And('a', 'b')
        >>> l('ac')
        False
        >>> l('ab')
        True
        >>> l('abc')
        True
        >>> l('')
        False
        """
        return all(op(s) for op in self.operands)

class Or(Regex):
    def _match(self, s):
        return any(op(s) for op in self.operands)

class Literal(Regex):
    def __init__(self, char):
        self.char = char
    def __repr__(self):
        return '"%s"' % self.char
    def __str__(self):
        return repr(self)
    @property
    def operands(self):
        return [self.char]
    def _match(self, s):
        """
        >>> l = Literal('a')
        >>> l('b')
        False
        >>> l('a')
        True
        """
        if s and s[0] == self.char:
            s.pop(0)
            return True
        return False

def parse(s):
    """
    >>> parse('[ab]c|de')
    Or(And(Or("a", "b"), "c"), And("d", "e"))
    >>> parse('abc')
    And("a", And("b", "c"))

    Grammar:
    regex => concat | regex
    regex => concat

    concat => group concat
    concat => group

    group => (regex)
    group => [chars]
    group => char

    chars => char chars
    chars => char
    char => anything but ]
    """
    r, rest = regex(s)
    assert not rest
    return r

def regex(s):
    """
    >>> regex('[ab]a')
    (And(Or("a", "b"), "a"), '')
    >>> regex('[ab]')
    (Or("a", "b"), '')

    #>>> regex('ab)')
    #(And("a", "b"), ')')
    """
    token, rest = concat(s)
    if not rest:
        return token, rest
    elif rest[0] == '|':
        next_token, rest = regex(rest[1:])
        return Or(token, next_token), rest
    else:
        assert rest[0] == ')'
        return token, rest

def concat(s):
    """
    >>> concat('[ab]a')
    (And(Or("a", "b"), "a"), '')
    >>> concat('[ab]')
    (Or("a", "b"), '')
    >>> concat('ab)')
    (And("a", "b"), ')')

    #>>> concat('b)')
    #("b", ')')
    """
    token, rest = group(s)
    if (not rest) or rest[0] in '|)':
        return token, rest
    else:
        next_token, rest = concat(rest)
        return And(token, next_token), rest

def group(s):
    """
    >>> group('[ab]a')
    (Or("a", "b"), 'a')
    >>> group('(ab)')
    (And("a", "b"), '')
    >>> group('ab)')
    ("a", 'b)')
    >>> group('ab)')
    ("a", 'b)')
    """
    if s[0] == '(':
        token, rest = regex(s[1:])
        return token, rest[1:]
    elif s[0] == '[':
        token, rest = chars(s[1:])
        return token, rest[1:]
    else:
        return Literal(s[0]), s[1:]

def chars(s):
    """
    >>> chars('ab]')
    (Or("a", "b"), ']')
    >>> chars('ab)')
    (Or("a", "b"), ')')
    """
    if s[0] in '])':
        return None, s
    else:
        chrs, rest = chars(s[1:])
        if chrs:
            return Or(Literal(s[0]), chrs), rest
        else:
            return Literal(s[0]), rest

def run_until_unchanged(tree, transforms):
    """
    >>> run_until_unchanged(combine_ands(And("a", And("b", And("c", "d")))), [combine_ands, combine_ors])
    And("a", "b", "c", "d")
    """
    while True:
        new_tree = reduce(lambda t, f: f(t), transforms, tree)
        if new_tree == tree:
            return tree
        tree = new_tree

def combine_operators(tree, operator):
    """
    >>> combine_ands(And("a", And("b", "c")))
    And("a", "b", "c")
    >>> combine_ands(And("a", And("b", And("c", "d"))))
    And("a", "b", And("c", "d"))
    """
    if isinstance(tree, operator):
        to_move = [op for op in tree.operands if isinstance(op, operator)]
        return type(tree)(*([op for op in tree.operands if not isinstance(op, operator)] +
                                [inner_op for op in to_move for inner_op in op.operands]))

combine_ands = lambda tree: combine_operators(tree, And)
combine_ors = lambda tree: combine_operators(tree, And)
simplify = lambda tree: run_until_unchanged(tree, [combine_ors, combine_ands])

if __name__ == '__main__':
    import doctest
    import sys
    doctest.testmod()
    if len(sys.argv) == 3:
        print sys.argv[1], sys.argv[2]
        p = parse(sys.argv[1])
        print p
        s = simplify(p)
        print s
        print s(sys.argv[2])
    else:
        print 'example: script.py "[ab]c" bc'

