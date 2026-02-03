# radijator

A simple script for efficient flashing settings of mobile radio stations and memories (channels) to chinese shitbox mobile radios, i.e. Baofeng.

Also you can use it to generate random DCS codes for requencies and convert the radijator JSON format to CHIRP compatible CSV format.

## Setting up

For now, the tool doesn't have a nice and clean way to be installed and it needs to be hotwired together with CHIRP installation.

For the tool to work, you need to clone both the radijator and CHIRP repository into a same base directory and it should follow this file system structure.

```
.
|- chirp # cloned CHRIP repository
|- radijator # cloned radijator repository
```

You can then check out specific version of chirp in the cloned repository or just use the `main` branch.

To install all dependencies for chirp, I recommend creating a virutal environment and installing all the dependencies.

> [!NOTE]
> This is for now tested only on Linux (Fedora 43) but it should work on any distribution and on any platform with minimal modifications.

> [!CAUTION]
> For Linux, comment out `wxPython` packages in `requirements.txt` file in chirp repo.
> Install that package through the system pakage manager.

```sh
cd chirp
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

You can then create an executable bash script in a PATH directory (i.e. `$HOME/.local/bin`) that will execute the `radijator.py` with all the required environment variable presets (PYTHONPATH, ...).

```bash
#!/bin/bash

BASE_DIRECTORY=/path/to/base/directory

source $BASE_DIRECTORY/chirp/bin/activate
export PYTHONPATH="$PYTHONPATH:$BASE_DIRECTORY/chirp:/usr/lib64/python3.14/site-packages"
python $BASE_DIRECTORY/radijator/radijator.py $@
deactivate
```

## License

BSD 2-clause license

## Author

Dušan Simić
