from proto import Message


def protobuf_to_dict(response: Message) -> dict:
    # noinspection PyTypeChecker
    return Message.to_dict(response, use_integers_for_enums=False)
