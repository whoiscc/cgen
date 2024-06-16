from contextlib import contextmanager


def string(item):
    w = Writer()
    item.write(w)
    return w.buf


class Writer:
    def __init__(self):
        self.buf = ""
        self.indent_level = 0
        self.fresh_line = True

    def write(self, content):
        if self.fresh_line and content:
            self.buf += " " * self.indent_level
            self.fresh_line = False
        self.buf += content

    def line_break(self):
        self.buf += "\n"
        self.fresh_line = True

    def space(self):
        self.write(" ")

    def parentheses(self):
        return self.wrap("(", ")", inline=True)

    def braces(self, *, inline=False):
        return self.wrap("{", "}", inline)

    def brackets(self):
        return self.wrap("[", "]", inline=True)

    def comma_delimited(self):
        return self.delimited(", ")

    def lines(self):
        while True:
            yield self
            self.line_break()

    @contextmanager
    def wrap(self, left, right, inline):
        self.write(left)
        if not inline:
            self.indent_level += 2
            self.line_break()
        try:
            yield self
        finally:
            if not inline:
                self.indent_level -= 2
                self.line_break()
            self.write(right)

    def delimited(self, delimiter):
        prefix = ""
        while True:
            self.write(prefix)
            prefix = delimiter
            yield self
