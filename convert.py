import sys

arg = sys.argv[1]
mlist = arg.split("|")
for place, x in enumerate(mlist):
	mlist[place] = x.strip(' \t\n\r')
print(mlist)