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
a = fib.declare(INT, 'a')
b = fib.declare(INT, 'b')
m = fib.declare(INT, 'm')
fib.assign(a, Int(1))
fib.assign(b, Int(1))
fib.assign(m, Int(2))
with fib.loop(Op("<", m, n)):
    t = fib.declare(INT, "t")
    fib.assign(t, a)
    fib.assign(a, Op("+", a, b))
    fib.assign(b, t)
    fib.assign(m, Op("+", m, Int(1)))
fib.ret(a)

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
