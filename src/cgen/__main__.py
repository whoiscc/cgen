from cgen import (
    CHAR,
    INT,
    Assign,
    Call,
    Function,
    FunctionType,
    Include,
    Int,
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
f.add(Run(Call(vec.drop, [v])))
f.ret(Int(0))

source = SourceCode()
source.add(Include("stdio.h"))
source.add(vec)
source.add(f)
print(string(source))
