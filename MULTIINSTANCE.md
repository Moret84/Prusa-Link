# PrusaLink multi instance
In this mode, an instance of PrusaLink is created for each new printer
detected on any of the USB ports of the host system, allowing the user
to connect multiple printers using a single Raspberry Pi.

## Setup
The multi instance image requires the same setup as the regular one,
but there are some differences

1) The multi-instance manager does not connect to printers on the GPIO
pins as the device udev auto-detection in Linux does not work on those
2) In this image, the manager of these PrusaLink instances is run as root.
However web interface of the instance manager is run under the user account.

## Running the manager
To run PrusaLink in the multi-instance mode run `prusalink-manager start`
as root. There are other options allowing you to specify which user to run the
instances and web under. The default is UID = 1000

Here's the help output of prusalink-manager

```
Multi-instance suite for PrusaLink

positional arguments:
  {start,stop,clean,rescan}
                        Available commands
    start               Start the instance managing daemon (needs root
                        privileges)
    stop                Stop any manager daemon running (needs root
                        privileges)
    clean               Danger! cleans all PrusaLink multi-instance
                        configuration
    rescan              Notify the daemon a printer has been connected

options:
  -h, --help            show this help message and exit
  -i, --info            include log messages up to the INFO level
  -d, --debug           include log messages up to the INFO level
  -u USERNAME, --username USERNAME
                        Which users to use for running and storing everything
  -p PREPEND_EXECUTABLES_WITH, --prepend-executables-with PREPEND_EXECUTABLES_WITH
                        Environment variables and path to the executables
                        directory
```
