from .main import Downloader


def autoload():
    return Downloader()


config = [{
    'name': 'download_providers',
    'groups': [
        {
            'label': 'Downloaders',
            'description': 'Select which Usenet downloader CouchPotato should use.',
            'type': 'list',
            'name': 'download_providers',
            'tab': 'downloaders',
            'options': [],
        },
    ],
}]
