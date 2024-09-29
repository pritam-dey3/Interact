.. Interact documentation master file, created by
   sphinx-quickstart on Mon Oct  2 00:53:19 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Interact's documentation!
====================================

.. toctree::
    :maxdepth: 2
    :caption: Contents:

    getting-started
    base
    handlers
    retrieval
    examples_toc

Interact
--------

A simple python library to interact and build applications with Large Language Models.

Installation
------------

.. code-block:: bash

   pip install -U "interact @ git+https://github.com/pritam-dey3/Interact.git"

or, if you use faiss for similarity search

.. code-block:: bash
    
    pip install -U "interact[faiss] @ git+https://github.com/pritam-dey3/Interact.git"


Start learning about Interact by reading the :doc:`getting-started` guide.

Why Interact?
-------------

Applications with Large Language Models can get complex very quickly. You need more customizability and control over the prompts and their execution to satisfactorily build an application.

``Interact`` was created with simplicity and scalability in mind. The core concepts of ``Message`` s, ``Handler`` s, and ``Cascade`` s are simple to understand and give *You* the power to build complex applications with ease.

More popular alternatives like ``langchain`` get frustrating to use when you want to customize either the process or the prompts according to your needs. ``Interact`` gives you control while maintaining a very simple and intuitive API.

