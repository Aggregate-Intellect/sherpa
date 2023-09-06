Set up Sherpa Slackbot in your Own Workspace
============================================

This tutorial describes how to run the Sherpa SlackBot in your own Slack Workspace. 
We will start by installing the dependencies necessary for the SlackBot. Then we will create a 
Slack APP by in a new workspace. Finally, we will connect the SlackBot to the Sherpa backend
so that you can talk to the SlackBot. 

Install Slack App
*****************

In order to make it easier to test the Slack APP, we will create a test Slack Workspace. Skip this step if you already have a Slack Workspace that you can play with. 

* Follow the instructions `here <https://slack.com/help/articles/206845317-Create-a-Slack-workspace>`__ to create a new Slack Workspace.

Next, we will create a new Slack app and add it to the Slack Workspace we just created.  

* Go to https://api.slack.com/apps
* In this page, you can view all apps you have created. Click on the button "Create New App" to create a new app.
      .. image:: slackbot_imgs/slackapp.png
       :width: 720
* Choose **From scratch** and give your app a name (We will use *Sherpa* throughout this tutorial). Then choose the workspace you just created. In my case, I called the app *Sherpa* and the workspace *sherpa-testing*. 
      .. image:: slackbot_imgs/slackapp2.png
       :width: 400
      .. image:: slackbot_imgs/slackapp3.png
       :width: 400
* Once you create the app, you will be redirected to the home page of the newly created app, on the side bar, find *OAuth & Permissions* and add the following *Scopes* (note: you may need to scroll down to see this option). These scopes will grant the Slack bot access to reading, writing, and sending messages to the Slack workspace. 
      .. image:: slackbot_imgs/slackapp4.png
       :width: 400
* Scroll the page and find *OAuth Tokens for Your Workspace*, click on the `install app` option, or click on `reinstall app` if you've already done this before. 
      .. image:: slackbot_imgs/slackapp5.png
        :width: 400
* Once you install the app, you should be able to see it appear in your Slack Workspace. 
      .. image:: slackbot_imgs/slackapp6.png
        :width: 400

**Congratulations! You have successfully created a Slack App and installed it in your Slack Workspace.**

Run the Slackbot Locally
************************
Next, we will run the slack app project locally. The slackapp project is part of this livebook's repository. If you haven't done so, clone the repository for this livebook at https://github.com/Aggregate-Intellect/sherpa. 

After you clone the repository, you can find the slackbot project under `apps/slackbot`. The `README` of the slackbot contains instruction to run the app with docker or a virtual environment, we will repeat the instruction with a local virual environment.

1. Install `conda <https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html?>`__ or `miniconda <https://docs.conda.io/en/latest/miniconda.html>`__ if you don't have it already.
2. Create a new conda environment with python 3.9. 
    :: 

        conda create -n slackbot python=3.9

3. Activate the environment
    :: 

        conda activate slackbot

4. Install the dependencies
    :: 

        pip install -r requirements.txt

5. Configuration: Copy the contents of ``slackbot/.env-sample``
   into your own ``slackbot/.env`` file.
    :: 

        cp .env-sample .env
   * Then, modify your configuration as needed. You need to add the environment variables in ``.env`` following the format of ``.env_sample``. The following parts describe how to access the configuration values that you will add to ``.env``:


  * You can find ``SLACK_SIGNING_SECRET`` and ``SLACK_VERIFICATION_TOKEN`` values in the `Basic Information` page of your Slack App.

    .. image:: slackbot_imgs/slackbot.png
        :width: 400
  * The ``SLACK_OAUTH_TOKEN`` can be found in the `OAuth & Permissions` page of your Slack App.
 
    .. image:: slackbot_imgs/slackbot2.png
        :width: 400
  * The ``OPENAI_API_KEY`` can be found in your OpenAI account page. If you you don't have one, create one at https://platform.openai.com/overview.

  * Serper is a search engine that we use to search for relevant articles. You can find the API key 
    in your Serper account page. If you don't have one, create one at https://serper.dev/. 
    You don't need it to run the app, but it will enable the Internet search function of the SlackBot. If you don't want to have this functionality, you can leave the `SERPER_API_KEY` empty.

  * You may also find there are optional *Pinecone* keys in the `.env` file. 
    Pinecone is a cloud-based vector database, by default, the app runs with an in-memory vector 
    database. However, if you want to build your own cloud vector database, you can learn more 
    about Pinecone here: https://www.pinecone.io/ and on the :doc:`Pinecone setup <3_pinecone_setup>` page.

6. We will need to have some files to load into the vector database and act as the long-term memory of the SlackBot. For the sake of this tutorial, copy the `README.md` file of this project to `apps/slackbot/file`. This file will be used as the long-term memory of the SlackBot.
7. Now, run the app with the following command

  ::

      python bolt_app.py

8. You should see something like below if everything is working properly. 
    
      .. image:: slackbot_imgs/slackbot3.png
        :width: 400

Great! We are almost there to let you communicate with your SlackBot.

Connect Slack Bot to the App
****************************
Up to this point, we have created a Slack App and installed it in a Slack Workspace. We have also run the SlackBot locally. Now, we will connect the Slack App to the SlackBot so that you can talk to the SlackBot in the Slack Workspace.

However, before we can do that, we will need to expose the local app to the Internet. There are many ways to do this, we will use `ngrok <https://ngrok.com/>`__ to expose the local app to the Internet.

1. Download and install ngrok from https://ngrok.com/download.
2. Run the following command in anther terminal window to expose the local app to the Internet. (Note we use port 3000 because we set the `SLACK_PORT` to 3000 in the `.env` file)

  ::

      ngrok http 3000
  
  * You should see this in the terminal window if everything is working properly

    .. image:: slackbot_imgs/slackbot4.png
        :width: 500

Now we have all the pieces ready, let's connect everything together.

3. Go to the `Event Subscriptions` page of your Slack App, and enter the URL of the ngrok forwarding address in the `Request URL` field. In the above image, the URL is `https://efb0-2607-fea8-125e-d700-79b8-a450-f057-a944.ngrok-free.app/slack/events` (Yes! Sadly the URL is randomly generated and we will need to change the URL every time when we restart `ngrok` :(. Don't hesitate to let us know if there is a way to persist the URL :)). Note that the URL should end with `/slack/events`. If everything is working properly, you should see a green check mark next to the URL field as `Verified`.

  .. image:: slackbot_imgs/integration.png
        :width: 500

4. Finally, we need let Slack know when we want the SlackBot to react to the messages. In the `Subscribe to bot events` section, add the following events:

  * `app_mention`

  .. image:: slackbot_imgs/integration2.png
        :width: 500

5. **Last but not least**, click on `Save Changes` button at the bottom of the page.

OK, we are almost there. In order to talk to the Slackbot, we will need to add it to one of the channels . Go to the `#general` channel of your Slack Workspace, click on the members button and select `Integrations -> Add An App`.
    
      .. image:: slackbot_imgs/integration3.png
          :width: 400

6. Select `Sherpa` (or the name you give to your app) in the pop-up window. 

      .. image:: slackbot_imgs/integration4.png
          :width: 400

Now we are all set! You can type any message and add `@Sherpa` (or the name of your app) to start talking with your own slack bot!

      .. image:: slackbot_imgs/integration5.png
          :width: 400

Have fun! And please join our `slack channel <https://aisc-to.slack.com/ssb/redirect>`__ if you are interested in contributing to this project!

Further Reading
***************

* `Slack API <https://api.slack.com/>`__
* `SlackBot <https://github.com/Aggregate-Intellect/sherpa/tree/main/apps/slackbot>`__
