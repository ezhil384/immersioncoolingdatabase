import os

def get_file_index(directory_path, target_filename):
    # 1. Get the list of files
    # (Filtering for .html to ensure we aren't counting hidden system files)
    files = [f for f in os.listdir(directory_path)]
    
    # 2. Files are already sorted, so we just find the index
    try:
        index = files.index(target_filename)
        return index
    except ValueError:
        return "File not found in the directory."

# Example:
folder_path = '../data/rsc_articles'
target = '10.1039_d5mh01385b.html'
print(f"The index is: {get_file_index(folder_path, target)}")