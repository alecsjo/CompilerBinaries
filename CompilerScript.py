#!/usr/bin/python3

import requests
import base64
import json
import re
import os
from os import path
import subprocess
import json
import sys
import shutil

def compile_binaries(url):
    # Getting the hash commits from the github URL. This reads any new updates to txt file
    page = requests.get(url)

    # Gets the Operating System of the computer you're running on
    current_platform = sys.platform
    print(current_platform)
    current_dir = os.getcwd()
    os.chdir(current_dir)

    # Iterating through each line from github URL. Parses the hash commits and inputs into hashCommits
    hashCommits = {}
    for line in page.iter_lines():
        if line:
            hash = re.search('commit.(.+?).js', line.decode('utf-8'))
            version = re.search('soljson-(.+?).+commit', line.decode('utf-8'))
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
    solidity_dir = current_dir + '/solidity'
    # Checks whether the Solidity Folder exists
    if not os.path.exists(solidity_dir):
        try:
            # subprocess.Popen(['git clone --recursive https://github.com/ethereum/solidity.git'], cwd=current_dir).communicate()
            os.system('git clone --recursive https://github.com/ethereum/solidity.git')
        except:
            print("couldn't clone the solidity repository!")

    # Helper script which installs all required external dependencies on macOS, Windows and on numerous Linux distros.
    try:
        if current_platform in {'linux','darwin'}:
            subprocess.Popen(['./scripts/install_deps.sh'], cwd=solidity_dir).communicate()
        else:
            # This is for Windows
            subprocess.Popen(['scripts\install_deps.bat'], cwd=solidity_dir).communicate()

    except:
        print("Couldn't download external dependencies")

    # Need this to create/upload releases

    # 2. Updates a local JSON file pointing to where the compiled artifact will be located when built and uploaded
    # Loops through each hash commmit and checkout to change the directory
    for hash in hashCommits.keys():
        # Checks if the current hash commit has already been compiled
        if (hash in finishedHashCommits.keys()) and (current_platform in finishedHashCommits[hash]["targets"].keys()):
            continue

        # This checks out each specific hash commit
        try:
            os.chdir(solidity_dir)
            # subprocess.call('git checkout -f ' + hash, shell = True)
            os.system('git checkout -f ' + hash)

            print("CHECKPOINT 1 " + hash)
        except:
            print("couldn't checkout this hash:" + hash)
            continue

        # Command line script that builds the binary
        try:
            #Note: this will install binaries solc and soltest at usr/local/bin
            if current_platform in {'linux','darwin'}:
                subprocess.Popen(['./scripts/build.sh'], cwd=solidity_dir).communicate()
            else:
                # This is for Windows!
                subprocess.Popen(['cmake --build . --config Releasecmake --build . --config Release'], cwd=solidity_dir).communicate()
            print("CHECKPOINT 2 " + hash)
        except:
            print("couldn't build binary for" + hash)
            continue

        print("CHECKPOINT 3 " + hash)
        # After the binary is created, it's OS and hash are written to the JSON'd FinishedCompilers.txt so it's not built again
        os.chdir(current_dir)
        solc_tag = 'solc-'+current_platform+'-'+hash
        repository = 'alecsjo/Binary-Compiler/releases/download/'
        if hash not in finishedHashCommits.keys():
            finishedHashCommits[hash] = {
                "version": hashCommits[hash],
                "full_version": hashCommits[hash] + "-" + hash,
                "targets": {
                    current_platform: "https://github.com/"+ repository + solc_tag + '/'+ solc_tag
                }
            }
        else:
            finishedHashCommits[hash]['targets'][current_platform] = "https://github.com/"+ repository + solc_tag + '/'+ solc_tag

        with open('FinishedCompilers.txt', 'w') as f:
            json.dump(finishedHashCommits, f, ensure_ascii=False)
        # 3.Creates a git commit detailing the new binary being added
        COMMIT_MESSAGE = "'"+'Finished building ' + solc_tag + "'"
        try:
            os.chdir(current_dir)
            # Stage the file
            # subprocess.call('git add FinishedCompilers.txt', shell = True)
            os.system('git add FinishedCompilers.txt')
            # Add your commit
            # subprocess.call('git commit -m ',COMMIT_MESSAGE, shell = True)
            os.system('git commit -m '+ COMMIT_MESSAGE)
            # Push the new or update files
            # subprocess.call('git push origin workBranch', shell = True)
            os.system('git push origin master')

        except:
            print('Some error occured while pushing the code')
            continue

        # 5. Uses the github api to create a new release and upload the binary to the release page
        try:
            # Moving the file into my Folder
            src = '/usr/local/bin/solc'
            dst = current_dir
            shutil.copy(src, dst)
            # Changing the name to have the platform and hash
            os.rename('solc',solc_tag)
            os.chdir(current_dir)
            os.environ["GITHUB_TOKEN"] = "d08f994212" + "a61b332bb8e1c8bb" + "54293fee9de2cd"
            message = 'githubrelease release alecsjo/Binary-Compiler create '+ solc_tag + ' --publish --name '+ '"' + solc_tag + '"' +' '+ '"'+solc_tag+'"'
            # subprocess.call(message, shell = True)
            os.system(message)
        except:
            print('Some error occured while creating the release')

if __name__ == '__main__':
    # 1. Reads from https://github.com/ethereum/solc-bin/blob/gh-pages/bin/list.txt
    url = 'https://raw.githubusercontent.com/ethereum/solc-bin/gh-pages/bin/list.txt'
    compile_binaries(url)
