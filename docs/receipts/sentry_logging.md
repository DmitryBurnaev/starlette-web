## About Sentry

Sentry is an Application Monitoring and Error Tracking Software.
It has limited free support for development purposes.

## Plugging-in

- Install package `sentry-sdk`
- Add SENTRY_DSN to your `.env`-file and to `settings.py`-file
- Subclass the `starlette_web.common.app.BaseStarletteApplication` in order to include:
    - `SentryLoggingIntegration` in `.post_app_init()`
- Change settings.APPLICATION_CLASS to link to your subclassed application
- Add `sentry_sdk.integrations.asgi.SentryAsgiMiddleware` to settings.MIDDLEWARES
