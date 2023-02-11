## A note on session scope

Whenever you create session to database, a connection is fetched from a connection pool.
Connection itself acts as a transaction, where operations do not mutate db unless committed.
By default, the transaction level (at least for PostgreSQL) is READ COMMITTED.

A session must be always instantiated with `async with` block, handling correct session closing.
An unclosed session, being un-committed/un-rollbacked, may hang out with `idle in transaction` status forever,
providing additional load on the server.

SQLAlchemy docs specifically state that session must not be opened for long. 
This behavior may lead to incorrect closing and hanging out.

As for http connections, a session is always opened for `dispatch`-method of BaseHTTPEndpoint.
Since http-endpoint life-cycle is typically short, it is a valid behavior.
However, you must not pass `request.db_session` to background task, since it spawns
on separate thread and may run for long time. Instead, pass object of `app` and create
new session inside background task.

In websocket connections, which are long-lived, a session is not created by default.
You must open sessions and handle session scopes by yourself.

Always take care of only using session within `async with` scope. 
`session.close` method actually created a callback to close session, so it may not
fall immediately, if you use session outside the scope, but it may lead to obnoxious
errors in production.
