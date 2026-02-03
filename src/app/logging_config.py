"""
Logging configuration with colored output.
"""

import functools
import logging
import re
import sys
from pathlib import Path

import colorlog


@functools.lru_cache(maxsize=1)
def get_color_table() -> dict[str, str]:
    """Build a mapping of color names to ANSI templates."""
    # new Define the color codes for different colors
    color_numbers = {
        "red": 91,
        "green": 92,
        "yellow": 93,
        "blue": 94,
        "purple": 95,
        "cyan": 96,
        "white": 97,
        "black": 98,
        "grey": 99,
        "gray": 100,
        "underline": 4,
        "invert": 7,
        "blink": 5,
        "lightblack": 108,
        "bold": 1,
    }
    data = {x: f"\033[{v}m%s\033[00m" for x, v in color_numbers.items()}

    # Add light versions of the colors to the color table
    for color in ["purple", "yellow", "blue", "red", "green", "cyan", "gray"]:
        data[f"light{color}"] = data.get(color, 0)

    # Add some additional color names to the color table
    data["aqua"] = data.get("cyan", 0)
    data["lightaqua"] = data.get("cyan", 0)
    data["lightgrey"] = data.get("gray", 0)
    data["grey"] = data.get("gray", 0)
    data["lightwhite"] = data.get("gray", 0)
    data["light"] = 0

    return data


def format_colored_text(textm: str) -> str:
    """
    Prints the given text with color formatting.

    The text can contain color tags like '<<color>>' where 'color' is the name of the color.
    The color will be applied to the text that follows the tag, until the end of the string or until a '<<default>>' tag is found.

    :param textm: The text to print. Can contain color tags.
    """
    color_table = get_color_table()
    # Define a pattern for color tags
    _color_pat = r"((:?\w+|previous);?(:?\w+|previous)?)"
    # Compile a regex for color tags
    colorTagR = re.compile(rf"(?:\03{{|<<){_color_pat}(?:}}|>>)")

    # Initialize a stack for color tags
    color_stack = ["default"]

    # If the input is not a string, print it as is and return
    if not isinstance(textm, str):
        return textm

    # If the text does not contain any color tags, print it as is and return
    if "\03" not in textm and "<<" not in textm:
        return textm

    # Split the text into parts based on the color tags
    text_parts = colorTagR.split(textm) + ["default"]

    # Enumerate the parts for processing
    enu = enumerate(zip(text_parts[::4], text_parts[1::4], strict=False))

    # Initialize the string to be printed
    toprint = ""

    # Process each part of the text
    for _, (text, next_color) in enu:
        # Get the current color from the color stack
        # print(f"i: {index}, {text=}, {next_color=}")
        current_color = color_stack[-1]

        # If the next color is 'previous', pop the color stack to get the previous color
        if next_color == "previous":
            if len(color_stack) > 1:  # keep the last element in the stack
                color_stack.pop()
            next_color = color_stack[-1]
        else:
            # If the next color is not 'previous', add it to the color stack
            color_stack.append(next_color)

        # Get the color code for the current color
        cc = color_table.get(current_color, "")

        # If the color code is not empty, apply it to the text
        if cc:
            text = cc % text

        # Add the colored text to the string to be printed
        toprint += text

    # Print the final colored text
    return toprint


def wrap_color_messages(format_message):
    """Wrap the color messages to include additional context."""

    def wrapper(record):
        # Add custom attributes or modify the record as needed
        return format_colored_text(format_message(record))

    return wrapper


def prepare_log_file(log_file, project_logger):
    log_file = Path(log_file).expanduser()
    try:
        log_file.parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        project_logger.error(f"Failed to create log directory: {e}")
        log_file = None
    return log_file


def setup_logging(
    level: str = "WARNING",
    name: str = "app",
    log_file: str | None = None,
) -> None:
    """
    Configure logging for the entire project namespace only.
    """
    project_logger = logging.getLogger(name)

    if project_logger.handlers:
        return

    numeric_level = getattr(logging, level.upper(), logging.INFO) if isinstance(level, str) else level
    project_logger.setLevel(numeric_level)
    project_logger.propagate = False

    formatter = colorlog.ColoredFormatter(
        fmt="%(filename)s:%(lineno)s %(funcName)s() - %(log_color)s%(levelname)-s %(reset)s%(message)s",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red,bg_white",
        },
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    # message colorizer
    formatter.formatMessage = wrap_color_messages(formatter.formatMessage)

    console_handler.setLevel(numeric_level)

    project_logger.addHandler(console_handler)

    if log_file:
        log_file = prepare_log_file(log_file, project_logger)
        setup_file_handler(project_logger, log_file, numeric_level)

        # Separate error log file
        log_file2 = log_file.with_suffix(".err")
        setup_file_handler(project_logger, log_file2, logging.WARNING)


def setup_file_handler(project_logger, log_file, level):
    file_formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)-8s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(level)
    project_logger.addHandler(file_handler)
