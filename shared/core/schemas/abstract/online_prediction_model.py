from enum import Enum

from core.serialization.schema import Schema


class Device(str, Enum):
    CPU = "cpu"
    CUDA = "cuda"


# dummy class not used to show which classes to implement and
# what to inherit in online prediction models schemas
class InputSampleSchema(Schema):
    pass


# dummy class not used to show which classes to implement and
# what to inherit in online prediction models schemas
class OutputSampleSchema(Schema):
    pass
