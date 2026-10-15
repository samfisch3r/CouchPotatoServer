CouchPotato
=====

[![Join the chat at https://gitter.im/CouchPotato/CouchPotatoServer](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/CouchPotato/CouchPotatoServer?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)
[![Python tests](https://github.com/samfisch3r/CouchPotatoServer/actions/workflows/tests.yml/badge.svg)](https://github.com/samfisch3r/CouchPotatoServer/actions/workflows/tests.yml)

CouchPotato (CP) is an automatic NZB downloader. You can keep a "movies I want"-list and it will search Usenet for NZBs of these movies every X hours.
Once a movie is found, it will send the NZB to an enabled Usenet downloader or save it to a watched directory.


## Running from Source

CouchPotatoServer can be run from source. This will use *git* as updater, so make sure that is installed.

### Ubuntu Linux

* Install Git, Python, and the native build prerequisites with `sudo apt install git python3 python3-venv python3-dev build-essential libxml2-dev libxslt1-dev`.
* If you enable automatic RAR extraction, install a compatible command-line RAR tool (such as `unrar`); configure its path in Renamer settings only if it is not on `PATH`.
* Clone the repository, then create an isolated Python environment and install the maintained dependencies:

  ```sh
  python3 -m venv .venv
  .venv/bin/pip install -r requirements.txt
  ```

* Start the application with `.venv/bin/python CouchPotato.py`.
* To run it as a service, install `init/couchpotato.service` as `/etc/systemd/system/couchpotato.service`, update its user and application path (including the `.venv` Python path), then run `sudo systemctl enable --now couchpotato`.
* Open `http://localhost:5050/`.

The fork targets Ubuntu and Python 3.12 through 3.14. Maintained third-party dependencies are installed from `requirements.txt`; some application-specific and media-processing libraries remain bundled. The database engine is a modified legacy dependency, so back up your data before upgrading and test with a copy first. The migration has not yet been validated against a production database or by running the service on Ubuntu.


## Development

Install the runtime and development dependencies, then run the tests with:

```sh
python3 -m pip install -r requirements.txt -r requirements-dev.txt
python3 -c "import sys; sys.path.append('libs'); import pytest; raise SystemExit(pytest.main(['couchpotato']))"
```

If you're going to add styling or doing some javascript work you'll need a few tools that build and compress scss -> css and combine the javascript files. [Node/NPM](https://nodejs.org/), [Grunt](http://gruntjs.com/installing-grunt), [Compass](http://compass-style.org/install/)

After you've got these tools you can install the packages using `npm install`. Once this process has finished you can start CP using the command `grunt`. This will start all the needed tools and watches any files for changes.
You can now change css and javascript and it wil reload the page when needed.

By default it will combine files used in the core folder. If you're adding a new .scss or .js file, you might need to add it and then restart the grunt process for it to combine it properly.

Don't forget to enable development inside the CP settings. This disables some functions and also makes sure javascript errors are pushed to console instead of the log.
