from typing import Callable

import faiss
import numpy as np
from faiss.swigfaiss import Index

from interact.similarity import Retriever

IdEntry = dict[int, str]


def validate_index_input(index_factory: str | None, index: Index | None) -> None:
    if index_factory is None and index is None:
        raise ValueError("Either index_factory or index must be provided.")
    if index_factory is not None and index is not None:
        raise ValueError("Only one of index_factory or index must be provided.")


class FaissRetriever(Retriever):
    def __init__(
        self,
        encoder: Callable[[list[str]], np.ndarray],
        data: list[str],
        index_factory: str | None = None,
        index: Index | None = None,
        train: bool = False,
    ) -> None:
        self.encoder = encoder
        self.map: IdEntry = {}

        validate_index_input(index_factory, index)
        if index is None:
            self.index_db: Index = faiss.index_factory(dim, index_factory)
        elif index_factory is not None:
            self.index_db: Index = index

        embeddings = self.encoder(data)
        if train:
            self.index_db.train(embeddings)  # type: ignore

        # update db and map
        self.add_entries(data)

    def update_map(self, entries: list[str]) -> IdEntry:
        prev_len = len(self.map)
        new_entry_w_ids = {}
        for i, entry in enumerate(entries):
            self.map[i + prev_len] = entry
            new_entry_w_ids[i + prev_len] = entry
        return new_entry_w_ids

    def add_entries(self, entries: list[str]) -> None:
        new_entries = self.update_map(entries)
        self.index_db.add_with_ids(
            self.encoder(entries), np.array(list(new_entries.keys()))
        )  # type: ignore

    def retrieve(self, query: str, k: int = 5) -> list[str]:
        assert isinstance(query, str), "Query must be a string."
        query_embedding = self.encoder([query])
        _, idxs = self.index_db.search(query_embedding, k)  # type: ignore
        return [self.map[i] for i in idxs[0]]
