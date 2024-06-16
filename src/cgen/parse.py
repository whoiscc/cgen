def parse(tokens):
    from cgen import Assign, Call, GetAttr, GetItem, Op, SetAttr, SetItem

    if not isinstance(tokens, tuple):
        return tokens
    match tokens:
        case (token,):
            return token
        case (
            left,
            "+"
            | "-"
            | "*"
            | "/"
            | "%"
            | "<<"
            | ">>"
            | "&"
            | "|"
            | "^"
            | "&&"
            | "||"
            | "=="
            | "!="
            | ">"
            | ">="
            | "<"
            | "<=" as op,
            right,
        ):
            return Op(op, parse(left), parse(right))
        case "&" | "sizeof" | "~" | "!" as op, right:
            return Op.unary(op, parse(right))
        case callee, list([*arguments]):
            return Call(parse(callee), [parse(argument) for argument in arguments])
        case struct, dot_attr if dot_attr.startswith("."):
            return GetAttr(parse(struct), dot_attr.removeprefix("."))
        case array, "[]", position:
            return GetItem(parse(array), parse(position))
        case place, "=", source:
            return Assign(parse(place), parse(source))
        case struct, dot_attr, "=", source if dot_attr.startswith("."):
            return SetAttr(parse(struct), dot_attr.removeprefix("."), parse(source))
        case array, "[]", position, "=", source:
            return SetItem(parse(array), parse(position), parse(source))
        case _:
            raise ValueError(tokens)


def parse_type(tokens):
    from cgen import Array, FunctionType, Pointer

    if not isinstance(tokens, tuple):
        return tokens
    match tokens:
        case (token,):
            return token
        # using Rust order here which is much more obvious then C
        case "*", inner:
            return Pointer(parse_type(inner))
        case inner, "[]", length:
            return Array(parse_type(inner), length)
        case list([*parameter_types]), "->", return_type:
            return FunctionType(
                parse_type(return_type), [parse_type(parameter_type) for parameter_type in parameter_types]
            )
        case _:
            raise ValueError(tokens)
