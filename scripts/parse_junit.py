import xml.etree.ElementTree as ET
import sys

report_file = sys.argv[1]

try:
    tree = ET.parse(report_file)
    root = tree.getroot()
    failures = int(root.attrib.get('failures', 0))
    errors = int(root.attrib.get('errors', 0))
    skipped = int(root.attrib.get('skipped', 0))
    total = int(root.attrib.get('tests', 0))

    if failures > 0 or errors > 0:
        print('BADGE_COLOR="red"')
        print('BADGE_TEXT="failing"')
    elif total == 0:
        print('BADGE_COLOR="lightgrey"')
        print('BADGE_TEXT="no tests"')
    else:
        print('BADGE_COLOR="brightgreen"')
        print('BADGE_TEXT="passing"')
except FileNotFoundError:
    print('BADGE_COLOR="lightgrey"')
    print('BADGE_TEXT="no report"')
except Exception as e:
    print(f'Error parsing XML: {e}')
    print('BADGE_COLOR="lightgrey"')
    print('BADGE_TEXT="error"')
