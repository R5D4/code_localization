#!/usr/bin/python

from sys import argv
import os
import errno
import argparse

#################### CONSTANTS ####################

# We want to include these in extracted sentences.
PUNCTUATION = ' .,?!-'
# Assume translatable characters are in hex.
HEX_START = "\\x"
# UTF-8 BOM character.
BOM = '\xef\xbb\xbf'

# File extension for tagged files
TAG_EXT = 'tagged'
# File extension for output files containing translatable text
OUT_EXT = 'out'


#################### HELPERS ####################

def add_tag(input_list, count):
    """ Adds an identifier in front of the extracted sentence """
    tag = '<EXTRACTED%d>' % count
    input_list.extend(list(tag))
    return count+1


def get_tag(count):
    """ Returns ID based on count given """
    tag = '<EXTRACTED%d>' % count
    return tag


def parse_translation(line):
    """ Parses out the tag and the translated string from a line """
    #print "translation to be parsed: %r" % line
    parsed = line.split(' ', 1)
    #print "parsed = %r" % parsed
    return parsed[0], parsed[1]


def make_dir(path):
    """ Try to create the output directory """
    try:
        os.makedirs(path)
    except OSError as exception:
        # if directory already exists do nothing
        if exception.errno != errno.EEXIST:
            raise


#################### EXTRACT ####################

# Extracts UTF-8 sentences from a file.
#   from_file - filename of the file to be extracted from
#   to_dir - directory to save the new files in
#
# Creates two files:
#   from_file.TAG_EXT - from_file with ID tags replacing translatable strings
#   from_file.OUT_EXT - ID tag followed by extracted translatable strings
#
# The original file is not changed.

def extract(from_file, to_dir):

    # make the directories for the output
    tagged_file = os.path.join(to_dir, from_file+'.'+TAG_EXT)
    make_dir(os.path.dirname(tagged_file))
    output_file = os.path.join(to_dir, from_file+'.'+OUT_EXT)
    make_dir(os.path.dirname(output_file))

    # output some status messages
    print "Extracting from %s..." % from_file,

    with open(from_file) as original, \
         open(output_file, "w") as output, \
         open(tagged_file, "w") as tagged:

        # used as a part of ID
        count = 0

        for line in original:

            if line.startswith(BOM):
                # skip BOM character
                line = line[3:]

            extracted = []
            # tracks if we're in the middle of a translatable sentence or not
            started = False

            for c in list(line):
                c_raw = "%r" % c
                #print "character is %r" % c_raw

                if HEX_START in c_raw: 
                    # start sentence when we find translatable character
                    if not started:
                        started = True
                        # only add ID at beginning of translatable sentence
                        count = add_tag(extracted, count)

                    extracted.append(c)

                elif c in PUNCTUATION and started:
                    # include normal punctuation in translatable sentences
                    extracted.append(c)

                elif started:
                    # not a translatable character and not a punctuation
                    # translatable string is interrupted
                    started = False
                    extracted.append('\n')
                    # write out the ID and the char to the tagged file
                    tagged.write(get_tag(count-1))
                    # write all nontranslatable characters as is to tagged file
                    tagged.write(c)

                else:
                    # not in the middle of a translatable sentence
                    # write all nontranslatable as is to tagged file
                    tagged.write(c)
                    
            # join the character array into a string
            o_string = "%s\n" % ''.join(extracted)
            final_string = o_string.strip()
            #print 'final_string: %r' % final_string

            # if not empty line, write to file
            if final_string:
                final_string += '\n'
                output.write(final_string)
                #print "%r" % final_string
    
    # Finished
    print "Done."


# Recursive extraction
def recursive_extract(input_dir, output_dir, exts):
    for root, dirs, files in os.walk(input_dir):
        for f in files:
            file_ext = f.split('.')[-1]
            if file_ext in exts:
                from_file = os.path.join(root, f)
                extract(from_file, output_dir)

    
#################### INSERT #################### 

# Inserts translated string into tagged file.
#   output_file - name of original file, path should be the directory with the
#                 corresponding tagged file
#   translated_lang - two character code for translation language (e.g. 'en')
#
# Looks for file_name.lang where file_name is tagged_file without TAG_EXT. 
# e.g. text.py.en
# These files are created by translating the tagged files from extraction step.
# The user then put these files with the corresponding tagged files
#
# The script will replace the ID tags in the tagged files with the 
# corresponding translated strings from the translated file

def insert(output_file, translated_lang):

    # print some status messages
    print "Inserting translation into %s..." % output_file,

    translation_file = output_file + '.' + translated_lang
    #print "translation file is %s" % translation_file
    tagged_file = output_file + '.' + TAG_EXT
    #print "tagged file is %s" % tagged_file

    with open(tagged_file) as tagged, \
         open(translation_file) as translated, \
         open(output_file, 'w') as output:

        # read the entire tagged file into memory - wasteful but easy!
        entire_file = tagged.read()
        #print "entire file: %s" % entire_file

        for line in translated:
            #print "processing line: %r" % line
            tag, translation = parse_translation(line)
            translation = translation.strip()
            translation = translation.replace("'","\\'")
            #print "cleaned up translation: %r" % translation 
            #print "tag = %s, translation = %s" % (tag, translation)
            entire_file = entire_file.replace(tag, translation)
            #print "so far: %s" % entire_file

        output.write(entire_file)

    # Finished.
    print "Done."


# Recursive insertion
def recursive_insert(directory, lang):
    for root, dirs, files in os.walk(directory):
        for f in files:
            file_ext = f.split('.')[-1]
            # if it's a language file, find corresponding tagged file
            if file_ext == lang:
                # base name only
                file_base = f.replace('.'+lang, '')
                tagged_file = file_base + '.' + TAG_EXT
                if tagged_file in files:
                    from_file = os.path.join(root, file_base)
                    insert(from_file, lang)
                else:
                    print "ERROR: {} not found. Skipped.".format(tagged_file)
    


#################### START HERE ####################

# examples:
# ./translate.py -x file.ext tempDir
# ./translate.py -i tempDir/file.ext en
# ./translate.py -xr folder tempDir py rpy
# ./translate.py -ir tempDir en

parser = argparse.ArgumentParser( "Extracts and inserts translatable strings")
group = parser.add_mutually_exclusive_group()
group.add_argument("-x", nargs=2, help="Extract")
group.add_argument("-i", nargs=2, help="Insert")
group.add_argument("-xr", nargs=2, help="Recursive Extract")
group.add_argument("-ir", nargs=2, help="Recursive Insert")
parser.add_argument("-t", nargs='+', help="File Type for recursive extraction")
args = parser.parse_args()
print "printing flags:"
print "-x = {}, -i = {}, -xr = {}, -ir = {}, -t = {}".format(args.x, args.i, 
                                                             args.xr, args.ir,
                                                             args.t)

if not (args.x or args.i or args.xr or args.ir):
    print "Please indicate either extraction or insertion."

elif args.xr and not args.t:
    print "Please enter at least one file type."
    
elif args.xr and args.t:
    print "Recursive extraction."
    input_dir = args.xr[0]
    output_dir = args.xr[1]
    file_exts = args.t
    recursive_extract(input_dir, output_dir, file_exts)

elif args.ir:
    print "Recursive insertion."
    directory = args.ir[0]
    lang = args.ir[1]
    recursive_insert(directory, lang)

elif args.x:
    print "Single-file extraction."
    from_file = args.x[0]
    to_dir = args.x[1]
    extract(from_file, to_dir)

elif args.i:
    print "Single-file insertion."
    output_file = args.i[0]
    translated_lang = args.i[1]
    insert(output_file, translated_lang)

