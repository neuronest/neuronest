import re
import sys

COLOR_OFF = "\033[0m"
RED = "\033[1;31m"
GREEN = "\033[1;32m"
YELLOW = "\033[1;33m"
BLUE = "\033[1;34m"

COMMIT_MESSAGE = ".git/COMMIT_EDITMSG"


# pylint: disable=W1401
# flake8: noqa: W605
def print_failed_message(commit_first_line: str, specific_message: str):
    print(f'{RED}Bad commit {BLUE}"{commit_first_line}"\n')
    print(f"{specific_message}")
    print(f"{RED}")
    print(
        """
              ,
     __  _.-"` `'-.
    /||\'._ __{}_(
    ||||  |'--.__\\
    |  L.(   ^_\^
    \ .-' |   _ |
    | |   )\___/
    |  \-'`:._]
    \__/;      '-.
    |   |o     __ \\
    |   |o     )( |
    |   |o     \/ \
    """
    )
    print(f"{COLOR_OFF}")
    print(f"\n{YELLOW}commit-msg hook failed (add --no-verify to bypass)\n{COLOR_OFF}")


if __name__ == "__main__":
    with open(COMMIT_MESSAGE) as f:
        data = f.readline()

    first_line = data.split("\n", 1)[0]

    header_regex = re.compile(
        r"^\((?:feat|fix|hotfix|update|refactor|clean|test|config|ci|doc|wip|merge)\)\s"
        r"(?:\[[-\s,a-z]{3,50}\]\s)?[A-Z].{1,100}$"
    )

    if not bool(header_regex.fullmatch(first_line)):
        specific_failed_message = f"{YELLOW}Commit message is invalid!"
        print_failed_message(first_line, specific_failed_message)
        sys.exit(1)

    sys.exit(0)
