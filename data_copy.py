import os
import shutil
import filecmp
import logging
import re
from datetime import datetime

from transfer_data import setup_logging, format_size, find_files_to_copy, copy_files

if __name__ == '__main__':

    # Setup logging
    log_dir = r'R:\CellDive\logs'  # Replace this with your desired directory
    os.makedirs(log_dir, exist_ok=True)  # Ensure the directory exists
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = os.path.join(log_dir, f'process_{timestamp}.log')
    setup_logging(log_file)

    # default pathways    
    org_data_path = r'D:\CellDive'
    new_data_path = r'R:\CellDive'

    # create a list of slides
    slideList = sorted([x for x in set(os.listdir(org_data_path)) if (os.path.isdir(os.path.join(org_data_path,x)) and ('checkpoint' not in x)) ])

    for slide in slideList:

        logging.info(f'Processing {slide}')
        original_dir = os.path.join(org_data_path,slide)
        new_dir = os.path.join(new_data_path,slide)

        # calculate total size of the files to copy
        files_to_copy, total_size = find_files_to_copy(original_dir, new_dir)
        logging.info(f'Total size of files to copy: {format_size(total_size)}')

        # copy files
        copy_status = copy_files(original_dir, new_dir, files_to_copy)
        logging.info(f'Copy status: {copy_status}')
