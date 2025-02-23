import tomllib as toml

LINES = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],  # Rows
        [0, 3, 6], [1, 4, 7], [2, 5, 8],  # Columns
        [0, 4, 8], [2, 4, 6]  # Diagonals
    ]


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


# Load configuration from a TOML file
def load_agent_config(agent_id="default"):
    with open("./src/etc/agents_config.toml", "rb") as f:
        config = toml.load(f)

    if agent_id in config:
        return config[agent_id]
    return config["default"]
