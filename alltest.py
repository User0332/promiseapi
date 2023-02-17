from promiseapi import Promise

promise1 = Promise(lambda resolve, reject: reject(Exception("oops - an error occurred!")))
promise2 = Promise(lambda resolve, reject: resolve("abc"))
promise3 = Promise(lambda resolve, reject: resolve(123))

promise4 = Promise.all([promise1, promise2]).then(
	lambda res: print(res),
	lambda err: print(err)
)