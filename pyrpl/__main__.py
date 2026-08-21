"""
Script to launch pyrpl from the command line.

Type python -m pyrpl [config_file_name] to create
a Pyrpl instance with the config file
"config_file_name"
"""
import sys
try:
    from pyrpl import Pyrpl, help_message
    from pyrpl.async_utils import LOOP
except ImportError:
    from . import Pyrpl, help_message
    from .async_utils import LOOP

def main():
    if any(arg in ('-h', '--help') for arg in sys.argv[1:]):
        print(help_message)
        return

    if len(sys.argv) > 3:
        print("usage: sinclair-pyrpl-wwlyn [[config=]config_file_name] "
              "[source=config_file_template] [hostname=hostname/ip]")
    kwargs = dict()
    for i, arg in enumerate(sys.argv):
        print (i, arg)
        if i == 0:
            continue
        try:
            k, v = arg.split('=', 1)
        except ValueError:
            k, v = arg, ""
        if v == "":
            if i == 1:
                kwargs["config"] = k
        else:
            kwargs[k] = v
    #APP = QtWidgets.QApplication.instance()
    #if APP is None:
    #    APP = QtWidgets.QApplication(sys.argv)

    print("Calling Pyrpl(**%s)"%str(kwargs))
    PYRPL = Pyrpl(**kwargs)
    if not LOOP.is_running():
        LOOP.run_forever()


if __name__ == '__main__':
    main()
