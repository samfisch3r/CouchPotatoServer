import subprocess
import tempfile
import unittest
from pathlib import Path
import sys

repository_root = Path(__file__).resolve().parents[2]
libs_dir = str(repository_root / 'libs')
if libs_dir not in sys.path:
    sys.path.append(libs_dir)

from git.repository import LocalRepository


class GitRepositoryPython3Test(unittest.TestCase):

    def test_git_command_output_is_text(self):
        with tempfile.TemporaryDirectory() as path:
            subprocess.run(['git', 'init', '-q'], cwd=path, check=True)
            subprocess.run(
                ['git', 'config', 'user.email', 'test@example.invalid'],
                cwd=path,
                check=True,
            )
            subprocess.run(
                ['git', 'config', 'user.name', 'Test'],
                cwd=path,
                check=True,
            )
            Path(path, 'README.txt').write_text(
                'migration smoke test\n', encoding='utf-8')
            subprocess.run(['git', 'add', 'README.txt'], cwd=path, check=True)
            subprocess.run(
                ['git', 'commit', '-m', 'test commit'],
                cwd=path,
                check=True,
                capture_output=True,
            )

            repository = LocalRepository(path)

            self.assertEqual(repository.getHead().getSubject(), 'test commit')
            self.assertEqual(len(repository.getHead().hash), 40)
            self.assertTrue(repository.isWorkingDirectoryClean())


if __name__ == '__main__':
    unittest.main()
