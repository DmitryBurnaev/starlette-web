# starlette-web
Simple components for web-app, based on "starlette" framework.


### Project Description

#### Target 
This is a simple moving part of common components from [podcast web-application](https://github.com/DmitryBurnaev/podcast-service)
Common parts are related to starlette web-framework and can be used for building web-applications.


## Environment Variables

### REQUIRED Variables

| argument              |                    description                    |                 example |
|:----------------------|:-------------------------------------------------:|------------------------:|
| SECRET_KEY            |           Django secret key (security)            |    _abc3412j345j1f2d3f_ |
| SITE_URL              |     URL address to the UI-part of the web APP     | https://web.project.com |
| DB_HOST               |             PostgreSQL database host              |               127.0.0.1 |
| DB_PORT               |             PostgreSQL database port              |                    5432 |
| DB_NAME               |             PostgreSQL database name              |                 podcast |
| DB_USERNAME           |           PostgreSQL database username            |                 podcast |
| DB_PASSWORD           |           PostgreSQL database password            |         podcast_asf2342 |

### OPTIONAL Variables

| argument          |                    description                    |             default |
|:------------------|:-------------------------------------------------:|--------------------:|
| JWT_EXPIRES_IN    |         Default time for token's lifespan         |           300 (sec) |
| APP_DEBUG         |               Run app in debug mode               |               False |
| LOG_LEVEL         |        Allows to set current logging level        |               DEBUG |
| SENTRY_DSN        | Sentry dsn (if not set, error logs won't be sent) |                     |
| REDIS_HOST        |                    Redis host                     |           localhost |
| REDIS_PORT        |                    Redis port                     |                6379 |
| REDIS_DB          |                     Redis db                      |                   0 |
| DB_NAME_TEST      |         Custom name for DB name for tests         | `DB_NAME` + `_test` |
| SENDGRID_API_KEY  | Is needed for sending Email (invite, passw., etc) |                     |
| EMAIL_FROM        |            Is needed for sending Email            |                     |
| DB_ECHO           |         Sending all db queries to stdout          |               False |
| CONSTANCE_BACKEND |        Backend class for constance storage        |                     |
| CONSTANCE_CONFIG  |                  Constants                        |                     |


* * *

### License

This product is released under the MIT license. See LICENSE for details.
