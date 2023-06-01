ChatGPT-like application for construction of mathematical financial models
==========================================================================

LLMs alone generally struggle with complex mathematical tasks. This
limitation is particularly evident when a problem requires intricate
simulations rather than basic arithmetic or a few simple calculations.
For instance, while GPT-4 can compute the interest paid on a loan, it
cannot determine the loan’s duration over several years. In this talk,
we show how we used ChatGPT to build an interface for a no-code
financial planning application and allow users to use the chat interface
to inspect and inquire about the financial projection model in the
background.

`SLIDES <https://www.tldraw.com/r/v2_c_9rVhxDX0fWGntAuD4ZcFu>`__ \|
`RECORDING <https://youtu.be/NRnjra-WGmY>`__

**SUMMARY**

1.  The interaction between LLMs and financial models is important.
2.  LLMs can be used to build models of the real world and provide
    information about it.
3.  Financial models are simple to see and find, making them a good
    context for LLMs.
4.  The goal is to use mathematical models for socioeconomical systems
    to improve and empower humanity to be more rational.
5.  Financial models are currently not easily accessible to people, but
    democratizing access to these models is important.
6.  LLMs have limitations in logical reasoning capability, but as the
    model scales, it becomes more skilled in performing logical
    reasoning tasks.
7.  If LLMs have reasoning capabilities, they can be used to help people
    understand how the world works and make good plans.
8.  LLMs can be used to simulate real-world scenarios in financial
    models.
9.  LLMs have different capabilities in understanding logical reasoning,
    with larger models performing better.
10. LLMs can generate code to solve financial problems, but may make
    mistakes in understanding certain formulas.
11. LLMs can be programmed to consider different factors, such as
    inflation, in financial simulations.
12. The limitations of LLMs become more apparent when dealing with more
    complex scenarios in financial simulations.
13. LLMs can be used to translate natural language to mathematical
    models, making it easier for non-modelers to understand.
14. Tools like Plan with Flow can be used to create systems that bridge
    the gap between natural language and mathematical models in
    financial simulations.
15. LLMs can be used to create intuitive user interfaces that allow
    non-modelers to interact with financial simulations.
16. To communicate with mathematical models, there is a need for a
    domain-specific language.
17. The process of going from a natural language prompt to a
    mathematical model involves several steps, including entity
    extraction and domain-specific language translation.
18. Intermittent steps such as descriptions of assets may be necessary
    to fit all details into a language model prompt.
19. LLMs can be used to extract financial information from natural
    language prompts and transfer it to a JSON format.
20. A domain-specific language is necessary to communicate with the
    mathematical model in financial simulations.
21. LLMs can be used to create simple user interfaces for financial
    simulations, such as changing assumptions about inflation rates.
22. To change assumptions, a mathematical operation is necessary to
    construct a vector of assumptions for each month.
23. A prompt format can be used to instruct the LLM on how to construct
    the vector, such as specifying when inflation rates change over
    time.
24. LLMs can be used to extract date changes and construct mathematical
    operations to convert assumptions into vectors.
25. A carefully formatted prompt is necessary to ensure accurate
    extraction of information.
26. To answer questions about the model, the LLM needs to be told what
    the mathematical model says and then parse that information.
27. LLMs can be used to answer questions about financial simulations,
    such as whether someone can afford to buy a house.
28. LLMs can be used to reason about financial simulations based on user
    inputs and update the context prompt accordingly.
29. To interact with financial simulations using LLMs, a detailed
    financial summary must be sent to the API to be embedded into the
    conversation context.
30. The ability to update the context prompt with new information allows
    for dynamic and responsive financial simulations.
31. The innovation of this work lies in the ability to use LLMs to
    traverse between natural language and a domain-specific language
    (DSL) for financial models.
32. DSLs are used to abstract complex systems into configuration files
    of parameters and settings, making it easier for non-experts to use.
33. The DSL used in this work simplifies the process of constructing and
    updating financial models in Excel or other software by allowing
    users to use natural language queries and prompts.
34. The integration of LLMs and DSLs allows for dynamic and responsive
    financial simulations with natural language interfaces.
35. The use of DSLs simplifies the process of constructing and updating
    financial models for non-experts by abstracting complex systems into
    configuration files of parameters and settings.
36. The reliability of the response schemas depends on the accuracy and
    completeness of the financial data used to construct the models.
37. The mathematical functions used in financial simulations are highly
    generalizable and can be used to solve complex tasks if the
    parameters and settings are properly defined.
38. Trust is a key factor in the productization of this work,
    particularly in the consumer space where financial decisions are at
    stake.
39. The solution to building trust is to involve humans in the loop,
    giving them control over the financial models and allowing them to
    make their own decisions.
40. The positioning of the product as an analytics tool rather than
    financial advice gives users the expectations of being in control
    and making their own decisions.

**Sina Shahandeh (Founder @ Plan with Flow)**

`Sina <https://www.linkedin.com/in/sinashahandeh/>`__ holds a PhD in
scientific computing and has led data science teams at three startups in
Toronto’s ecosystem. Before founding Plan with Flow, Sina served as the
Vice President of Data Science at ecobee Inc., leading to an exit valued
at $770 million. Currently, Sina is based in Madrid.

.. image:: https://github.com/Aggregate-Intellect/practical-llms/blob/main/docs/img/sinas.png
  :width: 600
  :alt: Sina Shahandeh Headshot