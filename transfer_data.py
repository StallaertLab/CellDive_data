import os
import shutil
import filecmp
import logging
import re
from datetime import datetime

def setup_logging(log_file):
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

def format_size(size_in_bytes):
    """Convert a size in bytes to a human-readable format (MB, GB, TB)."""
    for unit in ['bytes', 'KB', 'MB', 'GB', 'TB']:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024.0
    return f"{size_in_bytes:.2f} TB"

def get_all_files(directory):
    """Return a set of all file paths (relative to directory) in a directory."""
    file_paths = set()
    for root, dirs, files in os.walk(directory):
        for file in files:
            relative_path = os.path.relpath(os.path.join(root, file), directory)
            file_paths.add(relative_path)
    return file_paths

def find_files_to_copy(original_dir, new_dir):
    """Find files to be copied and calculate total size."""
    
    original_files = get_all_files(original_dir)
    new_files = get_all_files(new_dir)

    missing_files = sorted(original_files - new_files)

    total_size = 0

    for file in missing_files:
        original_file_path = os.path.join(original_dir, file)
        new_file_path = os.path.join(new_dir, file)

        # Get the size of the missing file and add it to the total
        file_size = os.path.getsize(original_file_path)
        total_size += file_size

    return missing_files, total_size

def copy_files(original_dir, new_dir, missing_files):
    """Copy missing files from original_dir to new_dir."""

    for file in missing_files:
        original_file_path = os.path.join(original_dir, file)
        new_file_path = os.path.join(new_dir, file)

        # Ensure the subdirectories exist in the new location
        new_file_dir = os.path.dirname(new_file_path)
        os.makedirs(new_file_dir, exist_ok=True)

        # Copy the file from original to new location
        shutil.copy2(original_file_path, new_file_path)

        # Verify if the file has been successfully copied before deleting the original
        if filecmp.cmp(original_file_path, new_file_path, shallow=True):
            logging.info(f"Copied: {original_file_path} -> {new_file_path}")
        else:
            logging.error(f"Failed to copy: {original_file_path} -> {new_file_path}")
            return False  # Stop if copy failed

    return True

def find_redundant_af(original_dir):

    sub_dir = os.path.join(original_dir, 'CD02011')
    
    # all not 0 and 1 rounds
    folder_list = [os.path.join(sub_dir, folder) for folder in os.listdir(sub_dir) if not folder.split("\\")[-1].startswith(("0.", "1."))]
    
    round_set = set([x.split('\\')[-1].split('.')[0] for x in folder_list])

    redundant_af_list = []
    for round in round_set:

        # all af folders of this round
        round_af_files = [x for x in folder_list if (((x.split('\\')[-1].split('.')[2]) == '1') and ((x.split('\\')[-1].split('.')[0]) == round))]

        if len(round_af_files) > 1:
            repeat_list = [int(x.split('\\')[-1].split('.')[-1]) for x in round_af_files if len(x.split('\\')[-1].split('.'))>3]
            repeat_max = max(repeat_list)

            for file in round_af_files:
                if file.split('\\')[-1].split('.')[-1] != str(repeat_max).zfill(3):
                    redundant_af_list.append(file) 

    return redundant_af_list

def find_files_to_delete(original_dir, new_dir, pattern, restriction_list = None):
    """Delete files in original_dir if they have been successfully copied to new_dir and match the pattern."""

    to_del_files = []
    total_size = 0

    original_files = get_all_files(original_dir)
    new_files = get_all_files(new_dir)

    # Only delete files that exist in both original and new locations
    copied_files = original_files & new_files

    for file in copied_files:
        original_file_path = os.path.join(original_dir, file)
        new_file_path = os.path.join(new_dir, file)

        match_found = True

        if restriction_list is not None:
            match_found = any(os.path.commonpath([path, original_file_path]) == path for path in restriction_list)

        # Verify if the file path matches the pattern 
        # and it has matching metadata
        # and it's not the autoalignment file
        if match_found and pattern.search(file.replace('/', '\\')) and not file.endswith('AutoAlignment.zip') and filecmp.cmp(original_file_path, new_file_path, shallow=True):
            
            to_del_files.append(original_file_path)
            
            file_size = os.path.getsize(original_file_path)
            total_size += file_size

            logging.info(f"File marked for deletion: {original_file_path}, {format_size(file_size)}")

    return to_del_files, total_size

def remove_files(file_list):
    """Deletes a list of files."""

    for file_path in file_list:
        os.remove(file_path)
        logging.info(f"File {file_path} removed.")

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

        # find and delete tiles
        logging.info(f'Mark tiles for deletion.')
        pattern = re.compile(r'CD02011\\(?![01]\.)[^\\]*\\raw')
        to_del_files, total_size = find_files_to_delete(original_dir, new_dir, pattern)
        logging.info(f'Total size of tiles to delete: {format_size(total_size)}')

        remove_files(to_del_files)

        # find and delete stitched images
        # it only moves files when there was a repeat of the imaging round (otherwise the files are moved automatically to final)
        logging.info(f'Mark stitched signal images for deletion.')
        pattern = re.compile(r'CD02011\\([2-9][0-9]*|1[0-9]*)\.0\.4(\.[^\\]*)?\\(?!raw\\)')
        to_del_files, total_size = find_files_to_delete(original_dir, new_dir, pattern)
        logging.info(f'Total size of stitched signal images to delete: {format_size(total_size)}')

        remove_files(to_del_files)

        # find and delete AF stitched images
        # if AF round was repeated
        logging.info(f'Mark stitched redundant AF images for deletion.')
        pattern = re.compile(r'CD02011\\([2-9][0-9]*|1[0-9]*)\.0\.1(\.[^\\]*)?\\(?!raw\\)')
        redundant_af_list = find_redundant_af(original_dir)
        to_del_files, total_size = find_files_to_delete(original_dir, new_dir, pattern, restriction_list = redundant_af_list)
        logging.info(f'Total size of stitched redundant AF images to delete: {format_size(total_size)}')

        remove_files(to_del_files)
