from cgen import I32, Function, Int


def fib():
    f = Function("fib")
    f.return_type = I32
    n = f.add_parameter(I32, "n")
    a = f.declare(I32, "a")
    b = f.declare(I32, "b")
    m = f.declare(I32, "m")
    f.add(a, "=", Int(1))
    f.add(b, "=", Int(1))
    f.add(m, "=", Int(2))
    with f.loop(m, "<", n):
        t = f.declare(I32, "t")
        f.add(t, "=", a)
        f.add(a, "=", (a, "+", b))
        f.add(b, "=", t)
        f.add(m, "=", (m, "+", Int(1)))
    f.ret(a)
    return f
