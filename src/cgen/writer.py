from contextlib import contextmanager


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
        return parentheses(self)

    def braces(self):
        return braces(self)

    def comma_delimited(self):
        return delimited(self, ", ")

    def lines(self):
        return lines(self)


@contextmanager
def parentheses(writer):
    writer.write("(")
    try:
        yield writer
    finally:
        writer.write(")")


@contextmanager
def braces(writer):
    writer.write("{")
    writer.indent_level += 2
    writer.line_break()
    try:
        yield writer
    finally:
        writer.indent_level -= 2
        writer.write("}")
        writer.line_break()


def delimited(writer, delimiter):
    prefix = ""
    while True:
        writer.write(prefix)
        prefix = delimiter
        yield writer


def lines(writer):
    while True:
        yield writer
        writer.line_break()
