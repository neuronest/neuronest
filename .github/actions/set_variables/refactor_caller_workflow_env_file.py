import argparse
import logging
import sys

sys.path.append(".github/actions/set_variables")

# we need to modify sys.path at runtime because the syntax
# "import from .github.actions.set_variables.create_env_file import EnvFile"
# does not work because of "." at the beginning
# this also results in conflicts between black and flake8/pylint
from create_env_file import EnvFile  # pylint: disable=C0413  # noqa: E402

# create logger
logger = logging.getLogger(
    ".github.actions.set_variables.refactor_caller_workflow_env_file"
)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--repository_where_variables_are_defined",
        type=str,
        required=True,
    )
    parser.add_argument(
        "--caller_workflow_env_file_path",
        type=str,
        required=True,
    )
    parser.add_argument(
        "--refactored_caller_workflow_env_file_path",
        type=str,
        required=True,
    )

    args = parser.parse_args()

    caller_workflow_variables_lines = EnvFile(
        path=args.caller_workflow_env_file_path
    ).read_variables_lines()

    repository_name_to_search_in_variable = (
        args.repository_where_variables_are_defined.replace("-", "_")
    )
    caller_workflow_variables_lines = [
        var_line.truncate_to_current_context(
            current_context=repository_name_to_search_in_variable
        )
        for var_line in caller_workflow_variables_lines
    ]

    for var_line in caller_workflow_variables_lines:
        var_line.to_file(args.refactored_caller_workflow_env_file_path)
