"Remove some python 2.6 features so fullmoon can run on toast"

import re, sys, os

r = re.compile("^@(.+)\nclass (\w+).*(?:\n\s.*\S+.*)*", re.M )

script = file( sys.argv[1] ).read() 

while True:
    m = r.search( script )
    if not m:
        break
    script = script[ : m.start() ] + "#" + script[ m.start() : m.end() ] + "\n%s(%s)" % m.groups() + script[ m.end() : ]

os.rename( sys.argv[1], sys.argv[1]+".orig" )

f = open( sys.argv[1], "w" )
f.write( script )
f.close()
