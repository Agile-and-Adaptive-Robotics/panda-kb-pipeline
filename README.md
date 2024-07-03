# panda-kb-pipeline


### Start Here: 
When first setting up your Latte Panda for interfacing with the KapohoBay (KB) Board go here for instructions on the setup proceedure: `/panda-kb-pipeline/SETUP.md`


### Daily Use:
Anytime you are using the KB to run your code follow these steps (these are also contained in the start-kb.sh script):

```bash
conda activate loihi
export KAPOHOBAY=1
lsusb -t
sudo rmmod ftdi_sio
echo "Removing ftdi driver"

lsusb -t

echo "checking KB connection" 
`python3 -c "import nxsdk; print(nxsdk.__path__[0])"`/bin/x86/kb/nx --test-fpio
```

Alternatively run the `start-kb.sh` script:
```
./start-kb.sh
```

### Project directory: FIXME: 
```bash
project/
├── include/
│   ├── MyClass.h
│   └── AnotherClass.h
├── src/
│   ├── MyClass.cpp
│   └── AnotherClass.cpp
└── main.cpp

```

### Neural Encodings: 
There are three basic types of encoding algorithms: 
1. Rate-based encoding (most common and well validated in observation of animals): Information about the stimulus is contained in the firing rate of the neuron, and not in individual spikes. [source](https://www.nature.com/articles/s41467-021-22332-8)
- example of rate based encoding from [SNNTorch](https://snntorch.readthedocs.io/en/latest/tutorials/tutorial_1.html)
- tutorial on [medium](https://medium.com/@rmslick/neural-coding-generating-spike-trains-for-images-using-rate-coding-6bb61afef5d4#id_token=eyJhbGciOiJSUzI1NiIsImtpZCI6IjJhZjkwZTg3YmUxNDBjMjAwMzg4OThhNmVmYTExMjgzZGFiNjAzMWQiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL2FjY291bnRzLmdvb2dsZS5jb20iLCJhenAiOiIyMTYyOTYwMzU4MzQtazFrNnFlMDYwczJ0cDJhMmphbTRsamRjbXMwMHN0dGcuYXBwcy5nb29nbGV1c2VyY29udGVudC5jb20iLCJhdWQiOiIyMTYyOTYwMzU4MzQtazFrNnFlMDYwczJ0cDJhMmphbTRsamRjbXMwMHN0dGcuYXBwcy5nb29nbGV1c2VyY29udGVudC5jb20iLCJzdWIiOiIxMTEwMjg3OTI0MTAxOTI5NjczMDAiLCJlbWFpbCI6InJlZWNld2F5dDk2QGdtYWlsLmNvbSIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJuYmYiOjE3MjAwMjQzNjEsIm5hbWUiOiJSZWVjZSBXYXl0IiwicGljdHVyZSI6Imh0dHBzOi8vbGgzLmdvb2dsZXVzZXJjb250ZW50LmNvbS9hL0FDZzhvY0lOTVh4Y1RKRWJuZHY0ODNsemxIeEZHc3FQYTVqa3NYLXpzQVZ0aUJTaENxMHFmTXNLPXM5Ni1jIiwiZ2l2ZW5fbmFtZSI6IlJlZWNlIiwiZmFtaWx5X25hbWUiOiJXYXl0IiwiaWF0IjoxNzIwMDI0NjYxLCJleHAiOjE3MjAwMjgyNjEsImp0aSI6IjYyOTk5ZjQ0NjVkNWNkYTNhNmY2ZTI1ZTBiYTZjNDQzZGMyYzMzZmYifQ.kjWxnQQp6LyUGS1JruAxDhF7yaAiDlkVs9ASYV_0RljyAAuSLvoN_w3QuGvoAC4ta20WdrU3a59VW_tAZX-dpFukkZYR95ramAKPu4xNnLw5CO8GYe3WSGgwKKgkptNDgg71YdEH0UR4W2bO3W9oOIiEa6wjuiMmaReAdGK6QYdmb7ofCr6_zWRWP0QgbEblZqYDS2mp-7od-FCPyviRvtOYAlJsdZAbG-HrlXbsyS9kn4wEz2OCTZn2dtEt3hY58kaj6cKJHzDIdryOujJvV3oz7GDv2es6AuufOcvUr1c5Ps6ag4B0QM6RQjIFgdMDbl8Djdt_AzcrnNJrJcOrWQ) for spike encoding, with github [repo](https://github.com/rmslick/RateCoding)
- for spike trains we need to select bot a time interval, and a sub-unit of time recording spiking events per time unit unit. (i.e. T and then divide T into T subnuts to create a time dimension). Each value must be mapped between [0,1]
2. Spike Count based encoding
3. Spike timing based encoding
