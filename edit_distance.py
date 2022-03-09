from utils import pre_process


def edit_distance(str1, str2):
    n, m = len(str1), len(str2)
    dp = [
        [j if i == 0 else i if j == 0 else 0 for j in range(m + 1)]
        for i in range(n + 1)
    ]

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if str1[i - 1] == str2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = (
                    min(
                        dp[i - 1][j],
                        dp[i][j - 1],
                        dp[i - 1][j - 1],
                    )
                    + 1
                )

    return dp[n][m]


def similarity(str1, str2):
    str1, str2 = pre_process(str1), pre_process(str2)
    div = max(len(str1), len(str2))
    return 1 - edit_distance(str1, str2) / div
