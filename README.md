# Introduction
Playing around with Amazon's Alexa using Flask-Ask. The plan was to get clients who wanted their own personalized Alexa skills. 

They would say, "Alexa, how long until my subway comes?". And Alexa would respond with that information. Creating custom Alexa skills that pulled from accessible web apis and returning that information should have been trivial, thanks to the generously open-source work of [Flask Ask](https://github.com/johnwheeler/flask-ask) 

If you actually want to run these skills, in the manner I did, that would've allowed multiple "clients" to access their own services, you'd have to: set up a server, install the code, and configure an Amazon Alexa Developer Console to point to that server. I also included local server instructions that used ngrok.

## Server setup
I was able to set up a virtual private server with ubuntu, gunicorn, nginx to allow multiple endpoints, with the goal of having multiple clients access their own `alexa.py` in their own separate directory, with their own sqlite database. I included two markdown notes `set_up_gunicorn_process.md` and `setup_new_client.md` that should help with the process.

## Local setup
* Clone this repo into your local repo
* cd into the directory, and `virtualenv env`
* `source env/Script/activate`
* `pip install -r requirements.txt`
* `python alexa.py`
* ngrok http 5000
    - see [here](https://developer.amazon.com/blogs/post/Tx14R0IYYGH3SKT/Flask-Ask-A-New-Python-Framework-for-Rapid-Alexa-Skills-Kit-Development) for detailed instructions
* now you have to set up your Amazon Alexa Developer console

## Set up on Amazon Alexa Developer Console
The way this is used in conjunction with Amazon Alexa's app testing feature on the [alexa developer console](), was to point it at a registered subdomain, e.g., phillip.nobisalexaservices.com

This will assume you're doing local setup, but it should be extremely similar.
* Create a new skill. See [this](https://developer.amazon.com/en-US/alexa/alexa-skills-kit/tutorials/fact-skill-1) or other similar tutorials.
* Create a new intent:
    * see `CryptoIntent-utterances.csv` and alexa_developer_console_1.PNG
* Click on endpoint
    * put in your ngrok url and choose I will upload a self-signed certificate in X 509 format.
* Go to Test
    * In the "Type or click and hold the mic" input, put in, run testing (or whatever invocation name you used when you created the new Alexa skill)
    * You'll actually have to change a little authentication check I put in. Alternatively, you can modify `AlexaMaster.verify_user()` to disable authentication
        - `sqlite3 phillip.db`
        - `update config
set data = '{"trains": {"northbound": "L16N", "southbound": "L13S", "train_line_name": "L Train", "direction": "Northbound", "stop_name": "Dekalb St"}, "user": {"access_key": "Your System.user.userId"}}'
where id =1;`
            + You can find `Your System.user.userId` in the alexa developer console Skill I/O. In Json Input, you should be able to find context.System.user.userId.
    * then put in "crypto status" (or other intents you set up)