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
        return wrap(self, "(", ")", inline=True)

    def braces(self, *, inline=False):
        return wrap(self, "{", "}", inline)

    def brackets(self):
        return wrap(self, "[", "]", inline=True)

    def comma_delimited(self):
        return delimited(self, ", ")

    def line(self):
        return line(self)


@contextmanager
def line(writer):
    try:
        yield writer
    finally:
        writer.line_break()


@contextmanager
def wrap(writer, left, right, inline):
    writer.write(left)
    if not inline:
        writer.indent_level += 2
        writer.line_break()
    try:
        yield writer
    finally:
        if not inline:
            writer.indent_level -= 2
        writer.write(right)
        if not inline:
            writer.line_break()


def delimited(writer, delimiter):
    prefix = ""
    while True:
        writer.write(prefix)
        prefix = delimiter
        yield writer
