import logging
from collections.abc import Sequence
from typing import Callable

import faiss
import numpy as np
from faiss import Index

from interact import Message
from interact.retrieval import Record, VectorDB

logger = logging.getLogger(__name__)


class FaissIndexDB(VectorDB):
    index_db: Index

    def __init__(
        self,
        index: Index | tuple[int, str],
        dataset: Sequence[Record],
        encoder: Callable[[list[str]], np.ndarray],
        train: bool = False,
    ) -> None:
        if isinstance(index, Index):
            self.index_db = index
        elif isinstance(index, tuple):
            self.index_db = faiss.index_factory(*index)
        else:
            raise ValueError("Invalid index input.")

        self.dataset = dataset
        self.encoder = encoder

        self.add_records(dataset, train=train)

    def add_records(self, dataset: Sequence[Record], train: bool = False) -> None:
        strings = self.refresh_records(dataset)
        embeddings = self.encoder(list(strings.values()))

        if train:
            logger.info("Training index.")
            self.index_db.train(embeddings)  # type: ignore

        logger.info("Adding records to index.")
        self.index_db.add_with_ids(embeddings, np.array(list(strings.keys())))  # type: ignore

    def query(self, query: Message, k: int = 5) -> list[Record]:
        query_str = str(query)
        query_embedding = self.encoder([query_str])
        _, idxs = self.index_db.search(query_embedding, k)  # type: ignore
        return self.collect_records(idxs[0])
