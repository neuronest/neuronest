import argparse
import logging
import os
import re
from typing import List, Optional, Tuple

DEPENDENT_REPOSITORY_VAR_LINE_NAME = "REPOSITORIES_DEPENDENCIES"
ARRAY_SEPARATOR = ","
TERRAFORM_VARIABLES_PREFIX = "TF_VAR_"

# create logger
logger = logging.getLogger("my_logger")


class VariableLine:
    NAME_AND_VALUE_SEPARATOR = "="

    def __init__(self, line: str):
        if not (
            self.NAME_AND_VALUE_SEPARATOR in line
            and not line.startswith(self.NAME_AND_VALUE_SEPARATOR)
            and not line.startswith("#")
        ):
            raise ValueError("line structure is not good for being VariableLine")
        self._value = None
        self._name = None
        self.line = line

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, new_name):
        self._name = new_name

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        self._value = new_value

    @property
    def line(self):
        return f"{self.name}{self.NAME_AND_VALUE_SEPARATOR}{self.value}"

    @line.setter
    def line(self, new_line):
        name, value = new_line.split(self.NAME_AND_VALUE_SEPARATOR)
        self.name = name
        self.value = value

    def to_file(self, file_path: str):
        with open(file_path, "a") as file:
            file.write(f"{self.line}{os.linesep}")

    def truncate_to_current_context(self, current_context: str):
        """
        Modifies the name and value parts so that they represent the current context,
        that is to say, we remove from the names the coordinates which are used to
        specify the origin of the variable from a broader context than currently.

        For example: the variable
        OBJECT_DETECTION_SERVICE_ACCOUNT_EMAIL=
        ${OBJECT_DETECTION_SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com
        becomes SERVICE_ACCOUNT_EMAIL=
        ${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com
        and
        TF_VAR_object_detection_service_account_email=
        ${OBJECT_DETECTION_SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com
        becomes TF_VAR_service_account_email=
        ${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com
        in "object_detection" context.
        """

        for variable_inside_value in self.get_variables_inside_value():
            if not current_context.lower() in variable_inside_value.lower():
                continue
            self.replace_variable_inside_value(
                variable=variable_inside_value,
                other_variable=variable_inside_value[
                    variable_inside_value.rfind(current_context.upper())
                    + len(current_context)
                    + 1 :
                ],
                inplace=True,
            )
            if not current_context.lower() in self.name.lower():
                continue
            new_var_line_name = self.name.upper()[
                self.name.upper().rfind(current_context.upper())
                + len(current_context)
                + 1 :
            ]
            if self.name.startswith(TERRAFORM_VARIABLES_PREFIX):
                self.name = f"{TERRAFORM_VARIABLES_PREFIX}{new_var_line_name.lower()}"
            else:
                self.name = new_var_line_name

    def replace_variable_inside_value(
        self,
        variable: str,
        other_variable: str,
        inplace: bool = False,
    ):
        variable_line_name = self.name
        variable_line_value = self.value.replace(
            "${" + variable + "}", "${" + other_variable + "}"
        )
        if not inplace:
            return VariableLine(line=f"{variable_line_name}={variable_line_value}")

        self.name = variable_line_name
        self.value = variable_line_value

        return None

    def add_namespace(
        self,
        namespace: str,
        add_to_name: bool = True,
        add_to_value: bool = False,
        variable_inside_value_to_add_to: Optional[str] = None,
    ):
        if add_to_name:
            name = f"{namespace}_{self.name}"
        else:
            name = self.name

        if not add_to_value:
            return VariableLine(
                line=f"{name}{self.NAME_AND_VALUE_SEPARATOR}{self.value}"
            )

        if variable_inside_value_to_add_to is not None:
            # only add the namespace to this variable only within the value part
            value = self.value.replace(
                "${" + variable_inside_value_to_add_to + "}",
                "${" + f"{namespace}_{variable_inside_value_to_add_to}" + "}",
            )
        else:
            # add the namespace to all variables within the value part
            value = ""
            i = 0
            while i < len(self.value):
                if self.value[i : i + 2] == "${":
                    value += "${" + f"{namespace}_"
                    i += 2
                else:
                    value += self.value[i]
                    i += 1
        return VariableLine(line=f"{name}={value}")

    def __str__(self):
        return self.line

    def get_variables_inside_value(self):

        if variables_inside_value := re.findall(
            "\$\{([^\}]*)\}", self.value  # pylint: disable=W1401  # noqa: W605
        ):
            return list(variables_inside_value)
        return None


class EnvFile:
    EXTENSION = ".env"

    def __init__(self, path: str):
        if not path.endswith(self.EXTENSION):
            raise ValueError(f"path should end with {self.EXTENSION} extension")
        self.path = path

    def readlines(self):
        with open(self.path, "r") as self_reader:
            lines = self_reader.readlines()
        return lines

    def read_variables_lines(self):
        variables_lines = []
        for line in self.readlines():
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

    @property
    def static_env_file_path(self):
        return f"{self.name}/{self.STATIC_VARIABLES_FILE_PATH}"

    @property
    def dynamic_env_file_path(self):
        return f"{self.name}/{self.DYNAMIC_VARIABLES_FILE_PATH}"

    def has_env_files(self):
        return os.path.isfile(self.static_env_file_path) or os.path.isfile(
            self.dynamic_env_file_path
        )

    def get_static_env_file(self):
        return EnvFile(path=self.static_env_file_path)

    def get_dynamic_env_file(self):
        return EnvFile(path=self.dynamic_env_file_path)

    def get_dependency_repositories(self):
        static_var_name_value = {
            var_line.name: var_line.value
            for var_line in self.get_static_env_file().read_variables_lines()
        }
        if dependency_repositories := static_var_name_value.get(
            DEPENDENT_REPOSITORY_VAR_LINE_NAME, ""
        ):
            dependency_repositories = dependency_repositories.rstrip(os.linesep).split(
                ARRAY_SEPARATOR
            )
            return [
                Repository(name=dependency_repository)
                for dependency_repository in dependency_repositories
            ]
        return []


def get_static_and_dynamic_var_lines(
    repository: Repository,
    add_namespace: bool = True,
) -> Tuple[List[VariableLine], List[VariableLine]]:

    all_repository_static_var_lines = []
    all_repository_dynamic_var_lines = []

    repository_level_static_var_lines = (
        repository.get_static_env_file().read_variables_lines()
    )
    repository_level_dynamic_var_lines = (
        repository.get_dynamic_env_file().read_variables_lines()
    )

    for dependency_repository in repository.get_dependency_repositories():
        (
            dependency_repository_static_var_lines,
            dependency_repository_dynamic_var_lines,
        ) = get_static_and_dynamic_var_lines(
            repository=dependency_repository,
            add_namespace=True,
        )

        all_repository_static_var_lines += dependency_repository_static_var_lines
        all_repository_dynamic_var_lines += dependency_repository_dynamic_var_lines

    all_repository_static_var_lines += repository_level_static_var_lines
    all_repository_dynamic_var_lines += repository_level_dynamic_var_lines

    if add_namespace:
        repository_name_as_namespace = repository.name.replace("-", "_").upper()
        repository_static_var_lines_names = set(
            static_var.name for static_var in all_repository_static_var_lines
        )
        for i, _ in enumerate(all_repository_dynamic_var_lines):
            all_repository_dynamic_var_lines[i] = all_repository_dynamic_var_lines[
                i
            ].add_namespace(
                repository_name_as_namespace, add_to_name=True, add_to_value=False
            )
            variables_inside_value = all_repository_dynamic_var_lines[
                i
            ].get_variables_inside_value()
            for variable_inside_value in variables_inside_value:
                if variable_inside_value in repository_static_var_lines_names:
                    all_repository_dynamic_var_lines[
                        i
                    ] = all_repository_dynamic_var_lines[i].add_namespace(
                        repository_name_as_namespace,
                        add_to_name=False,
                        add_to_value=True,
                        variable_inside_value_to_add_to=variable_inside_value,
                    )
        for i, _ in enumerate(all_repository_static_var_lines):
            all_repository_static_var_lines[i] = all_repository_static_var_lines[
                i
            ].add_namespace(
                repository_name_as_namespace, add_to_name=True, add_to_value=False
            )

    return all_repository_static_var_lines, all_repository_dynamic_var_lines


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--repository_name",
        type=str,
        required=True,
    )
    parser.add_argument(
        "--environment_variables_file_path",
        type=str,
        required=True,
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
    )
    parser.add_argument(
        "--variable_prefix_to_filter_on",
        type=str,
        required=False,
        default=None,
    )
    parser.add_argument(
        "--discard_shared_variables",
        type=boolean_string,
        required=False,
        default=False,
    )

    args = parser.parse_args()

    shared_static_variables_lines = EnvFile(
        path=".github/variables/static_variables.env"
    ).read_variables_lines()
    shared_dynamic_variables_lines = EnvFile(
        path=".github/variables/dynamic_variables.env"
    ).read_variables_lines()

    main_repository = Repository(name=args.repository_name)
    if main_repository.has_env_files():
        (
            repository_static_variables_lines,
            repository_dynamic_variables_lines,
        ) = get_static_and_dynamic_var_lines(
            repository=main_repository, add_namespace=False
        )
    else:
        repository_static_variables_lines = []
        repository_dynamic_variables_lines = []
        logger.warning(
            f"the repositories {main_repository.name} have none of the files "
            f"{main_repository.static_env_file_path} and {main_repository.dynamic_env_file_path} "
            f"needed to load variables"
        )

    shared_variables_lines_names = set(
        shared_var_line.name
        for shared_var_line in shared_static_variables_lines
        + shared_dynamic_variables_lines
    )
    all_variables_lines = (
        shared_static_variables_lines
        + repository_static_variables_lines
        + shared_dynamic_variables_lines
        + repository_dynamic_variables_lines
    )
    if args.discard_shared_variables:
        all_variables_lines = [
            var_line
            for var_line in all_variables_lines
            if var_line.name not in shared_variables_lines_names
        ]
    if args.variable_prefix_to_filter_on:
        all_variables_lines = [
            var_line
            for var_line in all_variables_lines
            if var_line.name.startswith(args.variable_prefix_to_filter_on)
            or var_line.name in shared_variables_lines_names
        ]

    if args.add_terraform_variables:
        # add the terraform variables and concatenate the list of lists
        # into a single list
        tf_var_lines = []
        for var_line in all_variables_lines:
            tf_var_line = VariableLine(line=var_line.line)
            tf_var_line.name = f"TF_VAR_{tf_var_line.name.lower()}"
            tf_var_lines.append(tf_var_line)
        all_variables_lines += tf_var_lines

    for variable_line in all_variables_lines:
        variable_line.to_file(args.environment_variables_file_path)
