# configlib
Python3 library for registering configurations. Current intended use case is handling directory strings.
I wish to improve the repr and verification such that both are its own class. This way the user can create their own verification schemes and printables.

The current intenstion behind the package is that a single import will handle your entire file structure. This way each part of the code knows the same directories by the
same names. This makes large data reduction scrips easier to setup and will it easier to make your project portable, both in system and also across systems.

## Documentation
### Getting started:
To start we add a simple import line to our majestic python file.
```python
from configlib import Config
```
Then we can use the register method to register variables under various aliases.
```python
# initialse a config obect
cfg = Config()

# add directories to project config
cfg.register('source','my/path/source')
cfg.register('data','my/path/data')
```
These object can then be called as properties as follows:
```python
# define some data loading function
def my_data_load_funntion(fromdir): ...

# call using the earlier created config object
my_data_load_function(fromdir=cfg.data)
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
This allows you to instantiate more sophisticated `Config` classes that you are free to create :)



