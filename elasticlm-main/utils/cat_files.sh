#!/bin/bash

# cat_files.sh: Echo the path and name of each file starting from a given directory,
#             display its contents, exclude specific files and directories, and add a blank line after each file.

# -------------------------------------------
# Usage:
#   ./cat_files.sh <path>
# Example:
#   ./cat_files.sh ../path
# -------------------------------------------

# Function to display usage instructions
usage() {
    echo "Usage: $0 <path>"
    exit 1
}

# Check if exactly one argument (the path) is provided
if [ "$#" -ne 1 ]; then
    echo "Error: Incorrect number of arguments."
    usage
fi

# Assign the first argument to the variable 'start_path'
start_path="$1"

# Verify that the provided path exists and is a directory
if [ ! -d "$start_path" ]; then
    echo "Error: '$start_path' is not a directory or does not exist."
    exit 1
fi

# Echo the starting path
echo "Starting from path: $start_path"

# Initialize a counter for the number of files processed
file_count=0

# Use 'find' to locate all regular files (-type f) starting from 'start_path',
# excluding:
#   - Files named '.env'
#   - Files named '.env-example'
#   - Files with the '.pckl' extension
#   - Files with the '.pyc' extension
#   - Files with the '.ico' extension
#   - Files named 'package-lock.json'
#   - Directories named '__pycache__', 'node_modules', and '.git'
#
# '-print0' is used to handle filenames with spaces or special characters.
# Using process substitution to avoid running the while loop in a subshell.
while IFS= read -r -d '' file; do
    # Increment the file counter
    file_count=$((file_count + 1))

    # Echo the full path of the current file
    echo "Path: $file"

    # Check if the file is readable
    if [ -r "$file" ]; then
        # Display the contents of the current file
        cat "$file"
    else
        echo "Warning: Cannot read file '$file'"
    fi

    # Add a blank line for separation
    echo
done < <(
    find "$start_path" \( \
        -type d \( -name "__pycache__" -o -name "node_modules" -o -name ".git" -o -name "fonts"  -o -name ".next" \) -prune -o \
        -type f ! -name ".env" ! -name ".env-example" ! -name "*.pckl" ! -name "*.pyc" ! -name "*.ico" ! -name "package-lock.json" ! -name "*woff" \
    \) -print0
)

# After processing, check if any files were found
if [ "$file_count" -eq 0 ]; then
    echo "No files found in '$start_path' matching the criteria."
else
    echo "Processed $file_count file(s)."
fi
