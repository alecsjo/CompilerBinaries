#!/usr/bin/python

import requests
import base64
import json
import re
from git import Repo
import os
import subprocess
import json

def compile_binaries(url):
    # Getting the hash commits from the github URL. This reads any new updates to txt file
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
    current_dir = os.getcwd()
    if os.path.isfile("FinishedCompilers.txt"):
        with open("FinishedCompilers.txt", "r") as ifile:
            line = ifile.readline()
            while line:
                finishedHashCommits.append(line.strip())
                line = ifile.readline()
    else:
        # Creates a new txt file if it doesn't exist
        open('FinishedCompilers.txt', 'w').close()

    # Should I be cloning the whole solidity file into my repo? (FIXME)
    # Cloning the Solidity github repository if not already created and stores it into the Solidity Folder
    git_url = 'https://github.com/ethereum/solidity.git'
    repo_dir = current_dir + '/Solidity'

    # Checks whether the Solidity Folder exists
    if not os.path.exists(repo_dir):
        os.makedirs(repo_dir)
    # Checks whether it's been cloned/empty
    if not os.listdir(repo_dir):
        Repo.clone_from(git_url, repo_dir)

    # # Initialize the Repo (Don't know if I need this)
    repo = Repo(current_dir)

    # # Helper script which installs all required external dependencies on macOS, Windows and on numerous Linux distros.
    os.system('cd Solidity')
    os.system('./scripts/install_deps.sh')

    # 2. Updates a local json file pointing to where the compiled artifact will be located when built and uploaded
    # Loop through each hash commmit and checkout to change the directory
    for hash in hashCommits:
        if hash not in finishedHashCommits:
            # This checks out each specific hash commit
            if os.getcwd() != repo_dir:
                os.system('cd Solidity')
            repo.git.checkout(hash)
    
            # Build the binary
            new_path = repo_dir + '/build'
            if not os.path.exists(new_path):
                os.makedirs(build)
            os.system('cd build')
            os.system('cmake .. && make')

            # # 3.Creates a git commit detailing the new binary being added
            # PATH_OF_GIT_REPO = current_dir  # make sure .git folder is properly configured
            # COMMIT_MESSAGE = "Finished building" + hash
            # try:
            #     repo = Repo(PATH_OF_GIT_REPO)
            #     repo.git.add(update = True)
            #     repo.index.commit(COMMIT_MESSAGE)
            #     origin = repo.remote(name='origin')
            #     # 4.Pushes to github
            #     origin.push()
            # except:
            #     print('Some error occured while pushing the code')
            # # 5. Uses the github api to create a new release and upload the binary to the release page

            # After the binary is created, hash commit is written to FinishedCompilers.txt so it's not built again
            os.system('cd ..')
            with open('FinishedCompilers.txt', 'w') as f:
                f.write(hash + '\n')

if __name__ == '__main__':
    # 1. Reads from https://github.com/ethereum/solc-bin/blob/gh-pages/bin/list.txt
    url = 'https://raw.githubusercontent.com/ethereum/solc-bin/gh-pages/bin/list.txt'
    compile_binaries(url)
