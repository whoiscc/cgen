from cgen import (
    INT,
    UNIT,
    USIZE,
    Function,
    Include,
    Int,
    Null,
    Pointer,
    Struct,
    Variable,
)
from cgen.writer import mangled


def gen_struct(inner_type):
    s = Struct(f"Vec__{mangled(inner_type)}")
    s.add_field(Pointer(inner_type), "buf")
    s.add_field(USIZE, "len")
    s.add_field(USIZE, "cap")
    return s


class Vec:
    def __init__(self, inner_type):
        self.inner_type = inner_type
        self.struct = gen_struct(self.inner_type)
        self.new = self.gen_new()
        self.drop = self.gen_drop()
        self.reserve = self.gen_reserve()
        self.push = self.gen_push()

    def gen_new(self):
        f = Function(f"vec_new__{mangled(self.inner_type)}")
        f.return_type = self.struct
        v = f.declare(self.struct, "v")
        f.add(v, ".buf", "=", Null(self.inner_type))
        f.add(v, ".len", "=", Int(0, USIZE))
        f.add(v, ".cap", "=", Int(0, USIZE))
        f.ret(v)
        return f

    def gen_drop(self):
        f = Function(f"vec_drop__{mangled(self.inner_type)}")
        v = f.add_parameter(self.struct, "v")
        with f.when((v, ".cap"), "!=", Int(0, USIZE)):
            free = Variable(([("*", self.inner_type)], "->", UNIT), "free")
            f.add(free, [(v, ".buf")])
            # not necessary if guarantee no double drop
            f.add(v, ".len", "=", Int(0, USIZE))
            f.add(v, ".cap", "=", Int(0, USIZE))
        return f

    def gen_reserve(self):
        f = Function(f"vec_reserve__{mangled(self.inner_type)}")
        v = f.add_parameter(("*", self.struct), "v")
        cap = f.add_parameter(USIZE, "cap")
        # consider not silently fail the opposite?
        with f.when(cap, ">", (v, ".cap")):
            realloc = Variable(([("*", self.inner_type), USIZE], "->", ("*", self.inner_type)), "realloc")
            f.add(v, ".buf", "=", (realloc, [(v, ".buf"), (("sizeof", self.inner_type), "*", cap)]))
            assert_func = Variable(([INT], "->", UNIT), "assert")
            f.add(assert_func, [((v, ".buf"), "!=", Null(self.inner_type))])
            f.add(v, ".cap", "=", cap)
        return f

    def gen_push(self):
        f = Function(f"vec_push__{mangled(self.inner_type)}")
        v = f.add_parameter(("*", self.struct), "v")
        element = f.add_parameter(self.inner_type, "element")
        with f.when((v, ".len"), "==", (v, ".cap")):
            cap = f.declare(USIZE, "cap")
            pos, neg = f.if_else((v, ".cap"), "==", Int(0, USIZE))
            with pos:
                f.add(cap, "=", Int(8, USIZE))
            with neg:
                f.add(cap, "=", ((v, ".cap"), "*", Int(2, USIZE)))
            f.add(self.reserve, [v, cap])
        f.add((v, ".buf"), "[]", (v, ".len"), "=", element)
        f.add(v, ".len", "=", ((v, ".len"), "+", Int(1, USIZE)))
        return f

    def items(self):
        yield Include("stdlib.h")
        yield Include("assert.h")
        yield self.struct
        yield self.new
        yield self.drop
        yield self.reserve
        yield self.push
