# configlib
Python3 library for registering hierarchical configuration files. In astronomical programming people love to have a bunch of
hard coded constants in their files. This package aims to encourage people to put all those parameter defintions
in a configuration file instead. For now the only supported format is `.yaml` but I aim to add other formats such as `.toml` in
the future.

## Installation
This package is not (yet) available on PyPI. As such, in order to install the package you need to git clone or
git fork the repo:
```bash
# using https
git clone https://github.com/NuggetOfficial/configlib.git

# or ssh
git clone git@github.com:NuggetOfficial/configlib.git
```
and then pip install it from the local repo directory
```bash
pip install ./your/repo/directory
```

## Documentation
### Getting started:
To start we add a simple import line to our majestic python file and initializing our workhorse object
```python
from configlib import Config

cfg = Config()
```
Much like the beloved `hdf5` format and `argparse` there are two primary operations on this object.
We either make a `group` or a `parameter`. 
```
my_group = cfg.add_group('my_group')
my_group.add_parameter('my_str', 'Hello world')
```

These object can then be called as properties as follows:
```python
#outputs Hello world to stdout
print(cfg.my_str)
```
These objects can be saved to and read from disk using the YAML standard. This is done through an `ConfigIO` object. The `writeto` and `readfrom` methods of this object
are handed to the `Config` object using a composition strategy. This allows us to use the object as follows.
```python
# write my beautiful config to disk
cfg.writeto(fpath='your_file')

# read my config from disk
cfg = Config.readfrom(fpath='your_file')
```
When no path string is given it the `ConfigIO` object will default to writing to and reading from `'config.yaml'` in your current working directory as given by the `pathlib` library.
Alternatively, you may want to do more sophisticated read and write actions. In that case, the `ConfigIO` class can be called directly.

```python
from configlib import ConfigIO

# write using a direct call from the IO object
ConfigIO.writeto(cfg, fpath='your_file')

# read in the same manner 
ConfigIO.readfrom(Config, fpath='your_file')
```
Although I have no particular use case intended for this. Im sure some of you will find it useful.
### More advanced:
In the offshoot that you have to not only load data that require some globals but you're also interested in output directories, intermediate directories, data reduction parameters, etc. etc... You might be better of creating several config groups each with their own purpose.
```python
from configlib import Config, FileConfig
cfg = Config()

# create config object for handling directories and files
file_cfg = cfg.add_group('files', FileConfig)
file_cfg.add_parameter('source','my/path/to/source')
file_cfg.add_parameter('data','my/path/to/data')

# create config object for some fitting algorithm
fit_cfg = cfg.add_group('fitting')
fit_cfg.add_parameter('method', 'leastsq')  # using leastsquares method

# function specific config
function_cfg = cfg.add_group('function')
function_cfg.add_parameter('order', 2)    # e.g 2nd order polynomial
function_cfg.add_parameter('c', 0.3)      # and c is known
```
The parameters in these groups can either be accessed directly trough the `Config` object.
```python
order  = cfg.order     # initializes as 2
method = cfg.method    # initializes as 'leastsq'
```
or they can be access by going down the tree manually
```python
assert cfg.fitting.function.order == cfg.order  # --> passes assertion
```
parameter names do not have to be unique so this implies that the dot search returns the first
instance of a parameter name that it finds.

