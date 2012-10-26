"""
Tests of input types (and actually responsetypes too).

TODO:
- test unicode in values, parameters, etc.
- test various html escapes
- test funny xml chars -- should never get xml parse error if things are escaped properly.
"""

from datetime import datetime
import json
from mock import Mock
from nose.plugins.skip import SkipTest
import os
import unittest
import xml.sax.saxutils as saxutils

from . import test_system
from capa import inputtypes

from lxml import etree

def tst_render_template(template, context):
    """
    A test version of render to template.  Renders to the repr of the context, completely ignoring the template name.
    """
    return repr(context)


system = Mock(render_template=tst_render_template)

def quote_attr(s):
    return saxutils.quoteattr(s)[1:-1]  # don't want the outer quotes

class OptionInputTest(unittest.TestCase):
    '''
    Make sure option inputs work
    '''

    def test_rendering(self):
        xml_str = """<optioninput options="('Up','Down')" id="sky_input" correct="Up"/>"""
        element = etree.fromstring(xml_str)

        state = {'value': 'Down',
                 'id': 'sky_input',
                 'status': 'answered'}
        option_input = inputtypes.get_class_for_tag('optioninput')(system, element, state)

        context = option_input._get_render_context()

        expected = {'value': 'Down',
                    'options': [('Up', 'Up'), ('Down', 'Down')],
                    'state': 'answered',
                    'msg': '',
                    'inline': '',
                    'id': 'sky_input'}

        self.assertEqual(context, expected)

class ChoiceGroupTest(unittest.TestCase):
    '''
    Test choice groups.
    '''
    def test_mult_choice(self):
        xml_template = """
  <choicegroup {0}>
    <choice correct="false" name="foil1"><text>This is foil One.</text></choice>
    <choice correct="false" name="foil2"><text>This is foil Two.</text></choice>
    <choice correct="true" name="foil3">This is foil Three.</choice>
  </choicegroup>
        """

        def check_type(type_str, expected_input_type):
            print "checking for type_str='{0}'".format(type_str)
            xml_str = xml_template.format(type_str)

            element = etree.fromstring(xml_str)

            state = {'value': 'foil3',
                     'id': 'sky_input',
                     'status': 'answered'}

            option_input = inputtypes.get_class_for_tag('choicegroup')(system, element, state)

            context = option_input._get_render_context()

            expected = {'id': 'sky_input',
                        'value': 'foil3',
                        'state': 'answered',
                        'input_type': expected_input_type,
                        'choices': [('foil1', '<text>This is foil One.</text>'),
                                    ('foil2', '<text>This is foil Two.</text>'),
                                    ('foil3', 'This is foil Three.'),],
                        'name_array_suffix': '',   # what is this for??
                        }

            self.assertEqual(context, expected)

        check_type('', 'radio')
        check_type('type=""', 'radio')
        check_type('type="MultipleChoice"', 'radio')
        check_type('type="TrueFalse"', 'checkbox')
        # fallback.
        check_type('type="StrangeUnknown"', 'radio')


    def check_group(self, tag, expected_input_type, expected_suffix):
        xml_str = """
  <{tag}>
    <choice correct="false" name="foil1"><text>This is foil One.</text></choice>
    <choice correct="false" name="foil2"><text>This is foil Two.</text></choice>
    <choice correct="true" name="foil3">This is foil Three.</choice>
  </{tag}>
        """.format(tag=tag)

        element = etree.fromstring(xml_str)

        state = {'value': 'foil3',
                 'id': 'sky_input',
                 'status': 'answered'}

        the_input = inputtypes.get_class_for_tag(tag)(system, element, state)

        context = the_input._get_render_context()

        expected = {'id': 'sky_input',
                    'value': 'foil3',
                    'state': 'answered',
                    'input_type': expected_input_type,
                    'choices': [('foil1', '<text>This is foil One.</text>'),
                                ('foil2', '<text>This is foil Two.</text>'),
                                ('foil3', 'This is foil Three.'),],
                    'name_array_suffix': expected_suffix,   # what is this for??
                    }

        self.assertEqual(context, expected)

    def test_radiogroup(self):
        self.check_group('radiogroup', 'radio', '[]')

    def test_checkboxgroup(self):
        self.check_group('checkboxgroup', 'checkbox', '[]')



class JavascriptInputTest(unittest.TestCase):
    '''
    The javascript input is a pretty straightforward pass-thru, but test it anyway
    '''

    def test_rendering(self):
        params = "(1,2,3)"

        problem_state = "abc12',12&hi<there>"
        display_class = "a_class"
        display_file = "my_files/hi.js"

        xml_str = """<javascriptinput id="prob_1_2" params="{params}" problem_state="{ps}"
                                      display_class="{dc}" display_file="{df}"/>""".format(
                                          params=params,
                                          ps=quote_attr(problem_state),
                                          dc=display_class, df=display_file)

        element = etree.fromstring(xml_str)

        state = {'value': '3',}
        the_input = inputtypes.get_class_for_tag('javascriptinput')(system, element, state)

        context = the_input._get_render_context()

        expected = {'id': 'prob_1_2',
                    'params': params,
                    'display_file': display_file,
                    'display_class': display_class,
                    'problem_state': problem_state,
                    'value': '3',
                    'evaluation': '',}

        self.assertEqual(context, expected)


class TextLineTest(unittest.TestCase):
    '''
    Check that textline inputs work, with and without math.
    '''

    def test_rendering(self):
        size = "42"
        xml_str = """<textline id="prob_1_2" size="{size}"/>""".format(size=size)

        element = etree.fromstring(xml_str)

        state = {'value': 'BumbleBee',}
        the_input = inputtypes.get_class_for_tag('textline')(system, element, state)

        context = the_input._get_render_context()

        expected = {'id': 'prob_1_2',
                    'value': 'BumbleBee',
                    'state': 'unanswered',
                    'size': size,
                    'msg': '',
                    'hidden': False,
                    'inline': False,
                    'do_math': False,
                    'preprocessor': None}
        self.assertEqual(context, expected)


    def test_math_rendering(self):
        size = "42"
        preprocessorClass = "preParty"
        script = "foo/party.js"

        xml_str = """<textline math="True" id="prob_1_2" size="{size}"
        preprocessorClassName="{pp}"
        preprocessorSrc="{sc}"/>""".format(size=size, pp=preprocessorClass, sc=script)

        element = etree.fromstring(xml_str)

        state = {'value': 'BumbleBee',}
        the_input = inputtypes.get_class_for_tag('textline')(system, element, state)

        context = the_input._get_render_context()

        expected = {'id': 'prob_1_2',
                    'value': 'BumbleBee',
                    'state': 'unanswered',
                    'size': size,
                    'msg': '',
                    'hidden': False,
                    'inline': False,
                    'do_math': True,
                    'preprocessor': {'class_name': preprocessorClass,
                                     'script_src': script}}
        self.assertEqual(context, expected)


class FileSubmissionTest(unittest.TestCase):
    '''
    Check that file submission inputs work
    '''

    def test_rendering(self):
        allowed_files = "runme.py nooooo.rb ohai.java"
        required_files = "cookies.py"

        xml_str = """<filesubmission id="prob_1_2"
        allowed_files="{af}"
        required_files="{rf}"
        />""".format(af=allowed_files,
                     rf=required_files,)


        element = etree.fromstring(xml_str)

        escapedict = {'"': '&quot;'}
        esc = lambda s: saxutils.escape(s, escapedict)

        state = {'value': 'BumbleBee.py',
                 'status': 'incomplete',
                 'feedback' : {'message': '3'}, }
        the_input = inputtypes.get_class_for_tag('filesubmission')(system, element, state)

        context = the_input._get_render_context()

        expected = {'id': 'prob_1_2',
                   'state': 'queued',
                   'msg': 'Submitted to grader.',
                   'value': 'BumbleBee.py',
                   'queue_len': '3',
                   'allowed_files': esc('["runme.py", "nooooo.rb", "ohai.java"]'),
                   'required_files': esc('["cookies.py"]')}

        self.assertEqual(context, expected)


class CodeInputTest(unittest.TestCase):
    '''
    Check that codeinput inputs work
    '''

    def test_rendering(self):
        mode = "parrot"
        linenumbers = 'false'
        rows = '37'
        cols = '11'
        tabsize = '7'

        xml_str = """<codeinput id="prob_1_2"
        mode="{m}"
        cols="{c}"
        rows="{r}"
        linenumbers="{ln}"
        tabsize="{ts}"
        />""".format(m=mode, c=cols, r=rows, ln=linenumbers, ts=tabsize)

        element = etree.fromstring(xml_str)

        escapedict = {'"': '&quot;'}
        esc = lambda s: saxutils.escape(s, escapedict)

        state = {'value': 'print "good evening"',
                 'status': 'incomplete',
                 'feedback' : {'message': '3'}, }

        the_input = inputtypes.get_class_for_tag('codeinput')(system, element, state)

        context = the_input._get_render_context()

        expected = {'id': 'prob_1_2',
                    'value': 'print "good evening"',
                   'state': 'queued',
                   'msg': 'Submitted to grader.',
                   'mode': mode,
                   'linenumbers': linenumbers,
                   'rows': rows,
                   'cols': cols,
                   'hidden': '',
                   'tabsize': int(tabsize),
                   'queue_len': '3',
                   }

        self.assertEqual(context, expected)


class SchematicTest(unittest.TestCase):
    '''
    Check that schematic inputs work
    '''

    def test_rendering(self):
        height = '12'
        width = '33'
        parts = 'resistors, capacitors, and flowers'
        analyses = 'fast, slow, and pink'
        initial_value = 'two large batteries'
        submit_analyses = 'maybe'


        xml_str = """<schematic id="prob_1_2"
        height="{h}"
        width="{w}"
        parts="{p}"
        analyses="{a}"
        initial_value="{iv}"
        submit_analyses="{sa}"
        />""".format(h=height, w=width, p=parts, a=analyses,
                     iv=initial_value, sa=submit_analyses)

        element = etree.fromstring(xml_str)

        value = 'three resistors and an oscilating pendulum'
        state = {'value': value,
                 'status': 'unsubmitted'}

        the_input = inputtypes.get_class_for_tag('schematic')(system, element, state)

        context = the_input._get_render_context()

        expected = {'id': 'prob_1_2',
                    'value': value,
                    'initial_value': initial_value,
                    'state': 'unsubmitted',
                    'width': width,
                    'height': height,
                    'parts': parts,
                    'analyses': analyses,
                    'submit_analyses': submit_analyses,
                   }

        self.assertEqual(context, expected)


class ImageInputTest(unittest.TestCase):
    '''
    Check that image inputs work
    '''

    def check(self, value, egx, egy):
        height = '78'
        width = '427'
        src = 'http://www.edx.org/cowclicker.jpg'

        xml_str = """<imageinput id="prob_1_2"
        src="{s}"
        height="{h}"
        width="{w}"
        />""".format(s=src, h=height, w=width)

        element = etree.fromstring(xml_str)

        state = {'value': value,
                 'status': 'unsubmitted'}

        the_input = inputtypes.get_class_for_tag('imageinput')(system, element, state)

        context = the_input._get_render_context()

        expected = {'id': 'prob_1_2',
                    'value': value,
                    'state': 'unsubmitted',
                    'width': width,
                    'height': height,
                    'src': src,
                    'gx': egx,
                    'gy': egy,
                    'state': 'unsubmitted',
                    'msg': ''}

        self.assertEqual(context, expected)

    def test_with_value(self):
        self.check('[50,40]', 35, 25)

    def test_without_value(self):
        self.check('', 0, 0)

    def test_corrupt_values(self):
        self.check('[12', 0, 0)
        self.check('[12, a]', 0, 0)
        self.check('[12 10]', 0, 0)
        self.check('[12]', 0, 0)
        self.check('[12 13 14]', 0, 0)



class CrystallographyTest(unittest.TestCase):
    '''
    Check that crystallography inputs work
    '''

    def test_rendering(self):
        height = '12'
        width = '33'
        size = '10'

        xml_str = """<crystallography id="prob_1_2"
        height="{h}"
        width="{w}"
        size="{s}"
        />""".format(h=height, w=width, s=size)

        element = etree.fromstring(xml_str)

        value = 'abc'
        state = {'value': value,
                 'status': 'unsubmitted'}

        the_input = inputtypes.get_class_for_tag('crystallography')(system, element, state)

        context = the_input._get_render_context()

        expected = {'id': 'prob_1_2',
                    'value': value,
                    'state': 'unsubmitted',
                    'size': size,
                    'msg': '',
                    'hidden': '',
                    'width': width,
                    'height': height,
                   }

        self.assertEqual(context, expected)


class ChemicalEquationTest(unittest.TestCase):
    '''
    Check that chemical equation inputs work.
    '''

    def test_rendering(self):
        size = "42"
        xml_str = """<chemicalequationinput id="prob_1_2" size="{size}"/>""".format(size=size)

        element = etree.fromstring(xml_str)

        state = {'value': 'H2OYeah',}
        the_input = inputtypes.get_class_for_tag('chemicalequationinput')(system, element, state)

        context = the_input._get_render_context()

        expected = {'id': 'prob_1_2',
                    'value': 'H2OYeah',
                    'status': 'unanswered',
                    'size': size,
                    'previewer': '/static/js/capa/chemical_equation_preview.js',
                    }
        self.assertEqual(context, expected)

