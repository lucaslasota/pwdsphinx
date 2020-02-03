import unittest
from os import listdir
from shutil import rmtree
from unittest.mock import Mock
from io import BytesIO
import sys

from pwdsphinx import sphinx

# to get coverage, run
# PYTHONPATH=.. coverage run ../tests/test.py
# coverage report -m

# disable the output of sphinx
sphinx.print = Mock()

data_dir = 'data/'
orig_data_files = set(listdir(data_dir))
char_classes = 'ulsd'
size = 80
pwd = 'asdf'
user = 'user1'
host = 'example.com'

class Input:
    def __init__(self):
       self.buffer = BytesIO(pwd.encode())

def cleanup():
    for f in listdir(data_dir):
        if f not in orig_data_files:
            rmtree(data_dir+f)


class TestEndToEnd(unittest.TestCase):

    def tearDown(self):
        cleanup()

    def test_create_user(self):
        with sphinx.connect() as s:
            self.assertIsInstance(sphinx.create(s, pwd, user, host, char_classes, size), str)

    def test_invalid_rules(self):
        with sphinx.connect() as s:
            self.assertRaises(ValueError, sphinx.create, s, pwd, user, host, "asdf", size)

    def test_recreate_user(self):
        with sphinx.connect() as s:
            self.assertIsInstance(sphinx.create(s, pwd, user, host, char_classes, size), str)

        with sphinx.connect() as s:
            self.assertIsNone(sphinx.create(s, pwd, user, host, char_classes, size))

    def test_get(self):
        with sphinx.connect() as s:
            self.assertIsInstance(sphinx.create(s, pwd, user, host, char_classes, size), str)

        with sphinx.connect() as s:
            self.assertIsInstance(sphinx.get(s, pwd, user, host), str)

    def test_get_nonexistant_host(self):
        with sphinx.connect() as s:
            self.assertIsNone(sphinx.get(s, pwd, user, host))

    def test_delete(self):
        with sphinx.connect() as s:
            self.assertIsInstance(sphinx.create(s, pwd, user, host, char_classes, size), str)

        with sphinx.connect() as s:
            self.assertTrue(sphinx.delete(s, pwd, user, host))

    def test_change(self):
        with sphinx.connect() as s:
            self.assertIsInstance(sphinx.create(s, pwd, user, host, char_classes, size), str)

        with sphinx.connect() as s:
            pwd0 = sphinx.get(s, pwd, user, host)
        self.assertIsInstance(pwd0, str)

        with sphinx.connect() as s:
            pwd1 = sphinx.change(s, pwd, user, host)
        self.assertIsInstance(pwd1, str)
        self.assertNotEqual(pwd0, pwd1)

    def test_commit_undo(self):
        # create
        with sphinx.connect() as s:
            pwd0 = sphinx.create(s, pwd, user, host, char_classes, size)
            self.assertIsInstance(pwd0, str)

        # get
        with sphinx.connect() as s:
            pwd1 = sphinx.get(s, pwd, user, host)
        self.assertIsInstance(pwd1, str)

        # change
        with sphinx.connect() as s:
            pwd2 = sphinx.change(s, pwd, user, host)
        self.assertIsInstance(pwd2, str)
        self.assertNotEqual(pwd1, pwd2)

        # get
        with sphinx.connect() as s:
            pwd3 = sphinx.get(s, pwd, user, host)
        self.assertIsInstance(pwd3, str)
        self.assertEqual(pwd1, pwd3)

        # commit
        with sphinx.connect() as s:
            pwd4 = sphinx.commit_undo(s, pwd, sphinx.COMMIT, user, host, )
        self.assertIsInstance(pwd4, str)
        self.assertEqual(pwd2, pwd4)

        # undo
        with sphinx.connect() as s:
            pwd5 = sphinx.commit_undo(s, pwd, sphinx.UNDO, user, host, )
        self.assertIsInstance(pwd5, str)
        self.assertEqual(pwd1, pwd5)

    def test_list_users(self):
        with sphinx.connect() as s:
            self.assertIsInstance(sphinx.create(s, pwd, user, host, char_classes, size), str)
        with sphinx.connect() as s:
            self.assertIsInstance(sphinx.create(s, pwd, 'user2', host, char_classes, size), str)
        with sphinx.connect() as s:
            users = sphinx.users(s, pwd, host)
            self.assertIsInstance(users, str)
            self.assertEqual(users, 'user1\nuser2')

    def test_write(self):
        test_str = 'some test string'
        with sphinx.connect() as s:
            self.assertTrue(sphinx.write(s, '\n'.join((pwd, test_str)).encode(), user, host))

    def test_read(self):
        test_str = 'some test string'
        with sphinx.connect() as s:
            self.assertTrue(sphinx.write(s, '\n'.join((pwd, test_str)).encode(), user, host))

        with sphinx.connect() as s:
            blob = sphinx.read(s, pwd, user, host).decode()
        self.assertIsInstance(blob, str)
        self.assertEqual(blob, test_str)

    def test_overwrite(self):
        test_str0 = 'some test string'
        with sphinx.connect() as s:
            self.assertTrue(sphinx.write(s, '\n'.join((pwd, test_str0)).encode(), user, host))

        with sphinx.connect() as s:
            blob = sphinx.read(s, pwd, user, host).decode()
        self.assertIsInstance(blob, str)
        self.assertEqual(blob, test_str0)

        test_str1 = 'another test string'
        with sphinx.connect() as s:
            self.assertTrue(sphinx.write(s, '\n'.join((pwd, test_str1)).encode(), user, host))

        with sphinx.connect() as s:
            blob = sphinx.read(s, pwd, user, host).decode()
        self.assertIsInstance(blob, str)
        self.assertEqual(blob, test_str1)

    def test_double_commit(self):
        # create
        with sphinx.connect() as s:
            pwd0 = sphinx.create(s, pwd, user, host, char_classes, size)
            self.assertIsInstance(pwd0, str)

        # change
        with sphinx.connect() as s:
            pwd2 = sphinx.change(s, pwd, user, host)
        self.assertIsInstance(pwd2, str)
        self.assertNotEqual(pwd0, pwd2)

        # commit
        with sphinx.connect() as s:
            pwd4 = sphinx.commit_undo(s, pwd, sphinx.COMMIT, user, host, )
        self.assertIsInstance(pwd4, str)
        self.assertEqual(pwd2, pwd4)

        # commit
        with sphinx.connect() as s:
            pwd5 = sphinx.commit_undo(s, pwd, sphinx.COMMIT, user, host, )
        self.assertIsNone(pwd5)

    def test_main_create(self):
        sys.stdin = Input()
        self.assertIsNone(sphinx.main(('sphinx.py', 'create', user, host, char_classes, size)))

    def test_main_get(self):
        sys.stdin = Input()
        self.assertIsNone(sphinx.main(('sphinx.py', 'create', user, host, char_classes, size)))
        sys.stdin = Input()
        self.assertIsNone(sphinx.main(('sphinx.py', 'get', user, host)))

    def test_main_delete(self):
        sys.stdin = Input()
        self.assertIsNone(sphinx.main(('sphinx.py', 'create', user, host, char_classes, size)))
        sys.stdin = Input()
        self.assertIsNone(sphinx.main(('sphinx.py', 'delete', user, host)))

    def test_main_change_commit_undo(self):
        sys.stdin = Input()
        self.assertIsNone(sphinx.main(('sphinx.py', 'create', user, host, char_classes, size)))
        sys.stdin = Input()
        self.assertIsNone(sphinx.main(('sphinx.py', 'change', user, host)))
        sys.stdin = Input()
        self.assertIsNone(sphinx.main(('sphinx.py', 'commit', user, host)))
        sys.stdin = Input()
        self.assertIsNone(sphinx.main(('sphinx.py', 'undo', user, host)))

    def test_main_write_read(self):
        class Input:
             def __init__(self, txt = None):
                 if txt:
                     self.buffer = BytesIO('\n'.join((pwd, txt)).encode())
                 else:
                     self.buffer = BytesIO(pwd.encode())
        sys.stdin = Input("some note")
        self.assertIsNone(sphinx.main(('sphinx.py', 'write', user, host)))
        sys.stdin = Input()
        self.assertIsNone(sphinx.main(('sphinx.py', 'read', user, host)))
        sys.stdin = Input("some other note")
        self.assertIsNone(sphinx.main(('sphinx.py', 'write', host)))

    def test_main_inv_param_create(self):
        self.assertRaises(SystemExit, sphinx.main, ('sphinx.py', 'create'))
    def test_main_inv_param_get(self):
        self.assertRaises(SystemExit, sphinx.main, ('sphinx.py', 'get'))
    def test_main_inv_param_change(self):
        self.assertRaises(SystemExit, sphinx.main, ('sphinx.py', 'change'))
    def test_main_inv_param_commit(self):
        self.assertRaises(SystemExit, sphinx.main, ('sphinx.py', 'commit'))
    def test_main_inv_param_undo(self):
        self.assertRaises(SystemExit, sphinx.main, ('sphinx.py', 'undo'))
    def test_main_inv_param_delete(self):
        self.assertRaises(SystemExit, sphinx.main, ('sphinx.py', 'delete'))
    def test_main_inv_param_list(self):
        self.assertRaises(SystemExit, sphinx.main, ('sphinx.py', 'list'))
    def test_main_inv_param_write(self):
        self.assertRaises(SystemExit, sphinx.main, ('sphinx.py', 'write'))
    def test_main_inv_param_read(self):
        self.assertRaises(SystemExit, sphinx.main, ('sphinx.py', 'read'))

if __name__ == '__main__':
    unittest.main()
