#!/usr/bin/python

import requests
import base64
import json
import re
from git import Repo
import os
import subprocess
import json
import sys
from github_release import gh_release_create

if __name__ == '__main__':
    # 1. Reads from https://github.com/ethereum/solc-bin/blob/gh-pages/bin/list.txt
    url = 'https://raw.githubusercontent.com/ethereum/solc-bin/gh-pages/bin/list.txt'
    compile_binaries(url)

def compile_binaries(url):
    # Getting the hash commits from the github URL. This reads any new updates to txt file
    page = requests.get(url)
    # Gets the Operating System of the computer you're running on
    current_platform = get_platform()
    current_dir = os.getcwd()

    # Iterating through each line from github URL. Parses the hash commits and inputs into hashCommits
    hashCommits = {}
    for line in page.iter_lines():
        if line:
            hash = re.search('commit.(.+?).js', line)
            version = re.search('soljson-(.+?).+commit', line)
            if hash and version:
                hash_found = hash.group(1)
                version_found = version.group(1)
                hashCommits[hash_found] = version_found

    # A JSON text file is used to track the hash commits that I've already downloaded
    # The JSON contains a dictionary that currently holds the Operating System + Hash commit as the key, and release URL as the value
    if os.path.isfile("FinishedCompilers.txt"):
        with open('FinishedCompilers.txt') as json_file:
            try:
                finishedHashCommits = json.load(json_file)
            except:
                finishedHashCommits = {}
    else:
        # Creates a new JSON text file if it doesn't exist
        open('FinishedCompilers.txt', 'w').close()
        finishedHashCommits = {}

    # Cloning the Solidity github repository if not already created and stores it into the Solidity Folder
    git_url = 'https://github.com/ethereum/solidity.git'
    solidity_dir = current_dir + '/Solidity'

    # Checks whether the Solidity Folder exists
    if not os.path.exists(solidity_dir):
        os.makedirs(solidity_dir)
    # Checks whether it's already been cloned/empty
    if not os.listdir(solidity_dir):
        Repo.clone_from(git_url, solidity_dir)

    # # Helper script which installs all required external dependencies on macOS, Windows and on numerous Linux distros.
    p = subprocess.Popen(['./scripts/install_deps.sh'], cwd=solidity_dir)
    p.wait()

    # 2. Updates a local JSON file pointing to where the compiled artifact will be located when built and uploaded
    # Loops through each hash commmit and checkout to change the directory
    for hash, version in hashCommits:
        # Checks if the current hash commit has already been compiled
        if (hash not in finishedHashCommits.keys()) or (current_platform not in finishedHashCommits[hash][targets].keys()):
            # This checks out each specific hash commit
            try:
                repo = Repo(solidity_dir)
                repo.git.checkout(hash)
            except:
                print("couldn't checkout this hash:" + hash)

            #Note: this will install binaries solc and soltest at usr/local/bin
            p = subprocess.Popen(['./scripts/build.sh'], cwd=solidity_dir)
            p.wait()

            # After the binary is created, the operating system + hash commit is written to the JSON'd FinishedCompilers.txt so it's not built again
            if hash not in finishedHashCommits.keys():
                finishedHashCommits{hash} = {
                    "version": version,
                    "full_version": version + "-" + hash,
                    "targets": {
                        current_platform: "https://github.com/alecsjo/Binary-Compiler/releases/tag/" + current_platform + hash
                    }
                }
            else:
                finishedHashCommits[hash][targets].append(
                    current_platform: "https://github.com/alecsjo/Binary-Compiler/releases/tag/" + current_platform + hash
                )

            with open('FinishedCompilers.txt', 'w') as outfile:
                json.dump(finishedHashCommits, outfile)

            # 3.Creates a git commit detailing the new binary being added
            COMMIT_MESSAGE = "Finished building " + current_platform + hash
            try:
                if os.getcwd() != current_dir:
                    os.chdir(current_dir)
                # Stage the file
                subprocess.call('git add -A', shell = True)
                # Add your commit
                subprocess.call('git commit -m "'+ COMMIT_MESSAGE +'"', shell = True)
                # Push the new or update files
                subprocess.call('git push origin workBranch', shell = True)
            except:
                print('Some error occured while pushing the code')

            # 5. Uses the github api to create a new release and upload the binary to the release page
            # Github only takes ZIP files, so I need to zip the binary first before
            gh_release_create(current_platform + hash, "2.0.0", publish=True, name=(current_platform + hash), asset_pattern="usr/local/bin/solc")

# This function gets the Operating System of the current computer
def get_platform():
    platforms = {
        'linux1' : 'Linux',
        'linux2' : 'Linux',
        'darwin' : 'OS X',
        'win32' : 'Windows'
    }
    if sys.platform not in platforms:
        return sys.platform
    return platforms[sys.platform]
