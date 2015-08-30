# code_localization

Extracts UTF-8 SENTENCES from mixed-language source code for localization.
Assumes the characters are represented as hex code.
Extracts the longest sentences the script can find (from one line)
so machine translation would have the most context to work with.

Also able to insert translated sentences back original positions; creates
a translated copy of the original file. 

## Usage examples

Say we have this directory structure:
  /Current (pwd)
      /Parent
          /Child1
              /File1.py
              /File2.py
          /Child2
              /File3.py
      /temp

Source code are located under the Parent directory. 'Current/temp' will be
used to hold the output.

### EXTRACTION

to extract, we run the script as follows

```bash
./translate.py -xr ./Parent ./temp -t py
```

This will extract all files ending in .py in the 'Parent' directory and
any of its subdirectories into an identical directory structure under 'temp'

I.e.
  /Current (pwd)
      /Parent
      ...
      /temp
          /Child1
              /File1.py.tagged
              /File1.py.out
              /File2.py.tagged
              /File2.py.out
          /Child2
              /File3.py.tagged
              /File3.py.out

### TRANSLATION

Now take the .out files and run them through Google translate or a translator.
Save the translated files as <original_name>.py.en for English (for example)
and put them with their corresponding .tagged files. 

The .tagged file with the .en translation together will be used to 
reconstruct the translated source code.

### INSERTION

After putting the translated .en files in the right place, run

```bash
./translate.py -ir ./temp en
```

The script will combine the .tagged file and .en files to create translated
source code files with their original names. Now the /temp directory
looks like

      /temp
          /Child1
              /File1.py.tagged
              /File1.py.out
              /File1.py
              /File2.py.tagged
              /File2.py.out
              /File2.py
          /Child2
              /File3.py.tagged
              /File3.py.out
              /File3.py
      
Now you have the translated files, you can replace the originals with them or
do whatever you want. This script will not try to overwrite your original 
files.
