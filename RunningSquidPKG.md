# Running SquidPKG #

You can run the SquipdPKG Python script from a remote server or on each host locally. The command line parameters are:
```
    -h, --help            show this help message and exit
    -p SOFTWARE, --path=SOFTWARE
                        Set path of software repository.
    -r ROOT, --root=ROOT  Set path of squidpkg root directory.
    -c CONFIG, --config=CONFIG
                        Set path of local config XML, else defaults to root
                        directory.
    -l LOG, --log=LOG     Set path of log file, else defaults to root directory.
    -t HOST, --hostname=HOST
                        Set hostname variable manually.
    -v, --verbose       Enable verbose mode.
    -d, --debug         Be more verbose.
```


The software repository path and SquidPKG root path are required parameters. The localconfig.xml file is what SquidPKG uses to see what is installed on the system, and at what version. If localconfig.xml is removed, SquidPKG will create a new one, and install all software in a host's profile (since it does not know what is installed). It is highly recommended that you set this for your needs, especially if running SquidPKG off of a server share (or else every new host will over-write the config file). You can manually modify localconfig.xml on a host machine if there is an issue with the automatic writing of the file, but this shouldn't be necessary.

You can use 'remove' instead of 'package-id' in profiles.xml to use the remove commands in a package XML file.

SquidPKG will automatically generate a log file in the format squidpkg`_`'hostname'.log in the specified log directory (or the SquidPKG root directory if not set manually). Look here for any install or other errors. You can also use the -v or --verbose flag to see more output as SquidPKG runs, or the -d or --debug flag to see a lot more output.