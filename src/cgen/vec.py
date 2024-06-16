from cgen import USIZE, Function, Include, Int, Null, Pointer, SetAttr, Struct


class Vec:
    def __init__(self, inner_type):
        self.inner_type = inner_type
        self.struct = gen_struct(self.inner_type)
        self.new = self.gen_new()

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

    def items(self):
        yield Include("stdlib.h")
        yield self.struct
        yield self.new

def gen_struct(inner_type):
    s = Struct("Vec")
    s.add_field(Pointer(inner_type), "buf")
    s.add_field(USIZE, "len")
    s.add_field(USIZE, "cap")
    return s

