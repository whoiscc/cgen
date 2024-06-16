from cgen import I32, Function


def fib():
    f = Function("fib")
    f.return_type = I32
    n = f.add_parameter(I32, "n")
    a = f.declare(I32, "a")
    b = f.declare(I32, "b")
    m = f.declare(I32, "m")
    f.add(a, "=", I32(1))
    f.add(b, "=", I32(1))
    f.add(m, "=", I32(2))
    with f.loop(m, "<", n):
        t = f.declare(I32, "t")
        f.add(t, "=", a)
        f.add(a, "=", (a, "+", b))
        f.add(b, "=", t)
        f.add(m, "=", (m, "+", I32(1)))
    f.ret(a)
    return f
