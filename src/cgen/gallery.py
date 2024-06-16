from cgen import INT, Function, Int


def fib():
    f = Function("fib")
    f.return_type = INT
    n = f.add_parameter(INT, "n")
    a = f.declare(INT, "a")
    b = f.declare(INT, "b")
    m = f.declare(INT, "m")
    f.add(a, "=", Int(1))
    f.add(b, "=", Int(1))
    f.add(m, "=", Int(2))
    with f.loop(m, "<", n):
        t = f.declare(INT, "t")
        f.add(t, "=", a)
        f.add(a, "=", (a, "+", b))
        f.add(b, "=", t)
        f.add(m, "=", (m, "+", Int(1)))
    f.ret(a)
    return f
