from cgen import INT, Function, Int, Op


def fib():
    f = Function("fib")
    f.return_type = INT
    n = f.add_parameter(INT, "n")
    a = f.declare(INT, "a")
    b = f.declare(INT, "b")
    m = f.declare(INT, "m")
    f.assign(a, Int(1))
    f.assign(b, Int(1))
    f.assign(m, Int(2))
    with f.loop(Op("<", m, n)):
        t = f.declare(INT, "t")
        f.assign(t, a)
        f.assign(a, Op("+", a, b))
        f.assign(b, t)
        f.assign(m, Op("+", m, Int(1)))
    f.ret(a)
