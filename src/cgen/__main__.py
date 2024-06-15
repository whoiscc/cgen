from cgen import INT, CHAR, Function, Pointer
from cgen.writer import Writer

f = Function("main")
f.return_type = INT
f.add_parameter(INT, "argc")
f.add_parameter(Pointer(Pointer(CHAR)), "argv")
f.declare(INT)
w = Writer()
f.write(w)
print(w.buf)
