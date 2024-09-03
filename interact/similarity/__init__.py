from interact import HandlerChain, Message, Handler


class Retriever(Handler):
    index_db: object

    def add_entries(self, entries: list[str]) -> None:
        raise NotImplementedError

    def retrieve(self, query: str) -> list[str]:
        raise NotImplementedError
