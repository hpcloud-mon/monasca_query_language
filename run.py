import sys

from mql import mql_parser

if len(sys.argv) == 1 or sys.argv[1] == 'test':
    sys.exit(mql_parser.main())

parsed_query = mql_parser.MQLParser(sys.argv[1]).parse()

results = parsed_query[0].evaluate()

print(results)
