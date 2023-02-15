from types import FunctionType
import threading

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


class PromiseFuncWrap:
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

		# if hasattr(thread, "_finally") and not hasattr(thread, "_finally_completed"):
		# 	thread._finally()

		if hasattr(thread, "_callback_res"): return thread._callback_res
		if hasattr(thread, "_callback_err"): raise thread._callback_err
		if hasattr(thread, "_catch_res"): return thread._catch_res
		if hasattr(thread, "_catch_err"): raise thread._catch_err

		if hasattr(thread, "_res"): return thread._res
		
		return thread._err

	def then(self, accept: FunctionType=None, reject: FunctionType=None):
		self.thread.add_callback(accept, reject)

		return PromiseFuncWrap(lambda: PromiseFuncWrap.__callback_resolver(self.thread))

	def catch(self, callback: FunctionType):
		return self.then(None, callback)

	def _finally(self, final: FunctionType):
		self.thread.add_callback(final=final)

		return self

class Promise:
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

		# if hasattr(thread, "_finally") and not hasattr(thread, "_finally_completed"):
		# 	thread._finally()

		if hasattr(thread, "_callback_res"): return resolve(thread._callback_res)
		if hasattr(thread, "_callback_err"): raise reject(thread._callback_err)
		if hasattr(thread, "_catch_res"): return resolve(thread._catch_res)
		if hasattr(thread, "_catch_err"): raise reject(thread._catch_err)

		if hasattr(thread, "_res"): return resolve(thread._res)
		
		return reject(thread._err)

	def then(self, accept: FunctionType=None, reject: FunctionType=None):
		self.thread.add_callback(accept, reject)

		return Promise(
			lambda resolve, reject:
			(Promise.__callback_resolver(resolve, reject, self.thread))
		)

	def catch(self, callback: FunctionType):
		return self.then(None, callback)

	def _finally(self, final: FunctionType):
		self.thread.add_callback(final=final)
		
		return self