CouchPotato
=====

[![Python tests](https://github.com/samfisch3r/CouchPotatoServer/actions/workflows/tests.yml/badge.svg)](https://github.com/samfisch3r/CouchPotatoServer/actions/workflows/tests.yml)

CouchPotato (CP) is an automatic NZB movie downloader. You can keep a "movies I want" list and it will frequently search Usenet via your configured NZB provider (such as Newznab indexers) for these movies.
Once a matching release is found, it automatically dispatches the download to SABnzbd connected via API key and can rename/organize completed downloads.


## Running from Source

CouchPotatoServer runs on modern Ubuntu with Python 3.12 through 3.14.

### Ubuntu Linux

* Install system prerequisites:
  ```sh
  sudo apt update
  sudo apt install -y git python3 python3-venv python3-dev build-essential
  ```
* If you enable automatic RAR extraction in Renamer settings, install a compatible command-line tool (such as `unrar`).
* Clone the repository and set up a Python virtual environment:

  ```sh
  python3 -m venv .venv
  .venv/bin/pip install --upgrade pip
  .venv/bin/pip install -r requirements.txt
  ```

* Start the application manually:
  ```sh
  .venv/bin/python CouchPotato.py
  ```
* Access the web interface at `http://localhost:5050/`.

### Running as a systemd Service

1. Copy `init/couchpotato.service` to `/etc/systemd/system/couchpotato.service`.
2. Ensure the `User`, `WorkingDirectory`, and `ExecStart` paths in the service file match your installation directory.
3. Enable and start the service:
   ```sh
   sudo systemctl daemon-reload
   sudo systemctl enable --now couchpotato.service
   ```

### Upgrading from Older Versions

Existing `settings.conf` configuration files and CodernityDB databases (`database/` directory) from older Python 2 installations are supported. Documents stored under Python 2 are automatically normalized on read. It is recommended to create a backup copy of your data directory before upgrading.


## Development & Testing

Install development dependencies and run the automated test suite:

```sh
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/pytest
```

If you're going to add styling or doing some javascript work you'll need a few tools that build and compress scss -> css and combine the javascript files. [Node/NPM](https://nodejs.org/), [Grunt](http://gruntjs.com/installing-grunt), [Compass](http://compass-style.org/install/)

After you've got these tools you can install the packages using `npm install`. Once this process has finished you can start CP using the command `grunt`. This will start all the needed tools and watches any files for changes.
You can now change css and javascript and it wil reload the page when needed.

By default it will combine files used in the core folder. If you're adding a new .scss or .js file, you might need to add it and then restart the grunt process for it to combine it properly.

Don't forget to enable development inside the CP settings. This disables some functions and also makes sure javascript errors are pushed to console instead of the log.
