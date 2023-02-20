## A note on database session scope

Whenever you create session to database, a connection is fetched from a (limited) connection pool.
Connection itself acts as a transaction, where operations do not mutate db, unless committed.
By default, the transaction level (at least for PostgreSQL) is READ COMMITTED.

A session must be always instantiated with `async with sessionmaker()` block, handling correct session closing.
An unclosed session, being un-committed/un-rollbacked, may hang out with `idle in transaction` status forever,
burdening server with an additional load.

SQLAlchemy docs specifically state that session must not be opened for long. 
This behavior may lead to incorrect closing and hanging out. 
Therefore, if your code runs a lengthy operation within `async with sessionmaker()`
block, which is not related to database, and you don't need an impartible transaction there,
it might be a good idea to split it into 2 `async with sessionmaker()` blocks.

As for http connections, a session is always opened for `dispatch`-method of BaseHTTPEndpoint.
Since http-endpoint life-cycle is typically short, it is a valid behavior.
However, you must not pass `request.db_session` to background task, since it spawns
on separate thread and may run for long time. Instead, pass object of `app` and create
new session inside background task.

In websocket connections, which are long-lived, a session is not created by default.
You must open sessions and handle session scopes by yourself. If websocket endpoint
features infinite loop, only open session within a loop iteration, not outside.

Always take care of only using session within `async with sessionmaker()` scope. 
`session.close` method actually created a callback to close session, so it may not
fall immediately, if you use session outside the scope, but it may lead to obnoxious
errors in production.

If you are implementing your own class for AsyncSession, make sure to wrap `__aexit__`
method with `anyio.CancelScope(shield=True)`, to prevent incorrect closing behavior when task is cancelled
(i.e., on websocket 1001 error).
