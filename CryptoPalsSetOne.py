from base64 import b64encode
from base64 import b64decode
from pprint import pprint
from gmpy2 import popcount
from itertools import combinations
from itertools import pairwise
from functools import cache
import timeit
import collections



def hexToBase64(hexInput):
    #Challenge One

    b64Input = b64encode(bytes.fromhex(hexInput)).decode()
    return b64Input

def fixedXOR(hexOne, hexTwo):
    byteOne = bytes.fromhex(hexOne)
    byteTwo = bytes.fromhex(hexTwo)
    XORArray = [None] *  len(byteOne)
    c = 0
    
    for i,o in zip(byteOne, byteTwo):
        XORArray[c] = (bytes([i ^ o]))
        c += 1

    return bytes.hex(bytes().join(XORArray))

def singleByteXORCipher(hexString):

    hexChars = [hex(i)[2:] for i in range(32,127)]
    inputLength = int(len(hexString)/2)

    stringDict = {}#Store text and value
    charDict = {}#Store key and value


    for i in hexChars:
        asciiHexString = (i*inputLength)
        XORedOutput = fixedXOR(hexString, asciiHexString)
        characterString = bytearray.fromhex(XORedOutput).decode('latin_1')#ascii representation
        stringValue = charValue(characterString)
        stringDict[characterString] = stringValue
        charDict[i] = stringValue
        
    
    return max(stringDict, key=stringDict.get), max(stringDict.values()), max(charDict, key=charDict.get)




def charValue(characterString):
    #could improve the character rankings here, include Upper case, puntuation etc
    '''Character frequency values from wiki'''
    charFreqTable = {
        'a': .08167, 'b': .01492, 'c': .02782, 'd': .04253,
        'e': .12702, 'f': .02228, 'g': .02015, 'h': .06094,
        'i': .06094, 'j': .00153, 'k': .00772, 'l': .04025,
        'm': .02406, 'n': .06749, 'o': .07507, 'p': .01929,
        'q': .00095, 'r': .05987, 's': .06327, 't': .09056,
        'u': .02758, 'v': .00978, 'w': .02360, 'x': .00150,
        'y': .01974, 'z': .00074, ' ': .16000
    }

    count = 0
    for character in characterString.lower():
        count = count + charFreqTable.get(character, 0)

    return count

def DetectSingleCharXOR(fileObj):
    detectedDict = {}

    with open(fileObj) as f:
        lines = f.readlines()
        for line in lines:
            text, score, char = (singleByteXORCipher(line))
            detectedDict[text] = score
    return max(detectedDict, key=detectedDict.get), max(detectedDict.values())

def RepeatingKeyXOR(textString, XORKey):
    hexString = textString.encode().hex()
    hexKey = XORKey.encode().hex()
    keyLength = len(hexKey)
    stringLength = len(hexString)
    stringMultiplier, characterRange = (divmod(stringLength,keyLength))

    #Make key length equal to string length
    hexKey = hexKey * stringMultiplier
    for i in range(0, characterRange, 2):
        hexKey = hexKey + hexKey[i] + hexKey[i+1]

    return fixedXOR(hexString, hexKey)

def breakRepeatingKeyXOR(fileObj):#input is a b64 string
    with open(fileObj) as f:
        b64String = f.read()
    hexString = b64decode(b64String).hex()
    byteString = bytes.fromhex(hexString)
    #CombKeyEditDistVerbose(byteString)
    #GuessKeyLengthWeightedAverage(byteString)
    print(GuessKeyLength(byteString, 4))
    #print(GuessKeyLengthVerbose(byteString, 8))
    print(GuessKeyLengthWeightedAverage(byteString))

def GuessKeyLength(byteString, numberOfBlocks):#Fixed number of blocks for this one
    pairDict = {}
    maxKeyLength = len(byteString)//numberOfBlocks

    if numberOfBlocks%2 != 0:
        raise ValueError('Number of Blocks must be even.')
    
    if numberOfBlocks * maxKeyLength > len(byteString):
        raise ValueError('maxKeyLength times the Number of Blocks cannot exceed the number of bytes in byteString, len(byteSttring is:', len(byteString))

    for keyLength in range(1, maxKeyLength+1, 1):
        byteBlocks = [byteString[i:i+keyLength] for i in range(0, numberOfBlocks*keyLength, keyLength)]
        pairDict[keyLength, numberOfBlocks] = PairKeyEditDist(byteBlocks, keyLength)

    pprint(pairDict)
    return (min(pairDict.values()), min(pairDict, key=pairDict.get))

def GuessKeyLengthVerbose(byteString, numberOfBlocks):#Fixed number of blocks for this one, all methods of combinations
    pairDict = {}
    combDict = {}
    overLappingPairDict = {}
    maxKeyLength = len(byteString)//numberOfBlocks

    if numberOfBlocks%2 != 0:
        raise ValueError('Number of Blocks must be even.')
    
    if numberOfBlocks * maxKeyLength > len(byteString):
        raise ValueError('maxKeyLength times the Number of Blocks cannot exceed the number of bytes in byteString, len(byteSttring is:', len(byteString))

    for keyLength in range(1, maxKeyLength+1, 1):
        byteBlocks = [byteString[i:i+keyLength] for i in range(0, numberOfBlocks*keyLength, keyLength)]
        pairDict[keyLength, numberOfBlocks] = PairKeyEditDist(byteBlocks, keyLength)
        combDict[keyLength, numberOfBlocks] = CombKeyEditDist(byteBlocks, keyLength)
        overLappingPairDict[keyLength, numberOfBlocks] = OverLappingPairKeyEditDist(byteBlocks, keyLength)

    print(min(pairDict.values()), min(pairDict, key=pairDict.get))
    print(min(combDict.values()), min(combDict, key=combDict.get))
    print(min(pairDict.values()), min(pairDict, key=pairDict.get))

def GuessKeyLengthWeightedAverage(byteString):#This function will average the hamming dist with respect for keylength for a variable number of blocks to gather a weighted guess of the correct keylength
    weightedPairDict = {}

    maxKeyLength = len(byteString)//2

    for keyLength in range(1, maxKeyLength+1, 1):
        maxBlocks = len(byteString)//keyLength
        byteBlocks = [byteString[i:i+keyLength] for i in range(0, maxBlocks*keyLength, keyLength)]
        PairKeyEditDistWeighted(byteBlocks, keyLength, weightedPairDict)

    sumKeyLengths = {k[0]:0 for k in weightedPairDict.keys()}
    counts = dict(collections.Counter(k[0] for k in weightedPairDict))

    for key in weightedPairDict:
        sumKeyLengths[key[0]] = sumKeyLengths[key[0]] + (weightedPairDict[key]/counts[key[0]])

    print(min(sumKeyLengths.values()), min(sumKeyLengths, key=sumKeyLengths.get))
    return (min(weightedPairDict.values()), min(weightedPairDict, key=weightedPairDict.get))
    
def PairKeyEditDistWeighted(byteBlocks, keyLength, weightedPairDict):
    pairDist = 0
    numberOfPairs = 0

    for i in range(0,len(byteBlocks)-1,2):#-1 here stops odd numbers going to function
        pairDist += hammingDistance(byteBlocks[i], byteBlocks[i+1])/keyLength
        numberOfPairs +=1
        weightedPairDict[keyLength, i+2] =  pairDist/numberOfPairs
    return weightedPairDict
    #return sum(pairDict.values())/len(pairDict)

def PairKeyEditDist(byteBlocks, keyLength):#Needs an even number of blocks to run
    dist = 0
    numberOfPairs = 0
    for i in range(0, len(byteBlocks), 2):
        dist += hammingDistance(byteBlocks[i], byteBlocks[i+1])/keyLength
        numberOfPairs += 1
    return dist/numberOfPairs

def CombKeyEditDist(byteBlocks, keyLength):#all possible combinations
    dist = 0
    numberOfPairs = 0
    blockCombs = combinations(byteBlocks, 2)
    for i in blockCombs:
        dist += (hammingDistance(i[0], i[1]))/keyLength
        numberOfPairs += 1
    return dist/numberOfPairs

def OverLappingPairKeyEditDist(byteBlocks, keyLength):#overlapping pairs
    dist = 0
    numberOfPairs = 0
    blockPairs = pairwise(byteBlocks)
    for i in blockPairs:
        dist += (hammingDistance(i[0], i[1]))/keyLength
        numberOfPairs += 1
    return dist/numberOfPairs
        
    
@cache
def hammingDistance(bytesOne, bytesTwo):

    dist = 0
    for i,o in zip(bytesOne, bytesTwo):
        val = i^o
        dist += popcount(val)
    return dist

def testDict():
    myDict = {}
    myDict['a'] = 2
    myDict = addDict(myDict)
    print(myDict)

def addDict(myDict):
    myDict['a'] = 1
    #print(myDict)
    return myDict

if __name__ == '__main__':

    #MyTuple = singleByteXORCipher('1b37373331363f78151b7f2b783431333d78397828372d363c78373e783a393b3736')
    #MyOtherTuple = (DetectSingleCharXOR('SingleXORSixtyChars.txt'))

    textString = 'Burning \'em, if you ain\'t quick and nimble I go crazy when I hear a cymbal'
    XORKey = 'ICE'
    #hexOut = RepeatingKeyXOR(textString, XORKey)
    #print(bytearray.fromhex(hexOut).decode('latin_1'))
    stringOne = "this is a test"
    stringTwo = "wokka wokka!!!"
    #print(hammingDistance(stringOne, stringTwo))

    breakRepeatingKeyXOR('B64RepeatingXOREncrypted.txt')
    '''with open('B64RepeatingXOREncrypted.txt') as f:
        b64String = f.read()
    hexString = b64decode(b64String).hex()
    byteString = bytes.fromhex(hexString)
    print(timeit.timeit('CombKeyEditDistVerbose(byteString)', globals=globals(), setup = 'from __main__ import byteString', number = 10)/10)
    print(timeit.timeit('CombKeyEditDist(byteString)', globals=globals(), setup = 'from __main__ import byteString', number = 10)/10)'''
    
    '''myDict = {}
    
    myDict['a', 'a'] = 1
    myDict['a', 'b'] = 2
    myDict['a', 'c'] = 3

    myDict['b', 'a'] = 4
    myDict['b', 'b'] = 5
    myDict['b', 'c'] = 6
    
    for i in myDict.keys(): 
        print(i[0])
    
    for i in myDict:
        print('hi')
        print(myDict[i])

    sumKeyLengths = {k[0]:0 for k in myDict.keys()}
    otherDict = {}

    for k in myDict.keys():
        otherDict[k[0]] = 0
        #otherDict[k[0]] += 1
        #print(otherDict(k[0]))

    print(otherDict.keys())
    print(sumKeyLengths.keys())
    print(otherDict)


    print(sumKeyLengths)

    counts = dict(collections.Counter(k[0] for k in myDict))
    print(type(counts['a']))

    for key in myDict:
        print(key)
        sumKeyLengths[key[0]] = sumKeyLengths[key[0]] + (myDict[key]/counts[key[0]])
    print(sumKeyLengths)
    
    for key in sumKeyLengths:
        sumKeyLengths[key[0]] = sumKeyLengths[key[0]]/counts[key[0]]
    print(sumKeyLengths)'''










    