# destiny-item-bot

## Requirements

* [PRAW: The Python Reddit API Wrapper](https://praw.readthedocs.io)


## How to use

1. create `config.py` and include the following:
   ```
   username = "<reddit_username>"
   password = "<reddit_password>"
   client_id = "<reddit_client_id>"
   client_secret = "<reddit_client_secret>"
   debug = False # set this to True while testing
   ```
2. Initialize new `Bot` and register `Matchers`
3. Execute `run()` function for bot
