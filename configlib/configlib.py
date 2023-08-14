# future annotations
from __future__ import annotations

# buildin
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Any, Callable
import logging
import warnings

# dependencies
from yaml import load, dump, Loader

__all__ = ['NameError', 'AliasUnavailableError', 'ConfigIO', 'ConfigFormatter', 'Config', 'BaseConfig', 'FileConfig', 'ArgumentParserWithFallback']

# Global default path 
DEFAULT_PATH_TO_CONFIG = Path.cwd()/'config.yml'
WARNING_STACK_LVL = 3

class NameError(Exception):
    def __init__(self, *args: object) -> None:
        msg = 'Unsupported Variable name. Varialbe cannot be private (_), private protected (__), dunder, sunder or overwrite a class function'
        super().__init__(msg, *args)

class AliasUnavailableError(Exception):
    def __init__(self, *args: object) -> None:
        msg = 'Unsupported Variable name. The alias has already been registered! please provide a different name.'
        super().__init__(msg, *args)

class DefaultNotRegisteredError(Exception):
    def __init__(self, arg:str, *args: object) -> None:
        msg = f'No default argument for <{arg}> in the fallback config, please register a default value in the fallback config.'
        super().__init__(msg, *args)


class ConfigIO:

    @staticmethod
    def __default_checks__(fpath:Path):

        # default case
        if fpath is None:
            fpath = DEFAULT_PATH_TO_CONFIG

        # catch edge case where saveas is given as a str
        if not isinstance(fpath, Path):
            fpath=Path(fpath)

        # return modified Path object
        return fpath
    
    @classmethod
    def writeto(cls, config:Config, fpath:Path=None) -> None:

        # do standard checks
        fpath = cls.__default_checks__(fpath)

        # if yaml file extension not in path -> add
        if not (str(fpath).endswith('.yml') or str(fpath).endswith('.yaml')):
            fpath = Path(str(fpath)+'.yml')

        todump = config._tree
        # save to disk in str format (! not bytes)
        with open(fpath,'w') as fp:

            # write to disk
            dump(todump, fp)

    @classmethod
    def readfrom(cls, configClass:Config, fpath:Path=None) -> Config:

         # do standard checks
        fpath = cls.__default_checks__(fpath)

        # open read only
        with open(fpath,'r') as fp:

            # read tree from disk
            loaded = load(fp, Loader)
        
        # Initialse config object and set tree
        state = loaded.get('general')
        obj = configClass(name=state._name, strict=state._strict)
        obj.settree(loaded)

        # return initialised Config object
        return obj

class ConfigFormatter:
    @classmethod
    def format(cls, config: BaseConfig):
        # initialise buffer
        printable = list()

        # table definition
        elbow = "└──"
        pipe  = "|  "
        tee   = "├──"
        blank = "   "

        printable.append('::'+str(type(config))+' @ '+"<{}>".format(hex(id(config)))+ f': name "{config._name}"'+ '::')
        def get_tree(_config, level=0, header=''):
            # function that generates a config tree string
            # get keys and associated names
            children = list(_config._tree.values())
            values   = list(_config._tree.keys())
        
            # recursive tree generator
            for level, (child, value) in enumerate(zip(children, values)):
                last = level == len(children)-1
                printable.append(header + (elbow if last else tee) + (str(value)+": "+repr(child))*(repr(child)!=value) + (str(value)+':')*(repr(child)==value))
                if hasattr(child,'_tree'):
                    get_tree(child, level=level, header = header + (blank if last else pipe))

        # get tree
        get_tree(config)

        # return string object
        return '\n'.join(printable)
        

    @classmethod
    def __repr__(cls, config:Config):
        return cls.format(config)
           


class ConfigHandler:

    _banned: list[str] = ['register', 'writeto', 'readfrom', 'tree', 'banned', 'strict','verified'] 
    
    @staticmethod
    def _isdunder(alias:str) -> bool:
        return alias[:2] =='__' or alias[-2:] == '__'
    
    @staticmethod
    def _issunder(alias:str) -> bool:
        return alias[-1:] == '_' or alias[:1] == '_'
    
    @classmethod
    def _isbanned(cls, alias:str) -> str:
        # return true if name is banned or private (_), private protected (__), dunder or sunder.
        return alias in cls._banned or cls._isdunder(alias) or cls._issunder(alias)
    
    @classmethod
    def _is_banned_or_registered(cls, obj:dict, alias: str, overwrite:bool, strict:bool):
        # catch banned name:
        if cls._isbanned(alias):

            # if strict throw error
            if strict:
                raise NameError

            # else warn used and do Nothing
            warnings.warn(f'{alias} is a banned name. Please provide a different name. Field was not registered!!', UserWarning, stacklevel=WARNING_STACK_LVL)
            return True
        
        # catch already registerd
        if alias in obj:
            # if user did not specify overwrite
            if not overwrite:

                if strict:
                    # raise blocking Error
                    raise AliasUnavailableError
                
                # otherwise warn user and do nothing
                warnings.warn(f'{alias} is already registered, if you mean to overwrite the path please provide overwrite=True to the function call.', UserWarning, stacklevel=WARNING_STACK_LVL)
                return True
            
        # otherwise not banned or registered
        return False
                
    @classmethod
    def registerGroup(cls, obj:dict, alias:str, configClass: Any, *, overwrite:bool=False, strict:bool=False) -> BaseConfig:

        # check if alias is valid
        cls._is_banned_or_registered(obj, alias, overwrite, strict)

        # add as property dynamically: this is dangerous!
        # --> Make sure all <self> altering edge cases are caught before this line\
        obj[alias] = configClass(name=alias, strict=strict)
        logging.info(f'added group of type <{configClass}> under alias {alias} to config')
    
        return obj[alias]

    @classmethod
    def register(cls, obj:dict, alias:str, value:Any, *, overwrite:bool=False, strict:bool=False, __finalise_entry__:Callable=lambda x,y: (x,y), **kwargs:dict):
        # check if alias is valid
        if not cls._is_banned_or_registered(obj, alias, overwrite=overwrite, strict=strict):

            # finalise array depending on config type
            alias, value = __finalise_entry__(alias, value, **kwargs)

            # add as property dynamically: this is dangerous!
            # --> Make sure all <self> altering edge cases are caught before this line
            obj[alias] = value
            logging.info(f'added directory {value} under alias {alias} to config')



class Config:
    'Config object that allows you to register variables and IO them to disk uisng the YAML standard.'
    # Initialisation # 
    def __init__(self, name:str='general', strict:bool=False) -> None:
        
        # set name
        self._name = name

        # set content manager and content fields
        self._handler = ConfigHandler
        self._tree = dict()
        self._strict  = strict

        # register the base name into the config object
        self.registerGroup(name, BaseConfig)

    @property
    def strict(self):
        # expose private _strict to user
        return self._strict
    
    def settree(self, _tree)-> None:
        self._tree.update(_tree)

    def registerGroup(self, alias:str, configClass:Any, *, overwrite:bool=False):
        # ask handler to register group
        return self._handler.registerGroup(self._tree, alias, configClass, overwrite=overwrite, strict=self.strict)
    
    def register(self, alias, value, *, group:str=None, overwrite=False):
        
        # set default
        if group is None:
            group = self._name

        # get config object
        obj = self._tree[group]
      
        # register in corresponding config object
        obj.register(alias, value, overwrite=overwrite, strict=self.strict)
    
    def __getattribute__(self, __name: str) -> BaseConfig | Any:
        return super().__getattribute__(__name)
    
    def __getattr__(self, __name) -> BaseConfig | Any:
        _tree = super().__getattribute__('_tree')
        if __name in _tree:
            return _tree[__name]

    def __contains__(self, __key):
        return self._tree.__contains__(__key)
    
     # IO #
    def writeto(self, fpath:Path=None) -> None:
        # write using IO object
        ConfigIO.writeto(self, fpath=fpath)

    @classmethod
    def readfrom(cls, fpath:Path=None) -> Config:
        # read using IO object
        return ConfigIO.readfrom(cls, fpath=fpath)
    
    def __add__(self, other):
        self.settree(other._tree)
        return self
    
    def __repr__(self):
        return ConfigFormatter.__repr__(self)
    
    def verified(self):
        return False
                
class BaseConfig:

    # set handler class
    _handler = ConfigHandler

    def __init__(self, name:str, strict:bool):  

        # initialise user defined parameters
        self._name = name
        self._strict=strict
    
        # initiliase buffer
        self._tree = dict()

    def __conform_subclass__(self):
        if self._tree != {}:
            # after initialisation if tree is not empty, make sure it conforms to __finalise_entry__
            
            self._tree = {alias:self.__finalise_entry__(alias, value)[-1] for alias, value in self._tree.items()}
    
    # # defined properties #
    def __finalise_entry__(self, alias:str, value:Any, **kwargs: dict):
        '''function called before alias and value are registered. In when subclassing the Config object
        overwrite this function with your desired functionality.'''

        # return alias and value to add
        return alias, value

    def __contains__(self, __key):
        self._tree.__contains__(__key)    

    def get(self, name:str, **kwargs:dict):
        # getter with default value if not registered in config.
        # will check if name is in self.__dict__ if AttributeError, will check
        # self._handler._tree if AttributeError again --> return default if defined
        with warnings.catch_warnings(action='error'):
            try:
                return self.__getattr__(name)
            except (AttributeError, UserWarning):
                # not registerd in self so maybe in children?
                for child in self._tree.values():
                        # if it has a _tree --> then its a config object
                        if hasattr(child,'_tree'):

                            # if name is registered in _tree
                            if name in child._tree:

                                # return value
                                return child.get(name)
                            
            # else if default
            if 'default' in kwargs:
                # return 
                return kwargs.pop('default')
            else:
                # otherwise if strict throw error else warn user
                if self._strict:
                    raise AttributeError
                else:
                    warnings.warn(f'alias <{name}> not registerd in <{self}> or children theirin', UserWarning, stacklevel=WARNING_STACK_LVL)

                                

    def __getattribute__(self, __name: str) -> BaseConfig | Any:
        # callback hook for every dot search
        return super().__getattribute__(__name)
    
    def __getattr__(self, __name: str) -> BaseConfig | Any:
        # check if key is in the _tree
        if __name in super().__getattribute__('_tree'):
            # then return
            return self._tree[__name]
        
        # otherwise
        else:
            # if strict
            if self._strict:
                # raise blocking error
                raise AttributeError(f"Attribute {__name} was not registered in Config object, please make sure to .register the attribute first")
            # else warn user
            warnings.warn(f"Attribute {__name} was not registered in Config object, please make sure to .register the attribute first", UserWarning, stacklevel=WARNING_STACK_LVL)

    def __add__(self, other:BaseConfig) -> Config:
        # + operator is overwritten to merge and prioritise left
        # merge trees
        newtree = self._tree | other._tree
        # return new cfg
        return other._create_(newtree, name=other._name, strict=False)

    def registerGroup(self, alias:str, configClass:Any, *, overwrite:bool=False, strict:bool=False):
        # ask handler to register group
        return self._handler.registerGroup(self._tree, alias, configClass, overwrite=overwrite, strict=strict)
    
    def register(self, alias:str, value:Any, *, overwrite:bool=False, strict:bool=False, **kwargs:dict) -> None:
        # check if alias is valid
        self._handler.register(self._tree, alias, value, overwrite=overwrite, strict=strict, __finalise_entry__=self.__finalise_entry__)

    @classmethod
    def _create_(cls, tree:dict, name:str, strict:bool):
        # helper function for __dunder__ operation overwrites
        cfg = cls(name=name, strict=strict)
        cfg.settree(tree)

        # return new object with intialised tree
        return cfg

    # UI #
    def __repr__(self) -> str:
       return ConfigFormatter.__repr__(self)
    
    def __eq__(self, other) -> bool:
        return self._tree == other._tree
    
    def __repr__(self) -> str:
        return self._name
        
    
    def __str__(self) -> str:
       return ConfigFormatter.format(self)
    
    def verified(self) -> bool:
        return False
    
    def settree(self, tree:dict) -> None:
        # set tree in handler directly
        self._tree.update(tree)

        # and make sure that the tree conforms to the subclass specific rules
        self.__conform_subclass__()

    def __enter__(self) -> dict:
        # return tree dict
        return self.tree
    
    def __exit__(self, *args):
        pass
        

class FileConfig(BaseConfig):
    def __finalise_entry__(self, alias:str, value:Path, **kwargs:dict):
        
        # catch typing edge case
        if type(value) is str:
            value = Path(value)

         # check if exists on system -> not?
        if not value.exists():
            
            # if allowed to create 
            if kwargs.pop('forcecreate', False):
                # then create
                value.mkdir(parents=True)
                logging.info(f'Directory {value} successfully created!')

            elif self._strict:
                # in case strict: throw blocking error     
                raise FileNotFoundError(f'Did not find directory <{value}>.')
            else:

                # warn user and do nothing
                warnings.warn(f'directory "{value}", registered as <{alias}>, does not exist on system!', UserWarning, stacklevel=WARNING_STACK_LVL)
        
        # return alias and value to register
        return alias, value
    
    # derived properties #
    def verified(self) -> bool:
        # verify that all registered directories exists on system
        return all([path.exists() for path in self._tree.values() if not self._tree is None])


class ArgumentParserWithFallback(ArgumentParser):
    def __init__(self, fallback:Config|None=None, **kwargs) -> None:
        # get standard behaviour
        super().__init__(**kwargs)

        # if fallback config not given, initialise regular argument parser
        # else assign fallback_config
        if not fallback is None:
            self._fallback_config = fallback
        else:
            return ArgumentParser(**kwargs)
        
        # initialise return product
        self._parsed_args = dict()

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):

        # parse known args
        self._parsed_args = self.parse_known_args()[0]

        # go into dict
        for arg, value in self._parsed_args.__dict__.items():

            # if value is None
            if value is None:

                # try to match config registry
                # if strict and no match raise error
                if self._fallback_config._strict:
                    try:
                        self._fallback_config.get(arg)
                    except AttributeError:
                        raise DefaultNotRegisteredError
                    
                # otherwise default to None if no match
                # and warn user of no match
                else:
                    try:
                        with warnings.catch_warnings(action='error'):
                            self._parsed_args.__dict__[arg] = self._fallback_config.get(arg)
                    except UserWarning:
                        warnings.warn(f'No default argument for <{arg}> in the fallback config: defaulted to None', stacklevel=WARNING_STACK_LVL)
                        self._parsed_args.__dict__[arg] = None
                        
    
    def parse_args(self) -> Namespace:
        # return output product
        return self._parsed_args
        


def UnitTests() -> bool:

    # create config and register
    cfg = Config()
    cfg.register('mystring','hello world')
    cfg.register('mybool', False)
    cfg.register('myint', 1)
    cfg.register('myfloat', 1.)
    cfg.register('mylist', list([1.,2.]))
    cfg.register('mydict', {'a':1, 'b':2})

    # other cfg
    other_cfg = Config()
    other_cfg.register('myfloat', 5.)

    # test operations
    res = cfg + other_cfg
    if res.myfloat != 5.:
        return False
    res = cfg / other_cfg
    if res.myfloat != 1.:
        return False
    res = cfg // other_cfg
    if res.myfloat != 1.:
        return False
    del other_cfg
    
    # test write, test read
    _cfg = cfg
    cfg.writeto()
    del cfg
    cfg = Config.readfrom()
    if _cfg != cfg:
        return False
    del _cfg, cfg

    # import os and platform to force remove file after read write test
    import os
    import platform
    match platform.system().lower():
        case 'windows':
            os.system('del -f config.yml')
        case 'linux':
            os.system('rm -f config.yml')
    
    # test cross configClass operations
    cfg      = Config()
    file_cfg = FileConfig()
    if type(cfg+file_cfg) != FileConfig or\
       type(file_cfg+cfg) != Config or\
       type(file_cfg // cfg) != Config or\
       type(cfg / file_cfg) != Config or\
       type(file_cfg / cfg) != FileConfig:
        return False
    del cfg
    del file_cfg

    # test errors
    cfg = Config(strict=True)
    try: 
        cfg.register('tree', 'tree')
        return False
    except NameError:
        pass
    cfg.register('myfloat', 5.)
    try:
        cfg.register('myfloat', 1.)
        return False
    except AliasUnavailableError:
        pass
    try:
        cfg.myint
        return False
    except AttributeError:
        pass
    del cfg
    cfg = FileConfig(strict=True)
    try:
        cfg.register('source', 'my/path/source')
        return False
    except FileNotFoundError:
        pass
    try:
        cfg.register('test',Path.cwd()/'configlib_unittest', forcecreate=True)
    except FileNotFoundError:
        return False
    if not cfg.verified():
        return False
    os.rmdir(Path.cwd()/'configlib_unittest')
                    
    # test warning
    del cfg
    cfg = FileConfig()
    with warnings.catch_warnings(category=UserWarning, append=True, action='error') as w:
        try:
            cfg.register('source', 'my/path/source')
            return False
        except UserWarning:
            pass
    del os, platform
    return True


if __name__ == '__main__':
    if UnitTests():
        # log succesful
        logging.info('Package testes succesfully')
    else:
        logging.warning('Package critically failed Unit testing!')