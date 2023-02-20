## Structured concurrency

Asyncio-way is built around calling asyncio.Task's and juggling callbacks.
In asyncio-paradigm, all tasks are on the same "level", i.e. there are no explicit
parent or child tasks, even though tasks may spawn other tasks. Context propagation
and tracebacks are not available in this paradigm.

Structured concurrency is a specific, stricter way to write asynchronous programs.
It disallows callbacks and requires that all spawned tasks are explicitly bound
to a task group, which controls that all tasks are executed before exiting its scope
or is able to cancel all its child tasks.

Structured concurrency was introduced by Nathaniel Smith, author of `trio`, alternative
asynchronous backend for Python. Trio is the only asynchronous backend, that fully 
propagates callstack, exceptions and such. A number of papers by N. Smith elaborate
more on this topic:

- https://vorpus.org/blog/some-thoughts-on-asynchronous-api-design-in-a-post-asyncawait-world/
- https://vorpus.org/blog/timeouts-and-cancellation-for-humans/
- https://vorpus.org/blog/notes-on-structured-concurrency-or-go-statement-considered-harmful/

## Anyio

Anyio is a wrapper around `asyncio` and `trio`, that brings `trio`-like API as asyncio
wrappers. **It is generally recommended to write your project with idiomatic anyio 
primitives**, even if `asyncio` is the underlying backend.

A number of Python-libraries exist for either trio, or anyio, including Redis and
database client libraries. However, in general, **for production scenario asyncio 
should be used**, as not everything is implemented for anyio.

AnyIO provides `anyio.to_thread.run_sync` wrappers for FileIO in Python.

## Cancellation and timeouts

Trio/Anyio specifically point out on utils for cancellation of asynchronous tasks 
and handling timeouts. So much, actually, that both of these functionalities are 
implemented with a same class `CancelScope`. Consider the following:

- all async-methods, that free resources (such as `session.__aexit__`), should be shielded
  from cancellation (with asyncio.shield or anyio.CancelScope), which may be caused
  by outer caller (i.e., gunicorn)
- all async-methods, that are potentially infinitely long, should be wrapped with
  timeout handler (asyncio.wait_for or anyio.CancelScope)

## Threads and processes

anyio provides primitive functions to spawn threads and processes, to run
synchronous functions in async context. Some notes should be taken:

- In general, a timeout for synchronous operation cannot be properly handled in
  Python. In some cases, you may wrap them in async-wrappers to utilize timeouts, 
  however proceed with caution.
- **AVOID AT ALL COSTS** using `anyio.to_thread.run_sync` to wrap a potentially
  infinite task with a timeout block, since it will leave an orphan pending thread 
  (even though, the control will be returned to main program). If running such code
  from console, it will be impossible to close. The reason is because there is no
  straightforward way to cancel a thread in Python.
- `anyio.to_process.run_sync`, on the other hand, is perfectly fine to use for 
  timeout wrapper, since it supports cancellation. 
  However, it only allows to pass pickleable arguments to process, so you need to
  prepare your call beforehand (i.e., call a prepared management command for the cause)
