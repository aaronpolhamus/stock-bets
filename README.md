# stock-bets
Stock bets' goal is to make it fun for groups of friends to place competitive, real-money stock market bets. Think of a cross between fantasy football and poker for people who like stocks.

## Getting started
* Make sure you have Docker installed and running
* Clone this repo
* Place an `.env` file in the `/backend` directory that defines the following variables:
  - `SECRET_KEY` (string): An impossible-to-guess secret key used for encrypting API data
  - `MINUTES_PER_SESSION` (integer):  How many minutes should a logged-in user's session last for (1440 is recommended)
  - `DB_HOST` (string): The MySQL database host for the API
  - `DB_PORT` (int): What port to expose the DB on
  - `DB_USER` (string): The user that the backend will use to login to the DB 
  - `DB_NAME` (string): The name of the DB that the aapplication will use
  - `DB_PASSWORD` (string): The DB password
  - `SQLALCHEMY_TRACK_MODIFICATIONS` (`True`/`False`): Set to `False` unless you have a really good reason not to
  - `SQLALCHEMY_ECHO` (`True`/`False`): Same here
  - `DEBUG_MODE` (`True`/`False`): As a rule of thumb, `True` for development, `False` for production
  - `TEST_CASE_UUID` (string): When you run the `backend.database.mock_data` as a main function (this happens automatically during functional API testing, or when you call `make db-mock-data`), you populate the database with a bunch of mock data. This can be useful for local development. By setting `TEST_CASE_UUID` to the uuid of the account that you use to develop with, your user account will automatically be populated with these fixtures they're run. The best way to do this is to leave this variable unset, login once with the account you'll use to develop, and then copy and paste this value from the `users` table. 
  - `TEST_CASE_EMAIL` (you@example.com): Same as above for the uuid: you should define these right next to each other in your dev `.env` file.  
* Place an `.env` file in the `/frontend` directory that defines the following variables:
  - `REACT_APP_GOOGLE_CLIENT_ID` (string): The Google client ID that the API is using for OAuth
  - `REACT_APP_FACEBOOK_APP_ID` (string): The Facebook application ID used for OAuth
* Follow the instructions [here](https://stackoverflow.com/questions/10175812/how-to-create-a-self-signed-certificate-with-openssl) to generate `cert.pem` and `key.pem` files. Place these in `/backend`
* To use the frontend with SSL locally, paste `chrome://flags/#allow-insecure-localhost` into your Google Chrome url. Just be careful: you may want to turn this back on at some point.
* `cd` to the repo root and run:
```
set -a
source backend/.env
source frontend/.env
cd frontend
npm run build
cd ..
make backend-build
```

If all environmental variables are properly defined this should be about all there is to it. To start the API server run `make backend-up`. `make backend-bash` and `make db-mysql` are shortcuts to the inside of each of these containers. To run the frontend during local development run `npm start` from the `/frontend` directory. It is already configured to run with the backend container as a local server proxy.

The `stock-bets` app has no toggles in the code of environmental variable that defines whether it is in development, production, testing, or staging. Rather, its behavior in each environment is purely a function of the environmental variables + non-versioned assets that define the resources that it has access to and the way it behaves. Here's a diagram of those non-versioned assets to accompany the description above: 
```
/stock-bets
|
|__/backend
|  |__.env
|  |__.cert.pem
|  |__.key.pem
|
|__/frontend
   |__.env
```

### Troubleshooting
* _MySQL db won't fire up:_ 
Sometimes the volume gets corrupted or some other problem that errors out the containers startup crops up. When this happens the easiest way to deal with the problem is to remove the MySQL image, prune all volumes, restart docker (for good measure), and then invoke `make db-up` to rebuild the container. [See this guide](https://github.com/Radu-Raicea/Dockerized-Flask/wiki/%5BDocker%5D-Remove-all-Docker-volumes-to-delete-the-database).
* _I'm getting unexpected DB connection errors:_ There are two "acceptable" ways to communicate with the DB in `stockbets`. All connections should be handled via the `scoped_session` object `db_session` in `database.db`. You can either communicate with the DB via the pure ORM, or you can open a db connection for sending raw SQL (minus string injections), using a context, e.g. `with db_session.connect() as conn: ...`. If you take this route, _it's essential that you close your transaction block with `db_session.remove()` or `db_session.commit()` when you are finished_. Dangling connections will cause downstream operations against the DB to break, even if they were instantiated inside a different scoped environment. 
* _What's up with all this really gnarly mocking?_: Yep, sorry about that. Because `stockbets` simulates a brokerage platform, where the logic for executing orders, gathering prices, and calculating winners is heavily time dependent, it's necessary to mock in a targeted way every invocation of `time.time()` in order to maintain test consistency. That's what makes `test_celery_tasks` so hairy, and can make debugging these tests when they break incredibly challenging. Superior test design patterns welcome if you see a better way! When debugging, set break points next to the the `time.time()` invocations to verify that your mocks are making it to the right place. 
* _How do I test celery tasks?_: When possible, it's nice to actually use celery in the same way that it will be used in production with the `task.delay(...)` invocation. However, it's frequently necessary to mock values into tasks, and to do this you need to run the task locally instead of on the worker clusters. For this, use `task.apply(args=[...], ...)`. 
