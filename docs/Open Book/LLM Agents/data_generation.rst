Leveraging Language Models for Training Data Generation and Tool Learning
=========================================================================

An emerging aspect of large language models is their ability to generate
datasets that allow them to self-improve. A fascinating recent example
is Toolformer (`Schick et al. <https://arxiv.org/abs/2302.04761>`__) in
which LLMs generate fine-tuning data that helps them learn how to use
tools at run-time. In this talk, we’ll examine this trend by taking a
close look at the Toolformer paper and other related research.

`SLIDES <https://github.com/Aggregate-Intellect/sherpa/blob/main/LLM%20Foundations/Self-Improving%20LLMs.pdf>`__
\| `RECORDING <https://youtu.be/Zk_UcqvTTAA>`__

**SUMMARY**

-  Large Language Models and Synthetic Data

   -  As AI adoption increases, the growing demand for human annotations
      will quickly surpass human capacity.
   -  One of the interesting new areas is to use large language models
      to create the training data that further improve themselves.
   -  These kinds of data augmentation techniques can be used to improve
      large language models, reducing the need for human annotation of
      training data. This can reserve the more expensive human labor for
      creating high-quality or mission critical datasets.
   -  Another trend we’re seeing in the industry is that human
      annotations will be used more for creating evaluation or quality
      control datasets, while LLMs will be used for generating training
      data. #machinelearning #datageneration #humansintheLoop

-  Techniques for Filtering Data for LLM Fine-Tuning

   -  Choosing the right data for fine-tuning is essential for improving
      LLMs’ performance. Various approaches can be used to filter down
      the generated data for direct use, or human annotator
      intervention.
   -  There are multiple ways to filter a data set for LLM fine-tuning,
      in this talk we discuss the following four: a perplexity-based
      approach (Toolformer), AI annotator (RLAIF), diversity of
      fine-tuning samples (Self-instruct), and self-consistency.

-  `Toolformer <https://arxiv.org/abs/2302.04761>`__

   -  Toolformer splits up a set of unlabelled data set and samples API
      calls to generate possible inputs and outputs for different tools.
      It then uses the model’s loss (perplexity/entropy) to predict the
      next words in the sequence to determine whether or not the tool
      has made the task easier.

-  `Reinforcement learning from AI
   feedback <https://arxiv.org/abs/2212.08073>`__ (RLAIF) for Harmless
   and Helpful Language Models

   -  RLAIF is a promising application for large language models where
      models can edit their own mistakes and learn from this signal.
   -  To train the model, harmful responses are generated through red
      teaming requests, and a ‘Constitution’ is used to guide the
      model’s behavior and critique its responses. The model is then
      fine-tuned on a dataset of revisions based on its critiques.
      #RedTeaming #ModelTraining
   -  The Constitution is created by humans as a guideline for the
      model’s behavior, but the model is able to critique itself and
      generate revisions based on the Constitution. This allows for more
      training data to be generated using the model itself.

-  `Self-Instruct: Aligning Language Model with Self Generated
   Instructions <https://arxiv.org/abs/2212.10560>`__

   -  This paper discusses using a model to generate new tasks and
      instructions to fine-tune itself on.
   -  It uses a diversity metric to choose samples - prioritizing
      generations that are significantly different from its current
      training data.

-  `Fine-Tuning Language Models with
   Self-Consistency <https://arxiv.org/abs/2210.11610>`__

   -  `Self-consistency <https://arxiv.org/abs/2203.11171>`__ is a
      recent concept in LLMs that involves creating multiple generations
      for the same input and using a form of voting to choose the most
      common one.
   -  This technique does not require the model to know the ground
      truth, meaning it can be applied on unlabelled data, but as the
      models become larger, the most frequent output is often the
      correct one.
   -  The model filters down data using self-consistency, and if the
      majority of generations produce a specific output, e.g., “nine,”
      the model takes all the cases where “nine” was generated as the
      output, assuming that these are correct, and feeds them back into
      the model which creates a feedback loop that improves the model’s
      performance over time.

*Resources*

-  `Toolformer: Language Models Can Teach Themselves to Use
   Tools <https://arxiv.org/abs/2302.04761>`__
-  `Constitutional AI: Harmlessness from AI
   Feedback <https://arxiv.org/abs/2212.08073>`__
-  `SELF-INSTRUCT: Aligning Language Model with Self Generated
   Instructions <https://arxiv.org/abs/2212.10560>`__
-  `Large Language Models Can
   Self-Improve <https://arxiv.org/abs/2210.11610>`__
-  `Self-Consistency Improves Chain of Thought Reasoning in Language
   Models <https://arxiv.org/abs/2203.11171>`__

----

**Gordon Gibson (ML Lead @ Ada)**

`Gordon <https://www.linkedin.com/in/gordon-gibson-874b3130/>`__ is the
Senior Engineering Manager of the Applied Machine Learning team at Ada
where he’s helped lead the creation of Ada’s ML engine and features.
Gordon’s background is in Engineering Physics and Operations Research,
and he’s passionate about building useful ML products.

.. image:: ../_imgs/gordong.jpeg
  :width: 400
  :alt: Gordon Gibson Headshot