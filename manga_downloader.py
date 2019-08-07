from subprocess import call
import requests
import math
from bs4 import BeautifulSoup
import re
import logging
import os
import glob
import sys

""" Function used in the script """
def parsePage(html_string):
    """Parses the raw page to html elements"""
    return BeautifulSoup(html_string, 'html.parser')


def listChapters(url):
    """
    Function to list the chapters of the given manga page.
    """
    html = requests.get(url)
    parsed_html = parsePage(html.text)
    listing = parsed_html.find(id='listing')
    chapters = [(SOURCE_LINK + str(link.get('href')), link.string)
                for link in listing.find_all('a')]
    return chapters


def checkForNewChapter(chapter_list, manga_name):
    """
    Compares the list created by listChapters with the directory and returns the chapters that has not been downloaded.
    """
    manga_documentation_file = LOG_FOLDER + manga_name + ".log"
    
    if os.path.exists(manga_documentation_file):
        f = open(manga_documentation_file, "r")
        downloaded_chapters = list(map(lambda chapter: re.sub(r"\n$", "", chapter), f.readlines()))

        f.close()
        new_chaps = [
            chapter for chapter in chapter_list if chapter[1] not in downloaded_chapters
        ]
    else:
        new_chaps = chapter_list
    return new_chaps


def download_chapter_page_return_link(url, chapter, folder):
    chapter = re.sub(regex_chapter_number, "", chapter.lower())
    html = requests.get(url)
    parsed_pages = parsePage(html.text)

    img_html = parsed_pages.img
    saveImage(img_html, folder)

    img_link = img_html.parent.get('href')
    return (img_link)


def saveImage(img_tag, image_location):
    """Retrieves the img source and extracts the images and saves to file directory"""

    img_url = img_tag['src']
    if not os.path.exists(image_location):
        os.makedirs(image_location)
    filename = image_location + "/" + img_tag.get('alt') + ".jpg"
    with open(filename, 'wb+') as f:
        if 'http' not in img_url:
            # sometimes an image source can be relative
            # if it is provide the base img_url which also happens
            # to be the site variable atm.
            img_url = '{}{}'.format(SOURCE_LINK, img_url)
        response = requests.get(img_url)
        f.write(response.content)


def document_downloaded_chapter(manga_name, chapter_name):
    """
    Function to document that a chapter has been succesfully installed.
    """
    if not os.path.exists(LOG_FOLDER):
        os.mkdir(LOG_FOLDER)
    
    manga_documentation_file = LOG_FOLDER + manga_name + ".log"
    f = open(manga_documentation_file, "a")
    f.write(chapter_name + "\n")
    f.close()


def nextPageLink(img_link, chapter):
    """
    Checks if next page is still current chapter and then creates link if so.
    Else it returns False
    """
    chapter = re.sub(regex_chapter_number, "", chapter)
    if "/%s/" % chapter in img_link:
        next_page = SOURCE_LINK + img_link
        return (next_page)
    else:
        return (False)


def searchForAnime(manga_name):
    """
    Function to search the mangareader site for link to a specific anime.
    """
    manga_list_url = "https://www.mangareader.net/alphabetical"
    page = requests.get(manga_list_url)
    parsed_page = parsePage(page.text)
    links = parsed_page.find_all('a')
    link_names = [link.string for link in links]
    matches = []
    for i, j in enumerate(link_names):
        if j != None and manga_name.lower() in j.lower():
            matches.append((links[i].get('href'), j))
            
    return matches

def determineStartEndChapters(chunks, new_chapters, chunk_index):
    chunk_start_index = chunks[chunk_index]
    chunk_end_index = chunks[chunk_index + 1] - 1
    chapter_start = re.sub(regex_chapter_number, "", new_chapters[chunk_start_index][1])
    chapter_end = re.sub(regex_chapter_number, "", new_chapters[chunk_end_index][1])
    return (chapter_start, chapter_end)

def calculateChapterIndex(amount_of_new_chapters, chunk_amount):
    """
    Creates a list of index's for the chapter folder index's.
    Each entry in the list is the starting chapter.
    If chunk_amount == -1 every chapter will get seperate folders
    """
    if chunk_amount == -1:
        chunks = [i for i in range(0, amount_of_new_chapters, 1)]
        chunks.append(amount_of_new_chapters)
        return(chunks)
    folder_size_floored = math.floor(amount_of_new_chapters / chunk_amount)
    residual_size = amount_of_new_chapters % chunk_amount
    chunks = [x for x in range(0, amount_of_new_chapters, folder_size_floored)]
    if len(chunks) > chunk_amount:
        del chunks[-1]
    residuals_per_chunk = math.ceil(residual_size / len(chunks))

    chunk_index = len(chunks) - 1

    while residual_size > 0:
        chunks[chunk_index] += residual_size - residuals_per_chunk
        residual_size -= residuals_per_chunk
        chunk_index -= 1

    chunks.append(amount_of_new_chapters)
    return(chunks)

def download_chapters(manga_title, chapters, chunks):
    """
    Input of chapters and chunks to begin the download of the new chapters and split it into the selected chunk amount.
    """
    chunk_chapter_indexs = calculateChapterIndex(len(chapters), chunks)
    chunk_index = 0

    for i, chapter in enumerate(chapters):
        logger.info("Downloading %s. %s chapters remaining" %
            (chapter[1], len(chapters) - (i + 1)))
        current_chapter_number = int(re.sub(regex_chapter_number, "", chapter[1]))
        chapter_start, chapter_end = determineStartEndChapters(chunk_chapter_indexs, chapters, chunk_index)
        if current_chapter_number > int(chapter_end):
            chunk_index += 1
            chapter_start, chapter_end = determineStartEndChapters(chunk_chapter_indexs, chapters, chunk_index)
        folder_name = "%s/%s (%s - %s)" % (manga_title,
                                        manga_title, chapter_start, chapter_end)
        img_link = download_chapter_page_return_link(
            chapter[0], chapter[1], folder_name)
        next_page = nextPageLink(img_link, chapter[1])
        while type(next_page) == str:
            img_link = download_chapter_page_return_link(
                next_page, chapter[1], folder_name)
            next_page = nextPageLink(img_link, chapter[1])
        document_downloaded_chapter(manga_title, chapter[1])
        if current_chapter_number == int(chapter_end):
            convertToKindleAndCleanup(folder_name)


def convertToKindleAndCleanup(volume_folder):
    call(["kcc-c2e", volume_folder, "-u", "-m", "-r", "1", "-p", "K578", "-b", "2"])
    call(["rm", "-rf", volume_folder])

LOG_FOLDER = "Logs/"
SOURCE_LINK = 'https://www.mangareader.net'
regex_chapter_number = re.compile(r".*\D+")

if __name__ == "__main__":
    THIS_PATH = os.path.dirname(os.path.realpath(__file__))
    LOG_FORMAT = "%(levelname)s %(asctime)s - %(message)s"
    logging.basicConfig(
        #filename=os.path.join(THIS_PATH, "manga_downloader.log"),
        level=logging.INFO,
        format=LOG_FORMAT,
        filemode='a')
    logger = logging.getLogger()


    """ Inputs search term and finds matches """
    search_term = input("Write the anime to search for: ")
    logger.info('Search term input by user was "%s".' % search_term)

    search_matches = searchForAnime(search_term)

    if len(search_matches) < 1:
        logger.info("No matches.")
        sys.exit()

    """ Inputs match index and downloads new chapters """
    match_index = input(
        "Found the following %s matche(s).\n %s \nPlease select one by indexing it (starting from 0): "
        % (len(search_matches), [(i, match[1])
                                for i, match in enumerate(search_matches)]))
    logger.info('Index input by user was "%s".' % match_index)

    if not re.match("\d+", match_index):
        logger.error("Only numbers allowed as input!")
        sys.exit()

    MANGA_TITLE = search_matches[int(match_index)][1]
    match_anime_page = SOURCE_LINK + search_matches[int(match_index)][0]

    match_anime_chapters = listChapters(match_anime_page)
    new_chapters = checkForNewChapter(match_anime_chapters, MANGA_TITLE)

    if len(new_chapters) < 1:
        logger.info("No new chapters to download.")
        sys.exit()

    chunk_amount = input("The %s new chapter(s) will be seperated into chunks.\n\
Please select the amount of chuncks (max ~50 chapters per chunk is recommended).\n\
Note: -1 will make a chunck for each chapter\n\
Insert amount of chunks: " % len(new_chapters))
    chunk_amount = int(chunk_amount)


    logger.info("Beginning to download chapters...")
    download_chapters(MANGA_TITLE, new_chapters, chunk_amount)



    logger.info("Finished downloading the chapters for the manga: %s." %
                MANGA_TITLE)




