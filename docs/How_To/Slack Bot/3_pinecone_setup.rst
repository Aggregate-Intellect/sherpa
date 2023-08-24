Set up Pinecone
===============

By default, Sherpa represents its documents within an in-memory vector 
database. However, if you want to use a cloud vector database instead, 
`Pinecone <https://www.pinecone.io>`__ is available as an option.
 
First go to `pinecone.io <https://www.pinecone.io/>`__ and create a free
account.

Login to your account and you should see your pinecone console.

Click “Create Index”

.. figure:: https://i.imgur.com/fha4AqT.png
   :alt: Imgur

   Imgur

Give a name to your pinecone index

The dimension is 1536, assuming that the embedding model is OpenAI’s
``text-embedding-ada-002`` model. Everything else should be default.

.. figure:: https://i.imgur.com/ihrUrrR.png
   :alt: Create new index

   Create new index

Once your index is created, it should show on the console.

.. figure:: https://i.imgur.com/860adzS.png
   :alt: Created index

   Created index

Now create a new API key.

.. figure:: https://i.imgur.com/TmXXZQY.png
   :alt: New API key

   New API key

Enter your copied API key, index name, and index environment in a
``.env`` file on your local machine, which should be placed inside
``sherpa/apps/slackbot`` directory. Checkout
``apps/slackbot/.env-sample`` as an example template for your working
``.env``. \*Note that namespace is not necessary for testing.
