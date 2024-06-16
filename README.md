# CGen: <ins>C</ins> Source Code <ins>Gen</ins>erator in Python

Or <ins>C</ins> with <ins>gen</ins>eric programming, depends on your preference.

[![PyPI - Version](https://img.shields.io/pypi/v/cgen.svg)](https://pypi.org/project/cgen)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/cgen.svg)](https://pypi.org/project/cgen)

-----

## Table of Contents

- [Motivation](#motivation)
- [Example](#example)
- [Installation](#installation)
- [License](#license)

## Motivation

The upside of C comparing to C++ is its easiness to reason about, while the downside is its lacking of features. Some of the missing features are able to be handcrafted e.g. emulating inheritance with dynamical sized struct (*flexible array members* in C11), manually rolling out virtual tables for dynamical dispatching, etc. Making such polyfills are (though tedious) still considered feasible. Generic programming, on the other hand, is mostly impractical without any help from compiler or external tools. The macro based generics will never be satisfying respecting productivity.

This project takes charge of the missing generic feature. With CGen you write Python code that generates C code. This extra layer of meta programming enables writing reusable C code with generic parameters as Python functions that can produce C code while generic C parameters become Python function parameters. And as the bonus you get the full power of Python as a constant evaluator. Whatever pre-computation you desired can be easily performed during/guiding the code generation.

CGen is different from all prior projects (to my best knowledge). Instead of simple string level substitution, CGen is aware of syntax tree and sematic. For example, you are passing a Python `Variable` object into every of its use sites instead of its identifier string. The object encapsulation eliminates any necessity of manually maintaining consistency intra/inter code snippets. Furthermore, CGen strongly types its generated code. It performs type checks on all assignments, function calls and expressions, with potential ability to perform type inference for better usability. It's more like a full C frontend backward instead of a simple preprocessor.

## Example

Excerpt from the demo in the current `__main__.py`

```python
vec = Vec(INT)  # instantiate `Vec<int>`

f = Function("main")
# ...
v = f.declare(vec.struct, "v")
f.add(v, "=", (vec.new, []))
with f.loop(m, "<", n):
    f.add(vec.push, [("&", v), m])
    f.add(m, "=", (m, "+", Int(1)))
f.add(vec.drop, [v])
f.ret(Int(0))

source = SourceCode()
source.add(Include("stdio.h"))
source.add(Include("stdlib.h"))
source.add(vec)
source.add(f)
print(generate(source))

```

Running result

```c
#include <stdio.h>
#include <stdlib.h>
struct Vec_int {
  int *buf;
  size_t len;
  size_t cap;
};
struct Vec_int vec_new_int();
void vec_drop_int(struct Vec_int);
void vec_push_int(struct Vec_int *, int);
// ... (other declarations omitted)
int main(int, char **);
struct Vec_int vec_new_int() {
  // ...
}
// ... (other definitions omitted)
int main(int argc, char **argv) {
  // ...
  struct Vec_int v;
  v = vec_new_int();
  while ((m) < (n)) {
    vec_push_int(&(v), m);
    m = (m) + (1);
  }
  vec_drop_int(v);
  return 0;
}
```

## Installation

Set up development with hatch

```console
hatch env create
```

Run the demo above with

```console
hatch run python3 -m cgen
```

## License

`cgen` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
