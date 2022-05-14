## About Sentry

Sentry is a Application Monitoring and Error Tracking Software.
Is has limited free support for development purposes.

## Plugging-in

- Install package `sentry-sdk`
- Add SENTRY_DSN to your .env-file and to settings.py-file
- Subclass starlette_web.common.app.BaseStarletteApplication to include:
    - SentryAsgiMiddleware in .get_middleware()
    - SentryLoggingIntegration in .post_app_init()
- Change settings.APPLICATION_CLASS to link to your subclassed application
