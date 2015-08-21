import parsimonious

class Grammar:

    def __init__(self):
        self.rules = []

    def rule(self, r):
        self.rules.append(r)
        def decorate(action):
            def decorator(self, node, children):
                result = action(self, node, children)
                if hasattr(result, "origin"):
                    result.origin(node)
                return result
            return decorator
        return decorate

    def parser(self, cls):
        extra_rules = []
        visitors = {}
        for kw in getattr(cls, "keywords", ()):
            extra_rules.append('%s = _ "%s" __' % (kw.upper(), kw))
            visitors["visit_%s" % kw.upper()] = lambda self, node, children: None

        for name, sym in getattr(cls, "symbols", {}).items():
            extra_rules.append('%s = _ "%s" _' % (name, sym))
            visitors["visit_%s" % name] = lambda self, node, children: None

        class Parser(cls, parsimonious.NodeVisitor):
            rules = "\n".join(self.rules + extra_rules)
            grammar = parsimonious.Grammar(rules)

        for k, v, in visitors.items():
            cls.__dict__[k] = v
        return Parser
