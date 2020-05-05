#!/usr/bin/env python
from flask_script import Server, Manager

from websub import commands
from websub.app import create_app

app = create_app(config_object='websub.conf.DevelopmentConfig')
manager = Manager(app)

manager.add_command("runserver", Server())
manager.add_command('run-callbacks-delivery-processor', commands.RunCallbacksDeliveryProcessor())
manager.add_command('run-callbacks-spreader-processor', commands.RunCallbacksSpreaderProcessor())


def main():
    manager.run()


if __name__ == "__main__":
    main()
