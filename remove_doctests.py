import sys

in_doc = False
for line in sys.stdin.read().split('\n'):
    doc_border = '"""' in line
    if line.count('"""') % 2 == 1:
        in_doc = not in_doc
    if '>>> ' in line:
        in_tests = True
    if not in_doc:
        in_tests = False
    doctest_line = line.strip() in ['import doctest', 'doctest.testmod()']
    #if not (in_doc and in_tests):
    if not (doc_border or in_doc or doctest_line):
        print line


