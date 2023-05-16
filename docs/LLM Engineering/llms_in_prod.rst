Integrating LLMs into Your Product: Considerations and Best Practices
=====================================================================

The proliferation of ChatGPT and other large language models has
resulted in an explosion of LLM-based projects and startups. While these
models can provide impressive initial demos, integrating them into a
product requires careful consideration and planning. This talk will
cover key considerations for creating, testing, and optimizing prompts
for LLMs, as well as how to run analytics on key user metrics to ensure
success.

`SLIDES <https://pitch.com/public/7fce9d3f-fec7-40f5-9273-99ff1655a4e8>`__
\| `RECORDING <https://youtu.be/1C3rU3fxcME>`__

**TWITTER THREAD SUMMARY OF THE TALK:**

-  Considerations for adopting LLMs

   -  1/16: Running large language models in house can be costly, which
      is why many people use APIs. It’s important to ensure your use
      case has a good ROI to avoid wasting resources.
   -  2/16: When deciding how much to invest in using LLMs, companies
      need to consider their bet size (level of investment) and company
      size (effort required to adopt LLMs). This should be done with a
      careful assessment of consequences on their existing customers and
      their product development roadmap.
   -  3/16: Therefore companies need to understand their business and
      customers before adopting LLMs. Voiceflow, a conversational AI
      platform used by various verticals, experimented with LLMs and how
      they should be combined with existing capabilities.
   -  4/16: Even large companies, eg. Google’s Bard and Bing’s demos
      have had instances where LLMs generated incorrect information
      damaging their brands. Having humans in the loop, domain experts
      when appropriate, is important to ensure accuracy.
   -  5/16: UX and UI are critical for LLM adoption. Incorporating fun
      and natural features, such as shortcuts and accepting / declining
      recommendations, are important for making LLMs easy to use and
      understand.
   -  6/16: Human-in-the-loop performance improvements at creation time
      are less risky than having that kind of feature in run time. One
      should carefully consider the trade offs when implementing user
      feedback loops.
   -  7/16: Caching might be a good way to reduce cost and improve
      performance. Though it has to be done in a way that context for
      different users is handled properly to ensure the best experience.

-  Deployment methodology for LLMs

   -  8/16: When deploying large language models, there are different
      options to consider. Using a pre-trained model service is easier,
      but building and hosting your own solution gives you more control.
   -  9/16: Building a product that generates revenue is essential, but
      investing time in a minimally viable platform is also important.
      Neglecting the platform can lead to technical debt and slow down
      the iteration process for new models. There should be a balance in
      effort put in model, product, and platform development.

-  Testing and Fine-Tuning for LLMs

   -  10/16: When deploying LLMs in production, testing is crucial.
      Denys Linkov built a test suite to check if prompts work,
      processing the code, running python, and documenting errors. This
      is on top of initial manual testing and collecting errors from the
      data warehouse.
   -  11/16: For example, since the output of Open AI API is
      probabilistic it might return poorly formatted JSON responses.
      This at inference time might be easy to deal with but at high
      volume could cause unforeseen failures in production systems.
   -  12/16: Fine-tuning can solve formatting issues, especially for
      few-shot learning including desired output, examples, and chain of
      thought reasoning.

-  Considerations for Third-Party Providers

   -  13/16: Running a product with LLMs comes with its own set of
      challenges, like unpredictable response formatting, unreliable
      uptime, or other upstream dependencies.
   -  14/16: When choosing NLP provider APIs or open-source libraries,
      it’s crucial to consider their reliability and ease of
      integration. Companies can opt for a single or multiple NLP
      provider APIs based on their required uptime.
   -  15/16: While OpenAI is perceived to have the best models, other
      providers may offer more reliability. The trade-off between model
      accuracy and uptime is a critical consideration for companies
      depending on their service requirements.
   -  16/16: With LLM space moving quickly, it might also become easier
      to deploy own models instead of relying on third-party providers
      at least for some components of the system.

*Resources*

-  `Talk
   Slides <https://pitch.com/public/7fce9d3f-fec7-40f5-9273-99ff1655a4e8>`__
-  `Prompt Engineering
   Guide <https://github.com/dair-ai/Prompt-Engineering-Guide>`__
-  `How GPT3 Works - Visualizations and
   Animations <https://jalammar.github.io/how-gpt3-works-visualizations-animations/>`__
-  `Open AI Product <https://openai.com/product>`__

**Denys Linkov (ML Lead @ Voiceflow)**

`Denys <https://www.linkedin.com/in/denyslinkov/>`__ is the ML lead at
Voiceflow focused on building the ML platform and data science
offerings. His focus is on realtime NLP systems that help Voiceflow’s
60+ enterprise customers build better conversational assistants.
Previously he worked at large bank as a senior cloud architect.
