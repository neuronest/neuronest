from __future__ import annotations

import argparse
import logging
import os
import re
import sys
from enum import Enum
from typing import Dict, List, Optional, Set

import yaml
from pydantic import BaseModel

# the script is used with python for which the core package is not installed,
# so we modify sys.path at runtime to be able to import code from core
# this also results in conflicts between black and flake8/pylint
sys.path.append("shared")
from core.utils import string_to_boolean  # pylint: disable=C0413  # noqa: E402

FUNCTIONAL_REPOSITORIES_PREFIX = "func-"
DEPENDENT_REPOSITORY_VAR_LINE_NAME = "REPOSITORIES_DEPENDENCIES"
ARRAY_SEPARATOR = ","
TERRAFORM_VARIABLES_PREFIX = "TF_VAR_"
OTHER_VARIABLES_DEFAULT_SECTION = "default"

# create logger
logger = logging.getLogger(__name__)


class NameSpaceError(Exception):
    pass


def add_namespace_to_string(
    string: str,
    namespace: str,
    already_added_ok: bool = False,
    namespace_and_string_binding_character: str = "_",
) -> str:
    for binding_character in list({"_", "-", namespace_and_string_binding_character}):
        if namespace.endswith(binding_character):
            namespace_and_string_binding_character = binding_character
            namespace = namespace[:-1]

    if not string.startswith(namespace):
        return f"{namespace}{namespace_and_string_binding_character}{string}"

    if not already_added_ok:
        raise NameSpaceError(
            f"The string {string} is already in " f"the namespace {namespace}"
        )

    return string


class VariableType(str, Enum):
    REPOSITORY = "REPOSITORY"
    MULTI_INSTANCE_RESOURCE = "MULTI_INSTANCE_RESOURCE"
    OTHER = "OTHER"


class VariableLine:
    NAME_AND_VALUE_SEPARATOR = "="
    REGEX_OF_VALUE_PART_VARIABLES = r"\$\{([^\}]*)\}"
    REPOSITORY_CODE_VARIABLE_NAME = "REPOSITORY_CODE"

    def __init__(self, line: str, variable_type: Optional[VariableType] = None):
        if not self.can_be_built_from_string(line):
            raise ValueError("line structure is not good for being VariableLine")
        self._value = None
        self._name = None
        self.line = line
        self.variable_type = variable_type

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, new_name: str):
        self._name = new_name

    @property
    def value(self) -> str:
        return self._value

    @value.setter
    def value(self, new_value: str):
        self._value = new_value

    @property
    def line(self) -> str:
        return f"{self.name}{self.NAME_AND_VALUE_SEPARATOR}{self.value}"

    @line.setter
    def line(self, new_line: str):
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

    def truncate_to_current_context(self, current_context: str) -> VariableLine:
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
            return truncated_variable_line

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
    ) -> Optional[VariableLine]:
        """
        Replaces a variable name that is in the value part with another variable name.

        Args:
            variable (str): The variable name to be replaced.
            other_variable (str): The new variable name to replace the existing one.
            inplace (bool, optional): Specifies whether to modify the variable in-place
                or return a modified copy.
                Defaults to False.

        Returns:
            str: The modified variable line with the updated variable name in the value
            part.

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

    def add_namespace_to_name(
        self,
        namespace: str,
        already_added_ok: bool = False,
    ) -> VariableLine:
        var_line = VariableLine(self.line)
        namespace = f"{namespace.replace('-', '_').upper()}{'_'}"

        var_line.name = add_namespace_to_string(
            string=var_line.name,
            namespace=namespace,
            already_added_ok=already_added_ok,
        )

        return var_line

    def add_namespace_to_value(
        self,
        namespace: str,
        already_added_ok: bool = False,
    ) -> VariableLine:
        var_line = VariableLine(self.line)
        namespace = namespace.replace("_", "-").lower()
        namespace = f"{namespace}" if namespace.endswith("-") else f"{namespace}-"

        var_line.value = add_namespace_to_string(
            string=var_line.value,
            namespace=namespace,
            already_added_ok=already_added_ok,
        )

        return var_line

    def add_namespace_to_value_variables(
        self,
        namespace: str,
        variable_inside_value_to_add_to: Optional[str] = None,
        already_added_ok: bool = False,
    ) -> VariableLine:
        var_line = VariableLine(self.line)
        namespace = f"{namespace.replace('-', '_').upper()}{'_'}"

        if variable_inside_value_to_add_to is not None:
            # only add the namespace to this variable only within the value part
            all_variables_inside_value_to_add_to = [variable_inside_value_to_add_to]
        else:
            all_variables_inside_value_to_add_to = var_line.get_variables_inside_value()

        for variable in all_variables_inside_value_to_add_to:
            var_line = var_line.replace_variable_inside_value(
                variable=variable,
                other_variable=add_namespace_to_string(
                    string=variable,
                    namespace=namespace,
                    already_added_ok=already_added_ok,
                ),
            )

        return var_line

    def add_namespace(
        self,
        namespace: str,
        add_to_name: bool = True,
        add_to_value: bool = False,
        add_to_value_variables: bool = False,
        variable_inside_value_to_add_to: Optional[str] = None,
        inplace: bool = False,
        already_added_ok: bool = False,
    ) -> Optional[VariableLine]:
        var_line = VariableLine(self.line)
        if add_to_name:
            var_line = var_line.add_namespace_to_name(
                namespace=namespace, already_added_ok=already_added_ok
            )
        if add_to_value:
            var_line = var_line.add_namespace_to_value(
                namespace=namespace, already_added_ok=already_added_ok
            )
        if add_to_value_variables:
            var_line = var_line.add_namespace_to_value_variables(
                namespace=namespace,
                already_added_ok=already_added_ok,
                variable_inside_value_to_add_to=variable_inside_value_to_add_to,
            )

        if not inplace:
            return var_line

        self.name = var_line.name
        self.value = var_line.value

        return None

    def __str__(self):
        return self.line

    def get_variables_inside_value(self) -> List[str]:
        if variables_inside_value := re.findall(
            self.REGEX_OF_VALUE_PART_VARIABLES, self.value
        ):
            return list(variables_inside_value)

        return []

    def is_a_multi_instance_resource(self) -> bool:
        return self.variable_type == VariableType.MULTI_INSTANCE_RESOURCE

    def is_a_repository_variable(self) -> bool:
        return self.variable_type == VariableType.REPOSITORY

    def is_a_repository_code(self) -> bool:
        return self.name == self.REPOSITORY_CODE_VARIABLE_NAME


class BranchConditionedSection(BaseModel):
    branch: Dict[str, List[str]]


class YamlEnvFile(BaseModel):
    repository_variables: List[str]
    multi_instance_resource_names: List[str]
    other_variables: BranchConditionedSection

    @classmethod
    def read_file(cls, file_path: str) -> YamlEnvFile:
        with open(file_path, "r") as self_reader:
            yaml_data = yaml.safe_load(self_reader)

        return cls.parse_obj(yaml_data)

    def to_variables_lines(
        self,
        branch_name: Optional[str] = None,
    ) -> List[VariableLine]:
        other_variables_section = self.other_variables.branch.get(
            branch_name or OTHER_VARIABLES_DEFAULT_SECTION,
            self.other_variables.branch[OTHER_VARIABLES_DEFAULT_SECTION],
        )

        return (
            [
                VariableLine(line=variable, variable_type=VariableType.REPOSITORY)
                for variable in self.repository_variables
            ]
            + [
                VariableLine(
                    line=variable, variable_type=VariableType.MULTI_INSTANCE_RESOURCE
                )
                for variable in self.multi_instance_resource_names
            ]
            + [
                VariableLine(line=variable, variable_type=VariableType.OTHER)
                for variable in other_variables_section
            ]
        )


class EnvFile:
    EXTENSION = ".env"

    def __init__(self, path: str):
        if not path.endswith(self.EXTENSION):
            raise ValueError(f"path should end with {self.EXTENSION} extension")
        self.path = path

    def readlines(self) -> List[str]:
        with open(self.path, "r") as self_reader:
            return self_reader.readlines()

    def read_variables_lines(self) -> List[VariableLine]:
        return [
            VariableLine(line=line.rstrip(os.linesep))
            for line in self.readlines()
            if VariableLine.can_be_built_from_string(line.rstrip(os.linesep))
        ]


class Repository:
    VARIABLES_FILE_PATH = "iac/variables.yaml"

    def __init__(self, name: str, branch_name: Optional[str] = None):
        self.name = name
        self.branch_name = branch_name

    @property
    def yaml_env_file_path(self) -> str:
        return f"{self.name}/{self.VARIABLES_FILE_PATH}"

    def has_yaml_env_file(self) -> bool:
        return os.path.isfile(self.yaml_env_file_path)

    def get_yaml_env_file(self) -> YamlEnvFile:
        return YamlEnvFile.read_file(self.yaml_env_file_path)

    def get_dependency_repositories(self) -> List[Repository]:
        variable_name_value = {
            var_line.name: var_line.value
            for var_line in self.get_yaml_env_file().to_variables_lines(
                branch_name=self.branch_name
            )
        }
        if (
            dependency_repositories := variable_name_value.get(
                DEPENDENT_REPOSITORY_VAR_LINE_NAME
            )
        ) is not None:
            dependency_repositories = dependency_repositories.rstrip(os.linesep).split(
                ARRAY_SEPARATOR
            )
            return [
                Repository(name=dependency_repository, branch_name=self.branch_name)
                for dependency_repository in dependency_repositories
            ]

        return []

    def get_base_code(self, prefix_to_remove: Optional[str] = None) -> str:
        # there is one and only one repository code by repo
        # since it is configuration, we don't test it explicitly
        base_code = [
            var_line
            for var_line in self.get_yaml_env_file().to_variables_lines(
                branch_name=self.branch_name
            )
            if var_line.is_a_repository_code()
        ][0].value

        if prefix_to_remove is None or not base_code.startswith(prefix_to_remove):
            return base_code

        return base_code[len(prefix_to_remove) :]


def get_all_repository_var_lines(
    repository: Repository,
    add_namespace: bool = True,
    variables_to_which_not_add_namespace: Optional[Set[str]] = None,
    add_namespace_to_name_of_multi_instance_resource: bool = True,
) -> List[VariableLine]:
    if variables_to_which_not_add_namespace is None:
        variables_to_which_not_add_namespace = {}

    all_repository_var_lines = []

    for dependency_repository in repository.get_dependency_repositories():
        dependency_repository_var_lines = get_all_repository_var_lines(
            repository=dependency_repository,
            add_namespace=True,
            variables_to_which_not_add_namespace=variables_to_which_not_add_namespace,
        )
        all_repository_var_lines += dependency_repository_var_lines

    all_repository_var_lines += repository.get_yaml_env_file().to_variables_lines(
        branch_name=repository.branch_name
    )

    for var_line in all_repository_var_lines:
        if add_namespace:
            variables_inside_value = var_line.get_variables_inside_value()
            for variable_inside_value in variables_inside_value:
                if variable_inside_value not in variables_to_which_not_add_namespace:
                    var_line.add_namespace(
                        repository.name,
                        add_to_value_variables=True,
                        add_to_name=False,
                        variable_inside_value_to_add_to=variable_inside_value,
                        inplace=True,
                        already_added_ok=True,
                    )
            var_line.add_namespace(
                repository.name,
                add_to_name=True,
                add_to_value_variables=False,
                inplace=True,
                already_added_ok=True,
            )
        if (
            add_namespace_to_name_of_multi_instance_resource
            and var_line.is_a_multi_instance_resource()
        ):
            if var_line.value.startswith(
                repository.get_base_code(
                    prefix_to_remove=FUNCTIONAL_REPOSITORIES_PREFIX
                )
            ):
                namespace = FUNCTIONAL_REPOSITORIES_PREFIX
            else:
                namespace = repository.get_base_code()

            var_line.add_namespace(
                namespace,
                add_to_value=True,
                add_to_name=False,
                add_to_value_variables=False,
                inplace=True,
                already_added_ok=True,
            )

    return all_repository_var_lines


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--repository_name",
        type=str,
        required=True,
    )
    parser.add_argument("--branch_name", type=str, required=False, default=None)
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
    parser.add_argument(
        "--keep_repository_variables",
        type=string_to_boolean,
        required=False,
        default=True,
    )

    args = parser.parse_args()

    shared_variables_lines = YamlEnvFile.read_file(
        file_path=".github/variables/variables.yaml"
    ).to_variables_lines(branch_name=args.branch_name)
    shared_variables_lines_names = set(
        shared_var_line.name for shared_var_line in shared_variables_lines
    )

    main_repository = Repository(
        name=args.repository_name, branch_name=args.branch_name
    )

    if main_repository.has_yaml_env_file():
        repository_variables_lines = get_all_repository_var_lines(
            repository=main_repository,
            add_namespace=False,
            add_namespace_to_name_of_multi_instance_resource=True,
            variables_to_which_not_add_namespace=shared_variables_lines_names,
        )
    else:
        repository_variables_lines = []
        logger.warning(
            f"the repository {main_repository.name} has no file "
            f"{main_repository.yaml_env_file_path} "
            f"needed to load variables"
        )

    all_variables_lines = shared_variables_lines + repository_variables_lines
    if not args.keep_repository_variables:
        all_variables_lines = [
            var_line
            for var_line in all_variables_lines
            if not var_line.is_a_repository_variable()
        ]

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
