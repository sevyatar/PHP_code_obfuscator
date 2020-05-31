#!/bin/bash

import os
import re
import hashlib
import shutil

SOURCE_CODE_DIRECTORY = "C:\\Users\\Evyatar\\Documents\\NetBeansProjects\\TodoList\\"
DESTINATION_CODE_DIRECTORY = "C:\\wamp\\www\\TodoList2\\TodoList\\"
DB_CONTAINER_FILE = "mappings.txt"

BLACKLIST_NAMES = (	'Config', 'Error', 'Flash', 'NotFoundException', 'TodoDao', 'TodoMapper', 'Todo', 'TodoSearchCriteria', 'TodoValidator', 'Utils', 
					'this', 
					'self', 
					'getMessage', 'handleException', 'error_field', 'quote', 'query', 'errorInfo', 'format', 'setTime', 'setDueOn', 'fetch', 'prepare', 'lastInsertId',  'execute', 
					'rowCount', 
					'loadClass', 
					'_GET', '_POST', '_REQUEST', '_SERVER', '_SESSION', '_FILES', '_COOKIE', '_ENV')
					
FILE_EXTENSION_TO_OBFUSCATE = ('.php', '.phtml')

mappings = {}

def GetFileContants(filename):
	fin = open(filename, 'r')
	data = fin.read()
	fin.close()
	
	return data

def GenerateDestinationPath(originalFilename):
	relativeOriginalFilename = originalFilename[len(SOURCE_CODE_DIRECTORY):]
	filenameToReturn = DESTINATION_CODE_DIRECTORY + relativeOriginalFilename
	
	dirname = filenameToReturn.rsplit("\\", 1)[0]
	if not os.path.exists(dirname):
		os.makedirs(dirname)
		
	return filenameToReturn
	
def WriteFile(filename, data):
	fout = open(filename, 'w+')
	data = fout.write(data)
	fout.close()
	
def DictionaryHasValue(dict, value):
	for currentValue in dict.values():
		if currentValue == value:
			return True
			
	return False

def CreateValueMapping(originalName):
	global mappings

	EncodedValue = hashlib.sha256(originalName.group(2)).hexdigest()
	# Name must not start with a digit
	if (EncodedValue[0].isdigit()):
		EncodedValue = "a" + EncodedValue
		
	mappings[originalName.group(2)] = EncodedValue

	return ""

def ReplaceNameWithMappedValue(originalName):
	global mappings
	
	if originalName.group(2) in BLACKLIST_NAMES:
		return (originalName.group(1) + originalName.group(2) + originalName.group(3))

	if (mappings.has_key(originalName.group(2))):
		return originalName.group(1) + mappings[originalName.group(2)] + originalName.group(3)
	else:
		return originalName.group(1) + originalName.group(2) + originalName.group(3)

		
def EncodeName(originalName):
	global mappings
	
	retVal = originalName.group(1)
	if originalName.group(2) in BLACKLIST_NAMES:
		return (retVal + originalName.group(2) + originalName.group(3))

	hashResult = hashlib.sha256(originalName.group(2)).hexdigest()
	# Name must not start with a digit
	if (hashResult[0].isdigit()):
		hashResult = "a" + hashResult
		
	# In case the variable is already obfuscated
	if DictionaryHasValue(mappings, originalName.group(2)):
		retVal += originalName.group(2)
			
	# In case we already have a mapping for this variable
	elif mappings.has_key(originalName.group(2)):
		retVal += hashResult
	else:	
		retVal += hashResult
		mappings[originalName.group(2)] = hashResult
		
	retVal += originalName.group(3)
		
	return retVal


# Looks for functions in the code, by looking for the following formats: 
#  function SomeFunction(
#  ::SomeFunction(
#  ->SomeFunction(
def ObfuscateFunctions(data):
	data = re.sub('(function )([a-zA-Z0-9_]+)(\()', ReplaceNameWithMappedValue, data)
	data = re.sub('(::)([a-zA-Z0-9_]+)(\()', ReplaceNameWithMappedValue, data)
	data = re.sub('(->)([a-zA-Z0-9_]+)(\()', ReplaceNameWithMappedValue, data)

	return data
	

# Looks for variable in the code, by looking for the following formats: 
#  $SomeVariable
def ObfuscateVariables(data):
	data = re.sub('(\$)([a-zA-Z0-9_]+)()', EncodeName, data)
	data = re.sub('(->)([a-zA-Z0-9_]+)([^a-zA-Z0-9_\(])', EncodeName, data)
	
	return data
	
# Looks for classes in the code, by looking for the following formats: 
#  SomeClass::
#  new SomeClass
#  class SomeClass
#  extends SomeClass
#  interface SomeClass
def ObfuscateClasses(data):
	data = re.sub('([^a-zA-Z0-9_])([a-zA-Z0-9_]+)(::)', ReplaceNameWithMappedValue, data)
	data = re.sub('(new )([a-zA-Z0-9_]+)()', ReplaceNameWithMappedValue, data)
	data = re.sub('(class )([a-zA-Z0-9_]+)()', ReplaceNameWithMappedValue, data)
	data = re.sub('(extends )([a-zA-Z0-9_]+)()', ReplaceNameWithMappedValue, data)
	data = re.sub('(interface )([a-zA-Z0-9_]+)()', ReplaceNameWithMappedValue, data)
	
	return data

def ObfuscateConstants(data):
	data = re.sub('(const )([A-Z0-9_]+)([^A-Z0-9_])', ReplaceNameWithMappedValue, data)
	data = re.sub('(::)([A-Z0-9_]+)([^A-Z0-9_])', ReplaceNameWithMappedValue, data)

	return data

def MapFunctions(data):
	re.sub('(function )([a-zA-Z0-9_]+)(\()', CreateValueMapping, data)

def MapConstants(data):
	re.sub('(const )([A-Z0-9_]+)([^A-Z0-9_])', CreateValueMapping, data)

def MapClasses(data):
	data = re.sub('(class )([a-zA-Z0-9_]+)()', CreateValueMapping, data)
	data = re.sub('(interface )([a-zA-Z0-9_]+)()', CreateValueMapping, data)

def CreateInitialMappings(sourceFilename):
	data = GetFileContants(sourceFilename)

	MapFunctions(data)
	MapClasses(data)
	MapConstants(data)


def ObfuscateSourceFile(sourceFilename, destFilename):
	data = GetFileContants(sourceFilename)
	
	data = ObfuscateVariables(data)
	data = ObfuscateFunctions(data)
	data = ObfuscateConstants(data)
	data = ObfuscateClasses(data)
	
	WriteFile(destFilename, data)
	
def WriteMappingsTofile():
	global mappings
	
	mappingsString = ""
	for key, value in mappings.iteritems():
		mappingsString += key + " - " + value + "\n"
	
	WriteFile(DB_CONTAINER_FILE, mappingsString)
	
		
def RunOnAllFiles(directory, isMappingRun):
	for (path, dirs, files) in os.walk(directory):
		for filename in files:
			sourcePath = os.path.join(path, filename)
			fileExtension = os.path.splitext(filename)[1]

			if (True == isMappingRun):
				if fileExtension in FILE_EXTENSION_TO_OBFUSCATE:
					CreateInitialMappings(sourcePath)
			else:
				destinationPath = GenerateDestinationPath(sourcePath)

				if fileExtension in FILE_EXTENSION_TO_OBFUSCATE:
					ObfuscateSourceFile(sourcePath, destinationPath)
				else:
					shutil.copy(sourcePath, destinationPath)

def Main():
	RunOnAllFiles(SOURCE_CODE_DIRECTORY, True)
	RunOnAllFiles(SOURCE_CODE_DIRECTORY, False)
	WriteMappingsTofile()

Main()

