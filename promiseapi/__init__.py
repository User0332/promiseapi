from types import FunctionType
from typing import Generic, Callable, Any, Union, NoReturn
from typing_extensions import TypeVar
import threading

# TYPEHINT THIS WHOLE LIBRARY WITH GENERICS AND CALLABLE[[t], t]

PromiseType = TypeVar("PromiseType", bound="Promise")
PromiseFuncWrapType = TypeVar("PromiseFuncWrapType", bound="PromiseFuncWrap")
PromiseReturnType = TypeVar("PromiseReturnType")
ResolverArgType = TypeVar("ResolverArgType")

class CallbackThread(threading.Thread):
	def add_callback(self, callback: FunctionType=None, catch: FunctionType=None, final: FunctionType=None):
		if callback is not None: self.callback = callback
		if catch is not None: self.catch = catch
		if final is not None: self._finally = final

		if hasattr(self, "_res") and (callback is not None):
			try: self._callback_res = self.callback(self._res)
			except Exception as e:
				self._callback_err = e

		if hasattr(self, "_err") and (catch is not None):
			try: self._catch_res = self.catch(self._err)
			except Exception as e:
				self._catch_err = e

		if (hasattr(self, "_finally") and hasattr(self, "_ran")) and not hasattr(self, "_finally_completed"):
			try: self._finally()
			except Exception: pass
			self._finally_completed = True

	def run(self):
		if self._target is not None:
			try:
				self._res = self._target(*self._args, *self._kwargs)
			except Exception as e:
				self._err = e

			if hasattr(self, "callback") and hasattr(self, "_res"):
				try: self._callback_res = self.callback(self._res)
				except Exception as e:
					self._callback_err = e
			
			if hasattr(self, "catch") and hasattr(self, "_err"):
				try: self._catch_res = self.catch(self._err)
				except Exception as e:
					self._catch_err = e

			if hasattr(self, "_finally") and not hasattr(self, "_finally_completed"):
				try: self._finally()
				except Exception: pass
				self._finally_completed = True

			self._ran = True

class CallbackThread_NotFuncWrap(CallbackThread):
	def run(self):
		if self._target is not None:
			self._target(*self._args, *self._kwargs)
			
			if hasattr(self, "callback") and hasattr(self, "_res"):
				try: self._callback_res = self.callback(self._res)
				except Exception as e:
					self._callback_err = e
			
			if hasattr(self, "catch") and hasattr(self, "_err"):
				try: self._catch_res = self.catch(self._err)
				except Exception as e:
					self._catch_err = e

			if hasattr(self, "_finally") and not hasattr(self, "_finally_completed"):
				try: self._finally()
				except Exception: pass
				self._finally_completed = True

			self._ran = True

class PromiseFuncWrap(Generic[PromiseReturnType]):
	def __init__(self, func: FunctionType):
		self.func = func
		self.thread = CallbackThread(target=func)
		self.thread.start()

	def __callback_resolver(thread: CallbackThread):
		while (
			(not hasattr(thread, "_callback_res")) and 
			(not hasattr(thread, "_catch_res")) and
			(not hasattr(thread, "_callback_err")) and 
			(not hasattr(thread, "_catch_err")) and
			thread.is_alive()
		): pass

		if hasattr(thread, "_callback_res"): return thread._callback_res
		if hasattr(thread, "_callback_err"): raise thread._callback_err
		if hasattr(thread, "_catch_res"): return thread._catch_res
		if hasattr(thread, "_catch_err"): raise thread._catch_err

		if hasattr(thread, "_res"): return thread._res
		
		return thread._err

	def __all_handler(promises: list[PromiseFuncWrapType]):
		vals = []

		while 1:
			if not promises: break
			for promise in promises.copy():
				if hasattr(promise.thread, "_res"):
					vals.append(promise.thread._res)
					promises.remove(promise)
					continue

				if hasattr(promise.thread, "_err"):
					raise promise.thread._err

		return vals

	def __all_settled_handler(promises: list[PromiseType]):
		vals = []

		while 1:
			if not promises: break
			for promise in promises.copy():
				if hasattr(promise.thread, "_res"):
					vals.append("fulfilled")
					promises.remove(promise)
					continue

				if hasattr(promise.thread, "_err"):
					vals.append("rejected")
					promises.remove(promise)
					continue

		return vals

	def __any_handler(resolve: FunctionType, reject: FunctionType, promises: list[PromiseType]):
		reasons = []

		while 1:
			if not promises: break
			for promise in promises.copy():
				if hasattr(promise.thread, "_res"):
					return promise.thread._res

				if hasattr(promise.thread, "_err"):
					reasons.append(promise.thread._err)
					promises.remove(promise)
					continue

		raise Exception(reasons)

	def __race_handler(resolve: FunctionType, reject: FunctionType, promises: list[PromiseType]):
		while 1:
			for promise in promises.copy():
				if hasattr(promise.thread, "_res"):
					return promise.thread._res

				if hasattr(promise.thread, "_err"):
					raise promise.thread._err

	def then(self, accept: Callable[[PromiseReturnType], Union[Any, None]]=None, reject: Callable[[Exception], Union[Any, None]]=None):
		self.thread.add_callback(accept, reject)

		return PromiseFuncWrap(lambda: PromiseFuncWrap.__callback_resolver(self.thread))

	def catch(self, callback: Callable[[Exception], Union[Any, None]]):
		return self.then(None, callback)

	def _finally(self, final: Callable[[], Union[Any, None]]):
		self.thread.add_callback(final=final)

		return self

	def all(promises: list[PromiseFuncWrapType]):
		return PromiseFuncWrap(
			lambda: PromiseFuncWrap.__all_handler(promises)
		)

	def allSettled(promises: list[PromiseFuncWrapType]):
		return PromiseFuncWrap(
			lambda: PromiseFuncWrap.__all_settled_handler(promises)
		)

	def any(promises: list[PromiseFuncWrapType]):
		return PromiseFuncWrap(
			lambda: PromiseFuncWrap.__any_handler(promises)
		)

	def race(promises: list[PromiseFuncWrapType]):
		return PromiseFuncWrap(
			lambda: PromiseFuncWrap.__race_handler(promises)
		)

class Promise(Generic[PromiseReturnType]):
	class Rejecter:
		def __call__(self, err: Exception) -> NoReturn: pass

	class Resolver(Generic[ResolverArgType]):
		def __call__(self, val: ResolverArgType) -> NoReturn: pass


	def __init__(self, handler: FunctionType):
		self.handler = handler
		self.thread = CallbackThread_NotFuncWrap(target=handler, args=(self.__resolve, self.__reject))
		self.thread.start()

	def __resolve(self, val):
		self.thread._res = val

	def __reject(self, val: Exception):
		self.thread._err = val

	def __callback_resolver(resolve: FunctionType, reject: FunctionType, thread: CallbackThread_NotFuncWrap):
		while (
			(not hasattr(thread, "_callback_res")) and 
			(not hasattr(thread, "_catch_res")) and
			(not hasattr(thread, "_callback_err")) and 
			(not hasattr(thread, "_catch_err")) and
			thread.is_alive()
		): pass

		if hasattr(thread, "_callback_res"): return resolve(thread._callback_res)
		if hasattr(thread, "_callback_err"): raise reject(thread._callback_err)
		if hasattr(thread, "_catch_res"): return resolve(thread._catch_res)
		if hasattr(thread, "_catch_err"): raise reject(thread._catch_err)

		if hasattr(thread, "_res"): return resolve(thread._res)
		
		return reject(thread._err)

	def __all_handler(resolve: FunctionType, reject: FunctionType, promises: list[PromiseType]):
		vals = []

		while 1:
			if not promises: break
			for promise in promises.copy():
				if hasattr(promise.thread, "_res"):
					vals.append(promise.thread._res)
					promises.remove(promise)
					continue

				if hasattr(promise.thread, "_err"):
					return reject(promise.thread._err)

		return resolve(vals)

	def __all_settled_handler(resolve: FunctionType, reject: FunctionType, promises: list[PromiseType]):
		vals = []

		while 1:
			if not promises: break
			for promise in promises.copy():
				if hasattr(promise.thread, "_res"):
					vals.append("fulfilled")
					promises.remove(promise)
					continue

				if hasattr(promise.thread, "_err"):
					vals.append("rejected")
					promises.remove(promise)
					continue

		return resolve(vals)

	def __any_handler(resolve: FunctionType, reject: FunctionType, promises: list[PromiseType]):
		reasons = []

		while 1:
			if not promises: break
			for promise in promises.copy():
				if hasattr(promise.thread, "_res"):
					return resolve(promise.thread._res)

				if hasattr(promise.thread, "_err"):
					reasons.append(promise.thread._err)
					promises.remove(promise)
					continue

		return reject(Exception(reasons))

	def __race_handler(resolve: FunctionType, reject: FunctionType, promises: list[PromiseType]):
		while 1:
			for promise in promises.copy():
				if hasattr(promise.thread, "_res"):
					return resolve(promise.thread._res)

				if hasattr(promise.thread, "_err"):
					return reject(promise.thread._err)

	def then(self, accept: Callable[[PromiseReturnType], Union[Any, None]]=None, reject: Callable[[Exception], Union[Any, None]]=None):
		self.thread.add_callback(accept, reject)

		return Promise(
			lambda resolve, reject:
			(Promise.__callback_resolver(resolve, reject, self.thread))
		)

	def catch(self, callback: Callable[[Exception], Union[Any, None]]):
		return self.then(None, callback)

	def _finally(self, final: Callable[[], Union[Any, None]]):
		self.thread.add_callback(final=final)
		
		return self

	def all(promises: list[PromiseType]):
		return Promise(
			lambda resolve, reject:
			Promise.__all_handler(resolve, reject, promises)
		)

	def allSettled(promises: list[PromiseType]):
		return Promise(
			lambda resolve, reject:
			Promise.__all_settled_handler(resolve, reject, promises)
		)

	def any(promises: list[PromiseType]):
		return Promise(
			lambda resolve, reject:
			Promise.__any_handler(resolve, reject, promises)
		)

	def race(promises: list[PromiseType]):
		return Promise(
			lambda resolve, reject:
			Promise.__race_handler(resolve, reject, promises)
		)
