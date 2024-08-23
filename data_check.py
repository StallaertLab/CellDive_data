import os
import re
from termcolor import colored

def format_size(size_in_bytes):
    """Convert a size in bytes to a human-readable format (MB, GB, TB)."""
    for unit in ['bytes', 'KB', 'MB', 'GB', 'TB']:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024.0
    return f"{size_in_bytes:.2f} TB"

def natural_sort_key(s):
    """Sort keys naturally by splitting numeric parts and converting them to integers."""
    return [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', s)]

def scan_directory(directory, size_threshold=10 * 1024 * 1024, level=0):
    total_size = 0
    num_files = 0
    num_subdirs = 0
    small_files_size = 0
    small_files_count = 0
    is_raw_dir_empty = False

    indent = '  ' * level
    print(f"{indent}{os.path.basename(directory)}:")

    if os.path.basename(directory) == 'raw' and not os.listdir(directory):
        print(colored(f"{indent}  No tiles present.", 'red'))
        is_raw_dir_empty = True

    if not is_raw_dir_empty:
        entries = sorted(os.scandir(directory), key=lambda e: natural_sort_key(e.name))
        for entry in entries:
            if entry.is_dir(follow_symlinks=False):
                num_subdirs += 1
                subdir_size, subdir_files, subdir_dirs = scan_directory(entry.path, size_threshold, level + 1)
                total_size += subdir_size
                num_files += subdir_files
                num_subdirs += subdir_dirs
            elif entry.is_file(follow_symlinks=False):
                file_size = os.path.getsize(entry.path)
                if file_size >= size_threshold:
                    print(f"{indent} {format_size(file_size)} {entry.name}")
                    total_size += file_size
                    num_files += 1
                else:
                    small_files_size += file_size
                    small_files_count += 1
    
        if small_files_count > 0:
            print(f"{indent}  {small_files_count} small files (total: {format_size(small_files_size)})")

        print()
        print(f"{indent}Total size: {format_size(total_size + small_files_size)}")
        #print(f"{indent}Number of files: {num_files + small_files_count}")
        #print(f"{indent}Number of subdirectories: {num_subdirs}")
        print()
        print()
    
    return total_size + small_files_size, num_files + small_files_count, num_subdirs

# Example usage
if __name__ == '__main__':

    directory_to_scan = r"R:\CellDive\BLCA-1"
    SIZE_THRESHOLD = 10 * 1024 * 1024  # 10 MB
    scan_directory(directory_to_scan, SIZE_THRESHOLD)

