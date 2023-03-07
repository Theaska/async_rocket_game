import asyncio
import random


async def sleep(tics=1):
    for _ in range(tics):
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
