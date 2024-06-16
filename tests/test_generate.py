from cgen import I32, Function, SourceCode
from cgen.gallery import fib
from cgen.writer import generate

fib_source = """\
int32_t fib(int32_t);
int32_t fib(int32_t n) {
  int32_t a;
  int32_t b;
  int32_t m;
  a = 1;
  b = 1;
  m = 2;
  while ((m) < (n)) {
    int32_t t;
    t = a;
    a = (a) + (b);
    b = t;
    m = (m) + (1);
  }
  return a;
}"""


def test_fib():
    s = SourceCode()
    s.add(fib())
    g = generate(s)
    assert g == fib_source


def test_declare():
    f = Function("test")
    x = f.declare(I32)
    assert x.name == "x"
    x = f.declare(I32)
    assert x.name == "x2"
    x = f.declare(I32)
    assert x.name == "x3"
    a = f.declare(I32, "a")
    assert a.name == "a"
    a = f.declare(I32, "a")
    assert a.name == "a2"
    a = f.declare(I32, "a")
    assert a.name == "a3"
