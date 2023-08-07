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
cfg.register('skiprows',1)
```
These object can then be called as properties as follows:
```python
# define some data loading function
def my_data_load_funntion(fromdir, skiprows=0): ...

# call using the earlier created config object
my_data_load_function(fromdir=cfg.data, skiprows=cfg.skiprows)
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
In the offshoot that you have to not only load data that require some globals but you're also interested in output directories, intermediate directories, data reduction parameters, etc. etc... You might be better of creating several config objects each with their own purpose.
```python
from configlib import Config, FileConfig

# create config object for handling directories and files
filecfg = FileConfig()
cfg.register('source','my/path/source')
cfg.register('data','my/path/data')

# create config object for some fitting algorithm
fitcfg = Config()
fitcfg.register('order', 5)          # 5th order polynomial
fitcfg.register('method', 'leastsq') # using leastsquares method
fitcfg.register('burnin', 50)        # and throw the first 50 samples away
```
Should you want to, these config object can be merged into one config objects. To do so, we can use the `+`, `/` and `//` operations.
The `+` operations will add and overwrite the object on the rightside of the `+` onto the left. This also means that the final class of the
config object will be the class of the left right object

The `/` operation will add the object but will prioritise the class and attributes of the object on the left.
Finally, the `//` operator will add the object, it will prioritise the left object but it will always cast the type to be the basic `Config` class.




