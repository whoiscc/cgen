# SPDX-FileCopyrightText: 2024-present U.N. Owen <void@some.where>
#
# SPDX-License-Identifier: MIT

class Unit:
    def write(self, writer):
        writer.write("void")

UNIT = Unit()

class Function:
    def __init__(self, name):
        self.name = name
        self.parameters = []
        self.return_type = UNIT
        self.body = []

    def write(self, writer):
        self.return_type.write(writer)
        writer.space()
        writer.write(self.name)
        with writer.parentheses():
            comma_writer = writer.comma_delimited()
            for parameter in self.parameters:
                parameter.write(next(comma_writer))
        writer.space()
        with writer.braces():
            lines_writer = writer.lines()
            for statement in self.body:
                statement.write(next(lines_writer))
