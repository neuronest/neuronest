import argparse
import os
from typing import List, Tuple

DEPENDENT_REPOSITORIES_IAC_VARIABLE_NAME = "REPOSITORIES_DEPENDENCIES"


class VariableLine:
    NAME_AND_VALUE_SEPARATOR = "="

    def __init__(self, line: str):
        if not (
            self.NAME_AND_VALUE_SEPARATOR in line
            and not line.startswith(self.NAME_AND_VALUE_SEPARATOR)
            and not line.startswith("#")
        ):
            raise ValueError("line structure is not good for being VariableLine")
        self.line = line

    @property
    def variable_name(self):
        return self.line.split(self.NAME_AND_VALUE_SEPARATOR)[0]

    @property
    def variable_value(self):
        return self.line.split(self.NAME_AND_VALUE_SEPARATOR)[1]

    def to_file(self, file_path: str):
        with open(file_path, "a") as file:
            file.write(f"{self.line}{os.linesep}")

    def __str__(self):
        return self.line


class EnvFile:
    EXTENSION = ".env"

    def __init__(self, path: str):
        if not path.endswith(self.EXTENSION):
            raise ValueError(f"path should end with {self.EXTENSION} extension")
        self.path = path

    def read(self):
        with open(self.path, "r") as self_reader:
            lines = self_reader.readlines()
        return lines

    def read_as_variables_lines(self):
        variables_lines = []
        for line in self.read():
            try:
                variables_lines.append(VariableLine(line=line.rstrip(os.linesep)))
            except ValueError:
                pass
        return variables_lines


class Repository:
    STATIC_VARIABLES_FILE_PATH = "iac/static_variables.env"
    DYNAMIC_VARIABLES_FILE_PATH = "iac/dynamic_variables.env"

    def __init__(self, name: str):
        self.name = name

    def get_static_env_file(self):
        return EnvFile(path=f"{self.name}/{self.STATIC_VARIABLES_FILE_PATH}")

    def get_dynamic_env_file(self):
        return EnvFile(path=f"{self.name}/{self.DYNAMIC_VARIABLES_FILE_PATH}")


def get_static_and_dynamic_variables_lines(
    repository_name: str,
    add_namespace_to_dependencies: bool = True,
) -> Tuple[List[VariableLine], List[VariableLine]]:
    repository = Repository(name=repository_name)

    all_repository_static_variables_lines = []
    all_repository_dynamic_variables_lines = []

    repository_level_static_variables_lines = (
        repository.get_static_env_file().read_as_variables_lines()
    )
    repository_level_dynamic_variables_lines = (
        repository.get_dynamic_env_file().read_as_variables_lines()
    )

    for dependent_repository_name in (
        {
            variable_line.variable_name: variable_line.variable_value
            for variable_line in repository_level_static_variables_lines
        }
        .get(DEPENDENT_REPOSITORIES_IAC_VARIABLE_NAME, "")
        .rstrip(os.linesep)
        .split()
    ):
        (
            dependent_repository_static_variables_lines,
            dependent_repository_dynamic_variables_lines,
        ) = get_static_and_dynamic_variables_lines(
            repository_name=dependent_repository_name,
            add_namespace_to_dependencies=add_namespace_to_dependencies,
        )
        if add_namespace_to_dependencies:
            namespace = dependent_repository_name.replace("-", "_").upper()
            dependent_repository_static_variables_lines = [
                VariableLine(line=f"{namespace}_{static_variable}")
                for static_variable in dependent_repository_static_variables_lines
            ]
            dependent_repository_dynamic_variables_lines = [
                VariableLine(line=f"{namespace}_{dynamic_variable}")
                for dynamic_variable in dependent_repository_dynamic_variables_lines
            ]
        all_repository_static_variables_lines += (
            dependent_repository_static_variables_lines
        )
        all_repository_dynamic_variables_lines += (
            dependent_repository_dynamic_variables_lines
        )

    all_repository_static_variables_lines += repository_level_static_variables_lines
    all_repository_dynamic_variables_lines += repository_level_dynamic_variables_lines

    return all_repository_static_variables_lines, all_repository_dynamic_variables_lines


if __name__ == "__main__":
    # Define the command-line arguments
    parser = argparse.ArgumentParser(description="Process some integers.")
    parser.add_argument(
        "--repository_name",
        type=str,
        required=True,
        help="The first required integer argument.",
    )
    parser.add_argument(
        "--environment_variables_file_path",
        type=str,
        required=True,
        help="The first required integer argument.",
    )

    def boolean_string(string):
        string = string.lower()
        boolean_string_true = "true"
        boolean_string_false = "false"
        if string not in {boolean_string_true, boolean_string_false}:
            raise ValueError(f"{string} is not a valid boolean string")
        return string == boolean_string_true

    parser.add_argument(
        "--add_terraform_variables",
        type=boolean_string,
        required=False,
        default=True,
        help="The first required integer argument.",
    )

    args = parser.parse_args()

    shared_static_variables_lines = EnvFile(
        path=".github/variables/static_variables.env"
    ).read_as_variables_lines()
    shared_dynamic_variables_lines = EnvFile(
        path=".github/variables/dynamic_variables.env"
    ).read_as_variables_lines()

    (
        repository_static_variables_lines,
        repository_dynamic_variables_lines,
    ) = get_static_and_dynamic_variables_lines(
        repository_name=args.repository_name, add_namespace_to_dependencies=True
    )

    all_variables_lines = (
        shared_static_variables_lines
        + repository_static_variables_lines
        + shared_dynamic_variables_lines
        + repository_dynamic_variables_lines
    )
    if args.add_terraform_variables:
        # add the terraform variables and concatenate the list of lists
        # into a single list
        all_variables_lines = sum(
            [
                [variable, VariableLine(line=f"TF_VAR_{str(variable).lower()}")]
                for variable in all_variables_lines
            ],
            [],
        )
    for variable_line in all_variables_lines:
        variable_line.to_file(args.environment_variables_file_path)
