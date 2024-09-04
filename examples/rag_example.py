# We will use the RAG model to generate a prompt for a given input and then use a similarity retriever to find similar sentences from a dataset.
# This example uses the `SentenceTransformer` library to extract embedding vectors from the sentences.

import asyncio

import numpy as np
import pandas as pd
from interact import handler
from interact.handlers import OpenAiLLM, SimilarityRetriever
from interact.retrieval import SimpleRecord
from interact.retrieval.faiss import FaissIndexDB
from sentence_transformers import SentenceTransformer


def get_sentences(use_urls=False):
    if use_urls:
        from io import StringIO

        import requests

        urls = [
            "https://raw.githubusercontent.com/brmson/dataset-sts/master/data/sts/semeval-sts/2012/MSRpar.train.tsv",
            "https://raw.githubusercontent.com/brmson/dataset-sts/master/data/sts/semeval-sts/2012/MSRpar.test.tsv",
            "https://raw.githubusercontent.com/brmson/dataset-sts/master/data/sts/semeval-sts/2012/OnWN.test.tsv",
            "https://raw.githubusercontent.com/brmson/dataset-sts/master/data/sts/semeval-sts/2013/OnWN.test.tsv",
            "https://raw.githubusercontent.com/brmson/dataset-sts/master/data/sts/semeval-sts/2014/OnWN.test.tsv",
            "https://raw.githubusercontent.com/brmson/dataset-sts/master/data/sts/semeval-sts/2014/images.test.tsv",
            "https://raw.githubusercontent.com/brmson/dataset-sts/master/data/sts/semeval-sts/2015/images.test.tsv",
        ]

        sentences = []
        # each of these dataset have the same structure, so we loop through each creating our sentences data
        url_datasets = []
        for url in urls:
            res = requests.get(url)
            # extract to dataframe
            url_data = pd.read_csv(
                StringIO(res.text), sep="\t", header=None, on_bad_lines="warn"
            )
            url_datasets.append(url_data)
        data = pd.concat(url_datasets)
        data.to_csv("dummy_strings.csv", index=False)

    data = pd.read_csv("dummy_strings.csv")
    sentences = data["1"].tolist()
    sentences.extend(data["2"].tolist())
    sentences = list(set(sentences))
    return sentences


# create a dataset of sentences
sentences = get_sentences(use_urls=True)
print(f"Number of sentences: {len(sentences)}")
dataset = [SimpleRecord(s) for s in sentences if isinstance(s, str)]

# load encoder model
model = SentenceTransformer("nomic-ai/nomic-embed-text-v1", trust_remote_code=True)


def encode(texts: list[str], dim: int = 512) -> np.ndarray:
    return model.encode(texts, convert_to_numpy=True)[:, :dim]  # type: ignore


# create faiss index
index_db = FaissIndexDB(
    (512, "IDMap,IVF30,PQ8"), dataset=dataset, encoder=encode, train=True
)


# define pipeline
@handler
async def create_prompt(msg, chain):
    return f"Describe how do you recognize {msg} without mentioning it's name in one sentence."


pipe = (
    create_prompt
    >> OpenAiLLM()
    >> SimilarityRetriever(index_db, k=3, join_policy="\n----x----\n")
)


if __name__ == "__main__":
    res = asyncio.run(pipe("a bmw car"))
    print(res, end="\n\n")

    for msg in pipe.history:
        print(f"{msg.sender}:\n{msg.primary}\n")
