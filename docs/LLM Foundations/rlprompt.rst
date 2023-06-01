Optimizing Large Language Models with Reinforcement Learning-Based Prompts
==========================================================================

Large language models (LLMs) have the potential to perform a wide range
of tasks by understanding human queries, but they are often sensitive to
the wording of the prompts, which can greatly affect the output. This
talk will introduce RLPrompt, an efficient algorithm that uses
reinforcement learning to systematically search for the best prompts to
improve LLM performance across diverse tasks.

`SLIDES <https://github.com/Aggregate-Intellect/practical-llms/blob/main/LLM%20Foundations/RLPrompt%20Presentation.pdf>`__
\| `RECORDING <https://youtu.be/SGInyKjzF7A>`__

**TWITTER THREAD SUMMARY OF THE TALK:**

-  LLMs Capabilities and Prompt Sensitivity

   -  Large language models (LLMs) are versatile and can perform tasks
      like summarization, code generation, sentiment analysis, dialogue,
      translation, and storytelling depending on the prompt.
   -  The wording of the prompt can significantly affect LLMs’
      performance, making it challenging to find the best prompt for a
      given task. Two prompts with the same meaning can lead to
      different outcomes.

-  Prompt Design Approaches

   -  Designing the best prompt can be time-consuming and repetitive.
      But it’s a great way to get started. The speaker suggests tweaking
      the prompt or trying different options based on intuition. #NLP
      #machinelearning #promptdesign
   -  Another way to find the best prompt is to use a machine to
      generate options. The speaker suggests paraphrasing or editing the
      original prompt and scoring each candidate through the LLM. #NLP
      #machinelearning #promptdesign
   -  Numerical tuning is a third approach to exploring prompt options.
      Instead of tweaking words, numerical tuning involves passing the
      numbers that represent the words into the LLM. This method can
      help explore all possible options without the limitations of human
      space. #NLP #machinelearning #numericaltuning

-  Reinforcement Learning-based Prompt Optimization

   -  Prompt optimization is a challenging problem due to the large
      number of candidates. One way to address it is to formulate it as
      a reinforcement learning problem. This allows for more effective
      identification of the best prompts.
   -  The reinforcement learning approach involves training a prompt
      policy to learn correlations between words and their underlying
      score or reward. It is a powerful way to optimize prompts for
      large language models.
   -  Optimized prompts for RL problems can perform better than
      human-written prompts, even if they don’t follow human language.
      This utility of RL prompts is important to understand.
   -  The optimized prompts can transfer well across models, and the
      reinforcement learning-based optimization allows for more
      effective identification of the best prompts. Careful optimization
      is key for large language models.

-  Framework for Prompt Optimization

   -  I developed a framework that combines a smaller language model for
      word correlations and a larger model for tasks. It can perform
      few-shot text classification and unsupervised control text
      generation. #MachineLearning #NLP
   -  Optimized prompts for the framework are consistently among the
      best performers, unlike manual prompts, which can vary widely in
      performance. Check out my graph comparing their performance across
      different models. #AI #NLP
   -  Shorter optimized prompts lead to faster model runs and lower
      costs. I found that optimized prompts trained on one model can
      also be applied to other models with similar or even better
      performance. #MachineLearning #Optimization
   -  My framework is better than human-written prompts at capturing how
      language models respond to prompts. See the graph comparing the
      performance of manual prompts vs. optimized prompts. #NLP
      #DataScience
   -  I made sure to package my framework code well and make it easy to
      set up. You can find it on GitHub. For instance, running a test
      style transfer experiment requires only 51 lines of code.
      #OpenSource #Python
   -  Optimized prompts from my framework can even turn negative
      sentences into more positive ones while preserving the original
      meaning. Want to see a demo? #AI #NLP #SentimentAnalysis

-  Future of Language Models

   -  Language models can recognize patterns beyond just human language.
      This means there may be prompts that work when prompt engineering
      fails. #LanguageModels #AI #PromptEngineering
   -  To use language models for more than a single query, we need to
      develop new ways of interacting with them that differ from how
      humans talk. #AI #NLP #LanguageModels
   -  Words are better than vectors for prompt optimization. They’re
      transferable and can be applied to different models with similar
      performance. Also, word-based prompts are less sensitive to model
      parameter changes than vector-based ones. #AI #NLP
      #PromptOptimization

*Resources*

-  RLPrompt: Optimizing Discrete Text Prompts with Reinforcement
   Learning
   `blog <https://blog.ml.cmu.edu/2023/02/24/rlprompt-optimizing-discrete-text-prompts-with-reinforcement-learning/>`__
   \| `paper <https://arxiv.org/abs/2205.12548>`__ \|
   `code <https://github.com/mingkaid/rl-prompt>`__
-  `Prefix-Tuning: Optimizing Continuous Prompts for
   Generation <https://arxiv.org/abs/2101.00190>`__
-  `Making Pre-trained Language Models Better Few-shot
   Learners <https://aclanthology.org/2021.acl-long.295.pdf>`__
-  `Prompt Waywardness: The Curious Case of Discretized Interpretation
   of Continuous Prompts <https://arxiv.org/abs/2112.08348>`__
-  `A Recipe For Arbitrary Text Style Transfer with Large Language
   Models <https://arxiv.org/abs/2109.03910>`__

**Mingkai Deng (PhD Student @ CMU)**

`Mingkai Deng <https://www.linkedin.com/in/mingkaideng/>`__ is a PhD
student at Carnegie Mellon University working at the intersection of
machine learning, computer vision, and natural language processing.
Prior to that, he was a data scientist who led award-winning projects
and built analytics products that serve multiple Fortune 500 clients.

.. image:: https://github.com/Aggregate-Intellect/practical-llms/blob/main/docs/img/mingkaid.jpeg
  :width: 600
  :alt: Mingkai Deng Headshot