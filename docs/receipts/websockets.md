## Writing a Websocket endpoint

Working with websockets has many caveats. Websocket is 2-sides message channel,
where messages may be sent at any time by both client and server. 
Typical use-cases are:

- infinitely push messages from server to client
- accept messages from client and perform short-timed actions
- in turns, accept and send messages from and to client
- chats

### Creating background task

starlette_web provides `starlette_web.common.ws.base_endpoint.BaseWSEndpoint` class
to handle all above-mentioned cases. The core idea is that on each receive from client,
server spawns a background task to handle request, which may be finite or infinite.

Overrideable methods:
- `_background_handler`
- `_register_background_task`
- `_unregister_background_task`
- `_handle_background_task_exception`

All tasks are spawned within a single-level `anyio.TaskGroup`, that takes care of
their cancellation. A cancellation occurs whenever any of tasks raises exception,
or when `WebsocketDisconnect` exception is raised. Raising any exception within
a task will cancel all cancel scope, so you may want to silence a non-CancelError
exception within `_handle_background_task_exception`

Receipts:
- `infinitely push messages from server to client` - create a task registry as a set,
  add task_id on register, discard task_id on unregister; in handler, check that
  if registry is empty before executing endless loop, otherwise return immediately;
- `accept messages from client and perform short-timed actions` - simply define 
  `_background_handler` to run a finite task, no (un)registration routine is necessary
  (unless you want to protect against DDOS)
- `in turns, accept and send messages from and to client` - at the beginning, start
  a single background task to send messages, after that do as in 2nd example. Use
  registration methods to monitor, which handlers do what, and pass data between
  receiving handlers and sending handler via local memory class-variable, 
  database or such.
- for example of simple chat, see `starlette_web.tests.views.websocket.ChatWebsocketTestEndpoint` and
  `starlette_web.tests.contrib.test_websocket_chat`

## Synchronizing multiple tasks

It is not recommended to run a highly-sophisticated logic with many infinite tasks,
which require pairwise synchronization with each other, since it not especially 
"structured concurrency" way, that trio/anyio enforce. There may become too many
orders of execution to handle, which is error-prone 
(see this paper https://vorpus.org/blog/some-thoughts-on-asynchronous-api-design-in-a-post-asyncawait-world/#c-c-c-c-causality-breaker, notes about `large/small Y/N`).

However, should you need to do so, use task-registration methods from base WS endpoint
(i.e. define a task_storage) and handle synchronization either with it, or with outer
data manager. 

**AVOID** raising a CancelError within a background task, since it propagates to parent
task group and cancels all tasks within that scope. Simply return inside background
handler, if you want to cancel a single task.

**AVOID** stuff like this https://stackoverflow.com/a/60675826
and, in general, passing event-handling primitives between tasks, 
other than class-level anyio.Lock()

## Manually calling websocket.receive

**AVOID** manually calling `websocket.receive` inside a background task, 
since it would introduce  a race condition with main dispatch method.

As in native Starlette implementation, you are not expected to call 
`websocket.receive` by yourself. If you want to override `dispatch` method and
still be able to support all above mentioned cases, you should use timeouts for
receive, since this operation effectively polls for message infinitely.

Starlette native implementation does not provide a timeout parameter for receive()
method. However, since all operations are async, you may (and should) use 
`anyio.move_on_after`/`anyio.fail_after` wrappers.
