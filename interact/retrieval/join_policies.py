from interact.retrieval import SimpleRecord


def numbered_paragraphs(records: list[SimpleRecord]) -> str:
    """Number paragraphs in a list of records."""
    concatenated = ""
    for i, item in enumerate(records):
        if not isinstance(item, SimpleRecord):
            raise ValueError(f"Expected SimpleRecord, got {type(item)}")
        concatenated += f"**{i + 1}**\n{item.text}\n\n"
    return concatenated