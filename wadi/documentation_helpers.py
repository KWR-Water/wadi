""" Functions to help the building of the documentation. Especially finding files is a pain in ReadTheDocs when compared
to local building of the documentation """

from pathlib import Path
import glob
import os
def get_data_dir():
    # cur_dir = Path.cwd()

    # data_file_not_found = True
    # max_directory_levels = 3
    # directory_level = 0

    # example_data_file = "**/hgc_example.xlsx"

    # while data_file_not_found:
    #     data_file = glob.glob(example_data_file, recursive=True)
    #     if len(data_file) > 0:
    #         data_file_not_found = False
    #         data_file_folder = (cur_dir / data_file[0]).parent
    #         os.chdir(cur_dir)
    #         return data_file_folder
    #     if directory_level > max_directory_levels:
    #         os.chdir(cur_dir)
    #         return None
    #     os.chdir('..')
    #     directory_level += 1
    return Path(__file__).parent / 'data_for_documentation'
