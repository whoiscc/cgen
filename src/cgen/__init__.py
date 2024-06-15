# SPDX-FileCopyrightText: 2024-present U.N. Owen <void@some.where>
#
# SPDX-License-Identifier: MIT
from contextlib import contextmanager

from cgen.writer import string


class Primitive:
    def __init__(self, name):
        self.name = name

    def write(self, writer):
        writer.write(self.name)

    def write_declaration(self, identifier, writer):
        self.write(writer)
        writer.space()
        writer.write(identifier)

    # consider override __eq__ by comparing name

UNIT = Primitive("void")
INT = Primitive("int")
CHAR = Primitive("char")

class Int:
    def __init__(self, value):
        assert isinstance(value, int)
        self.value = value

    @property
    def ty(self):
        return INT

    def write(self, writer):
        writer.write(str(self.value))


class String:
    def __init__(self, value):
        assert isinstance(value, str)
        self.value = value

    @property
    def ty(self):
        return Pointer(CHAR)

    def write(self, writer):
        writer.write("(char[])")
        with writer.braces(inline=True):
            comma_writer = writer.comma_delimited()
            for c in self.value:
                next(comma_writer).write(repr(c))


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

    def __eq__(self, other):
        return isinstance(other, Pointer) and self.inner == other.inner

    def __hash__(self):
        return hash((self.inner, "*"))


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

    def __eq__(self, other):
        return isinstance(other, Array) and self.inner == other.inner

    def __hash__(self):
        return hash((self.inner, "[]"))


class FunctionType:
    def __init__(self, return_type, parameter_types):
        self.return_type = return_type
        self.parameter_types = parameter_types

    def write(self, writer):
        self.return_type.write(writer)
        writer.space()
        with writer.parentheses():
            comma_writer = writer.comma_delimited()
            for ty in self.parameter_types:
                ty.write(next(comma_writer))

    def write_declaration(self, identifier, writer):
        self.return_type.write(writer)
        writer.space()
        writer.write(identifier)
        with writer.parentheses():
            comma_writer = writer.comma_delimited()
            for ty in self.parameter_types:
                ty.write(next(comma_writer))

    def __eq__(self, other):
        return isinstance(other,  FunctionType) and (self.return_type, self.parameter_types) == (other.return_type, other.parameter_types)

    def __hash__(self):
        return hash((self.parameter_types, "->", self.return_type))


class Function:
    def __init__(self, name):
        self.name = name
        self.parameters = []
        self.return_type = UNIT
        self.body = Block()
        self.active_block = self.body
        self.variable_count = 0

    def add_parameter(self, ty, identifier = None):
        identifier = identifier or "arg" + str(len(self.parameters) + 1)
        variable = Variable(ty, identifier)
        self.parameters.append(variable)
        return variable

    @property
    def ty(self):
        return FunctionType(self.return_type, [parameter.ty for parameter in self.parameters])

    def declare(self, ty, identifier = None):
        if not identifier:
            self.variable_count += 1
            identifier = "x" + str(self.variable_count)
        variable = Variable(ty, identifier)
        self.active_block.statements.append(Declare(variable))
        return variable

    def assign(self, place, source):
        self.active_block.statements.append(Assign(place, source))

    def run(self, inner):
        self.active_block.statements.append(Run(inner))

    def if_else(self, condition):
        statement = IfElse(condition)
        self.active_block.statements.append(statement)
        return (select_block(self, statement.positive), select_block(self, statement.negative))


    def ret(self, inner):
        assert inner.ty == self.return_type
        self.active_block.statements.append(Return(inner))

    def write_declaration(self, writer):
        self.ty.write_declaration(self.name, writer)
        writer.write(";")

    def write(self, writer):
        writer.write(self.name)

    def write_definition(self, writer):
        self.return_type.write(writer)
        writer.space()
        writer.write(self.name)
        with writer.parentheses():
            comma_writer = writer.comma_delimited()
            for variable in self.parameters:
                variable.write_declaration(next(comma_writer))
        writer.space()
        self.body.write(writer)


class Block:
    def __init__(self):
        self.statements = []

    def write(self, writer):
        with writer.braces():
            for statement in self.statements:
                with writer.line():
                    statement.write(writer)


@contextmanager
def select_block(function, block):
    previous_active_block = function.active_block
    function.active_block = block
    try:
        yield
    finally:
        function.active_block = previous_active_block


class Variable:
    def __init__(self, ty, name):
        self.ty = ty
        self.name = name

    @classmethod
    def type_unchecked(cls, name):
        return cls(None, name)

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


class Assign:
    def __init__(self, place, source):
        if source.ty:
            assert place.ty == source.ty, f"assign {string(place.ty)} with {string(source.ty)}"
        self.place = place
        self.source = source

    def write(self, writer):
        self.place.write(writer)
        writer.space()
        writer.write("=")
        writer.space()
        self.source.write(writer)
        writer.write(";")


class Return:
    def __init__(self, inner):
        self.inner = inner

    def write(self, writer):
        writer.write("return")
        writer.space()
        self.inner.write(writer)
        writer.write(";")


class Run:
    def __init__(self, inner):
        self.inner = inner

    def write(self, writer):
        self.inner.write(writer)
        writer.write(";")


class IfElse:
    def __init__(self, condition):
        self.condition = condition
        self.positive = Block()
        self.negative = Block()

    def write(self, writer):
        writer.write("if")
        writer.space()
        with writer.parentheses():
            self.condition.write(writer)
        writer.space()
        self.positive.write(writer)
        writer.write("else")
        writer.space()
        self.negative.write(writer)


class Call:
    def __init__(self, callee, arguments):
        callee_type = callee.ty
        if callee_type:
            assert isinstance(callee_type, FunctionType)
            assert len(arguments) == len(callee_type.parameter_types)
            for argument, ty in zip(arguments, callee_type.parameter_types):
                assert argument.ty == ty
        self.callee = callee
        self.arguments = arguments

    @property
    def ty(self):
        return self.callee.ty.return_type

    def write(self, writer):
        self.callee.write(writer)
        with writer.parentheses():
            comma_writer = writer.comma_delimited()
            for argument in self.arguments:
                argument.write(next(comma_writer))


class Index:
    def __init__(self, array, position):
        array_type = array.ty
        if array.ty:
            assert isinstance(array_type, (Array, Pointer))
            # TODO: assert position type
        self.array = array
        self.position = position

    @property
    def ty(self):
        return self.array.ty.inner

    def write(self, writer):
        self.array.write(writer)
        with writer.brackets():
            self.position.write(writer)


class Op:
    def __init__(self, op, left, right):
        # TODO: check left/right types
        self.op = op
        self.left = left
        self.right = right

    @property
    def ty(self):
        return INT # TODO

    def write(self, writer):
        if self.left:
            self.left.write(writer)
            writer.space()
        writer.write(self.op)
        writer.space()
        self.right.write(writer)


class IncludeSystem:
    def __init__(self, name):
        self.name = name

    def write(self, writer):
        writer.write(f"#include <{self.name}>")
        writer.line_break()

def write_items(items, writer):
    for item in items:
        if isinstance(item, IncludeSystem):
            item.write(writer)
    for item in items:
        if isinstance(item, Function):
            with writer.line():
                item.write_declaration(writer)
    for item in items:
        if isinstance(item, Function):
            item.write_definition(writer)
