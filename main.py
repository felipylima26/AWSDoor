import argparse
import sys
from awsdoor.DoorModule import DoorModule

# [System.Environment]::SetEnvironmentVariable('AWS_ACCESS_KEY_ID','AKIA......')
# [System.Environment]::SetEnvironmentVariable('AWS_SECRET_ACCESS_KEY','....ahkZ5rX')
# [System.Environment]::SetEnvironmentVariable('AWS_DEFAULT_REGION','eu-west-3')


if __name__ == "__main__":
    modules = DoorModule.available_modules()
    module_help = 'The module type : {}{}'.format(
        '\n\t- ' * (len(modules) > 0),
        '\n\t- '.join([f'{elt["name"]} ({elt["type"]}): {elt["help"]}' for elt in modules])
    )
    parser = argparse.ArgumentParser(
        description="AwsDoor",
        formatter_class = argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "-m",
        '--module',
        help=module_help,
        choices=[elt['type'] for elt in modules],
        required=True
    )
    args, _ = parser.parse_known_args(sys.argv[1:])
    module_object = DoorModule.get_module(args.module)
    module = module_object(sys.argv[1:])
    module.run()



