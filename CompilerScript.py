#!/usr/bin/python

import requests
import base64
import json
import re
from git import Repo
import os
import subprocess

# 1. Reads from https://github.com/ethereum/solc-bin/blob/gh-pages/bin/list.txt

# Getting the hash commits from the github URL. This reads any new updates to txt file
url = 'https://raw.githubusercontent.com/ethereum/solc-bin/gh-pages/bin/list.txt'
page = requests.get(url)

# Iterating through each line and storing the hash commits into hashCommits
hashCommits = []
for line in page.iter_lines():
    if line:
        m = re.search('commit.(.+?).js', line)
        if m:
            found = m.group(1)
            hashCommits.append(found)

# A text file is used to track the hash commits that I've already downloaded
finishedHashCommits = []
current_dir = '/Users/alec/Desktop/MerkleX/Binary-Compiler' #Change it so it's not hardcoded (FIXME)
# current_ dir = os.getcwd()
os.chdir(current_dir)
if os.path.isfile("FinishedCompilers.txt"):
    with open("FinishedCompilers.txt", "r") as ifile:
        line = ifile.readline()
        while line:
            finishedHashCommits.append(line.strip())
            line = ifile.readline()
else:
    # Creates a new txt file if it doesn't exist
    open('FinishedCompilers.txt', 'w').close()





# Initialize the Repo (Don't know if I need this)
repo = Repo.init(current_dir).git
index = Repo.init(current_dir).index

# I shouldn't be cloning the whole solidity repo into my repo (FIXME)
# Cloning the Solidity github repository if not already created and stores it into the Solidity Folder
git_url = 'https://github.com/ethereum/solidity.git'
repo_dir = '/Users/alec/Desktop/MerkleX/CompilerScript/Solidity' #Change it so it's not hardcoded (FIXME)
if not os.path.exists(repo_dir):
    os.makedirs(repo_dir)
if not os.listdir(repo_dir):
    Repo.clone_from(git_url, repo_dir)

# Change directory into the folder
os.chdir(repo_dir)

# 2. Updates a local json file pointing to where the compiled artifact will be located when built and uploaded
# Loop through each hash commmit and checkout to change the directory
for hash in hashCommits:
    if hash not in finishedHashCommits:
        repo.checkout(hash)
        # Build the binary
        subprocess.run('mkdir build')
        subprocess.run('cd build')
        subprocess.run('cmake .. && make')

        # 3.Creates a git commit detailing the new binary being added
        PATH_OF_GIT_REPO = current_dir  # make sure .git folder is properly configured
        COMMIT_MESSAGE = "Finished building" + hash
        try:
            repo = Repo(PATH_OF_GIT_REPO)
            repo.git.add(update=True)
            repo.index.commit(COMMIT_MESSAGE)
            origin = repo.remote(name='origin')
            # 4.Pushes to github
            origin.push()
        except:
            print('Some error occured while pushing the code')

        # 5. Uses the github api to create a new release and upload the binary to the release page

        # After the binary is created, hash commit is written to FinishedCompilers.txt so it's not built again
        with open(current_dir, 'FinishedCompilers.txt', r) as f:
            f.write(hash + '\n')
