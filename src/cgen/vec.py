from cgen import (
    INT,
    UNIT,
    USIZE,
    Assign,
    Call,
    Function,
    FunctionType,
    GetAttr,
    Include,
    Int,
    Null,
    Op,
    Pointer,
    Run,
    SetAttr,
    SetItem,
    Struct,
    Variable,
)


class Vec:
    def __init__(self, inner_type):
        self.inner_type = inner_type
        self.struct = gen_struct(self.inner_type)
        self.new = self.gen_new()
        self.drop = self.gen_drop()
        self.reserve = self.gen_reserve()
        self.push = self.gen_push()

    def gen_new(self):
        f = Function("vec_new")
        f.return_type = self.struct
        v = f.declare(self.struct, "v")
        f.add(SetAttr(v, "buf", Null(self.inner_type)))
        f.add(SetAttr(v, "len", Int(0, USIZE)))
        f.add(SetAttr(v, "cap", Int(0, USIZE)))
        f.ret(v)
        return f

    def gen_drop(self):
        f = Function("vec_drop")
        v = f.add_parameter(self.struct, "v")
        with f.if_else(Op("!=", GetAttr(v, "cap"), Int(0, USIZE)))[0]:
            free = Variable(FunctionType(UNIT, [Pointer(self.inner_type)]), "free")
            f.add(Run(Call(free, [GetAttr(v, "buf")])))
            # not necessary if guarantee no double drop
            f.add(SetAttr(v, "len", Int(0, USIZE)))
            f.add(SetAttr(v, "cap", Int(0, USIZE)))
        return f

    def gen_reserve(self):
        f = Function("vec_reserve")
        v = f.add_parameter(Pointer(self.struct), "v")
        cap = f.add_parameter(USIZE, "cap")
        # not silently fail the opposite?
        with f.if_else(Op(">", cap, GetAttr(v, "cap")))[0]:
            realloc = Variable(FunctionType(Pointer(self.inner_type), [Pointer(self.inner_type), USIZE]), "realloc")
            f.add(
                SetAttr(v, "buf", Call(realloc, [GetAttr(v, "buf"), Op("*", Op.unary("sizeof", self.inner_type), cap)]))
            )
            assert_func = Variable(FunctionType(UNIT, [INT]), "assert")
            f.add(Run(Call(assert_func, [Op("!=", GetAttr(v, "buf"), Null(self.inner_type))])))
            f.add(SetAttr(v, "cap", cap))
        return f

    def gen_push(self):
        f = Function("vec_push")
        v = f.add_parameter(Pointer(self.struct), "v")
        element = f.add_parameter(self.inner_type, "element")
        with f.if_else(Op("==", GetAttr(v, "len"), GetAttr(v, "cap")))[0]:
            cap = f.declare(USIZE, "cap")
            pos, neg = f.if_else(Op("==", GetAttr(v, "cap"), Int(0)))
            with pos:
                f.add(Assign(cap, Int(8, USIZE)))
            with neg:
                f.add(Assign(cap, Op("<<", GetAttr(v, "cap"), Int(1))))
            f.add(Run(Call(self.reserve, [v, cap])))
        f.add(SetItem(GetAttr(v, "buf"), GetAttr(v, "len"), element))
        f.add(SetAttr(v, "len", Op("+", GetAttr(v, "len"), Int(1, USIZE))))
        return f

    def items(self):
        yield Include("stdlib.h")
        yield Include("assert.h")
        yield self.struct
        yield self.new
        yield self.drop
        yield self.reserve
        yield self.push


def gen_struct(inner_type):
    s = Struct("Vec")
    s.add_field(Pointer(inner_type), "buf")
    s.add_field(USIZE, "len")
    s.add_field(USIZE, "cap")
    return s
