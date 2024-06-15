from cgen import Function
from cgen.writer import Writer

f = Function("main")
w = Writer()
f.write(w)
print(w.buf)
