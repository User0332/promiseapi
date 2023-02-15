import time
from types import FunctionType
from promiseapi import PromiseFuncWrap, Promise

def myfunc():
	raise RuntimeError("uh oh")
	return "Hello, World!"

def myfunc2():
	return "Hello Again!"

PromiseFuncWrap(myfunc) \
	.then(
		lambda res: print(f"Succeeded: {res}"),
		lambda err: print(f"Failed: {type(err).__name__}: {err}")
	) \
	.then(
		lambda res: print(f"The callback function for myfunc() returned {res!r}"),
		lambda err: print(f"The callback function failed too!!! Error: {err}")
	)


PromiseFuncWrap(myfunc2) \
	.then(
		lambda res: 8/0,
		lambda err: print(f"Failed: {type(err).__name__}: {err}")
	) \
	.then(
		lambda res: print(f"The callback function for myfunc2() returned {res!r}"),
		lambda err: print(f"The callback function failed! {type(err).__name__}: {err}")
	)

def my_promise_executor(resolve: FunctionType, reject: FunctionType):
	a = 5
	b = 4

	time.sleep(2)
	if a > b: resolve(True)
	elif a == b: reject(RuntimeError("A and B are the same!"))
	else: resolve(False)

def super_fast_promise(resolve: FunctionType, reject: FunctionType):
	resolve("cool!")

Promise(my_promise_executor) \
	.then(
		lambda res: (print(f"A > B: {res}"), 123)[1],
	) \
	.catch(lambda err: (print(f"An error occurred: {type(err).__name__}: {err}"), 1234)[1]) \
	._finally(lambda: print("All done!")) \
	.then(lambda res: print(f"This should be the return value of the previous `then` or 'catch' statement: {res}"))

# BUG: the above 'finally' statement exectues twice

Promise(super_fast_promise) \
	.then(lambda res: print(f"This executes first - {res}"))

Promise(super_fast_promise) \
	._finally(lambda: print("All done with super fast promise (for the second time!"))