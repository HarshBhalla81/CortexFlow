class Executor:

    def run(
        self,
        component,
        payload
    ):

        if hasattr(
            component,
            "execute"
        ):
            return component.execute(
                payload
            )

        if hasattr(
            component,
            "run"
        ):
            return component.run(
                payload
            )

        raise ValueError(
            "Unsupported component"
        )