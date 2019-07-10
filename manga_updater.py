import manga_downloader as md
import logging
import os
import re
import numpy as np

if __name__ == "__main__":
    

    THIS_PATH = os.path.dirname(os.path.realpath(__file__))
    LOG_FORMAT = "%(levelname)s %(asctime)s - %(message)s"
    logging.basicConfig(
        filename=os.path.join(THIS_PATH, "manga_updater.log"),
        level=logging.INFO,
        format=LOG_FORMAT,
        filemode='a')
    logger = logging.getLogger()
    

    mangas_to_update = [re.sub(r".log", "", manga_log) for manga_log in os.listdir(md.LOG_FOLDER)]
    logger.info("Mangas to update \n%s" % mangas_to_update)

    search_results = [md.searchForAnime(manga) for manga in mangas_to_update]
    logger.debug("Search Results \n%s" % search_results)
    exact_matches = [match for manga in search_results for match in manga if match[1] in mangas_to_update]
    logger.debug("Exact Matches \n%s" % exact_matches)

    chapters_pr_manga = [md.listChapters(md.SOURCE_LINK + manga[0]) for manga in exact_matches]
    logger.debug("Listed chapters of size %s" % len(chapters_pr_manga))
    print("Checking matches for new chapters...")
    for i, manga in enumerate(exact_matches):
        new_chapters = md.checkForNewChapter(chapters_pr_manga[i], manga[1])
        logger.info("New Chapters for %s\n%s" % (manga[1], new_chapters))
        if len(new_chapters) > 0:
            chunks = int(input("%s new chapter(s) for manga titled: %s\n\
                Select the amount of chunks to split this into: " % (len(new_chapters), manga[1])))
            logger.info("Downloading %s chapter(s) for manga titled: %s\n" % (len(new_chapters), manga[1]))
            md.download_chapters(manga[1], new_chapters, chunks)
        else: 
            logger.info("No new chapters for manga titled: %s" % manga[1])
    print("Finished updating your mangas.")