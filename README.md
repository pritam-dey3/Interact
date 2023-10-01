# Interact
A simple python library to interact and build applications with Large Language Models.

## Core Concept
`Interact` has three main components / assumptions:

* Entities in an application communicate through `Message`s.
* `Message`s are passed through `Handler`s that can modify (transform, format, etc.) the `Message`.
* `Handler`s are chained together to form a `Cascade`. `Cascade`s hold a sequence of `Handler`s that are executed in order.

## Installation
```bash
pip install git+https://github.com/pritam-dey3/interact
```

## Example Usage
```python
from interact.base import Cascade, Handler, Message
from interact.handlers import OpenAiLLM
import asyncio


class CompanyNamePrompt(Handler):
    role = "CompanyNameGenerator"
    prompt = (
        "What would be an appropriate name for a business specializing in {product}?"
    )

    async def process(self, msg: Message, csd: Cascade) -> str:
        new_msg = self.prompt.format(product=msg.primary)
        csd.vars["product"] = msg.primary
        return new_msg


class CompanyTaglinePrompt(Handler):
    role = "CompanyTaglineGenerator"
    prompt = (
        "What would be an appropriate tagline for a business specializing in {product}"
        " and with company name {company_name}?\nFormat your output in the following"
        " format:\n<company_name>: <tagline>"
    )

    async def process(self, msg: Message, csd: Cascade) -> str:
        new_msg = self.prompt.format(
            company_name=msg.primary, product=csd.vars["product"]
        )
        return new_msg


name_and_tagline_generator = (
    CompanyNamePrompt() >> OpenAiLLM() >> CompanyTaglinePrompt() >> OpenAiLLM()
)

print(asyncio.run(name_and_tagline_generator.start("socks")).last_msg)
# >> The Sock Spot: Step into Comfort
```

## Why Interact?
Applications with Large Language Models can get complex very quickly. You need more customizability and control over the prompts and their execution to satisfactorily build an application.

`Interact` was ccreated with simplicity and scalability in mind. The core concepts of `Message`s, `Handler`s, and `Cascade`s are simple to understand and gives _You_ the power to build complex applications with ease.

More popular alternatives like `langchain` gets frustrating to use when you want to customize either the process or the prompts according to your needs. `Interact` gives you the control while maintaining a very simple and intuitive API.

 