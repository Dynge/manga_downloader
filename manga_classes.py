import requests
import subprocess
import platform
import more_itertools as mit
from bs4 import BeautifulSoup
import re
import os
import logging
import math
import sys


def secure_url(url: str):
    """
    sometimes an image source can be relative
    if it is provide the base img_url which also happens
    to be the site variable atm.
    """
    logging.debug(url)
    _source_site = "https://www.mangareader.net/"
    if "http" not in url:
        return "{}{}".format(_source_site, url)
    else:
        return url


class WebPage:
    def __init__(self, url):
        """Initializing a WebPage Object. The WebPage object consists of a parsed HTML object."""
        self.parse_page(url)

    def parse_page(self, url):
        """Parses the raw page to html elements"""
        request = requests.get(secure_url(url))
        self.url = request.url
        self.status = request.status_code
        self.html = BeautifulSoup(request.text, "html.parser")


class Page:
    def __init__(self, img_html):
        """Initialize a Page. The page has a title and source link"""
        self.source = img_html["src"]
        self.title = img_html.get("alt")

    def download_page(self, folder_location):
        if not os.path.exists(folder_location):
            os.makedirs(folder_location)
        filename = "{}/{}.jpg".format(folder_location, self.title)
        try:
            response = requests.get(self.clean_image_source(self.source), timeout=5)
            with open(filename, "wb+") as f:
                f.write(response.content)
                response.close()
            self.timeout = False
        except:
            self.timeout = True

    def clean_image_source(self, image_src):
        if "http" not in image_src:
            return "{}{}".format("https:", image_src)
        else:
            return image_src


class Chapter:
    def __init__(self, name: int, url: str):
        """Initialize a Chapter with a name and url link. An empty list of pages is also created."""
        self.name = name
        self.url = url
        self.web = WebPage(self.url)
        self.pages = []

    def add_page(self, page):
        """Add a page to the list of pages."""
        self.pages.append(page)

    def collect_pages(self):
        """Find all images from the chapter and append them to the pages of the chapter."""
        logging.info("Collecting pages for chapter {}".format(self.name))
        page_count = 0
        imgs = []
        while True:
            page_count += 1
            page_url = "{}{}{}".format(self.url, "/", page_count)
            logging.debug("Page Url: {}".format(page_url))
            page = WebPage(page_url)
            imgs.append(page.html.find(class_="mI").find("img"))
            if page.status != 200 or page.url != page_url:
                break
        for img in imgs:
            self.add_page(Page(img))


class Manga:
    def __init__(self, name, url):
        """Initialize a Manga object. The manga consists of a name, a url link aswell as an empty list of chapters."""
        self.url = url
        self.name = name
        self.web = WebPage(url)
        self.load_already_downloaded()
        self.chapter_names = self.get_chapter_names()
        self.chapters = []

    def add_chapter(self, chapter: Chapter):
        """Adds a chapter to the list of chapters"""
        self.chapters.append(chapter)

    def get_chapter_names(self):
        logging.info("Retrieving all the chapter names from {}...".format(self.name))
        manga_a_htmls = self.web.html.find(class_="d48").find_all("a")
        return [a_html.string for a_html in manga_a_htmls]

    def collect_chapters(self, already_downloaded=None):
        """Reads the Manga main HTML page and finds the chapters, their respective names and the links."""
        manga_a_htmls = self.web.html.find(class_="d48").find_all("a")
        chapter_info = {
            int(re.findall(r"\d{1,4}", a_html.string)[0]): secure_url(
                a_html.get("href")
            )
            for a_html in manga_a_htmls
            if int(re.findall(r"\d{1,4}", a_html.string)[0]) not in already_downloaded
        }

        [self.add_chapter(Chapter(name, link)) for name, link in chapter_info.items()]

    def load_already_downloaded(self):
        log_folder = "Logs"
        log_file = "{}/{}.log".format(log_folder, self.name)
        logging.debug("Logging folder: {}".format(log_file))
        if os.path.exists(log_file):
            logged_chapters = []
            with open(log_file, "r") as f:
                for line in f.readlines():
                    logged_chapters.append(int(line))
            self.already_downloaded = logged_chapters
        else:
            self.already_downloaded = []

    def download_new_chapters(self, kindle_convert=True):
        self.collect_chapters(self.already_downloaded)
        n_chunks = math.ceil(len(self.chapters) / 10)
        chunks = [list(c) for c in mit.divide(n_chunks, self.chapters)]

        bundle_names = [
            "{}/{} {} to {}".format(
                self.name,
                self.name,
                chunk[0].name,
                chunk[-1].name,
            )
            for chunk in chunks
        ]
        logging.info("Downloading the following chunks: {}".format(bundle_names))

        self.downloaded_bundles = []
        for name, chunk in zip(bundle_names, chunks):
            logging.info("Collecting pages for the chunk: {}".format(name))
            [chapter.collect_pages() for chapter in chunk]
            logging.info("Downloading pages for the chunk: {}".format(name))
            [page.download_page(name) for chapter in chunk for page in chapter.pages]
            timeout_pages = [
                page
                for chapter in chunk
                for page in chapter.pages
                if page.timeout == True
            ]
            while len(timeout_pages) > 0:
                logging.info(
                    "Trying to download these pages again: {}".format(
                        [page.title for page in timeout_pages]
                    )
                )
                [page.download_page(name) for page in timeout_pages]
                timeout_pages = [page for page in timeout_pages if page.timeout == True]
            if kindle_convert:
                KindleConverter(self, name)
            self.downloaded_bundles.append(name)


class Searcher:
    def __init__(self, query: str):
        query_underscore = re.sub(" ", "+", query)
        self.web = WebPage(
            "https://www.mangareader.net/search/?nsearch=" + query_underscore
        )
        self.mangas = self.search_results()

    def search_results(self):
        result_htmls = self.web.html.find(class_="d52").find_all("a")
        logging.debug(result_htmls)
        results = {
            result_html.string: secure_url(result_html.get("href"))
            for result_html in result_htmls
        }
        logging.debug(results)
        return results


class KindleConverter:
    def __init__(self, mangaobject, folder):
        self.log_folder = "Logs"
        self.log_file = "{}/{}.log".format(self.log_folder, mangaobject.name)
        self.convert_to_mobi(folder)
        self.log_downloaded_chapters(mangaobject, folder)
        self.remove_image_folder(folder)

    def convert_to_mobi(self, folder):
        subprocess.call(
            ["kcc-c2e", folder, "-u", "-m", "-r", "1", "-p", "K578", "-b", "2"]
        )

    def remove_image_folder(self, folder):
        logging.debug(folder)
        if platform.system() == "Linux":
            subprocess.call(["rm", "-rf", folder])
        elif platform.system() == "Windows":
            subprocess.call(["rmdir", "/S/Q", folder], shell=True)

    def log_downloaded_chapters(self, mangaobject, folder):
        """
        Function to document that a chapter has been succesfully installed.
        """
        if not os.path.exists(self.log_folder):
            os.mkdir(self.log_folder)

        with open(self.log_file, "a") as f:
            chapter_range = re.findall(r"\d{1,4}", folder)
            for chapter in range(int(chapter_range[0]), int(chapter_range[1]) + 1):
                f.write("{}\n".format(chapter))


if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO)

    """ Inputs search term and finds matches """
    search_term = input("Write the anime to search for: ")
    logging.info('Search term input by user was "%s".' % search_term)

    search = Searcher(search_term)

    if len(search.mangas) < 1:
        logging.info("No matches.")
        sys.exit()

    """ Inputs match index and downloads new chapters """
    manga_keys = list(search.mangas.keys())
    match_index = int(
        input(
            "Found the following %s matche(s).\n %s \nPlease select one by indexing it (starting from 0): "
            % (
                len(search.mangas),
                [(i, match) for i, match in enumerate(manga_keys)],
            )
        )
    )
    logging.info('Index input by user was "%s".' % match_index)

    desired_manga = list(manga_keys)[match_index]
    manga_object = Manga(desired_manga, search.mangas[desired_manga])

    if len(manga_object.chapter_names) == len(manga_object.already_downloaded):
        logging.info("No new chapters.")
        sys.exit()
    else:
        manga_object.download_new_chapters()
