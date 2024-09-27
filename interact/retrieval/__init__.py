from typing import Annotated, Literal, Protocol, Sequence, TypeVar

import numpy as np
from pydantic import BaseModel, ConfigDict, model_validator

from interact import Message

SemanticTextStr = Annotated[str, "SemanticText"]


class Record(BaseModel):
    """A class representing a record with semantic fields."""

    model_config = ConfigDict(frozen=True)

    # class Config:
    #     frozen = True

    @model_validator(mode="after")
    def _post_root(self):
        self._semantic_fields = []
        for field_name, field in self.model_fields.items():
            if len(field.metadata) > 0 and field.metadata[0] == "SemanticText":
                self._semantic_fields.append(field_name)

        if len(self._semantic_fields) == 0:
            raise ValueError(f"No semantic fields found in the record {self}.")
        return self

    def __str__(self) -> str:
        semantic_texts = {attr: getattr(self, attr) for attr in self._semantic_fields}
        if len(semantic_texts) == 1:
            return next(iter(semantic_texts.values()))
        else:
            return "\n".join([
                f"{attr}: {text}" for attr, text in semantic_texts.items()
            ])


class SimpleRecord(Record):
    text: SemanticTextStr
    metadata: dict

    model_config = ConfigDict(extra="allow")

    # class Config:
    #     extra = "allow"

    def __init__(self, text, **data):
        super().__init__(text=text, metadata=data)  # type: ignore


class EncoderType(Protocol):
    """A protocol for an encoder function."""

    def __call__(
        self, texts: list[str], mode: Literal["passage", "query"]
    ) -> np.ndarray: ...


T = TypeVar("T", bound=Record)


class VectorDB(Protocol[T]):
    """A protocol for a vector database."""

    encoder: EncoderType

    _records_store: list[T] = []
    _strings_store: list[str] = []
    _strings_to_records: dict[int, int] = {}

    def add_records(self, dataset: list[T]) -> None:
        raise NotImplementedError

    def query(self, query: Message, k: int) -> list[T]:
        raise NotImplementedError

    def refresh_records(self, dataset: Sequence[T]) -> dict[int, str]:
        """
        Refreshes the records in the dataset and updates the internal data stores.

        Args:
            dataset (list[Record]): A list of Record objects representing the dataset.

        Returns:
            dict[int, str]: A dictionary mapping string IDs to the strings in the dataset.

        """
        # Store the current length of the strings store to identify new strings added
        last_string_id = len(self._strings_store)

        for record in dataset:
            assert isinstance(
                record, Record
            ), f"Invalid record type: {type(record)}, expected Record."
            # Assign a new record ID based on the current length of the records store
            record_id = len(self._records_store)
            self._records_store.append(record)

            # Add the record's semantic fields to the strings store and map them to the record ID
            for semantic_field in record._semantic_fields:
                string = getattr(record, semantic_field)
                # Assign a new string ID based on the current length of the strings store
                string_id = len(self._strings_store)
                self._strings_store.append(string)
                # Map the string ID to the record ID in the strings to records dictionary
                self._strings_to_records[string_id] = record_id

        return {
            string_id: self._strings_store[string_id]
            for string_id in range(last_string_id, len(self._strings_store))
        }

    def collect_records(self, string_ids: list[int]) -> list[T]:
        """
        Gathers the records corresponding to the given string IDs.

        Args:
            string_ids (list[int]): A list of string IDs.

        Returns:
            list[Record]: A list of Record objects corresponding to the given string IDs. If a record appears multiple times in string_ids, later occurrences will be ignored.

        """
        record_ids = []
        for string_id in string_ids:
            record_id = self._strings_to_records.get(string_id)
            if record_id is not None and record_id not in record_ids:
                record_ids.append(record_id)
        return [self._records_store[record_id] for record_id in record_ids]
