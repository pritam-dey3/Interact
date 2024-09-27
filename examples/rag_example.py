import asyncio
from functools import partial
from typing import Literal

import numpy as np
from openai import OpenAI

from interact import HandlerChain, Message, handler
from interact.handlers import OpenAiLLM, SimilarityRetriever
from interact.retrieval import SimpleRecord
from interact.retrieval.faiss import FaissIndexDB

import os
os.environ["OPENAI_API_KEY"] = "bad_key"

# an example dataset to demonstrate rag
article = """In 2032, a dog named Timmy made history by becoming the first canine to land on Mars. At the age of 5, Timmy was specially selected for the mission due to his calm temperament and ability to adapt to new environments.

Timmy traveled aboard the SpaceX Falcon X7, a rocket designed for deep space exploration. The spacecraft featured advanced life support systems and a speed of 22,000 miles per hour, ensuring Timmy’s safe journey to the red planet.

The mission took approximately seven months, and Timmy spent most of the trip in a custom-built habitat. This habitat included a climate-controlled sleeping area and robotic arms for providing food and water.

Upon landing on Mars in February 2033, Timmy became an international sensation, with scientists closely monitoring his behavior in the planet's 38% lower gravity. Equipped with a lightweight, pressurized dog suit, Timmy was able to explore the Martian surface safely, with built-in oxygen tanks, temperature regulation, and radiation shielding to protect him from the planet’s extreme conditions.

On March 12, 2033, just a month after his landing, Timmy completed his first full exploration of a Martian crater, gathering data on how living beings adapt to the environment. His successful adaptation to Mars led NASA to announce plans to involve service animals in human missions by 2035."""

paragraphs = article.split("\n\n")

dataset = [SimpleRecord(s) for s in paragraphs if isinstance(s, str)]


# the encoder function must take `texts` (list of strings to encode) and `mode` (either "passage" or "query") as arguments
# the mode argument is required since many text embedding models can produce different embeddings based on whether the input is a passage or a query
# in this example, we use the text-embedding-3-small model from OpenAI, which does not require the mode argument
def encode(
    texts: list[str], mode: Literal["passage", "query"], dim: int = 512
) -> np.ndarray:
    client = OpenAI()
    response = client.embeddings.create(input=texts, model="text-embedding-3-small")
    emb_matrix = np.ndarray((0, dim))
    for resp_emb in response.data:
        emb_matrix = np.r_[
            emb_matrix, np.array(resp_emb.embedding[:dim])[np.newaxis, :]
        ]
    return emb_matrix


@handler
async def enhance_query(msg: Message, chain: HandlerChain):
    chain.variables["query"] = msg
    return (
        "The following query is about a dog named Timmy who went to Mars. Rewrite the query to make it more verbose and easier to understand in one sentence.\n"
        f"Original query: {msg}"
        "Only rewrite the query in one sentence. Do not include any additional information, salutations, or sign-offs."
    )


@handler
async def answer(msg: Message, chain: HandlerChain):
    query = chain.variables["query"]
    prompt = (
        "Answer the given query from the context given below. Do not include any information that is not present in the context.\n"
        f"--- Context start---\n{msg}\n--- Context end ---\n\n"
        f"Query: {query}"
    )
    return prompt


def main(dim=512):
    index_db = FaissIndexDB(
        (dim, "IDMap,Flat"),
        dataset=dataset,
        encoder=partial(encode, dim=dim),
        train=True,
    )

    pipe = (
        enhance_query
        >> OpenAiLLM()
        >> SimilarityRetriever(index_db, k=2, join_policy="\n----x----\n")
        >> answer
        >> OpenAiLLM()
    )
    res = asyncio.run(pipe("When did Timmy land on Mars?"))
    print(res)

    for msg in pipe.history:
        print(f"{msg.sender}:\n{msg.primary}\n")


if __name__ == "__main__":
    main()
