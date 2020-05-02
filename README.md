# stock-bets
Stock bets' goal is to make it fun for groups of friends to place competitive, real-money stock market bets. Think of a ross between fantasy football and poker for people who like stocks.

## Getting started
* Make sure you have Docker installed and running
* Clone this repo
* Place an `.env` file in the `/backend` directory that defines the following variables:
  - `SECRET_KEY` (string): An impossible-to-guess secret key used for encrypting API data
  - `MINUTES_PER_SESSION` (integer):  How many minutes should a logged-in user's session last for (1440 is recommended)
  - `DB_HOST` (string): The MySQL database host for the API
  - `DB_PORT` (int): What port to expose the DB on
  - `DB_USER` (string): The user that the backend will use to login to the DB 
  - `DB_NAME` (string): The name of the DB that we are using
  - `DB_PASSWORD` (string): The DB password
  - `SQLALCHEMY_TRACK_MODIFICATIONS` (`True`/`False`): Set to `False` unless you have a really good reason not to
  - `SQLALCHEMY_ECHO` (`True`/`False`): Same here
  - `DEBUG_MODE` (`True`/`False`): As a rule of thumb, `True` for development, `False` for production
* Place an `.env` file in the `/frontend` directory that defines the following variables:
  - `REACT_APP_GOOGLE_CLIENT_ID` (string): The Google client ID that the API is using for OAuth
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
make build
```

If all environmental variables are properly defined this should be about all there is to it. To start the API server run `make backend-up`. `make backend-bash` and `make db-mysql` are shortcuts to the inside of each of these containers. To run the frontend during local development run `npm start`. It is already configured to run with the backend container as a local server proxy.