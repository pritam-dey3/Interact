
===============
Getting Started
===============

Core Concept
------------

.. mermaid::

    graph LR
        subgraph "HandlerChain"
            A[Handler 1] -- "Message" --- B[Handler 2]
            B -- "Message" --- C[Handler 3]
        end
        Input["Input (Message)"] --> A
        C --> Output["Output (Message)"]


``Interact`` has three main components / assumptions:

- Entities in an application communicate through ``Message`` s.
- ``Message`` s are passed through ``Handler`` s that can modify (transform, format, etc.) the ``Message``.
- ``Handler`` s are chained together to form a ``HandlerChain``. ``HandlerChain`` s hold a sequence of ``Handler`` s that are executed in order.



Example Usage
-------------

We will build a simple application that generates a company name and tagline based on a product. We will do this in two steps:

- Generate a company name based on a product.
- Generate a tagline based on the company name and product.

Importing neccessary modules
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. code-block:: python

    import asyncio

    from dotenv import load_dotenv

    from interact import HandlerChain, Message, handler
    from interact.handlers import OpenAiLLM

    load_dotenv()  # load openai api key from .env file

Define handlers
~~~~~~~~~~~~~~~
We define two ``Handler`` s, ``CompanyNamePrompt`` and ``CompanyTaglinePrompt`` that will generate the prompts for the company name and tagline.

.. code-block:: python

    @handler
    async def company_name(msg: Message, chain: HandlerChain) -> str:
        chain.variables["product"] = msg.primary
        return (
            f"What would be an appropriate name for a business specializing in {msg.primary}?"
            "Only mention the company name and nothing else."
        )


    @handler
    async def company_tagline(msg: Message, chain: HandlerChain) -> str:
        return (
            f"What would be an appropriate tagline for a business specializing in {chain.variables['product']}"
            f" and with company name {msg.primary}?\nFormat your output in the following"
            f" format:\n{msg.primary}: <tagline>"
        )

Note that:

- Interact allows you to define simple async functions as ``Handler`` s. These functions are responsible for *transforming* the ``Message``s.
- You may choose to do anything inside these functions, including making API calls, formatting the prompts, anything your application needs to transform the input ``Message``.
- The functions are decorated with the ``@handler`` decorator to indicate that they are ``Handler`` s. Under the hood, the decorator creates a ``Handler`` object from the function.
- The input to the function is a ``Message`` and current ``HandlerChain``. The ``Message`` is the resulting output from the previous ``Handler`` in the ``HandlerChain``.
- The current ``HandlerChain`` is passed to the function to allow handlers to create and access variables in the ``HandlerChain``. This is useful when you want to share information across multiple handlers in a ``HandlerChain``. Note in this example, in  ``company_name`` we store the product name in the variable ``product`` and accessed it later in ``company_tagline`` handler.

Define the Chain
~~~~~~~~~~~~~~~~

We chain the ``Handler`` s using the ``>>`` operator to form a ``HandlerChain``. Then we start the chain by calling it with the initial ``Message`` "socks".

.. code-block:: python

    name_and_tagline_generator = (
        CompanyNamePrompt() >> OpenAiLLM() >> CompanyTaglinePrompt() >> OpenAiLLM()
    )
    print(asyncio.run(name_and_tagline_generator("socks")))
    # The Sock Spot: Step into Comfort

