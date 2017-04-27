
'''
Grad Parser
GRAmmar Definition Parser
'''



# TODO write grammar syntax documentation
# based on BNF / EBNF grammar
'''
=  definition
|  alternation
-> range
[] optional
() group
*  repeat 0+
+  repeat 1+
-  backreference negation
'''



# a simple example of the functionality of this module
'''
import grad_parser as grad

g = grad.Grammar()
g.import_grammar(grad.basics)
g.load_grammar(
    \'''
    
    def = beginl 'def ' : name : '(' : [params] : ')' : ':' :
        indent(statement*)
    params = list(param, : ',' :)
    param = name [: '=' : value]
    
    list(A, B) = A (B A)*
    indent(A) = ((' ' | '\t')+ A endl)+
    
    name = ('_' | alpha) ('_' | alphanum)*
    alphanum = alpha | num
    alpha = 'a' -> 'z' | 'A' -> 'Z'
    num = '0' -> '9'
    : = (' ' | '\t')*
    
    \'''
)
'''





class ParseError(Exception):
    pass

class NotImplementedError(Exception):
    pass


class Match:
    def __init__(self, start, next, children=[], name=''):
        self.start = start
        self.next = next
        self.name = name
        self.children = children
    
    def __repr__(self):
        if len(self.children) == 0:
            if self.name == '':
                return 'Match({}:{})'.format(self.start, self.next)
            else:
                return 'Match({} {}:{})'.format(self.name, self.start, self.next)
        elif self.name == '':
            return 'Match({}:{} [])'.format(self.start, self.next)
        else:
            return 'Match({} {}:{} [])'.format(self.name, self.start, self.next)

class Grammar:
    # TODO integrate patterns
    
    def __init__(self):
        self.rules = []
        self.lookup = {}
        self.patterns = {}
    
    def name(self):
        return self.name
    
    def get_rule(self, name):
        return self.rules[self.lookup[name]]
    
    def has_rule(self, name):
        return name in self.lookup
    
    def add_rule(self, rule):
        if isinstance(rule, NamedRule):
            if rule.name in self.lookup:
                del self.rules[self.lookup(rule.name)]
            self.lookup[rule.name] = len(self.rules)
            self.rules.append(rule)
            rule.resolve_references(self)
            # TODO resolve references in a smarter way
            # currently only low-level references are resolved
        else:
            raise TypeError('Expected a NamedRule')
    
    def get_reference(self, rule):
        if isinstance(rule, str):
            if self.has_rule(rule):
                return self.get_rule(rule)
            else:
                raise Exception('Unresolved reference ' + rule)
        else:
            rule.resolve_references(self)
            return rule
    
    def parse(self, text):
        if len(self.rules) == 0:
            return []
        index = 0
        matches = []
        while index < len(text):
            match = None
            for rule in self.rules[::-1]:
                match = rule.parse(text, index)
                if match is None or match.next == index:
                    continue
                else:
                    break
            if match is None or match.next == index:
                index += 1
                continue
            else:
                matches.append(match)
                index = match.next
        return matches
    
    def import_grammar(self, grammar):
        for rule in grammar.rules:
            self.add_rule(rule)
    
    def load_grammar(self, text):
        # TODO parse grammar from text
        pass



class Rule:
    def __init__(self):
        pass
    
    def parse(self, text, start):
        raise NotImplementedError()
    
    def resolve_references(self, grammar):
        pass

class Pattern():
    def __init__(self, args, inner):
        self.args = args
        self.inner = inner
    
    def make_rule(inners):
        # TODO make rules from patterns
        pass

class NamedRule(Rule):
    def __init__(self, name, inner):
        self.name = name
        self.inner = inner
    
    def parse(self, text, start):
        match = self.inner.parse(text, start)
        if match is None:
            return None
        elif match.name == '':
            match.name = self.name
            return match
        else:
            return Match(match.start, match.next, [match], self.name)
    
    def resolve_references(self, grammar):
        self.inner = grammar.get_reference(self.inner)

class Empty(Rule):
    def parse(self, text, start):
        return Match(start, start)

class BeginLine(Rule):
    def parse(self, text, start):
        if start >= len(text):
            return None
        elif start == 0:
            return Match(start, start)
        elif text[start - 1] == '\n':
            return Match(start, start)
        elif text[start] == '\n':
            return Match(start, start + 1)
        else:
            return None

class EndLine(Rule):
    def parse(self, text, start):
        if start >= len(text):
            return None
        elif start == len(text) - 1:
            return Match(start, start)
        elif text[start] == '\n':
            return Match(start, start + 1)
        else:
            return None

class Indent(Rule):
    def __init__(self, inner):
        self.inner = inner
    
    def parse(self, text, start):
        # TODO
        pass

class Chars(Rule):
    def __init__(self, chars):
        self.chars = chars
    
    def parse(self, text, start):
        if start >= len(text):
            return None
        elif text[start] in self.chars:
            return Match(start, start + 1)
        else:
            return None

class Range(Rule):
    def __init__(self, low, high):
        self.low = low
        self.high = high
    
    def parse(self, text, start):
        if start >= len(text):
            return None
        elif self.low <= text[start] <= self.high:
            return Match(start, start + 1)
        else:
            return None

class Literal(Rule):
    def __init__(self, literal):
        self.literal = literal
    
    def parse(self, text, start):
        i = start
        for c in self.literal:
            if text[i] != c:
                return None
            i += 1
        return Match(start, i)

class Optional(Rule):
    def __init__(self, inner):
        self.inner = inner
    
    def parse(self, text, start):
        match = self.inner.parse(text, start)
        if match is not None:
            return match
        else:
            return Match(start, start)
    
    def resolve_references(self, grammar):
        self.inner = grammar.get_reference(self.inner)

class Alternation(Rule):
    def __init__(self, inners):
        self.inners = inners
    
    def parse(self, text, start):
        for inner in self.inners:
            match = inner.parse(text, start)
            if match is not None:
                return match
        return None
    
    def resolve_references(self, grammar):
        for i in range(len(self.inners)):
            self.inners[i] = grammar.get_reference(self.inners[i])

class Concatenation(Rule):
    def __init__(self, inners):
        self.inners = inners
    
    def parse(self, text, start):
        matches = []
        i = start
        for inner in self.inners:
            match = inner.parse(text, i)
            if match is None:
                return None
            matches.append(match)
            i = match.next
        return Match(start, i, matches)
    
    def resolve_references(self, grammar):
        for i in range(len(self.inners)):
            self.inners[i] = grammar.get_reference(self.inners[i])

class Repeat(Rule):
    def __init__(self, inner, min_matches=0):
        self.inner = inner
        self.min_matches = min_matches
    
    def parse(self, text, start):
        matches = []
        i = start
        n = 0
        match = self.inner.parse(text, i)
        while match is not None:
            matches.append(match)
            i = match.next
            n += 1
            match = self.inner.parse(text, i)
        if n >= self.min_matches:
            return Match(start, i, matches)
        else:
            return None
    
    def resolve_references(self, grammar):
        self.inner = grammar.get_reference(self.inner)

# TODO remove list class in favor of patterns
class List(Rule):
    def init(self, inner, sep):
        self.inner = inner
        self.sep = sep
    
    def parse(self, text, start):
        matches = []
        i = start
        n = 0
        match = self.inner.parse(text, i)
        while match is not None:
            matches.append(match)
            i = match.next
            n += 1
            match = self.sep.parse(text, i)
            if match is None:
                break
            else:
                matches.append(match)
                i = match.next
            match = self.inner.parse(text, i)
        return Match(start, i, matches)
    
    def resolve_references(self, grammar):
        self.inner = grammar.get_reference(self.inner)
        self.sep = grammar.get_reference(self.sep)




# TODO define useful grammars
meta = Grammar()

basics = Grammar()

json = Grammar()

python = Grammar()
