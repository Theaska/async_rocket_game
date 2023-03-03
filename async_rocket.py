import asyncio
import curses
from itertools import cycle
import random
import time


SPACE_KEY_CODE = 32
LEFT_KEY_CODE = 260
RIGHT_KEY_CODE = 261
UP_KEY_CODE = 259
DOWN_KEY_CODE = 258

SHIP_SPEED = 2
STARS_COUNT = 100
ANIMATION_SPEED = 0.1
STARS_SYMBOLS = '+*.:'
BORDER_SIZE = 1


FRAME_1 = 'frames/rocket_frame_1.txt'
FRAME_2 = 'frames/rocket_frame_2.txt'


def read_controls(canvas):
    """Read keys pressed and returns tuple witl controls state."""
    rows_direction = columns_direction = 0
    space_pressed = False

    while True:
        pressed_key_code = canvas.getch()

        if pressed_key_code == -1:
            # https://docs.python.org/3/library/curses.html#curses.window.getch
            break

        if pressed_key_code == UP_KEY_CODE:
            rows_direction = -1

        if pressed_key_code == DOWN_KEY_CODE:
            rows_direction = 1

        if pressed_key_code == RIGHT_KEY_CODE:
            columns_direction = 1

        if pressed_key_code == LEFT_KEY_CODE:
            columns_direction = -1

        if pressed_key_code == SPACE_KEY_CODE:
            space_pressed = True

    return rows_direction, columns_direction, space_pressed


def draw_frame(canvas, start_row, start_column, text, negative=False):
    """Draw multiline text fragment on canvas,
    erase text instead of drawing if negative=True is specified."""
    rows_number, columns_number = canvas.getmaxyx()

    for row, line in enumerate(text.splitlines(), round(start_row)):
        if row < 0:
            continue

        if row >= rows_number:
            break

        for column, symbol in enumerate(line, round(start_column)):
            if column < 0:
                continue

            if column >= columns_number:
                break

            if symbol == ' ':
                continue

            # Check that current position it is not
            # in a lower right corner of the window
            # Curses will raise exception in that case. Don`t ask why…
            # https://docs.python.org/3/library/curses.html#curses.window.addch
            if row == rows_number - 1 and column == columns_number - 1:
                continue

            symbol = symbol if not negative else ' '
            canvas.addch(row, column, symbol)


def get_frame_size(text):
    """Calculate size of multiline text fragment,
    return pair — number of rows and colums."""

    lines = text.splitlines()
    rows = len(lines)
    columns = max([len(line) for line in lines])
    return rows, columns


async def fire(
    canvas,
    start_row,
    start_column,
    rows_speed=-0.3,
    columns_speed=0
):
    """Display animation of gun shot, direction and speed can be specified."""

    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await asyncio.sleep(0)

    canvas.addstr(round(row), round(column), 'O')
    await asyncio.sleep(0)
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed


async def blink(canvas, row, column, offset_tics=10, symbol='*'):
    while True:
        for _ in range(offset_tics):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol, curses.A_DIM)
        for _ in range(20):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        for _ in range(3):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        for _ in range(5):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        for _ in range(3):
            await asyncio.sleep(0)


def get_rand_point(from_, to_):
    """Return random point from [`from_`; `to_`)"""
    return random.randint(from_, to_)


def get_frames(*frames_paths):
    frames = []

    for path in frames_paths:
        with open(path) as file:
            frames.append(file.read())

    return frames


def get_pos(max_size, current_pos, delta):
    return max(0, min(max_size, current_pos + delta))


async def animate_spaceship(canvas, rows_size, cols_size):
    frame_1, frame_2 = get_frames(FRAME_1, FRAME_2)
    frames_iterator = cycle((frame_1, frame_1, frame_2, frame_2))
    x_pos = 0
    y_pos = 0
    for frame in frames_iterator:
        delta_x, delta_y, _ = read_controls(canvas)
        frame_width, frame_height = get_frame_size(frame)
        x_pos = get_pos(rows_size - frame_width, x_pos, delta_x * SHIP_SPEED)
        y_pos = get_pos(cols_size - frame_height, y_pos, delta_y * SHIP_SPEED)
        draw_frame(canvas, x_pos, y_pos, frame, negative=False)
        await asyncio.sleep(0)
        draw_frame(canvas, x_pos, y_pos, frame, negative=True)


def draw(canvas):
    # get opened console size
    width_window, height_window = canvas.getmaxyx()
    canvas.nodelay(True)
    curses.curs_set(False)
    coroutines = [
        blink(
            canvas,
            get_rand_point(BORDER_SIZE, width_window - BORDER_SIZE),
            get_rand_point(BORDER_SIZE, height_window - BORDER_SIZE),
            random.randint(0, 10),
            random.choice(STARS_SYMBOLS)
        ) for _ in range(STARS_COUNT)
    ]
    coroutines.append(fire(canvas, width_window // 2, height_window // 2))
    coroutines.append(animate_spaceship(canvas, width_window, height_window))
    while True:
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)
        canvas.refresh()
        time.sleep(ANIMATION_SPEED)


def main():
    curses.wrapper(draw)


if __name__ == '__main__':
    main()
