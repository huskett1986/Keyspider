import os
import sys
import subprocess

venv_dir = ".venv"
python_exe = os.path.join(venv_dir, "bin", "python")

if not os.path.exists(venv_dir):
    print("Creating virtual environment...")
    subprocess.check_call([sys.executable, "-m", "venv", venv_dir])

pip_path = os.path.join(venv_dir, "bin", "pip")
if not os.path.exists(pip_path):
    print("Pip not found in virtual environment. Bootstrapping with ensurepip...")
    subprocess.check_call([python_exe, "-m", "ensurepip", "--upgrade"])
    subprocess.check_call([python_exe, "-m", "pip", "install", "--upgrade", "pip"])

if sys.prefix == sys.base_prefix:
    print("Re-running script inside virtual environment...")
    os.execv(python_exe, [python_exe] + sys.argv)

required = ["requests", "beautifulsoup4", "tqdm"]
for package in required:
    try:
        if package == "beautifulsoup4":
            __import__("bs4")
        else:
            __import__(package)
    except ImportError:
        print(f"Installing missing package: {package}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from tqdm import tqdm
import html

ascii_art = r"""
                                :     -                                 
                               -       -                                
                              =         =                               
                             +           +                              
                            .-           -.                             
                            %.           :#                             
                            %=    -+-    =%  .                          
                         .  ++  @%#+*#@  =*  .                          
                         :  #: %@#*+*#%@ -#  :                          
                         *- .@-@@%%*#%@@=@. -*                          
                          :*  %@@@#*#@@@#  *:                           
                           .%#--@@@@@@@:-#%.                            
                             -=+#@##%@#+=-                              
                               -%@@%@@%-                                
                           *%%- %%@@@%@.:%%#                            
                          *:  +%..= =. %=  .#                           
                         #: -%=         =%- .%:                         
                        @  :#             @.  %                         
                        *  .%            .@.  %                         
                        .. .#            .%.  =                         
                         : :*            .%. :                          
                           .#             @.                            
                             #.          #                              
                              :-       ::                               
                                -     -        
"""
title = "Keyspider v2.3 by Huskett"
GREEN = "\033[32m"
RESET = "\033[0m"

print(f"{GREEN}{ascii_art}{RESET}")
print(f"{GREEN}{title.center(70)}{RESET}\n")


def get_local_input():
    word = input("Enter the word to search for: ").strip()
    while True:
        path = input("Enter the path to search recursively (e.g., /mnt/e): ").strip()
        if os.path.isdir(path):
            break
        else:
            print("The path entered is not a valid directory. Please try again.")
    while True:
        search_type = input("Choose search type - 'content', 'filename', or 'both': ").strip().lower()
        if search_type in ['content', 'filename', 'both']:
            break
        else:
            print("Please enter 'content', 'filename', or 'both'.")
    min_count = 1
    if search_type in ['content', 'both']:
        while True:
            try:
                min_count = int(input("Enter the minimum number of times the word should appear: ").strip())
                if min_count < 1:
                    raise ValueError
                break
            except ValueError:
                print("Please enter a valid positive integer for the minimum count.")
    return word, min_count, path, search_type


def search_local_files(word, min_count, path, html_file, search_type):
    matching_files = []
    try:
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Search Results for '{html.escape(word)}'</title>
    <style>
        body {{ font-family: Arial, sans-serif; background-color: #1e1e1e; color: #e0e0e0; }}
        h1 {{ text-align: center; color: #00ff88; }}
        ul {{ list-style: none; padding: 0; }}
        li {{ margin: 8px 0; }}
        a {{ color: #5bc0de; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        .container {{ max-width: 800px; margin: auto; padding: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Files containing '{html.escape(word)}' (search type: {search_type})</h1>
        <ul>
""")

            total_files = sum(len(files) for _, _, files in os.walk(path))
            print(f"Total files to process: {total_files}")

            with tqdm(total=total_files, desc="Processing files") as pbar:
                for root, dirs, files in os.walk(path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        match_found = False
                        if search_type in ['filename', 'both'] and word.lower() in file.lower():
                            match_found = True
                        elif search_type in ['content', 'both']:
                            try:
                                count = 0
                                with open(file_path, 'r', encoding='utf-8', errors='ignore') as file_content:
                                    for line in file_content:
                                        count += line.lower().count(word.lower())
                                        if count >= min_count:
                                            match_found = True
                                            break
                            except Exception:
                                pass
                        if match_found:
                            f.write(f"<li><a href='file:///{file_path}'>{html.escape(file_path)}</a></li>\n")
                            matching_files.append(file_path)
                        pbar.update(1)

            f.write("</ul></div></body></html>")
    except Exception as e:
        print(f"An error occurred: {e}")
    return matching_files


def download_page(url, html_content):
    parsed_url = urlparse(url)
    filename = f"{parsed_url.netloc}{parsed_url.path.replace('/', '_')}.html"
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(html_content)
    print(f"Saved page: {filename}")


def crawl_site(url, keyword, visited=None):
    if visited is None:
        visited = set()
    if url in visited:
        return
    visited.add(url)
    try:
        print(f"Processing: {url}")
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        if keyword.lower() in soup.get_text().lower():
            download_page(url, response.text)
        for link in soup.find_all('a', href=True):
            full_url = urljoin(url, link['href'])
            if urlparse(full_url).netloc == urlparse(url).netloc:
                crawl_site(full_url, keyword, visited)
    except requests.RequestException as e:
        print(f"Failed to access {url}: {e}")


def generate_tree_html(start_path, output_file):
    all_paths = []
    for root, dirs, files in os.walk(start_path):
        for d in dirs:
            all_paths.append(os.path.join(root, d))
        for f in files:
            all_paths.append(os.path.join(root, f))
    total_items = len(all_paths)

    def walk_directory(path, pbar):
        tree = []
        try:
            entries = sorted(os.listdir(path), key=lambda x: x.lower())
        except PermissionError:
            return tree
        for entry in entries:
            full_path = os.path.join(path, entry)
            pbar.update(1)
            if os.path.isdir(full_path):
                subtree = walk_directory(full_path, pbar)
                tree.append((entry, subtree))
            else:
                tree.append(entry)
        return tree

    def render_tree(tree):
        html_output = "<ul>"
        for item in tree:
            if isinstance(item, tuple):
                folder_name, children = item
                html_output += f"<li><details><summary>{html.escape(folder_name)}</summary>"
                html_output += render_tree(children)
                html_output += "</details></li>"
            else:
                html_output += f"<li>{html.escape(item)}</li>"
        html_output += "</ul>"
        return html_output

    with tqdm(total=total_items, desc="Building tree") as pbar:
        directory_tree = walk_directory(start_path, pbar)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Directory Tree</title>
    <style>
        body {{ font-family: Consolas, monospace; background-color: #1e1e1e; color: #f1f1f1; }}
        h1 {{ text-align: center; color: #00ff88; }}
        ul {{ list-style-type: none; padding-left: 20px; }}
        li {{ margin: 4px 0; }}
        details summary {{ cursor: pointer; color: #00ffa6; }}
        details[open] summary {{ color: #00e6e6; }}
    </style>
</head>
<body>
    <h1 style="text-align:center;">Directory Tree of {html.escape(start_path)}</h1>
""")
        f.write(render_tree(directory_tree))
        f.write("</body></html>")
    print(f"Directory tree saved to {output_file}")


def main():
    mode = input("Search Mode - 'local', 'web', or 'tree': ").strip().lower()
    if mode == "local":
        word, min_count, path, search_type = get_local_input()
        html_file = f"{word}.html"
        print(f"\nSearching for '{word}' (type: {search_type}) in '{path}'...\n")
        matching_files = search_local_files(word, min_count, path, html_file, search_type)
        print(f"Results saved to {html_file}" if matching_files else "No matching files found.")
    elif mode == "web":
        base_url = input("Enter the website URL to search: ").strip()
        keyword = input("Enter the keyword to find: ").strip()
        if not os.path.exists('downloaded_pages'):
            os.makedirs('downloaded_pages')
        os.chdir('downloaded_pages')
        crawl_site(base_url, keyword)
    elif mode == "tree":
        path = input("Enter the path to generate a directory tree (e.g., /mnt/c): ").strip()
        if os.path.isdir(path):
            output_file = "directory_tree.html"
            generate_tree_html(path, output_file)
        else:
            print("Invalid path. Please enter a valid directory.")
    else:
        print("Invalid mode. Please enter 'local', 'web', or 'tree'.")


if __name__ == "__main__":
    main()

