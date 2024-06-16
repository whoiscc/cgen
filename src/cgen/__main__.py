from cgen import (
    CHAR,
    INT,
    USIZE,
    Function,
    FunctionType,
    Include,
    Int,
    Pointer,
    SourceCode,
    Variable,
)
from cgen.vec import Vec
from cgen.writer import generate

vec = Vec(INT)

printf = Variable.type_unchecked("printf")
atoi = Variable(FunctionType(INT, [Pointer(CHAR)]), "atoi")

f = Function("main")
f.return_type = INT
argc = f.add_parameter(INT, "argc")
argv = f.add_parameter(("*", ("*", CHAR)), "argv")
n = f.declare(INT, "n")
f.add(n, "=", (atoi, [(argv, "[]", Int(1, USIZE))]))
v = f.declare(vec.struct, "v")
f.add(v, "=", (vec.new, []))
m = f.declare(INT, "m")
f.add(m, "=", Int(0))
with f.loop(m, "<", n):
    f.add(vec.push, [("&", v), m])
    f.add(m, "=", (m, "+", Int(1)))
f.add(vec.drop, [v])
f.ret(Int(0))

source = SourceCode()
source.add(Include("stdio.h"))
source.add(Include("stdlib.h"))
source.add(vec)
source.add(f)
print(generate(source))
