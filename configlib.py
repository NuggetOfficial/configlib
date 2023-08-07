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
        longest_value= max([len(str(path))  for path  in config._tree.values()])
        longest_key  = max([len(str(alias)) for alias in config._tree.keys()])
        
        # define formatting functions
        keyformat   = lambda key  : str(key)   + ' '*(longest_key-len(str(key)))
        valueformat = lambda value: str(value) + ' '*(longest_value-len(str(value)))

        # define pre and post amble of repr object
        preamble = f'\n {type(config)} @ <{hex(id(config))}> \n'
        postamble = '\n---- verified:\t{} ----\n'.format(getattr(config, 'verified', None))

        # generate table content
        content  = ["|{}|".format(keyformat(key))+"|\t{}|".format(valueformat(value)) for key, value in config._tree.items()]

        # return table
        return preamble+'\n'.join(content)+postamble
    

class Config:
    'Config object that allows you to register variables and IO them to disk uisng the YAML standard.'
    # Initialisation # 
    def __init__(self, tree:dict={}, strict:bool=False) -> None:

        self._tree: dict = tree
        self._banned: list[str] = ['register', 'writeto', 'readfrom', 'tree', 'banned', 'strict']
        self._strict = strict

        # post init
        self.__post_init__()

    def __post_init__(self):

        # if a tree is set by the user
        if self._tree != {}:

            # register all the entries
            [self.register(alias, value) for alias, value in self._tree.items()]

    
    # defined properties #
    @property
    def tree(self):
        # expose private _tree to user
        return self._tree
    
    @property
    def banned(self):
        # expose private _banned to user
        return self._banned
    
    @property
    def strict(self):
        # expose private _strict to user
        return self._strict
    
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
            if self._strict:
                raise NameError
            
            # create message
            msg = f'{alias} is a banned name. Please provide a different name'

            # else warn used and do Nothing
            warnings.warn(msg)
            return None

        # catch already registerd
        if alias in vars(self).keys():
            
            # if user did not specify overwrite
            if not overwrite:

                if self._strict:
                    # raise blocking Error
                    raise AliasUnavailableError
                
                # else create message
                msg = f'{alias} is already registered, if you mean to overwrite the path please provide overwrite=True to the function call.'

                # amd warn user, do nothing
                warnings.warn(msg)
                return None

        # finalise array depending on config type
        alias, value = self.__finalise_entry__(alias, value, **kwargs)

        # add to tree
        logging.info(f'added directory {value} under alias {alias} to config')
        self._tree[alias] = value

        # add as property dynamically: this is dangerous!
        # --> Make sure all <self> altering edge cases are caught before this line
        self.__setattr__(alias,value)

    # def __setattr__(self, __name: str, __value: Any) -> None:

    #     if self._isbanned()

    #     if __name not in self._tree:
    #         self._tree[__name]=__value
        
        
        
    # def __getattribute__(self, __name: str) -> Any:
    #     pass


    def __add__(self, other:Config) -> Config:
        
        if type(self) == type(other):
            # merge trees
            newtree = self._tree | other._tree
            
            # Create new Config object
            cfg = Config(tree=newtree, strict=False)

            # return new cfg
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

            elif self._strict:
                # in case strict: throw blocking error     
                raise FileNotFoundError(f'Did not find directory <{value}>.')
            else:
                # create message,
                msg = f'directory "{value}", registered as <{alias}>, does not exist on system!'

                # warn user and do nothing
                warnings.warn(msg)
        
        # return alias and value to register
        return alias, value
    
    # derived properties #
    @property
    def verified(self) -> bool:
        # verify that all registered directories exists on system
        return all([path.exists() for path in self._tree.values() if not self._tree is None])

if __name__ == '__main__':
    cfg = FileConfig()
    cfg.register('source','my/path/source')
    #print(cfg)

    #tree = {'source':'my/path/source', 'data':'my/path/data'}
    #precfg= FileConfig(tree=tree)
    #print(precfg)
    print(cfg)
    othercfg = FileConfig()
    othercfg.register('data','my/path/data')
    print(cfg)

    combinedcfg = cfg + othercfg
    #print(cfg)
    #print(othercfg)
    #print(combinedcfg)

    
    
    