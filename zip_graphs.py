#!/usr/bin/env python3

import os
from fnmatch import fnmatch
from zipfile import ZipFile

with ZipFile('graphs.zip', 'w') as graphszip:
    for folder_name, subfolders, filenames in os.walk("."):

        # Skip folders
        if ".git" in folder_name:
            continue

        for filename in filenames:
            # Only add pdfs
            if not fnmatch(filename, '*.pdf'):
                continue

            file_path = os.path.join(folder_name, filename)

            graphszip.write(file_path)
