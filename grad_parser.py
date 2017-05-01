
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
g.use(grad.basics)
g.load(
    \'''
    
    def = beginl 'def ' : name : '(' : [params] : ')'
        : ':' : indent(statement*)
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
    def __init__(self, start, next, parts=[], name=''):
        self.start = start
        self.next = next
        self.name = name
        self.parts = parts
    
    def __repr__(self):
        if self.name == '':
            return 'Match({}:{})'.format(self.start, self.next)
        else:
            return 'Match({} {}:{})'.format(self.name, self.start, self.next)
    
    def show(self, text):
        '''Show this match within the specified text'''
        return text[self.start, self.next]



class Pattern:
    '''Factory for creating variable rules'''
    
    class RuleBuilder:
        '''Builds a rule by resolving local references'''
        
        def __init__(self, args, rules):
            self.args = args
            self.rules = rules
        
        def get_reference(self, rule):
            '''Replaces references to named rules with the rules they reference'''
            if isinstance(rule, Reference):
                if rule in self.args:
                    return self.get_rule(rule)
            else:
                rule.resolve_references(self)
                return rule
    
    def __init__(self, params, inner):
        self.params = params
        self.inner = inner
    
    def make_rule(self, args):
        '''Creates a rule from the provided arguments'''
        if len(self.params) != len(inners):
            raise ParseError('Unexpected number of arguments to pattern')
        
        rb = Pattern.RuleBuilder(self.params, args)
        return rb.get_reference(self.inner.copy_with_references())

class Rule:
    def parse(self, text, start):
        '''Attempts to parse text[start:]. Returns a Match object or None'''
        raise NotImplementedError()
    
    def copy_with_references(self):
        '''Returns a reference-preserving copy of this rule'''
        raise NotImplementedError()
    
    def resolve_references(self, grammar):
        '''Converts references to the rules they are meant to reference'''
        pass

class Reference(Rule):
    def __init__(self, name):
        self.name = name
    
    def copy_with_references(self):
        return Reference(self.name)

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
    
    def copy_with_references(self):
        return self
    
    def resolve_references(self, grammar):
        self.inner = grammar.get_reference(self.inner)

class Empty(Rule):
    def parse(self, text, start):
        return Match(start, start)
    
    def copy_with_references(self):
        return Empty()

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
    
    def copy_with_references(self):
        return BeginLine()

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
    
    def copy_with_references(self):
        return EndLine()

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
    
    def copy_with_references(self):
        return Chars(self.chars)

class All(Rule):
    def parse(self, text, start):
        if start >= len(text):
            return None
        else:
            return Match(start, start + 1)
    
    def copy_with_references(self):
        return All()

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
    
    def copy_with_references(self):
        return Range(self.low, self.high)

class Literal(Rule):
    def __init__(self, literal):
        self.literal = literal
    
    def parse(self, text, start):
        if start + len(self.literal) >= len(text):
            return None
        i = start
        for c in self.literal:
            if text[i] != c:
                return None
            i += 1
        return Match(start, i)
    
    def copy_with_references(self):
        return Literal(self.literal)

class Optional(Rule):
    def __init__(self, inner):
        self.inner = inner
    
    def parse(self, text, start):
        match = self.inner.parse(text, start)
        if match is not None:
            return match
        else:
            return Match(start, start)
    
    def copy_with_references(self):
        return Optional(self.inner.copy_with_references())
    
    def resolve_references(self, grammar):
        self.inner = grammar.get_reference(self.inner)

class Negation(Rule):
    def __init__(self, poistive, negative):
        self.poistive = poistive
        self.negative = negative
    
    def parse(self, text, start):
        match = self.poistive.parse(text, start)
        if match is None:
            return None
        neg_match = self.negative.parse(text, start)
        if neg_match is None:
            return match
        else:
            return None
    
    def copy_with_references(self):
        return Negation(
            self.poistive.copy_with_references(),
            self.negative.copy_with_references())
    
    def resolve_references(self, grammar):
        self.poistive = grammar.get_reference(self.poistive)
        self.negative = grammar.get_reference(self.negative)

class Alternation(Rule):
    def __init__(self, inners):
        self.inners = inners
    
    def parse(self, text, start):
        for inner in self.inners:
            match = inner.parse(text, start)
            if match is not None:
                return match
        return None
    
    def copy_with_references(self):
        inners = []
        for i in self.inners:
            inners.append(i.copy_with_references())
        return Alternation(inners)
    
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
    
    def copy_with_references(self):
        inners = []
        for i in self.inners:
            inners.append(i.copy_with_references())
        return Concatenation(inners)
    
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
    
    def copy_with_references(self):
        return Repeat(self.inner.copy_with_references(), self.min_matches)
    
    def resolve_references(self, grammar):
        self.inner = grammar.get_reference(self.inner)



class Grammar:
    # TODO integrate patterns
    
    def __init__(self):
        self.rules = []
        self.lookup = {}
        self.patterns = {}
    
    def get_rule(self, name):
        '''Returns the named rule with the given name'''
        return self.rules[self.lookup[name]]
    
    def has_rule(self, name):
        '''Returns whether or not this grammar contains a named rule'''
        return name in self.lookup
    
    def add_rule(self, rule):
        '''Adds a rule with references to lower level rules or itself'''
        if isinstance(rule, NamedRule):
            if self.has_rule(rule.name):
                del self.rules[self.lookup(rule.name)]
            self.lookup[rule.name] = len(self.rules)
            self.rules.append(rule)
            rule.resolve_references(self)
        else:
            raise TypeError('Expected a NamedRule')
    
    def get_reference(self, rule):
        '''Replaces references to named rules with the rules they reference'''
        if isinstance(rule, Reference):
            if self.has_rule(rule.name):
                return self.get_rule(rule.name)
            else:
                raise Exception('Unresolved reference ' + rule)
        else:
            rule.resolve_references(self)
            return rule
    
    def parse(self, text, names=None):
        '''Parses text with this grammar (optionally only for certain rules)'''
        if names = None:
            rules = self.rules
        elif len(names) == 0:
            return []
        else:
            rules = []
            for name in names:
                rules.append(self.get_rule(name))
        index = 0
        matches = []
        while index < len(text):
            match = None
            for rule in rules[::-1]:
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
    
    def use(self, grammar):
        '''Use (import) definitions from another grammar on top of this one'''
        for rule in grammar.rules:
            self.add_rule(rule)
        self.patterns.update(grammar.patterns)
    
    def load(self, text):
        '''Parse and load a grammar definition on top of the current grammar'''
        # TODO parse grammar from text
        pass



'''
comment = '#' (all - endl)* endl;
rule_def = beginl s word s '=' s rule s ';';
pattern_def = beginl s word s '(' s (word s)* ')' s '=' s rule s ';';

rule = pattern | group
    | optional | alternation
    | concatenation | not | repeat
    | range | literal | word;
pattern = word s '(' s (rule s)* ')';
group = '(' s rule s ')';
concatenation = rule s rule;
alternation = rule s '|' s rule;
not = rule s '-' s rule;
optional = '[' s rule s ']';
repeat = rule s ('+' | '*');
range = literal s '->' s literal;
literal = "'" (char | '"')*  "'" | '"' (char | "'")* '"';

char = '\\\\' | '\\n' | '\\t'
    | '\\\'' | '\\\"' | '\\u' hex hex hex hex
    | all - '\\' - '\n';
hex = '0' -> '9' | 'a' -> 'f' | 'A' -> 'F';
word = letter (letter | '_' | '0' -> '9')*;
letter = 'a' -> 'z' | 'A' -> 'Z';
s = (' ' | '\t' | '\n' )*;
'''

meta = Grammar()
s = NamedRule('s',
    Repeat(Alternation([Literal(' '), Literal('\t'), Literal('\n')]))
)
letter = NamedRule('letter',
    Alternation([Range('a', 'z'), Range('A', 'Z')])
)
word = NamedRule('word',
    Concatenation([letter, Repeat(Alternation([letter, Literal('_'), Range('0', '9')]))])
)
hex = NamedRule('hex',
    Alternation([Range('0', '9'), Range('a', 'f'), Range('A', 'F')])
)
char = NamedRule('char',
    Alternation(Literal('\\\\'), Literal('\\n'), Literal('\\t'), Literal('\\\''),
    Literal('\\\"'), Negation(All(), Alternation([Literal('\\'), Literal('\n')])))
)
rule = NamedRule('rule',
    Empty()
)
Literal = NamedRule('Literal',
    Alternation([
        Concatenation([Literal("'"), Repeat(Alternation(char, Literal('"'))), Literal("'")]),
        Concatenation([Literal('"'), Repeat(Alternation(char, Literal("'"))), Literal('"')])
    ])
)
# TODO finish building meta grammar




# TODO define other useful grammars
basics = Grammar()
json = Grammar()
python = Grammar()
