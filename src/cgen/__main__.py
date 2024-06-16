from cgen import (
    CHAR,
    INT,
    Function,
    FunctionType,
    Include,
    Int,
    Pointer,
    Variable,
    write_items,
)
from cgen.vec import Vec
from cgen.writer import Writer

vec = Vec(INT)

printf = Variable.type_unchecked("printf")
atoi = Variable(FunctionType(INT, [Pointer(CHAR)]), "atoi")

f = Function("main")
f.return_type = INT
argc = f.add_parameter(INT, "argc")
argv = f.add_parameter(Pointer(Pointer(CHAR)), "argv")
f.ret(Int(0))

w = Writer()
write_items((Include("stdio.h"), Include("stdlib.h"), *list(vec.items()), f), w)
print(w.buf)
