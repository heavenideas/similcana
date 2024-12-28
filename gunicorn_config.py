import os

port = os.environ.get('PORT', '10000')
bind = f"0.0.0.0:{port}"
workers = 2  # Reduce number of workers
threads = 2  # Reduce number of threads
timeout = 120
max_requests = 1000
max_requests_jitter = 50
worker_class = 'sync'
worker_tmp_dir = '/dev/shm'  # Use shared memory for temp files 