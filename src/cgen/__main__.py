from cgen import (
    CHAR,
    INT,
    Call,
    Function,
    FunctionType,
    IncludeSystem,
    Index,
    Int,
    Op,
    Pointer,
    String,
    Variable,
    write_items,
)
from cgen.writer import Writer

fib = Function("fib")
fib.return_type = INT
n = fib.add_parameter(INT, "n")
(pos, neg) = fib.if_else(Op("<=", n, Int(2)))
with pos:
    fib.ret(Int(1))
with neg:
    fib.ret(Op('+', Call(fib, [Op("-", n, Int(1))]), Call(fib, [Op("-", n, Int(2))])))

printf = Variable.type_unchecked("printf")
atoi = Variable(FunctionType(INT, [Pointer(CHAR)]), "atoi")

f = Function("main")
f.return_type = INT
argc = f.add_parameter(INT, "argc")
argv = f.add_parameter(Pointer(Pointer(CHAR)), "argv")
n = f.declare(INT, 'n')
f.assign(n, Call(atoi, [Index(argv, Int(1))]))
f.run(Call(printf, [String("fib(%d) = %d\n"), n, Call(fib, [n])]))
f.ret(Int(0))

w = Writer()
write_items((IncludeSystem("stdio.h"), IncludeSystem("stdlib.h"), fib, f), w)
print(w.buf)
