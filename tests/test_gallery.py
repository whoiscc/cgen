from cgen import SourceCode
from cgen.gallery import fib
from cgen.writer import generate

fib_source = """\
int fib(int);
int fib(int n) {
  int a;
  int b;
  int m;
  a = 1;
  b = 1;
  m = 2;
  while ((m) < (n)) {
    int t;
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
