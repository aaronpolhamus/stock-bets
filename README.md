# stock-bets
Stock bets' goal is to make it fun for groups of friends to place competitive, real-money stock market bets. Think of a cross between fantasy football and poker for people who like stocks.

## Getting started
* Make sure you have Docker installed and running
* Clone this repo
* Place an `.env` file in the `/backend` directory that defines the following variables:
  - `TEST_CASE_UUID` (string): When you run the `backend.database.mock_data` as a main function (this happens automatically during functional API testing, or when you call `make db-mock-data`), you populate the database with a bunch of mock data. This can be useful for local development. By setting `TEST_CASE_UUID` to the uuid of the account that you use to develop with, your user account will automatically be populated with these fixtures they're run. The best way to do this is to leave this variable unset, login once with the account you'll use to develop, and then copy and paste this value from the `users` table. 
  - `TEST_CASE_EMAIL` (you@example.com): Same as above for the uuid: you should define these right next to each other in your dev `.env` file.  
  - `TEST_CASE_NAME` (string): How would you like your username to show up while developing locally?
  - `GECKO_DRIVER_LOCATION` (string): The url for downloading the Mozilla gecko driver in case Selenium needs to fallback from using Chromium. This is generally not going to be required for development.
  - `IEX_API_SECRET_PROD` (string): IEX production API secret
  - `IEX_API_SECRET_SANDBOX` (string): IEX sandbox API secret
  - `SENDGRID_API_KEY` (string): SENDGRID API to send emails 
  - `EMAIL_SENDER` (string): The sender of the emails you have configured on sendgrind 
* To use the frontend with SSL locally, paste `chrome://flags/#allow-insecure-localhost` into your Google Chrome url. Just be careful: you may want to turn this back on at some point.
* Make sure that you don't have an current port mappings to `3306`, `5000`, `5672`, `15672`, `6379`, or `5555` on your host. Your dev env needs all of these. 
* `cd` to the repo root and run `make up`. This is the "master" local launch command--it will build and raise the entire backend, install and build your npm dependencies, and start the web app on port `3000`. 

If all environmental variables are properly defined this should be about all there is to it. A couple quick tips:
* To start the API server run `make api-up`. This will start the redis, mysql, and celery worker containers as well.
* Run all backend unit/integration tests with `make backend-test`. 
* Run `make db-mysql` to directly inspect/edit the DB (or connect to the container in your PyCharm, for example). 
* All backend containers have local volume mounts. On the flask API server, this means that your local changes are immediately reflected, and the server restarts whenever you change something (note that if you make a breaking change it will crash, and you'll need to fix what's broken before calling `make api-up` again). The celery worker is less flexible, and needs to be rebuilt from the updated backend image before it will reflect local changes to business logic. To do othis call `make worker-restart`. Keep this in mind when you're iterating and re-testing on the backend. 
* To run the frontend during local development run `npm start` from the `/frontend` directory. `make up` does this by default, and re-loads all dependencies. If you're working locally and just want to update the backend, just run `make worker-restart` and you should be good. 

### localstack
We use localstack to test and develop locally without need of any real-world credentials. This means that we have the power 
of the whole aws cloud local, with the disadvantage that if needed, you cannot call `aws s3 ls` for example, you will need 
to do a `aws --entrypoint-url=https://localstack:4572 s3 ls`. where the port would be whatever service from aws you are going 
to be testing. Add to your envs the following variables
  - `AWS_ACCESS_KEY_ID`
  - `AWS_SECRET_ACCESS_KEY`
  - `AWS_PUBLIC_BUCKET_NAME` 


### Troubleshooting
* _MySQL db won't fire up:_ 
Sometimes the volume gets corrupted or some other problem that errors out the containers startup crops up. When this happens the easiest way to deal with the problem is to remove the MySQL image, prune all volumes, restart docker (for good measure), and then invoke `make db-up` to rebuild the container. [See this guide](https://github.com/Radu-Raicea/Dockerized-Flask/wiki/%5BDocker%5D-Remove-all-Docker-volumes-to-delete-the-database).
* _I'm getting unexpected DB connection errors:_ There are two "acceptable" ways to communicate with the DB in `stockbets`. All connections should be handled via the `scoped_session` object `db_session` in `database.db`. You can either communicate with the DB via the pure ORM, or you can open a db connection for sending raw SQL (without string injections, please!), using a context, e.g. `with db_session.connect() as conn: ...`. If you take this route, _it's essential that you close your transaction block with `db_session.remove()` or `db_session.commit()` when you are finished_. Dangling connections will cause downstream operations against the DB to break, even if they were instantiated inside a different scoped environment. 
* _My tests are hanging and I don't know why...:_ If this is happening, the first thing to check is that you have an unclosed `db_session` operation. The prefered pattern is to embed the execution of all business logic in a celery task with `base=BaseTask` as the task's base class. This will handle all unclosed connections automatically. Once a task is defined, you can still execute it synchronously on, e.g. on the API server, with the `task.apply(args=*args, kwargs=**kwargs)` method. 
* _What's up with all this really gnarly test mocking?_: Yep, sorry about that. Because `stockbets` simulates a brokerage platform, where the logic for executing orders, gathering prices, and calculating winners is heavily time dependent, it's necessary to mock in a targeted way every invocation of `time.time()` in order to maintain test consistency. That's what makes `test_celery_tasks` so hairy, and can make debugging these tests when they break incredibly challenging. Superior test design patterns welcome if you see a better way! When debugging, set break points next to the the `time.time()` invocations to verify that your mocks are making it to the right place. 
* _How do I test celery tasks?_: When possible, it's nice to actually use celery in the same way that it will be used in production with the `task.delay(...)` invocation. However, it's frequently necessary to mock values into tasks, and to do this you need to run the task locally instead of on the worker clusters. For this, use `task.apply(args=[...], ...)`. 
* _CORS-related frontend errors_: Yeah, this is a thing. The current project setup should allow your Chrome browser to communicate with the API server on `localhost` after invoking `chrome://flags/#allow-insecure-localhost`, but holler if you're having an issue. Before you do, check the server api logs with `make api-logs` when sending your API requests. The current setup will return a CORS error if the server responds with `500`, even if the issue isn't CORS but an internal problem with  business logic raising an exception.
* _Everything is broken, I can't figure out what's going on. Is this a docker issue?_: There's _probably_ a quicker fix, but if you think that tearing everything down and starting from scratch is the answer run `make destroy-everything` (you can run the individual commands inside if any don't execute successfully), restart your docker machine, and call `make up`. If that doesn't fix the problem, check in with a teammate. 

### Notes on business logic
The business logic modules stored in `/backend/logic` have an order that is important preserve. That logic is: 
```
1) schemas.py
2) base.py
3) stock_data.py
4) payments.py
5) metrics.py
6) visuals.py
7) friends.py
8) games.py
9) auth.py
```

When asking yourself "where do I put this piece of business logic?" the answer is "as far downstream (i.e. close to the games module) as you can whie respecting this order". We've tried to further break down the logical modules with comments indicating what different branches of application logic they deal with, but there is room for constant improvement here. 

### Style
#### Overall
* Favor a functional over object-oriented style (although object-oriented is sometimes the best approach, especially for custom, complex data structures)
* Never ever repeat yourself. Wherever you're working, if you find yourself writing the same block of code two different times, turn that into an importable function to invoke
* Seek informative name choices for variables and functions, and accept that sometimes this may lead to longer names. 

#### Javascript
* We use [eslint standard](https://standardjs.com/) for javascript formatting. Please configure your editor to implement automatic standard fixes upon committing
* All components should be composed in a functional style, with state being with [react hooks](https://reactjs.org/docs/hooks-intro.html). 

#### Python
* All python code should be [PEP-8 compliant](https://www.python.org/dev/peps/pep-0008/)

### Production notes
`.env.dev` versions credential information for your local environment so that you don't have to keep track of everything. Here's an inventory of all the variables that need to be defined for deploying to production:
* `ENV` (should be equal to `prod`) 
* `SERVICE`
* `SECRET_KEY`
* `CHECK_WHITE_LIST`
* `MYSQL_HOST`
* `MYSQL_PORT`
* `MYSQL_USER`
* `MYSQL_DATABASE`
* `MYSQL_ROOT_PASSWORD`
* `SQLALCHEMY_TRACK_MODIFICATIONS`
* `SQLALCHEMY_ECHO` (should be equal to `False`)
* `DEBUG_MODE` (should be equal to `False`)
* `RABBITMQ_DEFAULT_USER`
* `RABBITMQ_DEFAULT_PASS`
* `RABBITMQ_HOST`
* `REDIS_HOST`
* `GECKO_DRIVER_LOCATION`
* `IEX_API_SECRET_PROD`
