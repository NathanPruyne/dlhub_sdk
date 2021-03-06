"""Tests for models for generic Python functions"""

from dlhub_sdk.models.servables.python import PythonClassMethodModel, \
    PythonStaticMethodModel
from dlhub_sdk.utils.schemas import validate_against_dlhub_schema
from dlhub_sdk.utils.types import compose_argument_block
from dlhub_sdk.version import __version__
from sklearn import __version__ as skl_version
from numpy import __version__ as numpy_version
from datetime import datetime
import unittest
import math
import os

_year = str(datetime.now().year)


class TestPythonModels(unittest.TestCase):
    maxDiff = 4096

    def test_pickle(self):
        pickle_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'model.pkl'))

        # Make the model
        model = PythonClassMethodModel.create_model(pickle_path, 'predict_proba', {'fake': 'kwarg'})
        model.set_title('Python example').set_name("class_method")

        # Make sure it throws value errors if inputs are not set
        with self.assertRaises(ValueError):
            model.to_dict()

        # Define the input and output types
        model.set_inputs('ndarray', 'Features for each entry', shape=[None, 4])
        model.set_outputs('ndarray', 'Predicted probabilities of being each iris species',
                          shape=[None, 3])

        # Make sure attempting to set "unpack" fails
        with self.assertRaises(ValueError):
            model.set_unpack_inputs(True)

        # Add some requirements
        model.add_requirement('scikit-learn', 'detect')
        model.add_requirement('numpy', 'detect')
        model.add_requirement('sklearn', 'latest')  # Dummy project, version # shouldn't change

        # Check the model output
        output = model.to_dict()
        assert output['dlhub']['files'] == {'pickle': pickle_path}
        assert output['dlhub']['dependencies']['python'] == {
            'scikit-learn': skl_version,
            'numpy': numpy_version,
            'sklearn': '0.0'
        }
        assert output['servable']['shim'] == 'python.PythonClassMethodServable'
        assert 'run' in output['servable']['methods']
        assert output['servable']['methods']['run']['input'] == {
            'type': 'ndarray',
            'description': 'Features for each entry',
            'shape': [None, 4]
        }
        assert output['servable']['methods']['run']['output'] == {
            'type': 'ndarray',
            'description': 'Predicted probabilities of being each iris species',
            'shape': [None, 3]
        }
        assert (output['servable']['methods']['run']
                ['method_details']['class_name'].endswith('.SVC'))
        assert (output['servable']['methods']['run']
                ['method_details']['method_name'] == 'predict_proba')

        self.assertEqual([pickle_path], model.list_files())
        validate_against_dlhub_schema(output, 'servable')

    def test_function(self):
        f = math.sqrt

        # Make the model
        model = PythonStaticMethodModel.from_function_pointer(f, autobatch=True)
        model.set_name("static_method").set_title('Python example')

        # Describe the inputs/outputs
        model.set_inputs('list', 'List of numbers', item_type='float')
        model.set_outputs('float', 'Square root of the number')

        # Generate the output
        output = model.to_dict()
        correct_output = {
            'datacite': {
                'creators': [],
                'titles': [{
                    'title': 'Python example'
                }],
                'publisher': 'DLHub',
                'resourceType': {
                    'resourceTypeGeneral': 'InteractiveResource'
                },
                'identifier': {
                    'identifier': '10.YET/UNASSIGNED',
                    'identifierType': 'DOI'
                },
                'publicationYear': _year,
                "descriptions": [],
                "fundingReferences": [],
                "relatedIdentifiers": [],
                "alternateIdentifiers": [],
                "rightsList": []
            },
            'dlhub': {
                'version': __version__,
                'domains': [],
                'visible_to': ['public'],
                "name": "static_method",
                'type': 'servable',
                'files': {}
            },
            'servable': {
                'type': 'Python static method',
                'shim': 'python.PythonStaticMethodServable',
                'methods': {
                    'run': {
                        'input': {
                            'type': 'list',
                            'description': 'List of numbers',
                            'item_type': {
                                'type': 'float'
                            }
                        },
                        'output': {
                            'type': 'float',
                            'description': 'Square root of the number'
                        },
                        'parameters': {},
                        'method_details': {
                            'module': 'math',
                            'method_name': 'sqrt',
                            'autobatch': True
                        }
                    }
                }
            }
        }
        self.assertEqual(output, correct_output)
        validate_against_dlhub_schema(output, 'servable')

    def test_multiarg(self):
        """Test making descriptions with more than one argument"""

        # Initialize the model
        model = PythonStaticMethodModel.from_function_pointer(max)
        model.set_name('test').set_title('test')

        # Define the inputs and outputs
        model.set_inputs('tuple', 'Two numbers',
                         element_types=[
                             compose_argument_block('float', 'A number'),
                             compose_argument_block('float', 'A second number')
                         ])
        model.set_outputs('float', 'Maximum of the two numbers')

        # Mark that the inputs should be unpacked
        model.set_unpack_inputs(True)

        # Check the description
        self.assertEqual(model['servable']['methods']['run'], {
            'input': {
                'type': 'tuple',
                'description': 'Two numbers',
                'element_types': [
                    {'type': 'float', 'description': 'A number'},
                    {'type': 'float', 'description': 'A second number'}
                ]
            },
            'output': {
                'type': 'float',
                'description': 'Maximum of the two numbers'
            },
            'method_details': {
                'module': 'builtins',
                'method_name': 'max',
                'unpack': True,
                'autobatch': False
            },
            'parameters': {}
        })

        validate_against_dlhub_schema(model.to_dict(), 'servable')
