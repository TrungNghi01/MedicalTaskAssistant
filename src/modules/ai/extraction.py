import os
import lzma
from tqdm import tqdm

def xz_file_indir(directory):
    files = []
    for filename in os.listdir(directory):
        if filename.endswith(".xz") and os.path.isfile(os.path.join(directory, filename)):
            files.append(filename)
    return files

folder_path = r"D:\Python\openwebtext\openwebtext"
output_file_train = "output_train.txt"
output_file_val = "output_val.txt"
vocab_file = "vocab.txt"
split_files = int(input("How many files would you like to split this into? "))

files = xz_file_indir(folder_path)

total_files = len(files)
max_count = total_files // split_files if split_files != 0 else total_files

split_index = int(total_files * 0.9)
files_train = files[:split_index]
files_val = files[split_index:]
vocab = set()

with open(train_split, "w", encoding="utf-8") as outfile:
    for filename in tqdm(files_train, total=len(files_train)):
        file_path = os.path.join(folder_path, filename)
        with lzma.open(file_path, 'rt', encoding='utf-8') as infile:
            text = infile.read()
            outfile.write(text)
            vocab.update(set(text))

with open(val_split, "w", encoding="utf-8") as outfile:
    for filename in tqdm(files_val, total=len(files_val)):
        file_path = os.path.join(folder_path, filename)
        with lzma.open(file_path, 'rt', encoding='utf-8') as infile:
            text = infile.read()
            outfile.write(text)
            vocab.update(set(text))

with open(vocab_file, 'w', encoding='utf-8') as vfile:
    for char in sorted(vocab):
        vfile.write(char + "\n")
