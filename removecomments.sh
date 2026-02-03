#!/bin/bash

# Check if filename is provided
if [ -z "$1" ] || [ -z "$2" ]
then
    echo "No filename provided. Usage: ./removecomments.sh infile.xml outfile"
    exit 1
fi

# Remove XML comments using sed
sed 's/<!--.*-->//' "$1" | sed '/^ *$/d' > "$2"
