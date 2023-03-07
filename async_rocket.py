import logger
import curses
from itertools import cycle
import random
import time
import datetime
import os

from utils import sleep, get_frames, get_rand_point
from physics import update_speed
from curses_tools import draw_frame, get_frame_size
from obstacles import Obstacle
from exposion import explode
from game_scenario import get_garbage_delay_tics, PHRASES


file_logger = logger.FileLogger('async_rocket', 'log.txt')
logger = file_logger.get_logger()


SPACE_KEY_CODE = 32
LEFT_KEY_CODE = 260
RIGHT_KEY_CODE = 261
UP_KEY_CODE = 259
DOWN_KEY_CODE = 258

SHIP_SPEED = 2
STARS_COUNT = 100
ANIMATION_SPEED = 0.1
STARS_SYMBOLS = '+*.:'
BORDER_SIZE = 2

YEAR = 1957
YEAR_CHANGE_TICS = 10
CAN_FIRE_YEAR = 1960


FRAMES_PATH = 'frames/'
ROCKET_FRAME_1 = os.path.join(FRAMES_PATH, 'rocket_frame_1.txt')
ROCKET_FRAME_2 = os.path.join(FRAMES_PATH, 'rocket_frame_2.txt')

DUCK_FRAME = os.path.join(FRAMES_PATH, 'duck.txt')
HUBBLE_FRAME = os.path.join(FRAMES_PATH, 'hubble.txt')
LAMP_FRAME = os.path.join(FRAMES_PATH, 'lamp.txt')
TRASH_LARGE_FRAME = os.path.join(FRAMES_PATH, 'trash_large.txt')
TRASH_SMALL_FRAME = os.path.join(FRAMES_PATH, 'trash_small.txt')
TRASH_XL_FRAME = os.path.join(FRAMES_PATH, 'trash_xl.txt')

GAME_OVER_FRAME = os.path.join(FRAMES_PATH, 'game_over.txt')

TRASH_FRAMES_PATHS = [
    DUCK_FRAME, HUBBLE_FRAME, LAMP_FRAME,
    TRASH_LARGE_FRAME, TRASH_SMALL_FRAME, TRASH_XL_FRAME
]

coroutines = []
obstacles = []
obstacles_in_last_collisions = []

ROW_SPEED = 0
COLUMN_SPEED = 0


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


async def fly_garbage(canvas, column, garbage_frame, speed=0.5):
    """Animate garbage, flying from top to bottom.
    Сolumn position will stay same, as specified on start."""
    rows_number, columns_number = canvas.getmaxyx()

    column = max(column, 0)
    column = min(column, columns_number - 1)

    row = 0

    garbage_col_size, garbage_row_size = get_frame_size(garbage_frame)
    obstacle = Obstacle(row, column, garbage_col_size, garbage_row_size)
    obstacles.append(obstacle)
    while row < rows_number:
        draw_frame(canvas, row, column, garbage_frame)
        await sleep()
        draw_frame(canvas, row, column, garbage_frame, negative=True)
        row += speed
        obstacle.row = row
        obstacle.column = column

        for obstacle_collision in obstacles_in_last_collisions:
            if obstacle_collision.has_collision(row, column):
                await explode(canvas, row, column)
                return


async def show_game_over(canvas):
    width_window, height_window = canvas.getmaxyx()
    frame, *_ = get_frames(GAME_OVER_FRAME)
    frame_rows_size, frame_cols_size = get_frame_size(frame)
    while True:
        await sleep()
        draw_frame(
            canvas,
            (width_window - frame_rows_size) / 2,
            (height_window - frame_cols_size) / 2,
            frame
        )


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
    await sleep()

    canvas.addstr(round(row), round(column), 'O')
    await sleep()
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await sleep()
        canvas.addstr(round(row), round(column), ' ')
        for index, obstacle in enumerate(obstacles.copy()):
            if obstacle.has_collision(row, column):
                obstacles_in_last_collisions.append(obstacles[index])
                del obstacles[index]
                return
        row += rows_speed
        column += columns_speed


async def blink(canvas, row, column, offset_tics=10, symbol='*'):
    while True:
        await sleep(offset_tics)

        canvas.addstr(row, column, symbol, curses.A_DIM)
        await sleep(20)

        canvas.addstr(row, column, symbol)
        await sleep(3)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await sleep(5)

        canvas.addstr(row, column, symbol)
        await sleep(3)


def get_pos(max_size, current_pos, delta):
    return max(0, min(max_size, current_pos + delta))


async def animate_spaceship(canvas, rows_size, cols_size):
    row_speed = ROW_SPEED
    column_speed = COLUMN_SPEED
    frame_1, frame_2 = get_frames(ROCKET_FRAME_1, ROCKET_FRAME_2)
    frames_iterator = cycle((frame_1, frame_1, frame_2, frame_2))
    x_pos = rows_size
    y_pos = cols_size // 2
    for frame in frames_iterator:
        delta_x, delta_y, space_pressed = read_controls(canvas)
        frame_width, frame_height = get_frame_size(frame)
        row_speed, column_speed = update_speed(
            row_speed,
            column_speed,
            delta_x,
            delta_y
        )
        x_pos = get_pos(
            rows_size - frame_width,
            x_pos,
            delta_x * SHIP_SPEED + row_speed
        )
        y_pos = get_pos(
            cols_size - frame_height,
            y_pos,
            delta_y * SHIP_SPEED + column_speed
        )
        draw_frame(canvas, x_pos, y_pos, frame, negative=False)
        await sleep()
        draw_frame(canvas, x_pos, y_pos, frame, negative=True)

        if space_pressed and YEAR >= CAN_FIRE_YEAR:
            coroutines.append(fire(canvas, x_pos, y_pos))

        for obstacle in obstacles:
            if obstacle.has_collision(x_pos, y_pos):
                await show_game_over(canvas)


async def fill_orbit_with_garbage(canvas, height_window):
    frames = get_frames(*TRASH_FRAMES_PATHS)
    while True:
        delay = get_garbage_delay_tics(YEAR)
        if delay is None:
            await sleep()
        else:
            await sleep(delay)
            x_pos = get_rand_point(BORDER_SIZE, height_window - BORDER_SIZE)
            coroutines.append(
                fly_garbage(
                    canvas,
                    x_pos,
                    random.sample(frames, 1)[0]
                )
            )


async def increase_year():
    global YEAR
    while YEAR <= datetime.date.today().year:
        await sleep(YEAR_CHANGE_TICS)
        YEAR += 1


def fill_orbit_with_stars(
    canvas,
    width_window,
    height_window,
    stars_count=STARS_COUNT
):
    coroutines.extend([
        blink(
            canvas,
            get_rand_point(BORDER_SIZE, width_window - BORDER_SIZE),
            get_rand_point(BORDER_SIZE, height_window - BORDER_SIZE),
            random.randint(0, 10),
            random.choice(STARS_SYMBOLS)
        ) for _ in range(stars_count)
    ])


async def show_year(canvas, pos_x, pos_y):
    while True:
        await sleep()
        draw_frame(canvas, pos_x, pos_y, str(YEAR))


async def show_scenario_information(canvas, pos_x, pos_y):
    while True:
        await sleep()
        if YEAR in PHRASES:
            phrase = PHRASES[YEAR]
            draw_frame(canvas, pos_x, pos_y, phrase)
            await sleep(YEAR_CHANGE_TICS)
            draw_frame(canvas, pos_x, pos_y, phrase, negative=True)


def draw(canvas):
    # get opened console size
    show_year_pos_x, show_year_pos_y = BORDER_SIZE, BORDER_SIZE
    year_len = 4
    curses.window.derwin(
        canvas, year_len, BORDER_SIZE, show_year_pos_y, show_year_pos_x
    )
    width_window, height_window = canvas.getmaxyx()
    canvas.nodelay(True)
    curses.curs_set(False)
    fill_orbit_garbage = fill_orbit_with_garbage(canvas, height_window)
    fill_orbit_with_stars(canvas, width_window, height_window)

    coroutines.append(animate_spaceship(canvas, width_window, height_window))
    coroutines.append(increase_year())
    coroutines.append(show_year(canvas, show_year_pos_y, show_year_pos_x))
    coroutines.append(fill_orbit_garbage)
    coroutines.append(
        show_scenario_information(
            canvas, show_year_pos_y, show_year_pos_x + year_len + BORDER_SIZE
        )
    )
    while True:
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)
        canvas.refresh()
        time.sleep(ANIMATION_SPEED)


def main():
    logger.info('Start application')
    curses.wrapper(draw)
    logger.info('Finish application')


if __name__ == '__main__':
    main()
