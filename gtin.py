from math import ceil


def get_check(code: str):
    check = 0
    multiplier = 1

    for ch in code[:-1]:
        check += int(ch) * multiplier
        multiplier = 3 if multiplier == 1 else 1

    return ceil(check / 10) * 10 - check


def is_valid_gtin(code):
    if type(code) != str:
        code = str(code)
    n = len(code)
    if n != 13 or not code.isnumeric():
        return False

    # India specific
    if code[:3] != "890":
        return False

    check = get_check(code)

    return check == int(code[12])
