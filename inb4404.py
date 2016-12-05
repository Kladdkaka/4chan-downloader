#!/usr/bin/python
import requests
import argparse
import logging
import os, re, time
import fileinput
from multiprocessing import Process

log = logging.getLogger('inb4404')
workpath = os.path.dirname(os.path.realpath(__file__))
args = None

media_regex = re.compile('(//i.4cdn.org/\w+/(\d+\.(?:jpg|png|gif|webm)))')


def load(url):
    r = requests.get(url, headers={'User-Agent': '4chan Browser'})
    return r.text


def main():
    global args
    parser = argparse.ArgumentParser(description='inb4404')
    parser.add_argument('thread', nargs=1, help='url of the thread (or filename; one url per line)')
    parser.add_argument('-r', '--reload', action='store_true', help='this reloads the file every 15 minutes')
    parser.add_argument('-v', '--verbose', action='store_true', help='display board/thread as well')
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s', datefmt='%I:%M:%S %p')

    if args.thread[0][:4].lower() == 'http':
        download_thread(args.thread[0])
    else:
        download_from_file(args.thread[0])


def download_thread(thread_link):
    try:
        board = thread_link.split('/')[3]
        thread = thread_link.split('/')[5].split('#')[0]

        directory = os.path.join(workpath, 'downloads', board, thread)
        if not os.path.exists(directory):
            os.makedirs(directory)

        while True:
            try:
                for link, img in list(set(media_regex.findall(load(thread_link)))):
                    img_path = directory + '/' + img
                    if not os.path.exists(img_path):
                        data = load('https:' + link)

                        if not args.verbose:
                            log.info(img)
                        else:
                            log.info(img.ljust(22) + 'at /' + board + '/' + thread)

                        with open(img_path, 'w') as f:
                            f.write(data)

                        ##################################################################################
                        # saves new images to a seperate directory
                        # if you delete them there, they are not downloaded again
                        # if you delete an image in the 'downloads' directory, it will be downloaded again
                        copy_directory = os.path.join(workpath, 'new', board, thread)
                        if not os.path.exists(copy_directory):
                            os.makedirs(copy_directory)
                        copy_path = copy_directory + '/' + img
                        with open(copy_path, 'w') as f:
                            f.write(data)
                        ##################################################################################
            except requests.HTTPError as err:
                print(err)
                time.sleep(10)
                try:
                    load(thread_link)
                except requests.HTTPError as err:
                    print(err)
                    log.info('%s 404\'d', thread_link)
                    break
                continue
            except Exception as err:  # wat
                print(err)
                log.warning('something went wrong')

            if not args.verbose:
                print('.')
            else:
                log.info('Nothing new was found at /' + board + '/' + thread)
            time.sleep(20)
    except KeyboardInterrupt:
        pass


def download_from_file(filename):
    try:
        while True:
            processes = []
            for link in filter(None, [line.strip() for line in open(filename) if line[:4] == 'http']):
                process = Process(target=download_thread, args=(link,))
                process.start()
                processes.append([process, link])
                if args.verbose:
                    log.info('Started: ' + link)

            if args.reload:
                time.sleep(60 * 5)  # 5 minutes
                links_to_remove = []
                for process, link in processes:
                    if not process.is_alive():
                        links_to_remove.append(link)
                    else:
                        process.terminate()

                for link in links_to_remove:
                    for line in fileinput.input(filename, inplace=True):
                        print(line.replace(link, '-' + link))
                    log.info('Marked as dead: ' + link)
                if args.verbose:
                    log.info('Reloading ' + args.thread[0])  # thread = filename in this case
                    # reloading basically happens at the beginning of the while True loop
            else:
                break

    except Exception as e:
        raise e


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
