# SPDX-FileCopyrightText: 2024-present U.N. Owen <void@some.where>
#
# SPDX-License-Identifier: MIT

class Primitive:
    def __init__(self, name):
        self.name = name

    def write(self, writer):
        writer.write(self.name)

    def write_declaration(self, identifier, writer):
        self.write(writer)
        writer.space()
        writer.write(identifier)

UNIT = Primitive("void")
INT = Primitive("int")
CHAR = Primitive("char")

class Pointer:
    def __init__(self, inner):
        self.inner = inner

    def write(self, writer):
        self.inner.write(writer)
        if type(self.inner) is not Pointer:
            writer.space()
        writer.write("*")

    def write_declaration(self, identifier, writer):
        self.write(writer)
        writer.write(identifier)


class Array:
    def __init__(self, inner, length):
        self.inner = inner
        self.length = length

    def write(self, writer):
        self.inner.write(writer)
        writer.write(f"[{self.length}]")

    def write_declaration(self, identifier, writer):
        self.inner.write(writer)
        writer.space()
        writer.write(identifier)
        writer.write(f"[{self.length}]")


class Function:
    def __init__(self, name):
        self.name = name
        self.parameters = []
        self.return_type = UNIT
        self.body = []

    def add_parameter(self, ty, identifier = None):
        identifier = identifier or "arg" + str(len(self.parameters) + 1)
        variable = Variable(ty, identifier)
        self.parameters.append(variable)
        return variable
    
    def declare(self, ty, identifier = None):
        identifier = identifier or "x" + str(sum(1 for s in self.body if type(s) is Declare) + 1)
        variable = Variable(ty, identifier)
        self.body.append(Declare(variable))
        variable

    def write(self, writer):
        self.return_type.write(writer)
        writer.space()
        writer.write(self.name)
        with writer.parentheses():
            comma_writer = writer.comma_delimited()
            for variable in self.parameters:
                variable.write_declaration(next(comma_writer))
        writer.space()
        with writer.braces():
            for statement in self.body:
                with writer.line():
                    statement.write(writer)


class Variable:
    def __init__(self, ty, name):
        self.ty = ty
        self.name = name

    def write_declaration(self, writer):
        self.ty.write_declaration(self.name, writer)

    def write(self, writer):
        writer.write(self.name)


class Declare:
    def __init__(self, variable):
        self.variable = variable

    def write(self, writer):
        self.variable.write_declaration(writer)
        writer.write(";")