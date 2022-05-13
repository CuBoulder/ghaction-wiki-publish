#!/usr/bin/env python3

import os
import shutil
from pathlib import Path
import re
import subprocess
import shutil

docroot = 'base_repo/docs'
wikiroot = 'wiki'

gh_repo = 'https://' + os.environ['GITHUB_ACTOR'] + ':' + os.environ['GH_TOKEN'] + '@github.com/' + os.environ['GITHUB_REPOSITORY'] + ".git"
gh_wiki_repo = 'https://' + os.environ['GITHUB_ACTOR'] + ':' + os.environ['GH_TOKEN'] + '@github.com/' + os.environ['GITHUB_REPOSITORY'] + ".wiki.git"

# Create working directory
os.mkdir(wikiroot)

# Clone the base repo
subprocess.run(f'/usr/bin/git clone {gh_repo} base_repo', shell=True)
# Clone the wiki repo
subprocess.run(f'/usr/bin/git clone {gh_wiki_repo} wiki_repo', shell=True)

toc = []

def clean_ordering_numbers_from_path(arg):
    exploded_path = str(arg).split('/')
    new_path = []
    for segment in exploded_path:
        if re.search('^[0-9]+\-', segment):
            segment = segment.split('-', 1)[1]
        new_path.append(segment)
    fixed_path = os.path.join(*new_path)
    print(f'Fixed: {fixed_path}')
    return fixed_path

for root, dirs, files in os.walk(docroot):
    dirs.sort()

    depth = str(os.path.relpath(root, docroot)).count('/')
    dir_title = clean_ordering_numbers_from_path(os.path.relpath(root, docroot).split('/')[-1].replace('_', ' '))
    dir_path = None

    if(os.path.exists(Path(root, 'index.md'))):
        dir_path = clean_ordering_numbers_from_path(Path(os.path.relpath(root, docroot), 'index.md')).replace('/', '-').rsplit('.', 1)[0]

    if dir_title != '.':
        toc.append({'depth': depth, 'title': dir_title, 'path': dir_path, 'is_dir': True})

    for f in sorted(files):
        depth = str(Path(os.path.relpath(root, docroot), f)).count('/')

        src = Path(root, f)

        fixed_path = clean_ordering_numbers_from_path(Path(os.path.relpath(root, docroot), f))

        dst_filename = fixed_path.replace('/', '-')
        title = clean_ordering_numbers_from_path(f).rsplit('.')[0]

        path = dst_filename.rsplit('.', 1)[0]


        shutil.copy(src, Path(wikiroot, dst_filename))

        skip_files = ['Home.md', '_Footer.md', '_Sidebar.md', 'index.md']

        if str(f) in skip_files:
            continue

        with open(src) as infile:
            firstline = infile.readline()
            if len(firstline) > 0:
                if firstline[0] == '#':
                    title = firstline[1:].strip()
                    print(title)

        toc.append({'depth': depth, 'title': title, 'path': path, 'is_dir': False})

tocstring = ''

for item in toc:
    if item['is_dir']:
        for _ in range(item['depth']):
            tocstring += '  '
        if item['path'] != None:
            tocstring += f'* [{item["title"]}]' + f'({item["path"]})'.replace(' ', '-')
        else:
            tocstring += f'* **{item["title"]}**'
    else:
        for _ in range(item['depth']):
            tocstring += '  '
        tocstring += f'* [{item["title"]}]' + f'({item["path"]})'.replace(' ', '-')
    tocstring += '\n'

with open(Path(wikiroot, '_Sidebar.md'), 'w') as outfile:
    outfile.write(tocstring)

with open(Path(wikiroot, '_Footer.md'), 'w') as outfile:
    pass

with open(Path(wikiroot, 'Home.md'), 'w') as outfile:
    outfile.write(tocstring)

print("Clean the wiki repo...")
subprocess.run(f'rm -rf wiki_repo/*', shell=True)

print("Copy the files in to the wiki repo...")
subprocess.run(f'cp wiki/* wiki_repo', shell=True)

# Commit the wiki repo
print("Commit the updates...")
subprocess.run(f'git config --global user.name "Github Actions"', shell=True, capture_output=True)
subprocess.run(f'git config --global user.email actions@github.com', shell=True, capture_output=True)
subprocess.run(f'git -C "./wiki_repo" add -A', shell=True, capture_output=True)
subprocess.run(f'git -C "./wiki_repo" commit -m "Github action commit"', shell=True, capture_output=True)
subprocess.run(f'git -C "./wiki_repo" push ', shell=True, capture_output=True)
