Learning-free Controllable Text Generation for Debiasing
========================================================

Large language Models (LLMs, e.g., GPT-3, OPT, TNLG,…) are shown to have
a remarkably high performance on standard benchmarks, due to their high
parameter count, extremely large training datasets, and significant
compute. Although the high parameter count in these models leads to more
expressiveness, it can also lead to higher memorization, which, coupled
with large unvetted, web-scraped datasets can cause different negative
societal and ethical impacts such as leakage of private, sensitive
information and generation of harmful text. In this talk, we introduce a
global score-based method for controllable text generation that combines
arbitrary pre-trained black-box models for achieving the desired
attributes in generated text from LLMs, without involving any
fine-tuning or structural assumptions about the black-box models.

`SLIDES <https://cseweb.ucsd.edu/~fmireshg/llms_april.pdf>`__ \|
`RECORDING <https://youtu.be/r8pAP9zMM_4>`__

**SUMMARY**

-  The speaker is introducing herself and her background, which includes
   defending her PhD dissertation and being a postdoc at the University
   of Washington, where she works on privacy and ethics in natural
   language processing (NLP).
-  The speaker is presenting a paper called “Mix and Match,” which is a
   learning-free controllable text generation method that uses existing
   models as building blocks.
-  The paper has different applications, including ethical and privacy
   ones, but it’s mainly focused on large language models and interfaces
   between them and financial models.
-  Large language models are transformer-based models that have huge
   parameter accounts and are pre-trained on massive datasets scraped
   from the web.
-  Large language models are good at generating fluent text that looks
   human-written but may not be truthful, and they have been subject to
   hype and excitement before, but it’s unclear where their development
   will lead.
-  Large language models can memorize harmful or biased data from the
   web and regurgitate it, which poses ethical concerns, especially if
   they are put into products.
-  The “Mix and Match” method aims to address some of these concerns by
   allowing more control over the model’s output and leveraging the
   strengths of existing models.
-  The speaker welcomes questions and interaction during the talk.
-  The speaker’s main goal is to present a method called “Mix and Match”
   that allows for more control over text generation from large language
   models by using existing models as building blocks.
-  The speaker emphasizes the importance of giving control to smaller
   organizations and individuals who may not have the resources to train
   their own models.
-  Large language models can leak their training data, which poses
   privacy concerns that have been previously identified but have become
   more prominent with the advent of transformer models like GPT-2.
-  The mix and match method aims to address some of these privacy
   concerns by allowing for more control over the model’s output without
   requiring additional training on sensitive data.
-  The talk is interactive, and the speaker welcomes questions and
   interruptions.
-  Large language models can generate creepy or inappropriate content,
   which can be a privacy concern and might require additional
   fine-tuning or control mechanisms to prevent.
-  One way to use large language models is for text generation, but
   controlling the output to enforce specific attributes or revisions
   can be challenging.
-  The Mix and Match method, which the speaker will discuss, aims to
   address some of these challenges by providing more direct control
   over generation without requiring additional training or resources.
-  Controllable generation and agency control are two specific tasks
   that the Mix and Match method can help to achieve. These tasks are
   important for applications like story writing or movie dialogues,
   where biases or stereotypes can be prevalent.
-  Gender bias and representation in movies and other works of fiction
   is a problem that can be addressed through techniques like attribute
   control in text generation.
-  Existing methods for attribute control include building or training
   new models, fine-tuning on specific data, or rejection sampling.
   However, these methods have limitations and may not be efficient or
   effective for all tasks.
-  The Mix and Match method aims to address some of these limitations by
   using a discriminator to directly enforce a desired attribute at
   decoding time. This approach requires fewer resources and can be more
   flexible than previous methods.
-  Some previous work in this area includes Pplm and Fudge, which both
   use discriminators to modify the generation of text. However, these
   methods have limitations and may require access to the full model,
   making them less suitable for black box models like GPT-3.
-  The Future Discriminator is a discriminator that is trained on all
   possible completions of uncompleted sentences. It assigns
   probabilities to each potential completion and can be used in
   conjunction with a generative model to create calibrated outputs that
   meet specific attribute constraints.
-  Fudge is a method for modifying the generation of text using a
   discriminator, but it requires access to a future discriminator and
   may not be suitable for black box models like GPT-3.
-  The proposed method involves building a globally normalized model
   that combines the potentials from various experts and heuristics. The
   potentials are treated as energy scores, and the model assigns
   probabilities to all possible sequences of words.
-  The proposed method is flexible and easy to use, as it allows for the
   composition of any number of models and constraints. It can also
   accommodate discrete constraints that are not differentiable, which
   is a limitation of prompting models like GPT.
-  The energy function is used to consolidate and enforce multiple
   constraints on the generation of text. It represents a sum of energy
   scores from various expert models and heuristics, and it can
   accommodate discrete constraints.
-  Sampling from an energy model is an iterative process that involves
   randomly selecting a token from the sequence, proposing a replacement
   from a model like BERT, and correcting the proposal using a
   correction step that involves the energy language model.
-  The normalization constant in the energy function is intractable, but
   there are methods for sampling from an energy model without
   calculating the probability distribution directly. The Metropolis
   Hastings Correction Step is one such method.
-  The iterative sampling process for generating text involves proposing
   replacements using a model like BERT and then correcting the proposal
   using the energy language model, which consolidates multiple
   constraints on the generation of text.
-  The corrector step is a Metropolis Hastings Correction Step, which
   involves checking if the energy improves after proposing a
   replacement and accepting or rejecting the proposal based on that.
   This is similar to Markov Chain Monte Carlo (MCMC) sampling.
-  The quality of the proposal model affects the diversity and
   appropriateness of the generated text.
-  The results of the method will be shown later in the talk.
-  The speaker acknowledges that there is a lot of math involved in the
   checking and correction steps, and that the method is similar to MCMC
   sampling.

**Fatemehsadat Mireshghallah (PhD Student @ UC San Diego)**

`Fatemeh <https://twitter.com/limufar>`__ received her Ph.D. from the
CSE department of UC San Diego and will join UW as a post-doctoral
fellow. Her research interests are Trustworthy Machine Learning and
Natural Language Processing. She is a recipient of the National Center
for Women & IT (NCWIT) Collegiate award in 2020 for her work on
privacy-preserving inference, a finalist of the Qualcomm Innovation
Fellowship in 2021 and a recipient of the 2022 Rising star in
Adversarial ML award.

.. image:: https://github.com/Aggregate-Intellect/practical-llms/blob/main/docs/img/fatemeh.jpeg
  :width: 600
  :alt: Fatemehsadat Mireshghallah Headshot