
import unittest
from aiocluster import setup


class SetupTests(unittest.TestCase):

    def test_find_worker_single_func_path(self):
        import os.path
        self.assertIs(setup.find_worker('os.open'), os.open)
        self.assertIs(setup.find_worker('os.path.basename'), os.path.basename)

    def test_find_worker_nested_func_path(self):
        x = setup.find_worker('aiocluster.worker.service.WorkerService.init')
        self.assertEqual(x.__name__, 'init')

    def test_find_worker_value_errors(self):
        self.assertRaises(ValueError, setup.find_worker, 'singlewordinvalid')
        self.assertRaises(ValueError, setup.find_worker, '')
        self.assertRaises(ValueError, setup.find_worker, '..')
        self.assertRaises(ValueError, setup.find_worker, '.s.')
        self.assertRaises(ValueError, setup.find_worker, '...')
        self.assertRaises(ValueError, setup.find_worker, '.a')
        self.assertRaises(ValueError, setup.find_worker, 'a.')
        self.assertRaises(ValueError, setup.find_worker, 'a.b.')
        self.assertRaises(ValueError, setup.find_worker, 'a.b..')
        self.assertRaises(ValueError, setup.find_worker, '.a.b')
        self.assertRaises(ValueError, setup.find_worker, '..a.b')
        self.assertRaises(ValueError, setup.find_worker, 'a..b')
        self.assertRaises(ValueError, setup.find_worker, 'a..b.')

    def test_find_worker_attr_errors(self):
        self.assertRaises(AttributeError, setup.find_worker, 'os.path.doesnotexist')
        self.assertRaises(AttributeError, setup.find_worker, 'os.doesnotexist.foo')

    def test_find_worker_import_errors(self):
        self.assertRaises(ImportError, setup.find_worker, 'doesnotexist.basename')
        self.assertRaises(ImportError, setup.find_worker, 'doesnotexist.a.b.c')

    def test_find_worker_type_errors(self):
        self.assertRaises(TypeError, setup.find_worker, 'os.path')
