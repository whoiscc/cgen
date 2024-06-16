from cgen import (
    CHAR,
    INT,
    USIZE,
    Assign,
    Call,
    Function,
    FunctionType,
    GetItem,
    Include,
    Int,
    Op,
    Pointer,
    Run,
    SourceCode,
    Variable,
)
from cgen.vec import Vec
from cgen.writer import string

vec = Vec(INT)

printf = Variable.type_unchecked("printf")
atoi = Variable(FunctionType(INT, [Pointer(CHAR)]), "atoi")

f = Function("main")
f.return_type = INT
argc = f.add_parameter(INT, "argc")
argv = f.add_parameter(Pointer(Pointer(CHAR)), "argv")
v = f.declare(vec.struct, "v")
f.add(Assign(v, Call(vec.new, [])))
n = f.declare(INT, "n")
f.add(Assign(n, Call(atoi, [GetItem(argv, Int(1, USIZE))])))
m = f.declare(INT, "m")
f.add(Assign(m, Int(0)))
with f.loop(Op("<", m, n)):
    f.add(Run(Call(vec.push, [Op.unary("&", v), m])))
    f.add(Assign(m, Op("+", m, Int(1))))
f.add(Run(Call(vec.drop, [v])))
f.ret(Int(0))

source = SourceCode()
source.add(Include("stdio.h"))
source.add(Include("stdlib.h"))
source.add(vec)
source.add(f)
print(string(source))
