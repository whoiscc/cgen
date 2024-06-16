from cgen import SourceCode
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
