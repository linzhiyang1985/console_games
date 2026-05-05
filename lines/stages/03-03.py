from .color import Color
size = (7, 7)
deck = [
    [Color.CYAN, None, None, None, None, None, None],
    [Color.YELLOW, None, None, None, None, None, Color.CYAN],
    [Color.MAGENTA, None, Color.MAGENTA, Color.DARK_YELLOW, Color.GREEN, None, Color.YELLOW],
    [Color.DARK_RED, None, Color.RED, None, None, None, Color.GREEN],
    [Color.BLUE, None, None, None, None, Color.DARK_YELLOW, Color.RED],
    [None, Color.DARK_RED, None, None, None, None, None],
    [None, None, None, None, None, None, Color.BLUE],
]