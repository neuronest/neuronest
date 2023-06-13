import argparse
import logging
import os
import re
import sys
from typing import List, Optional, Tuple, Union

# the script is used with python for which the core package is not installed,
# so we modify sys.path at runtime to be able to import code from core
# this also results in conflicts between black and flake8/pylint
sys.path.append("shared")
from core.utils import string_to_boolean  # pylint: disable=C0413  # noqa: E402

DEPENDENT_REPOSITORY_VAR_LINE_NAME = "REPOSITORIES_DEPENDENCIES"
ARRAY_SEPARATOR = ","
TERRAFORM_VARIABLES_PREFIX = "TF_VAR_"

# create logger
logger = logging.getLogger(".github.actions.set_variables.create_env_file")


class VariableLine:
    NAME_AND_VALUE_SEPARATOR = "="
    REGEX_OF_VALUE_PART_VARIABLES = r"\$\{([^\}]*)\}"

    def __init__(self, line: str):
        if not self.can_be_built_from_string(line):
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

    @classmethod
    def can_be_built_from_string(cls, string: str) -> bool:
        return (
            string.count(cls.NAME_AND_VALUE_SEPARATOR) == 1
            and not string.startswith(cls.NAME_AND_VALUE_SEPARATOR)
            and not string.startswith("#")
            and not string.endswith(os.linesep)
        )

    def to_file(self, file_path: str):
        with open(file_path, "a") as file:
            file.write(f"{self.line}{os.linesep}")

    def truncate_to_current_context(self, current_context: str):
        """
        Modifies the name and value parts so that they represent the current context,
        that is to say, we remove the coordinates which are used to
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
        truncated_variable_line = VariableLine(line=self.line)
        for (
            variable_inside_value
        ) in truncated_variable_line.get_variables_inside_value():
            if not current_context.lower() in variable_inside_value.lower():
                continue
            truncated_variable_line.replace_variable_inside_value(
                variable=variable_inside_value,
                other_variable=variable_inside_value[
                    variable_inside_value.rfind(current_context.upper())
                    + len(current_context)
                    + 1 :
                ],
                inplace=True,
            )
            if not current_context.lower() in truncated_variable_line.name.lower():
                continue
            new_var_line_name = truncated_variable_line.name.upper()[
                truncated_variable_line.name.upper().rfind(current_context.upper())
                + len(current_context)
                + 1 :
            ]
            if truncated_variable_line.name.startswith(TERRAFORM_VARIABLES_PREFIX):
                truncated_variable_line.name = (
                    f"{TERRAFORM_VARIABLES_PREFIX}{new_var_line_name.lower()}"
                )
            else:
                truncated_variable_line.name = new_var_line_name
        return truncated_variable_line

    def replace_variable_inside_value(
        self,
        variable: str,
        other_variable: str,
        inplace: bool = False,
    ) -> Union["VariableLine", None]:
        """
        Replaces a variable name that is in the value part with another variable name.

        Args:
            variable (str): The variable name to be replaced.
            other_variable (str): The new variable name to replace the existing one.
            inplace (bool, optional): Specifies whether to modify the variable in-place
                or return a modified copy.
                Defaults to False.

        Returns:
            str: The modified variable line with the updated variable name in the value part.

        Example:
            >>> var_line = VariableLine(
            >>>                     "WEBAPP_SERVICE_ACCOUNT_EMAIL="
            >>>                     "${WEBAPP_SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam"
            >>>                     ".gserviceaccount.com"
            >>>                )
            >>> var_line.replace_variable_inside_value(
            ...     variable="WEBAPP_SERVICE_ACCOUNT_NAME",
            ...     other_variable="PEOPLE_COUNTING_WEBAPP_SERVICE_ACCOUNT_NAME",
            ...     inplace=True
            ... )
            'WEBAPP_SERVICE_ACCOUNT_EMAIL=${PEOPLE_COUNTING_WEBAPP_SERVICE_ACCOUNT_NAME}'
            @${PROJECT_ID}.iam.gserviceaccount.com'
        """
        variable_line_value = self.value.replace(
            "${" + variable + "}", "${" + other_variable + "}"
        )
        if not inplace:
            return VariableLine(line=f"{self.name}={variable_line_value}")

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

        var_line = VariableLine(
            line=f"{name}{self.NAME_AND_VALUE_SEPARATOR}{self.value}"
        )

        if not add_to_value:
            return var_line

        if variable_inside_value_to_add_to is not None:
            # only add the namespace to this variable only within the value part
            all_variables_inside_value_to_add_to = [variable_inside_value_to_add_to]
        else:
            all_variables_inside_value_to_add_to = var_line.get_variables_inside_value()

        for variable in all_variables_inside_value_to_add_to:
            var_line = var_line.replace_variable_inside_value(
                variable=variable,
                other_variable=f"{namespace}_{variable}",
            )
        return var_line

    def __str__(self):
        return self.line

    def get_variables_inside_value(self):

        if variables_inside_value := re.findall(
            self.REGEX_OF_VALUE_PART_VARIABLES, self.value
        ):
            return list(variables_inside_value)
        return []


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
        return [
            VariableLine(line=line.rstrip(os.linesep))
            for line in self.readlines()
            if VariableLine.can_be_built_from_string(line.rstrip(os.linesep))
        ]


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

    def has_all_env_files(self):
        return os.path.isfile(self.static_env_file_path) and os.path.isfile(
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
        if (
            dependency_repositories := static_var_name_value.get(
                DEPENDENT_REPOSITORY_VAR_LINE_NAME
            )
        ) is not None:
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
    parser.add_argument(
        "--add_terraform_variables",
        type=string_to_boolean,
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
        type=string_to_boolean,
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
    if main_repository.has_all_env_files():
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
            f"{main_repository.static_env_file_path} and "
            f"{main_repository.dynamic_env_file_path} "
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
        for variable_line in all_variables_lines:
            tf_var_line = VariableLine(line=variable_line.line)
            tf_var_line.name = f"TF_VAR_{tf_var_line.name.lower()}"
            tf_var_lines.append(tf_var_line)
        all_variables_lines += tf_var_lines

    for variable_line in all_variables_lines:
        variable_line.to_file(args.environment_variables_file_path)
