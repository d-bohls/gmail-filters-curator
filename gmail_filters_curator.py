"""Sort and validate an xml file containing exported gmail filters."""

import json
import logging
import os
import xml.dom.minidom
from typing import Dict, List
from xml.dom.minidom import Element
from xml.etree import ElementTree

xml_default_namespace = 'http://www.w3.org/2005/Atom'
xml_apps_namespace = 'http://schemas.google.com/apps/2006'

xml_namespaces_dict = {
    '': xml_default_namespace,
    'apps': xml_apps_namespace,
}


def get_xml_tag_with_namespace(namespace: str, tag: str) -> str:
    return f'{{{namespace}}}{tag}'


def get_filter_entry_label(entry: ElementTree.Element) -> str:
    label = ''
    for child in entry:
        if child.tag == get_xml_tag_with_namespace(xml_apps_namespace, 'property'):
            if child.attrib['name'] == 'label':
                label = child.attrib['value']
                break
    assert len(label) > 0
    return label


def sort_filter_entries_by_label(xml_root: Element) -> None:
    filter_entries = xml_root.findall(get_xml_tag_with_namespace(xml_default_namespace, 'entry'))
    filter_entries.sort(key=lambda e: get_filter_entry_label(e))
    for entry in filter_entries:
        xml_root.remove(entry)
        xml_root.append(entry)


def check_filter_entity_properties(xml_root: Element, rules_json_path: str) -> None:
    with open(rules_json_path) as rules_file:
        json_filter_file = json.loads(rules_file.read())

    filter_rules = json_filter_file['rules']
    labels_to_ignore = json_filter_file['ignored labels']
    xml_filter_entries = xml_root.findall(get_xml_tag_with_namespace(xml_default_namespace, 'entry'))
    
    for xml_entry in xml_filter_entries:
        encountered_elements = set()
        encountered_properties = set()
        label = get_filter_entry_label(xml_entry)
        if label in labels_to_ignore:
            logging.info(f'Ignoring: {label}')
            continue
        logging.debug(f'Checking: {label}')
        for element in xml_entry:
            encountered_elements.add(element.tag)
            assert element.tag in filter_rules
            json_rule_element = filter_rules[element.tag]
            if isinstance(json_rule_element, dict):
                attribute_name = element.attrib['name']
                encountered_properties.add(attribute_name)
                assertion = json_rule_element[attribute_name]
            else:
                assertion = json_rule_element

            eval_result = eval(assertion)
            assert eval_result, f'Issue with filter for label {label}. Assertion failed: {assertion}'

        expected_elements = set(filter_rules.keys())
        expected_properties = set(filter_rules[get_xml_tag_with_namespace(xml_apps_namespace, 'property')].keys())
        unexpected_elements = encountered_elements - expected_elements
        unexpected_properties = encountered_properties - expected_properties
        missing_elements = expected_elements - encountered_elements
        missing_properties = expected_properties - encountered_properties
        assert not unexpected_elements
        assert not unexpected_properties
        assert not missing_elements
        assert not missing_properties


def get_xml_root(xml_file: str, xml_namespaces: Dict[str, str]) -> Element:
    for prefix, uri in xml_namespaces.items():
        ElementTree.register_namespace(prefix, uri)

    xml_tree = ElementTree.parse(xml_file)
    return xml_tree.getroot()


def write_xml_root(xml_root: Element, output_path: str) -> None:
    xml_string = ElementTree.tostring(xml_root)
    xml_dom = xml.dom.minidom.parseString(xml_string)
    xml_pretty_str = xml_dom.toprettyxml(encoding='UTF-8').decode('UTF-8')
    xml_pretty_str = os.linesep.join([s for s in xml_pretty_str.splitlines() if s.strip()])
    with open(output_path, 'wb') as text_file:
        text_file.write(xml_pretty_str.encode('UTF-8'))


def parse_args(args: List[str]) -> Dict[str, str]:
    import argparse
    parser_description = 'A script to check and sort an xml file containing exported Gmail filters.'
    dir_of_executing_file = os.path.dirname(os.path.abspath(__file__))
    default_input_filepath = os.path.join(dir_of_executing_file, 'gmail_filters_export.xml')
    default_output_filepath = os.path.join(dir_of_executing_file, 'gmail_filters_output.xml')
    default_rules_filepath = os.path.join(dir_of_executing_file, 'rules.json')
    parser = argparse.ArgumentParser(description=parser_description)
    parser.add_argument('-inFile', default=default_input_filepath, help='Filepath to an input xml file.')
    parser.add_argument('-outFile', default=default_output_filepath, help='Filepath to the output xml file.')
    parser.add_argument('-rulesFile', default=default_rules_filepath, help='Filepath to json file that describes '
                                                                           'validation.')
    parser.add_argument(
        '-d', '--debug',
        help="Show debug logging.",
        action="store_const", dest="log_level", const=logging.DEBUG,
        default=logging.WARNING,
    )
    parser.add_argument(
        '-v', '--verbose',
        help="Show verbose logging.",
        action="store_const", dest="log_level", const=logging.INFO,
    )

    return vars(parser.parse_args(args))


def main(args: List[str]) -> None:
    args_dict = parse_args(args)
    
    logging.basicConfig(level=args_dict['log_level'])
    logging.debug('Debug logging enabled.')
    logging.info('Verbose logging enabled.')

    input_filter_xml_path = args_dict['inFile']
    output_filter_xml_path = args_dict['outFile']
    rules_json_path = args_dict['rulesFile']

    xml_root = get_xml_root(input_filter_xml_path, xml_namespaces_dict)
    check_filter_entity_properties(xml_root, rules_json_path)
    sort_filter_entries_by_label(xml_root)
    write_xml_root(xml_root, output_filter_xml_path)


if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
