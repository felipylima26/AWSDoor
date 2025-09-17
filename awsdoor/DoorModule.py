from typing import List, Dict, Type

class DoorModule:
    def __init__(self, argv:list[str]):
        raise NotImplemented

    def run(self):
        raise NotImplemented

    @staticmethod
    def available_modules() -> list[dict]:
        modules = []
        for obj in DoorModule.__subclasses__():
            name = obj.__name__
            help = ''
            if hasattr(obj, 'Meta') and hasattr(obj.Meta, 'name'):
                name = obj.Meta.name
            if hasattr(obj, 'Meta') and hasattr(obj.Meta, 'help'):
                help = obj.Meta.help
            modules.append({
                'type': obj.__name__,
                'name': name,
                'help': help,
            })
        return modules

    @staticmethod
    def get_module(module:str) -> Type['DoorModule']:
        for obj in DoorModule.__subclasses__():
            if obj.__name__ == module:
                return obj
        raise ValueError(f'The module {module} does not exist')

