# Sort and validate an xml file containing exported gmail filters - Version 0.1
# Coded by: Damon Bohls
# Date modified: 03/15/2021

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
    return '{' + namespace + '}' + tag


def check_filter_entity_properties(xml_root: Element) -> None:
    required_filter_entry_tags = {
        get_xml_tag_with_namespace(xml_default_namespace, 'category'),
        get_xml_tag_with_namespace(xml_default_namespace, 'title'),
        get_xml_tag_with_namespace(xml_default_namespace, 'id'),
        get_xml_tag_with_namespace(xml_default_namespace, 'updated'),
        get_xml_tag_with_namespace(xml_default_namespace, 'content'),
        get_xml_tag_with_namespace(xml_apps_namespace, 'property'),
    }

    required_filter_entry_properties = {
        'from',
        'label',
        'shouldNeverSpam',
    }

    filter_entries = xml_root.findall(get_xml_tag_with_namespace(xml_default_namespace, 'entry'))
    for entry in filter_entries:
        entry_tags = set()
        entry_properties = set()
        for child in entry:
            entry_tags.add(child.tag)
            if child.tag == get_xml_tag_with_namespace(xml_default_namespace, 'category'):
                assert child.attrib['term'] == 'filter'
            elif child.tag == get_xml_tag_with_namespace(xml_default_namespace, 'title'):
                assert child.text == 'Mail Filter'
            elif child.tag == get_xml_tag_with_namespace(xml_default_namespace, 'id'):
                assert child.text is not None and len(child.text) > 0
            elif child.tag == get_xml_tag_with_namespace(xml_default_namespace, 'updated'):
                assert child.text is not None and len(child.text) > 0
            elif child.tag == get_xml_tag_with_namespace(xml_default_namespace, 'content'):
                assert child.text is None
            elif child.tag == get_xml_tag_with_namespace(xml_apps_namespace, 'property'):
                entry_properties.add(child.attrib['name'])
                if child.attrib['name'] == 'from':
                    assert len(child.attrib['value']) > 0
                elif child.attrib['name'] == 'label':
                    assert len(child.attrib['value']) > 0
                elif child.attrib['name'] == 'shouldArchive':
                    print('has shouldArchive')
                    assert child.attrib['value'] == 'false'
                elif child.attrib['name'] == 'shouldNeverSpam':
                    assert child.attrib['value'] == 'true'
                elif child.attrib['name'] == 'shouldStar':
                    print('has shouldStar')
                    assert child.attrib['value'] == 'true'
                elif child.attrib['name'] == 'shouldAlwaysMarkAsImportant':
                    print('has shouldAlwaysMarkAsImportant')
                    assert child.attrib['value'] == 'true'
                elif child.attrib['name'] == 'sizeOperator':
                    assert child.attrib['value'] == 's_sl'
                elif child.attrib['name'] == 'sizeUnit':
                    assert child.attrib['value'] == 's_smb'
                else:
                    print('unknown property: ' + child.attrib['name'] + '=' + child.attrib['value'])
            else:
                print('unknown tag: ' + child.tag)

        assert entry_tags.issuperset(required_filter_entry_tags)
        assert entry_properties.issuperset(required_filter_entry_properties)


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
    with open(output_path, 'w') as text_file:
        text_file.write(xml_pretty_str)


def parse_args(args: List[str]) -> Dict[str, str]:
    import argparse
    parser_description = 'A script to check and sort an xml file containing exported Gmail filters.'
    dir_of_executing_file = os.path.dirname(os.path.abspath(__file__))
    default_input_filepath = os.path.join(dir_of_executing_file, 'gmail_filters_export.xml')
    default_output_filepath = os.path.join(dir_of_executing_file, 'gmail_filters_output.xml')
    parser = argparse.ArgumentParser(description=parser_description)
    parser.add_argument('-inFile', default=default_input_filepath, help='Filepath to an input xml file.')
    parser.add_argument('-outFile', default=default_output_filepath, help='Filepath to the output xml file.')
    return vars(parser.parse_args(args))


def main(args: List[str]) -> None:
    args_dict = parse_args(args)
    input_filter_xml_path = args_dict['inFile']
    output_filter_xml_path = args_dict['outFile']

    xml_root = get_xml_root(input_filter_xml_path, xml_namespaces_dict)
    check_filter_entity_properties(xml_root)
    sort_filter_entries_by_label(xml_root)
    write_xml_root(xml_root, output_filter_xml_path)


if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
