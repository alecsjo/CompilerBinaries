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
# Different Servers may need to download this
from github_release import gh_release_create


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
        with open('FinishedCompilers.txt') as json_file:
            try:
                finishedHashCommits = json.load(json_file)
            except:
                finishedHashCommits = {}
                finishedHashCommits[get_platform()] = []
    else:
        # Creates a new txt file if it doesn't exist
        open('FinishedCompilers.txt', 'w').close()
        finishedHashCommits = {}
        finishedHashCommits[get_platform()] = []

    # Cloning the Solidity github repository if not already created and stores it into the Solidity Folder
    git_url = 'https://github.com/ethereum/solidity.git'
    solidity_dir = current_dir + '/Solidity'

    # Checks whether the Solidity Folder exists
    if not os.path.exists(solidity_dir):
        os.makedirs(solidity_dir)
    # Checks whether it's been cloned/empty
    if not os.listdir(solidity_dir):
        Repo.clone_from(git_url, solidity_dir)

    # # Helper script which installs all required external dependencies on macOS, Windows and on numerous Linux distros.
    p = subprocess.Popen(['./scripts/install_deps.sh'], cwd=solidity_dir)
    p.wait()

    # 2. Updates a local json file pointing to where the compiled artifact will be located when built and uploaded
    # Loop through each hash commmit and checkout to change the directory
    for hash in hashCommits:
        if (get_platform()+hash) not in finishedHashCommits.keys():
            # This checks out each specific hash commit
            if os.getcwd() != solidity_dir:
                os.chdir(solidity_dir)
            try:
                repo = Repo(solidity_dir)
                repo.git.checkout(hash)
            except:
                print("couldn't checkout this hash!")

            #note: this will install binaries solc and soltest at usr/local/bin
            p = subprocess.Popen(['./scripts/build.sh'], cwd=solidity_dir)
            p.wait()

            # After the binary is created, the operating system + hash commit is written to the JSON'd FinishedCompilers.txt so it's not built again
            finishedHashCommits[get_platform()+hash] = "URL: dont know yet"

            with open('FinishedCompilers.txt', 'w') as outfile:
                json.dump(finishedHashCommits, outfile)

            # 3.Creates a git commit detailing the new binary being added
            COMMIT_MESSAGE = "Finished building " + get_platform() + hash
            try:
                if os.getcwd() != current_dir:
                    os.chdir(current_dir)
                #Stage the file
                subprocess.call('git add -A', shell = True)
                # Add your commit
                subprocess.call('git commit -m "'+ COMMIT_MESSAGE +'"', shell = True)
                #Push the new or update files
                subprocess.call('git push origin workBranch', shell = True)
            except:
                print('Some error occured while pushing the code')


            # # 5. Uses the github api to create a new release and upload the binary to the release page
            # This is how you create a release
            gh_release_create("usr/local/bin", "2.0.0", publish=True, name="Awesome 2.0", asset_pattern="dist/*")

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

if __name__ == '__main__':
    # 1. Reads from https://github.com/ethereum/solc-bin/blob/gh-pages/bin/list.txt
    url = 'https://raw.githubusercontent.com/ethereum/solc-bin/gh-pages/bin/list.txt'
    compile_binaries(url)
