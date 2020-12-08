import zipfile
import re
from json import loads
import sys


def main(args=[]):
    file = args[1]
    assert zipfile.is_zipfile(file)
    mappings = loadMappings(args[2] or "mappings.tiny")
    refmap = loadRefmap(args[3] or "refmap.json")
    with zipfile.ZipFile(file, 'r') as inJar:
        with zipfile.ZipFile(f'{file[:-4]}-dev.jar', 'w') as outJar:
            for member in inJar.namelist():
                if member.endswith(".java"):
                    print(member)
                    with inJar.open(member) as inFile:
                        inp = inFile.read().decode("utf-8")
                        inp = refmapRemapper(inp, member.replace(".java", ""), refmap)
                        inp = remapStr(inp, mappings)
                        outJar.writestr(member, inp)
                else:
                    with inJar.open(member) as inFile:
                        outJar.writestr(member, inFile.read())

def loadRefmap(fname):
    with open(fname, "r") as f:
        return loads(f.read())

def refmapRemapper(file, fname, refmap):
    if fname in refmap["mappings"]:
        ref = refmap["mappings"][fname]
        for key in ref.keys():
            file = ('"'+ ref[key] + '"').join(file.split('"' + key + '"'))
    return file


def loadMappings(fname):
    mappings = {'method': {}, 'classPath': {}, 'class': {}, 'field': {}}
    with open(fname, "r") as f:
        for line in f.readlines()[1:]:
            line = line.split()
            if line[0] == 'c':
                mappings['classPath'][".".join(line[-2].replace("$", "/").split("/"))] = ".".join(line[-1].replace("$", "/").split("/"))
                mappings['classPath'][line[-2]] = line[-1]
                mappings['class'][line[-2].replace("$", "/").split("/")[-1]] = line[-1].replace("$", "/").split("/")[-1]
            if line[0] == 'm':
                mappings['method'][line[-2]] = line[-1]
            if line[0] == 'f':
                mappings['field'][line[-2]] = line[-1]
    return mappings


def remapStr(inputStr, mappings):
    classPathMatches = re.finditer(r'[^\s(<"L]+class_\d+', inputStr)
    shiftAmmt = 0
    for match in classPathMatches:
        if match.group(0) in mappings['classPath']:
            inputStr = inputStr[:match.start(0) + shiftAmmt] + mappings['classPath'][match.group(0)] + inputStr[match.end(0) + shiftAmmt:]
            shiftAmmt += len(mappings['classPath'][match.group(0)]) - (match.end(0) - match.start(0))
    classMatches = re.finditer(r'class_\d+', inputStr)
    shiftAmmt = 0
    for match in classMatches:
        if match.group(0) in mappings['class']:
            inputStr = inputStr[:match.start(0) + shiftAmmt] + mappings['class'][match.group(0)] + inputStr[match.end(0) + shiftAmmt:]
            shiftAmmt += len(mappings['class'][match.group(0)]) - (match.end(0) - match.start(0))
    methodMatches = re.finditer(r'method_\d+', inputStr)
    shiftAmmt = 0
    for match in methodMatches:
        if match.group(0) in mappings['method']:
            inputStr = inputStr[:match.start(0) + shiftAmmt] + mappings['method'][match.group(0)] + inputStr[match.end(0) + shiftAmmt:]
            shiftAmmt += len(mappings['method'][match.group(0)]) - (match.end(0) - match.start(0))
    fieldMatches = re.finditer(r'field_\d+', inputStr)
    shiftAmmt = 0
    for match in fieldMatches:
        if match.group(0) in mappings['field']:
            inputStr = inputStr[:match.start(0) + shiftAmmt] + mappings['field'][match.group(0)] + inputStr[match.end(0) + shiftAmmt:]
            shiftAmmt += len(mappings['field'][match.group(0)]) - (match.end(0) - match.start(0))
    return inputStr


if __name__ == "__main__":
    main(sys.argv)
