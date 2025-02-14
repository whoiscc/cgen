# SPDX-FileCopyrightText: 2024-present U.N. Owen <void@some.where>
#
# SPDX-License-Identifier: MIT
from contextlib import contextmanager

from cgen.parse import parse, parse_type
from cgen.writer import generate


class Primitive:
    def __init__(self, name):
        self.name = name

    def write(self, writer):
        writer.write(self.name)

    def write_declaration(self, identifier, writer):
        self.write(writer)
        writer.space()
        writer.write(identifier)

    def write_mangled(self, writer):
        self.write(writer)

    # consider override __eq__ by comparing name?


UNIT = Primitive("void")
I32 = Primitive("int32_t")
U8 = Primitive("uint8_t")
U32 = Primitive("uint32_t")
U64 = Primitive("uint64_t")
USIZE = Primitive("size_t")

# these are part of the language so has to be here
# do not use them; use what Rust has
INT = Primitive("int")  # for comparison result type
CHAR = Primitive("char")  # for string literal type


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

    def write_mangled(self, writer):
        writer.write("ptr_")
        self.inner.write_mangled(writer)

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

    def write_mangled(self, writer):
        writer.write(f"array{self.length}_")
        self.inner.write_mangled(writer)

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
        with writer.parentheses():
            writer.write("*")
            writer.write(identifier)
        with writer.parentheses():
            comma_writer = writer.comma_delimited()
            for ty in self.parameter_types:
                ty.write(next(comma_writer))

    def writer_mangled(self, writer):
        raise NotImplementedError  # need to carefully think about this...

    def __eq__(self, other):
        return isinstance(other, FunctionType) and (self.return_type, self.parameter_types) == (
            other.return_type,
            other.parameter_types,
        )

    def __hash__(self):
        return hash((self.parameter_types, "->", self.return_type))


def mangled_name(writer, name, type_arguments):
    writer.write(name)
    if not type_arguments:
        return
    writer.write("_")
    for _, argument in sorted(type_arguments.items()):
        writer.write("_")
        argument.write_mangled(writer)


class Struct:
    def __init__(self, name, **type_arguments):
        self.name = name
        self.type_arguments = type_arguments
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
        mangled_name(writer, self.name, self.type_arguments)

    def write_mangled(self, writer):
        writer.write(f"struct_{self.name}")

    def writer_definition(self, writer):
        writer.write("struct")
        writer.space()
        mangled_name(writer, self.name, self.type_arguments)
        writer.space()
        with writer.braces():
            for (ty, identifier), line_writer in zip(self.fields, writer.lines()):
                ty.write_declaration(identifier, line_writer)
                line_writer.write(";")
        writer.write(";")


class Int:
    def __init__(self, value, ty=I32):
        assert isinstance(value, int)
        self.value = value
        assert ty in (INT, I32, U8, U32, U64, USIZE)  #
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
        with writer.parentheses():
            self.ty.write(writer)
        writer.space()
        writer.write("NULL")


class Function:
    def __init__(self, name, **type_arguments):
        self.name = name
        self.type_arguments = type_arguments
        self.parameters = []
        self.return_type = UNIT
        self.body = Block()
        self.active_block = self.body
        self.identifiers = {}
        self.labels = {}

    def add_parameter(self, ty, identifier=None):
        assert not self.body.statements, "parameter must be added first"
        identifier = identifier or "arg" + str(len(self.parameters) + 1)
        assert all(variable.name != identifier for variable in self.parameters)
        variable = Variable(ty, identifier)
        self.parameters.append(variable)
        return variable

    @property
    def ty(self):
        return FunctionType(self.return_type, [parameter.ty for parameter in self.parameters])

    def declare(self, ty, identifier_hint=None):
        identifier_hint = identifier_hint or "x"
        identifier = identifier_hint
        if identifier in self.identifiers:
            self.identifiers[identifier] += 1
            identifier += str(self.identifiers[identifier])
        else:
            self.identifiers[identifier] = 1
        variable = Variable(ty, identifier)
        self.active_block.statements.append(Declare(variable))
        return variable

    def if_else(self, *condition_tokens):
        statement = IfElse(parse(tuple(condition_tokens)))
        self.active_block.statements.append(statement)
        return (self.block_context(statement.positive), self.block_context(statement.negative))

    def when(self, *condition_tokens):
        return self.if_else(*condition_tokens)[0]

    def loop(self, *condition_tokens):
        statement = While(parse(tuple(condition_tokens)))
        self.active_block.statements.append(statement)
        return self.block_context(statement.body)

    def label(self, name_hint=None):
        name_hint = name_hint or "l"
        name = name_hint
        if name in self.labels:
            self.labels[name] += 1
            name += str(self.labels[name])
        else:
            self.labels[name] = 1
        label = Label(name)
        self.active_block.statements.append(label)
        return label

    def add(self, *statement_tokens):
        statement = parse(tuple(statement_tokens))
        if not isinstance(statement, (Assign, SetAttr, SetItem)):
            statement = Run(statement)
        self.active_block.statements.append(statement)

    @contextmanager
    def block_context(self, block):
        previous_active_block = self.active_block
        self.active_block = block
        try:
            yield
        finally:
            self.active_block = previous_active_block

    def ret(self, *tokens):
        inner = parse(tuple(tokens))
        assert inner.ty == self.return_type
        self.active_block.statements.append(Return(inner))

    # intentionally duplicate FunctionType.write_declaration
    # the `writer_declaration` contract in this codebase promises to work with any identifier
    # specified by caller, while the "forward declaration" has a fixed function name
    # this is a forward declaration
    #   int add(int, int);
    # this is a declaration (potentially in global scope)
    #   int (*assignable_add)(int, int);  // later may execute `assignable_add = add;`
    def write_forward_declaration(self, writer):
        self.return_type.write(writer)
        writer.space()
        self.write(writer)
        with writer.parentheses():
            comma_writer = writer.comma_delimited()
            for variable in self.parameters:
                variable.ty.write(next(comma_writer))
        writer.write(";")

    def write(self, writer):
        mangled_name(writer, self.name, self.type_arguments)

    def write_definition(self, writer):
        self.return_type.write(writer)
        writer.space()
        mangled_name(writer, self.name, self.type_arguments)
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
            if not self.statements:
                writer.write(";")
            for statement in self.statements:
                statement.write(next(line_writer))


class Variable:
    def __init__(self, ty, name):
        self.ty = parse_type(ty)
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
            assert place.ty == source.ty, f"assign {generate(place.ty)} with {generate(source.ty)}"
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
        writer.space()
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


class Label:
    def __init__(self, name):
        self.name = name

    def write(self, writer):
        writer.write(f"{self.name}:")


class Goto:
    def __init__(self, label=None):
        self.label = label

    def write(self, writer):
        assert self.label
        writer.write("goto")
        writer.space()
        writer.write(f"{self.label.name};")


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
        if op in ["+", "-", "*", "/", "%"]:
            assert left.ty == right.ty
        # TODO: other type checks
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
        if self.op == "&" and not self.left:
            return Pointer(self.right.ty)
        if self.op in ("==", "!=", ">", ">=", "<", "<="):
            return INT
        return self.left.ty  # TODO: complete the cases

    def write(self, writer):
        if self.left:
            with writer.parentheses():
                self.left.write(writer)
            writer.space()
        writer.write(self.op)
        if self.left:
            writer.space()
        with writer.parentheses():
            self.right.write(writer)


class GetItem:
    def __init__(self, array, position):
        array_type = array.ty
        if array_type:
            assert isinstance(array_type, (Array, Pointer))
        position_type = position.ty
        if position_type:
            assert position_type == USIZE
        self.array = array
        self.position = position

    @property
    def ty(self):
        return self.array.ty.inner

    def write(self, writer):
        self.array.write(writer)
        with writer.brackets():
            self.position.write(writer)


class SetItem:
    def __init__(self, array, position, source):
        array_type = array.ty
        if array_type:
            assert isinstance(array_type, (Array, Pointer))
            source_type = source.ty
            if source_type:
                assert source_type == array_type.inner
        position_type = position.ty
        if position_type:
            assert position_type == USIZE
        self.array = array
        self.position = position
        self.source = source

    def write(self, writer):
        self.array.write(writer)
        with writer.brackets():
            self.position.write(writer)
        writer.space()
        writer.write("=")
        writer.space()
        self.source.write(writer)
        writer.write(";")


class GetAttr:
    def __init__(self, struct, attr):
        self.ty = None
        struct_type = struct.ty
        if struct_type and isinstance(struct_type, Pointer):
            self.arrow = True
            struct_type = struct_type.inner
        else:
            self.arrow = False
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
        if self.arrow:
            writer.write(f"->{self.attr}")
        else:
            writer.write(f".{self.attr}")


class SetAttr:
    def __init__(self, struct, attr, source):
        struct_type = struct.ty
        if struct_type and isinstance(struct_type, Pointer):
            self.arrow = True
            struct_type = struct_type.inner
        else:
            self.arrow = False
        if struct_type:
            assert isinstance(struct_type, Struct)
            field_type = next(ty for ty, name in struct_type.fields if name == attr)
            assert source.ty == field_type
        self.struct = struct
        self.attr = attr
        self.source = source

    def write(self, writer):
        self.struct.write(writer)
        if self.arrow:
            writer.write(f"->{self.attr}")
        else:
            writer.write(f".{self.attr}")
        writer.space()
        writer.write("=")
        writer.space()
        self.source.write(writer)
        writer.write(";")


class Cast:
    def __init__(self, ty, inner):
        # TODO: check cast validity
        self.ty = ty
        self.inner = inner

    def write(self, writer):
        with writer.parentheses():
            self.ty.write(writer)
        writer.space()
        self.inner.write(writer)


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
            case compound_item:
                for item in compound_item.items():
                    self.add(item)

    def write(self, writer):
        for item in self.includes:
            item.write(writer)
        line_writer = writer.lines()
        for item in self.structs:
            item.writer_definition(next(line_writer))
        for item in self.functions:
            item.write_forward_declaration(next(line_writer))
        for item in self.functions:
            item.write_definition(next(line_writer))
