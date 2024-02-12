class InteractError(Exception):
    pass


class CascadeError(InteractError):
    pass


class HandlerError(InteractError):
    pass


class UnsupportedCascade(CascadeError):
    def __init__(self, obj1, obj2) -> None:
        print(obj1)
        super().__init__(
            f"Unsupported cascade between {str(obj1)} and {str(obj2)}."
            " Cascade is supported between `Handler`s and `Cascade`s"
        )


class ChatInterruptionError(Exception):
    pass


class CascadeOutputValidationError(Exception):
    pass
