def pre_process(s):
    if type(s) != str or len(s) == 0:
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
