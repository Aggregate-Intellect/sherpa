Running LLMs in Your Environment
================================

The availability of Large Language Models as a service (LLMaaS) has
sparked a new wave of applications, use cases and companies. But what
alternatives exist if you want to host your own LLMs? In this talk we’ll
cover the landscape of LLMs and their deployment options. We’ll discuss
the tradeoffs of hosting your own LLM vs using a commercial offering,
including security, compliance, cost and delivery times. We’ll also
cover a number of available open source options and how they can be
hosted within your own environment whether a virtual private cloud or on
prem.

`SLIDES <https://pitch.com/public/9120173c-bb54-4806-9849-e2b6670b2bcd>`__
\| `RECORDING <https://youtu.be/REv-GgieWto>`__

**SUMMARY**

-  The talk covers the topic of deploying large language models in your
   own environment, specifically models that perform better than the
   original GPT-3.
-  Several new projects related to large language models have been
   released, such as Open Assistant and Red Pajama data set.
-  Controversy exists around what constitutes a large language model,
   with Denys defining it as any general purpose model that performs
   better than original GPT-3.
-  Francy 5 XXL, Llama 13 billion, and Flan XXL are all considered large
   language models under this definition.
-  Flan is the only open source large language model that can be used
   commercially due to Llama’s restrictive license.
-  Reasons for deploying large language models in your own environment
   could include performance reasons and licensing restrictions.
-  Compliance and data localization requirements may necessitate
   deploying large language models in specific regions or on-premises.
-  Keeping domain-specific data in-house can be advantageous for
   training models and maintaining a strategic advantage.
-  Costs associated with training, inference, and embedding should be
   considered when deciding whether to deploy large language models in
   your own environment.
-  Deploying a large language model in your own environment can involve
   significant costs, both monetary and in terms of uptime and latency.
-  Factors to consider when deciding whether to deploy include
   compliance and data localization requirements, the advantages of
   keeping domain-specific data in-house, and trust in third-party
   vendors.
-  Considerations around costs include training cost, inference cost,
   embedding cost, and network cost.
-  Uptime and latency can also be important factors to consider when
   deciding whether to deploy in your own environment or use a
   third-party service.
-  Trust in vendors, network security, compliance certifications, and
   identity and access management are important considerations when
   deciding whether to deploy large language models in your own
   environment or use a third-party service.
-  In terms of network security, private connections and virtual private
   clouds are options for organizations that prioritize this type of
   defense.
-  Identity and access management can be easier to manage when deploying
   in your own environment, with the ability to use existing cloud
   identities and follow standard IM practices.
-  Identity and access management is crucial for managing user access to
   multiple services and preventing security compromises.
-  The definition of “own environment” can vary, depending on factors
   like cloud infrastructure and data localization requirements.
-  Some services, like Databricks, offer the option to deploy within
   your own cloud environment while still providing the service’s
   interface.
-  On-premises solutions and server applications were more common in the
   past, but cloud computing has changed the landscape.
-  Protecting API keys and preventing security breaches is important for
   organizations using third-party services like Open AI.
-  Segmenting access across different environments, such as dev,
   staging, and prod, can help prevent security breaches and limit the
   impact if one key is compromised.
-  The definition of “own environment” can depend on factors like
   dedicated URLs or contractual obligations, but it’s ultimately up to
   the organization to determine what they consider to be their own
   environment.
-  Setting up a mature ML Ops practice is crucial for deploying LLMs in
   your own environment, but it can be a complex and difficult process.
-  Deploying LLMs in your own environment can range from using a fully
   managed solution to training your own model from scratch.
-  Latency, cost, and model hallucination are some of the challenges
   that come with hosting LLMs in your own environment.
-  There are various libraries, frameworks, and papers available to help
   with LLM deployment and training, such as Deep-speed Chat, Ray’s
   Alfa, and Llama C++.
-  It’s important for the community to share and discuss their
   experiences with LLM deployment and training, as well as relevant
   architecture diagrams and blog posts.
-  Laura is a way to fine-tune models with a minimal number of
   parameters, which can improve performance without requiring a lot of
   resources.
-  Stable 8-bit inference allows for running large language models on
   smaller hardware, which can make it easier to deploy models in
   production.
-  4-bit inference is a recent development that allows for high accuracy
   with very little bandwidth, which is impressive.
-  Advancements in hardware and libraries are making LLM Ops more like
   ML Ops, and it’s becoming easier to manage and deploy large language
   models.
-  The notebook demo shows that it’s possible to run large language
   models on easy-to-access hardware like T4 GPUs, but it’s important to
   do proper ML Ops deployments.
-  Zero trust is an interesting concept in security where access is
   granted based on authentication and smart monitoring rather than
   assuming certain criteria for access.
-  Multi-tenancy for large language models can involve segregating
   instances for data storage, compute, and model weights, but it can be
   expensive.
-  Using Laura for fine-tuning can make it easier to have a shared
   service for hosting the primary language model and swapping out
   smaller sidecars for each user.
-  The practicality of multi-tenancy depends on the organization’s
   priorities and cost considerations.
-  There are frameworks like Microsoft Semantic Kernel and marketplaces
   where you can rent cloud compute from other people, which can
   decentralize compute and reduce reliance on big players.
-  Federated learning and decomposition techniques can be interesting
   for distributed computing but networking latency and bandwidth can be
   a challenge for larger models.
-  Prompt injection can happen regardless of where your application is
   deployed and is a security risk, especially if you have many services
   relying on it.
-  Companies training models should be aware of the potential for
   specific prompts to generate malicious code, and application and data
   design are important considerations for avoiding these risks.
-  Good data security practices are important for ensuring the
   reliability and security of language models.
-  Latency and uptime are still major challenges for large language
   models, and the user experience needs to be taken into consideration.
-  Hosting your own language model may not always be the best solution,
   as commercially available models often still perform better.
-  Entity GPUs may offer a potential solution to latency issues, but
   further exploration is needed.

**Denys Linkov (ML Lead @ Voiceflow)**

`Denys <https://www.linkedin.com/in/denyslinkov/>`__ is the ML lead at
Voiceflow focused on building the ML platform and data science
offerings. His focus is on realtime NLP systems that help Voiceflow’s
60+ enterprise customers build better conversational assistants.
Previously he worked at large bank as a senior cloud architect.

.. image:: https://github.com/Aggregate-Intellect/practical-llms/blob/main/docs/img/denysl.jpeg
  :width: 600
  :alt: Denys Linkov Headshot