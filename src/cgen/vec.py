from cgen import (
    UNIT,
    USIZE,
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
    Struct,
    Variable,
)


class Vec:
    def __init__(self, inner_type):
        self.inner_type = inner_type
        self.struct = gen_struct(self.inner_type)
        self.new = self.gen_new()
        self.drop = self.gen_drop()

    def gen_new(self):
        f = Function("vec_new")
        f.return_type = self.struct
        v = f.declare(self.struct, "v")
        # malloc = Variable(FunctionType(Pointer(self.inner_type), [USIZE]), "malloc")
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

    def items(self):
        yield Include("stdlib.h")
        yield self.struct
        yield self.new
        yield self.drop

def gen_struct(inner_type):
    s = Struct("Vec")
    s.add_field(Pointer(inner_type), "buf")
    s.add_field(USIZE, "len")
    s.add_field(USIZE, "cap")
    return s

