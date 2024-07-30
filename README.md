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
- [Wish List](#wish-list)

## Motivation

CGen is a framework for projects demanding "C as human maintainable assembly".

(Ok I know assembly is human maintainable compared to machine code but you probably get the point.)

The C source code written for such demands does not require high level abstractions; to the opposite those features may be even intentionally avoided to keep the code faithfully reflecting hardware behaviors for e.g. reasoning about the performance characteristics, or just simply making it absolutely clear what's going on at the lowest level. 

C already saves programmer from tedious mechanical tasks like register allocation and offset calculation, but it is short for one key feature that occasionally becomes the pain point: code generation/duplication. The low level nature of C renders more painful cases, including:
* Loop unrolling
* State machine with explicit `goto` control flow
* Repeated processing logic for multiple data types i.e. generic programming

The builtin mechanism for code generation/expansion in C i.e. macro is unsatisfying; an obvious fact that is needless to explain. People roll out code generation scripts as their own macro solutions, and Python has been a popular choice for writing such scripts. CGen then serves as a framework for writing scripts and a collection of generally useful scripts.

CGen is different from all prior arts (to my best knowledge). Instead of simple string level substitution, CGen is aware of syntax tree and sematic. For example, you are passing a Python `Variable` object into every of its use sites instead of its identifier string. The object encapsulation eliminates any necessity of manually maintaining consistency intra/inter code snippets. Furthermore, CGen strongly types its generated code. It performs type checks on all assignments, function calls and expressions, with potential ability to perform type inference for better usability. It's more like a full C frontend backward instead of a simple preprocessor.

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

Manually unrolling the runtime loop into a compile time loop
```diff
v = f.declare(vec.struct, "v")
f.add(v, "=", (vec.new, []))
# ...
-m = f.declare(I32, "m")
-f.add(m, "=", Int(0))
-with f.loop(m, "<", n):
-    f.add(vec.push, [("&", v), m])
-    f.add(m, "=", (m, "+", Int(1)))
+for i in range(100):
+    m = Int(i, I32)
+    with f.when(m, "<", n):
+        f.add(vec.push, [("&", v), m])
f.add(vec.drop, [v])
f.ret(Int(0))
```

Generated
```c
  if ((0) < (n)) {
    vec_push__int32_t(&(v), 0);
  } else {
    ;
  }
  if ((1) < (n)) {
    vec_push__int32_t(&(v), 1);
  } else {
    ;
  }
  if ((2) < (n)) {
    vec_push__int32_t(&(v), 2);
  } else {
    ;
  }
  // ...
```

## Installation

Set up development environment with Hatch

```console
hatch env create
```

Run the demo above with

```console
hatch run python3 -m cgen
```

Compile and run the generated code

```console
hatch run python3 -m cgen | cc -x c -
./a.out 100
```

## License

`cgen` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.

## Wish List

* Code generation for regular expression and benchmark against Python's `re` module.
