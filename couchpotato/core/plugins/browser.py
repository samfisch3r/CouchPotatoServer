import os
import traceback

from couchpotato import CPLog
from couchpotato.api import addApiView
from couchpotato.core.helpers.encoding import sp, toUnicode
from couchpotato.core.helpers.variable import getUserDir
from couchpotato.core.plugins.base import Plugin

from couchpotato.environment import Env

log = CPLog(__name__)

autoload = 'FileBrowser'

class FileBrowser(Plugin):

    def __init__(self):
        addApiView('directory.list', self.view, docs = {
            'desc': 'Return the directory list of a given directory',
            'params': {
                'path': {'desc': 'The directory to scan'},
                'show_hidden': {'desc': 'Also show hidden files'}
            },
            'return': {'type': 'object', 'example': """{
    'is_root': bool, //is top most folder
    'parent': string, //parent folder of requested path
    'home': string, //user home folder
    'empty': bool, //directory is empty
    'dirs': array, //directory names
}"""}
        })

    def getDirectories(self, path = '/', show_hidden = True):

        # Return the filesystem root if the path is empty.
        if path == '/' or not path:
            path = '/'

        dirs = []
        path = sp(path)
        for f in os.listdir(path):
            p = sp(os.path.join(path, f))
            if os.path.isdir(p) and ((self.is_hidden(p) and bool(int(show_hidden))) or not self.is_hidden(p)):
                dirs.append(toUnicode('%s%s' % (p, os.path.sep)))

        return sorted(dirs)

    def getFiles(self):
        pass

    def view(self, path = '/', show_hidden = True, **kwargs):

        soft_chroot = Env.get('softchroot')
        
        home = getUserDir()
        if soft_chroot.enabled:
            if not soft_chroot.is_subdir(home):
                home = soft_chroot.get_chroot()

        if not path:
            path = home
            if path.endswith(os.path.sep):
                path = path.rstrip(os.path.sep)
        else:
            path = soft_chroot.chroot2abs(path)

        try:
            dirs = self.getDirectories(path = path, show_hidden = show_hidden)
        except:
            log.error('Failed getting directory "%s" : %s', (path, traceback.format_exc()))
            dirs = []

        if soft_chroot.enabled:
            dirs = list(map(soft_chroot.abs2chroot, dirs))

        sep = getattr(soft_chroot, 'sep', os.path.sep) if soft_chroot.enabled else os.path.sep
        parent = os.path.dirname(path.rstrip('/\\'))
        if parent == path.rstrip('/\\'):
            parent = '/'
        elif parent != '/':
            parent += sep

        is_root = path == '/'

        if soft_chroot.enabled:
            is_root = soft_chroot.is_root_abs(path)

            # fix paths:
            if soft_chroot.is_subdir(parent):
                parent = soft_chroot.abs2chroot(parent)
            else:
                parent = sep

            home = soft_chroot.abs2chroot(home)

        return {
            'is_root': is_root,
            'empty': len(dirs) == 0,
            'parent': parent,
            'home': home,
            'dirs': dirs,
        }


    def is_hidden(self, filepath):
        name = toUnicode(os.path.basename(os.path.abspath(filepath)))
        return name.startswith('.')
