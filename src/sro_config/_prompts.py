"""
Small helpers for interactive input() prompts.

Each one loops - printing a message and re-asking the same question - until the answer
is actually valid, instead of letting a stray ValueError from a bad character propagate
up and crash the whole interactive session.
"""


def prompt_yes_no(prompt):
    """Loops until the user answers Y or N (case-insensitive); returns True/False."""
    while True:
        answer = input(prompt).strip().upper()
        if answer == "Y":
            return True
        if answer == "N":
            return False
        print(f"Invalid input - '{answer}' isn't Y or N. Please try again.\n")


def prompt_int(prompt):
    """Loops until the user enters a whole number; returns it as an int."""
    while True:
        answer = input(prompt).strip()
        try:
            return int(answer)
        except ValueError:
            print(f"Invalid input - '{answer}' is not a whole number. Please try again.\n")


def prompt_int_list(prompt):
    """Loops until the user enters a comma-separated list of whole numbers; returns the list."""
    while True:
        answer = input(prompt).strip()
        try:
            return [int(x) for x in answer.split(",")]
        except ValueError:
            print(
                f"Invalid input - '{answer}' isn't a comma-separated list of whole numbers "
                "(e.g. '0,1,2'). Please try again.\n"
            )
