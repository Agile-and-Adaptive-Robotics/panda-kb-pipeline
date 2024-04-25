import time

'''
Wrappers to perform generic performance benchmarks

Author: Reece Wayt

'''

#execution_times = []

def timeit(func):
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        #print(f"{func.__name__} executed in {end_time - start_time:.4f} seconds.")
        return result, elapsed_time
    return wrapper


def measure_throughput(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        data_size = func(*args, **kwargs)  # Expecting func to return the size of data processed
        end_time = time.time()
        duration = end_time - start_time
        if duration > 0:
            throughput = data_size / duration  # Adjust units of throughput as necessary
            print(f"{func.__name__} throughput: {throughput:.4f} units/second.")
        else:
            print(f"{func.__name__} executed too quickly to measure throughput accurately.")
        return data_size
    return wrapper