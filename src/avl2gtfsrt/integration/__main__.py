import click
import logging

from avl2gtfsrt.integration.instancemanager import InstanceManager


@click.group()
def cli():
    pass

@cli.command()
def run():
    
    # set logging default configuration
    logging.basicConfig(format="[%(levelname)s] %(asctime)s %(message)s", level=logging.INFO)

    # startup instances regarding the config YAML file
    try:
        mgr: InstanceManager = InstanceManager()
        mgr.run()
    except Exception as ex:
        logging.exception(ex)

if __name__ == '__main__':
    cli()