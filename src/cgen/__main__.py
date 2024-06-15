from cgen import CHAR, INT, Function, Pointer
from cgen.writer import string

f = Function("main")
f.return_type = INT
argc = f.add_parameter(INT, "argc")
f.add_parameter(Pointer(Pointer(CHAR)), "argv")
x = f.declare(INT)
f.assign(x, argc)
f.ret(x)
print(string(f))
