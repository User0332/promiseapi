import time
from promiseapi import (
	PromiseFuncWrap,
	Promise,
)

def myfunc():
	raise RuntimeError("uh oh")

	return "value"

def myfunc2():
	return "Hello Again!"

PromiseFuncWrap[str](myfunc) \
	.then(
		lambda res: print(f"Succeeded: {res}"),
		lambda err: print(f"Failed: {type(err).__name__}: {err}")
	) \
	.then(
		lambda res: print(f"The callback function for myfunc() returned {res!r}"),
		lambda err: print(f"The callback function failed too!!! Error: {err}")
	)

PromiseFuncWrap[str](myfunc2) \
	.then(
		lambda res: 8/0,
		lambda err: print(f"Failed: {type(err).__name__}: {err}")
	) \
	.then(
		lambda res: print(f"The callback function for myfunc2() returned {res!r}"),
		lambda err: print(f"The callback function failed! {type(err).__name__}: {err}")
	)

def my_promise_executor(resolve: Promise.Resolver[bool], reject: Promise.Rejecter):
	a = 5
	b = 4

	time.sleep(2)
	if a > b: resolve(True)
	elif a == b: reject(RuntimeError("A and B are the same!"))
	else: resolve(False)

def super_fast_promise(resolve: Promise.Resolver, reject: Promise.Rejecter):
	resolve("cool!")

Promise[str](my_promise_executor) \
	.then(
		lambda res: (print(f"A > B: {res}"), 123)[1],
	) \
	.catch(lambda err: (print(f"An error occurred: {type(err).__name__}: {err}"), 1234)[1]) \
	._finally(lambda: print("All done!")) \
	.then(lambda res: print(f"This should be the return value of the previous `then` or 'catch' statement: {res}"))

Promise[str](super_fast_promise) \
	.then(lambda res: print(f"This executes first - {res}"))

Promise[str](super_fast_promise) \
	._finally(lambda: print("All done with super fast promise (for the second time!"))