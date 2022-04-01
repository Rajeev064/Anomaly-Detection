from math import ceil
import pandas as pd
import editdistance

"""
    Contains helper functions used by various modules.
"""


def pre_process(s):
    if not s:
        return

    if type(s) != str:
        s = str(s)

    if len(s) == 0:
        return ""

    s = s.lower()
    s = [part.strip() for part in s.split(" ") if len(part.strip()) > 0]
    return " ".join(s)


def closest(val, iter, sim_fn):
    closest_val = None
    max_score = 0

    for item in iter:
        score = sim_fn(val, item)
        if closest_val is None or score > max_score:
            closest_val = item
            max_score = score

    return [closest_val, max_score]


def closest_number(str):
    try:
        return float(str)
    except ValueError as err:
        pass

    replace_char = "5"
    saw_dot = False
    chars = []
    for ch in str:
        if ch.isdigit() or (ch == "." and not saw_dot):
            chars.append(ch)
            if ch == ".":
                saw_dot = True
        else:
            chars.append(replace_char)

    return float("".join(chars))


def std_dist(val, range):
    return abs(val - range["mean"]) / range["std"]


def std_similarity(val, range):
    if val < range["min"] or val > range["max"]:
        return 0

    div = (
        std_dist(range["min"], range)
        if val <= range["mean"]
        else std_dist(range["max"], range)
    )

    return 1 - (std_dist(val, range) / div)


def get_gtin_check(code: str):
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

    check = get_gtin_check(code)

    return check == int(code[12])


def get_numeric_range(series: pd.Series):
    return {
        "std": series.std(),
        "mean": series.mean(),
        "median": series.median(),
        "min": series.min(),
        "max": series.max(),
    }


def str_similarity(str1, str2):
    if type(str1) != str:
        str1 = str(str1)

    if type(str2) != str:
        str2 = str(str2)

    str1, str2 = pre_process(str1), pre_process(str2)
    div = max(len(str1), len(str2))
    return 1 - editdistance.eval(str1, str2) / div
