from cgen import CHAR, INT, Call, Function, IncludeSystem, Index, Int, Pointer, String, Variable, write_items
from cgen.writer import Writer

printf = Variable.type_unchecked("printf")

f = Function("main")
f.return_type = INT
argc = f.add_parameter(INT, "argc")
argv = f.add_parameter(Pointer(Pointer(CHAR)), "argv")
f.run(Call(printf, [String("executable: %s\n"), Index(argv, Int(0))]))
f.ret(Int(0))

w = Writer()
write_items((IncludeSystem("stdio.h"), f), w)
print(w.buf)
