import colorama

# Some ANSI escape sequences for colours and effects
BLACK = '\u001b[30m'
RED = '\u001b[31m'
GREEN = '\u001b[32m'
YELLOW = '\u001b[33m'
BLUE = '\u001b[34m'
MAGENTA = '\u001b[35m'
CYAN = '\u001b[36m'
WHITE = '\u001b[37m'
RESET = '\u001b[0m'
BOLD = '\u001b[1m'
UNDERLINE = '\u001b[4m'
REVERSE = '\u001b[7m'


def cprint(text: str, *effects: str, return_message: bool) -> str:
    """
   Prints or returns the given text string with specified color and other visual effects
   by leveraging the ANSI escape sequences.

   This function creates a stylized output by concatenating the desired visual
   effects, the input text, and the reset sequence, and then either prints or returns this
   resulting string depending upon the `return_message` flag. Before and after printing, the function initializes and
   de-initializes the colorama library, respectively, to ensure the proper
   functioning of the color and style sequences.

   :param text: A string representing the text to be printed.

   :param effects: A variable number of strings each representing a desired
   visual effect. These effects should correspond to the ANSI escape sequences,
   and can include color sequences (like RED, BLUE, etc.), and others (like
   BOLD, UNDERLINE, etc.). The function concatenates these effects in the order
   they are provided, and applies them to the printed text.

   :param return_message: A boolean indicating whether to return the formatted text (True)
   or to print it (False).

   If `return_message` is True, the function will return the stylized text as a string.
   If it is False, the function will print the stylized text and return None.

   Example usage:

   ```
   colour_print("Hello, world!", RED, BOLD)
   ```
   This example prints the text "Hello, world!" in bold red color.
   """
    effect_string = "".join(effects)
    output_string = "{0}{1}{2}".format(effect_string, text, RESET)
    colorama.init()
    if return_message:
        return output_string
    else:
        print(output_string)
    colorama.deinit()
