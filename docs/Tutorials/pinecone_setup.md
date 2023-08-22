
# Guide for quick setup of Pinecone

First go to [pinecone.io](https://www.pinecone.io/) and create a free account.

Login to your account and you should see your pinecone console.

Click "Create Index"

![Imgur](https://i.imgur.com/fha4AqT.png)

Give a name to your pinecone index

The dimension is 1536, assuming that the embedding model is OpenAI's `text-embedding-ada-002` model. Everything else should be default. 

![Create new index](https://i.imgur.com/ihrUrrR.png)

Once your index is created, it should show on the console.

![Created index](https://i.imgur.com/860adzS.png)

Now create a new API key.

![New API key](https://i.imgur.com/TmXXZQY.png)

Enter your copied API key, index name, and index environment in a `.env` file on your local machine, which should be placed inside `sherpa/apps/slackbot` directory. Checkout `apps/slackbot/.env-sample` as an example template for your working `.env`. *Note that namespace is not necessary for testing.


