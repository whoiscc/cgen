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
USIZE = Primitive("size_t")

class Pointer:
    def __init__(self, inner):
        self.inner = inner

    def write(self, writer):
        self.inner.write(writer)
        if not isinstance(self.inner, Pointer):
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
        writer.write(f"{identifier}[{self.length}]")

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

class Struct:
    def __init__(self, name):
        self.name = name
        self.fields = []

    def add_field(self, ty, identifier):
        self.fields.append((ty, identifier))

    def write_declaration(self, identifier, writer):
        self.write(writer)
        writer.space()
        writer.write(identifier)

    def write(self, writer):
        writer.write("struct")
        writer.space()
        writer.write(self.name)

    def writer_definition(self, writer):
        writer.write("struct")
        writer.space()
        writer.write(self.name)
        writer.space()
        with writer.braces():
            for (ty, identifier), line_writer in zip(self.fields, writer.lines()):
                ty.write_declaration(identifier, line_writer)
                line_writer.write(";")
        writer.write(";")


class Int:
    def __init__(self, value, ty = INT):
        assert isinstance(value, int)
        self.value = value
        assert ty in (INT, USIZE)
        self.ty = ty

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

class Null:
    def __init__(self, inner_type):
        self.inner_type = inner_type

    @property
    def ty(self):
        return Pointer(self.inner_type)

    def write(self, writer):
        writer.write("NULL")

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

    def add(self, statement):
        self.active_block.statements.append(statement)

    def if_else(self, condition):
        statement = IfElse(condition)
        self.active_block.statements.append(statement)
        return (block_context(self, statement.positive), block_context(self, statement.negative))

    def loop(self, condition):
        statement = While(condition)
        self.active_block.statements.append(statement)
        return block_context(self, statement.body)

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
            line_writer = writer.lines()
            for statement in self.statements:
                statement.write(next(line_writer))

@contextmanager
def block_context(function, block):
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

class While:
    def __init__(self, condition):
        self.condition = condition
        self.body = Block()

    def write(self, writer):
        writer.write("while")
        writer.space()
        with writer.parentheses():
            self.condition.write(writer)
        writer.space()
        self.body.write(writer)

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

class Op:
    def __init__(self, op, left, right):
        # TODO: check left/right types
        self.op = op
        self.left = left
        self.right = right

    @classmethod
    def unary(cls, op, right):
        return cls(op, None, right)

    @property
    def ty(self):
        if self.op == "sizeof":
            return USIZE
        return INT # TODO

    def write(self, writer):
        if self.left:
            with writer.parentheses():
                self.left.write(writer)
            writer.space()
        writer.write(self.op)
        writer.space()
        with writer.parentheses():
            self.right.write(writer)

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

class GetAttr:
    def __init__(self, struct, attr):
        self.ty = None
        struct_type = struct.ty
        if struct_type:
            assert isinstance(struct_type, Struct)
            for ty, name in struct_type.fields:
                if name == attr:
                    self.ty = ty
            assert self.ty
        self.struct = struct
        self.attr = attr

    def write(self, writer):
        self.struct.write(writer)
        writer.write(f".{self.attr}")


class SetAttr:
    def __init__(self, struct, attr, source):
        struct_type = struct.ty
        if struct_type:
            assert isinstance(struct_type, Struct)
            field_type = next(ty for ty, name in struct_type.fields if name == attr)
            assert source.ty == field_type
        self.struct = struct
        self.attr = attr
        self.source = source

    def write(self, writer):
        self.struct.write(writer)
        writer.write(f".{self.attr}")
        writer.space()
        writer.write("=")
        writer.space()
        self.source.write(writer)
        writer.write(";")

class Include:
    def __init__(self, name, *, system=True):
        self.name = name
        self.system = system

    def write(self, writer):
        if self.system:
            writer.write(f"#include <{self.name}>")
        else:
            writer.write(f'#include "{self.name}"')
        writer.line_break()

    def __eq__(self, other):
        return isinstance(other, Include) and (other.name, other.system) == (self.name, self.system)

    def __hash__(self):
        return hash((self.name, self.system))


class SourceCode:
    def __init__(self):
        self.includes = set()
        self.structs = []
        self.functions = []

    def add(self, item):
        match item:
            case Include():
                self.includes.add(item)
            case Struct():
                self.structs.append(item)
            case Function():
                self.functions.append(item)
            case _:
                for item in item.items():
                    self.add(item)

    def write(self, writer):
        for item in self.includes:
            item.write(writer)
        line_writer = writer.lines()
        for item in self.structs:
            item.writer_definition(next(line_writer))
        for item in self.functions:
            item.write_declaration(next(line_writer))
        for item in self.functions:
            item.write_definition(next(line_writer))
