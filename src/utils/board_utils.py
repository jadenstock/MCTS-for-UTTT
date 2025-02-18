def three_in_a_row(arr):
    """Return "x" if "x" has three in a row, return "o" if "o" has a three in a row, else ""
    Cells are arranged as:
        0 | 1 | 2
        ---------
        3 | 4 | 5
        ---------
        6 | 7 | 8
    """
    if (arr[0] == arr[1] == arr[2]) or (arr[0] == arr[3] == arr[6]) or (arr[0] == arr[4] == arr[8]):
        if arr[0] != "":
            return arr[0]

    if (arr[1] == arr[4] == arr[7]) or (arr[3] == arr[4] == arr[5]) or (arr[2] == arr[4] == arr[6]):
        if arr[4] != "":
            return arr[4]

    if (arr[6] == arr[7] == arr[8]) or (arr[2] == arr[5] == arr[8]):
        if arr[8] != "":
            return arr[8]

    return ""