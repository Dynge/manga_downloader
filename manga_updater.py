import manga_downloader as md
import logging
import os
import re
import sys
import argparse
import numpy as np

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Script to update your kindle mangas.")
    parser.add_argument("-a", "--all", action="store_true",
                        help="Used to automatically update all.")
    parser.add_argument("-cs", "--chunk_size", default=False,
                        type=int, nargs=1, help="Used to specify chunk size for all updateable mangas.")

    args = parser.parse_args()

    THIS_PATH = os.path.dirname(os.path.realpath(__file__))
    LOG_FORMAT = "%(levelname)s %(asctime)s - %(message)s"
    logging.basicConfig(
        #filename=os.path.join(THIS_PATH, "manga_updater.log"),
        level=logging.INFO,
        format=LOG_FORMAT,
        filemode='a')
    logger = logging.getLogger()

    mangas_to_update = [re.sub(r".log", "", manga_log)
                        for manga_log in os.listdir(md.LOG_FOLDER)]
    logger.info("Mangas to update \n%s" % mangas_to_update)
    logger.info("Finding the list of chapters for your mangas...")
    search_results = [md.searchForAnime(manga) for manga in mangas_to_update]
    logger.debug("Search Results \n%s" % search_results)
    exact_matches = [
        match for manga in search_results for match in manga if match[1] in mangas_to_update]
    logger.debug("Exact Matches \n%s" % exact_matches)

    chapters_pr_manga = [md.listChapters(
        md.SOURCE_LINK + manga[0]) for manga in exact_matches]
    logger.debug("Listed chapters of size %s" % len(chapters_pr_manga))
    logger.info("Checking your mangas for new chapters...")

    updateable_mangas = list()
    for i, manga in enumerate(exact_matches):
        new_chapters = md.checkForNewChapter(chapters_pr_manga[i], manga[1])
        if len(new_chapters) > 0:
            logger.info("%s new chapter(s) for manga titled: %s" %
                  (len(new_chapters), manga[1]))
            updateable_mangas.append((manga[1], new_chapters))
        else:
            logger.info("No new chapters for manga titled: %s" % manga[1])
    if not updateable_mangas:
        logger.info("Exiting script as there is no mangas to update.")
        sys.exit()
    if args.all == True:
        for manga, new_chapters in updateable_mangas:
            chunks = args.chunk_size
            if not chunks:
                chunks = int(input("%s new chapter(s) for manga titled: %s\nSelect the amount of chunks to split this into: " % (
                    len(new_chapters), manga)))
            logger.info("Downloading %s chapter(s) for manga titled: %s\n" % (
                len(new_chapters), manga))
            md.download_chapters(manga, new_chapters, chunks)
    else:
        manga_index_str = input("Select the manga(s) to update by space-separated index: \n%s\n" % [(i, manga[0]) for i, manga in enumerate(updateable_mangas)])
        manga_index = map(int, manga_index_str.split(" "))
        for index in manga_index:
            chunks = args.chunk_size
            if not chunks:
                chunks = int(input("%s new chapter(s) for manga titled: %s\nSelect the amount of chunks to split this into: " % (
                    len(updateable_mangas[index][1]), updateable_mangas[index][0])))
            logger.info("Downloading %s chapter(s) for manga titled: %s\n" % (
                len(updateable_mangas[index][1]), updateable_mangas[index][0]))
            md.download_chapters(updateable_mangas[index][0], updateable_mangas[index][1], chunks)   
    
    logger.info("Finished updating your mangas.")
