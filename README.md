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