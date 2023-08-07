# future annotations
from __future__ import annotations

# buildin
from pathlib import Path
from typing import Any
import logging
import warnings

# dependencies
from yaml import load, dump, Loader

# Global default path 
DEFAULT_PATH_TO_CONFIG = Path.cwd()/'config.yml'

class NameError(Exception):
    def __init__(self, *args: object) -> None:
        msg = 'Unsupported Variable name. Varialbe cannot be private (_), private protected (__), dunder, sunder or overwrite a class function'
        super().__init__(msg, *args)

class AliasUnavailableError(Exception):
    def __init__(self, *args: object) -> None:
        msg = 'Unsupported Variable name. The alias has already been registered! please provide a different name.'
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

        # save to disk in str format (! not bytes)
        with open(fpath,'w') as fp:

            # write to disk
            dump(config.tree, fp)

    @classmethod
    def readfrom(cls, configType:Config, fpath:Path=None) -> Config:

         # do standard checks
        fpath = cls.__default_checks__(fpath)

        # open read only
        with open(fpath,'r') as fp:

            # read tree from disk
            tree = load(fp, Loader)

        # return initialised Config object
        return configType(tree)

class ConfigRepr:
    @staticmethod
    def __repr__(config: Config):
           
        # get longest entries, char wise
        longest_value= max([len(str(path))  for path  in config._handler._tree.values()])
        longest_key  = max([len(str(alias)) for alias in config._handler._tree.keys()])
        
        # define formatting functions
        keyformat   = lambda key  : str(key)   + ' '*(longest_key-len(str(key)))
        valueformat = lambda value: str(value) + ' '*(longest_value-len(str(value)))

        # define pre and post amble of repr object
        preamble = f'\n {type(config)} @ <{hex(id(config))}> \n'
        postamble = '\n---- verified:\t{} ----\n'.format(config.verified())

        # generate table content
        content  = ["|{}|".format(keyformat(key))+"|\t{}|".format(valueformat(value)) for key, value in config._handler._tree.items()]

        # return table
        return preamble+'\n'.join(content)+postamble

class ConfigDict:
    def __init__(self, tree:dict={}, strict:bool=False) -> None:
        self._tree = tree
        self._strict = strict

class Config:
    'Config object that allows you to register variables and IO them to disk uisng the YAML standard.'
    # Initialisation # 
    def __init__(self, strict:bool=False) -> None:

        self._handler = ConfigDict(dict(), strict)
        self._banned: list[str] = ['register', 'writeto', 'readfrom', 'tree', 'banned', 'strict','verified']

    def __conform_subclass__(self):
        if self._handler._tree !={}:
            # after initialisation if tree is not empty, make sure it conforms to __finalise_entry__
            self._handler._tree = {alias:self.__finalise_entry__(alias, value)[-1] for alias, value in self._handler._tree.items()}

    # # defined properties #
    @property
    def tree(self):
        # expose private _tree to user
        return self._handler._tree
    
    @property
    def banned(self):
        # expose private _banned to user
        return self._banned
    
    @property
    def strict(self):
        # expose private _strict to user
        return self._handler._strict
    
    # util #
    @staticmethod
    def _isdunder(alias:str) -> bool:
        return alias[:2] =='__' or alias[-2:] == '__'
    
    @staticmethod
    def _issunder(alias:str) -> bool:
        return alias[-1:] == '_' or alias[:1] == '_'
    
    def _isbanned(self, alias:str) -> str:
        # return true if name is banned or private (_), private protected (__), dunder or sunder.
        return alias in self._banned or self._isdunder(alias) or self._issunder(alias)
    
    def __finalise_entry__(self, alias:str, value:Any, **kwargs: dict):
        '''function called before alias and value are registered. In when subclassing the Config object
        overwrite this function with your desired functionality.'''

        # return alias and value to add
        return alias, value

    # core functionality #
    def register(self, alias:str, value:Any, *, overwrite:bool=False, **kwargs:dict) -> None:

         # catch banned name:
        if self._isbanned(alias):

            # if strict throw error
            if self._handler._strict:
                raise NameError

            # else warn used and do Nothing
            warnings.warn(f'{alias} is a banned name. Please provide a different name', UserWarning)
            return None

        # catch already registerd
        if alias in self._handler._tree:
            # if user did not specify overwrite
            if not overwrite:

                if self._handler._strict:
                    # raise blocking Error
                    raise AliasUnavailableError
                
                # otherwise warn user and do nothing
                warnings.warn(f'{alias} is already registered, if you mean to overwrite the path please provide overwrite=True to the function call.', UserWarning)
                return None

        # finalise array depending on config type
        alias, value = self.__finalise_entry__(alias, value, **kwargs)

        # add as property dynamically: this is dangerous!
        # --> Make sure all <self> altering edge cases are caught before this line
        self._handler._tree[alias] = value
        logging.info(f'added directory {value} under alias {alias} to config')
        
    def __getattribute__(self, __name: str) -> Any:
        # callback hook for every dot search
        return super().__getattribute__(__name)
    
    def __getattr__(self, __name: str) -> Any:
        # if __getattribute__ raises attribute error search in the _handler
        # get handler from super in order to get _tree
        _handler = self._handler
        _tree    = _handler._tree

        # check if key is in the _tree
        if __name in _tree:
            # then return
            return _tree[__name]
        
        # otherwise
        else:
            # if strict
            if _handler._strict:
                # raise blocking error
                raise AttributeError(f"Attribute {__name} was not registered in Config object, please make sure to .register the attribute first")
            # else warn user
            warnings.warn(f"Attribute {__name} was not registered in Config object, please make sure to .register the attribute first", UserWarning)

    def __add__(self, other:Config) -> Config:
        # + operator is overwritten to merge and prioritise left
        # merge trees
        newtree = self._handler._tree | other._handler._tree 
        # return new cfg
        return other._create_(newtree, strict=False)
    
    def __truediv__(self, other: Config):
        # / operator is overwritten to merge and prioritise right
        # merge trees
        newtree = other._handler._tree | self._handler._tree
        # return new cfg
        return self._create_(newtree, strict=False)
    
    @classmethod
    def _create_(cls, tree:dict, strict:bool):
        # helper function for __dunder__ operation overwrites
        cfg = cls(strict=False)
        cfg.settree(tree)

        # return new object with intialised tree
        return cfg
    
    # IO #
    def writeto(self, fpath:Path=None) -> None:
        # write using IO object
        ConfigIO.writeto(self, fpath=fpath)

    @classmethod
    def readfrom(cls, fpath:Path=None) -> Config:
        # read using IO object
        ConfigIO.readfrom(cls, fpath=fpath)

    # UI #
    def __repr__(self) -> str:
       return ConfigRepr.__repr__(self)
    
    def verified(self) -> bool:
        return False
    
    def settree(self, tree:dict) -> None:
        # set tree in handler directly
        self._handler._tree = tree

        # and make sure that the tree conforms to the subclass specific rules
        self.__conform_subclass__()

class FileConfig(Config):
    def __finalise_entry__(self, alias:str, value:Path, **kwargs:dict):
        
        # catch typing edge case
        if type(value) is str:
            value = Path(value)

         # check if exists on system -> not?
        if not value.exists():
            
            # if allowed to create 
            if getattr(kwargs, 'forcecreate', False):
                    # then create
                    value.mkdir(parents=True)
                    logging.info(f'Directory {value} successfully created!')

            elif self._handler._strict:
                # in case strict: throw blocking error     
                raise FileNotFoundError(f'Did not find directory <{value}>.')
            else:

                # warn user and do nothing
                warnings.warn(f'directory "{value}", registered as <{alias}>, does not exist on system!', UserWarning)
        
        # return alias and value to register
        return alias, value
    
    # derived properties #
    def verified(self) -> bool:
        # verify that all registered directories exists on system
        return all([path.exists() for path in self._handler._tree.values() if not self._handler._tree is None])
    


    
    
    