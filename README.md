# Warning
This branch is only for Linux and Mac. Select the *windows* branch if you want to use this script on a Windows machine.

# Manga Downloader
This python script allows you to search for mangas, download chapters and automatically creates a .mobi format file for the manga.

Thus making your manga ready to upload to your Kindle and enjoy.

The manga_updater.py is used to update your currently logged mangas such that you do not need to run the script multiple times to get the latests chapters of your favorite manga.

## Dependencies:
* KCC (source: https://github.com/ciromattia/kcc)
  *  Note: Install KCC with $pip3 install KindleComicConverter 

* Python3
  * Packages: requests, bs4

## Setup
1. First download Python3 and the packages listed in *Dependencies*:

    $ pip3 install <package_name>.  

2. Download KCC with pip

    $ pip3 install KindleComicConverter

3. Download a KindleGen and follow instructions from https://github.com/ciromattia/kcc/wiki/FAQ (*"Why option to create MOBI is not available"*).

4. IF WINDOWS: Place the KindleGen.exe where the kcc-c2e.exe file in is located in your python scripts folder (mine was located in **C:/Users/USER/AppData/Local/Programs/Python/Python37-32/Scripts**)

The script should now be ready to use. 

## Usage:
Simple place the manga_downloader.py file in the parent folder you would like to download the files in. Locate the file in terminal and type:

$ python3 manga_downloader.py

$ python3 manga_updater.py


* manga_updater.py has addtional options. Add **-h** to see the help message.
