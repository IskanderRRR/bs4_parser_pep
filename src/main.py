import os
import re
from urllib.parse import urljoin
import logging

import requests_cache
from bs4 import BeautifulSoup
from tqdm import tqdm
from collections import defaultdict

from constants import (MAIN_DOC_URL, PEPS_URL,
                       EXPECTED_STATUS, STATUS_PATTERN,
                       BASE_DIR, DOWNLOADS_SUBDIR,
                       ARCHIVE_PATTERN)
from configs import configure_argument_parser, configure_logging
from outputs import control_output
from utils import get_response, find_tag


def whats_new(session):
    whats_new_url = urljoin(MAIN_DOC_URL, 'whatsnew/')
    response = get_response(session, whats_new_url)
    if response is None:
        return
    soup = BeautifulSoup(response.text, features='lxml')
    main_div = find_tag(soup, 'section', attrs={'id': 'what-s-new-in-python'})
    div_with_ul = find_tag(main_div, 'div', attrs={'class': 'toctree-wrapper'})
    sections_by_python = div_with_ul.find_all(
        'li', attrs={'class': 'toctree-l1'}
    )
    results = [('Ссылка на статью', 'Заголовок', 'Редактор, Автор')]
    for section in tqdm(sections_by_python):
        version_a_tag = find_tag(section, 'a')
        version_link = urljoin(whats_new_url, version_a_tag['href'])
        response = get_response(session, version_link)
        if response is None:
            continue
        soup = BeautifulSoup(response.text, 'lxml')
        h1 = find_tag(soup, 'h1')
        dl = find_tag(soup, 'dl')
        dl_text = dl.text.replace('\n', ' ')
        results.append(
            (version_link, h1.text, dl_text)
        )
    return results


def latest_versions(session):
    response = get_response(session, MAIN_DOC_URL)
    if response is None:
        return
    soup = BeautifulSoup(response.text, 'lxml')
    sidebar = find_tag(soup, 'div', attrs={'class': 'sphinxsidebarwrapper'})
    ul_tags = find_tag(sidebar, 'ul')
    for ul in ul_tags:
        if 'All versions' in ul.text:
            a_tags = find_tag(ul, 'a')
            break
    else:
        raise Exception('Не найден список c версиями Python')
    results = []
    pattern = r'Python (?P<version>\d\.\d+) \((?P<status>.*)\)'
    for a_tag in a_tags:
        link = a_tag['href']
        text_match = re.search(pattern, a_tag.text)
        if text_match is not None:
            version, status = text_match.groups()
        else:
            version, status = a_tag.text, ''
        results.append(
            (link, version, status)
        )
    results = [('Ссылка на документацию', 'Версия', 'Статус')]

    return results


def download(session):
    downloads_url = urljoin(MAIN_DOC_URL, 'download.html')
    response = get_response(session, downloads_url)
    if response is None:
        return
    soup = BeautifulSoup(response.text, 'lxml')
    main_tag = find_tag(soup, 'div', attrs={'role': 'main'})
    table_tag = find_tag(main_tag, 'table', attrs={'class': 'docutils'})
    pdf_a4_tag = find_tag(
                 table_tag, 'a', attrs={'href': re.compile(ARCHIVE_PATTERN)})
    pdf_a4_link = pdf_a4_tag['href']
    archive_url = urljoin(downloads_url, pdf_a4_link)
    filename = os.path.basename(archive_url)
    downloads_dir = BASE_DIR / DOWNLOADS_SUBDIR
    downloads_dir.mkdir(exist_ok=True)
    archive_path = downloads_dir / filename
    response = session.get(archive_url)
    with open(archive_path, 'wb') as file:
        file.write(response.content)
    logging.info(f'Архив был загружен и сохранён: {archive_path}')


def pep(session):
    response = get_response(session, PEPS_URL)
    if response is None:
        return

    soup = BeautifulSoup(response.text, features='lxml')
    peps_by_index = find_tag(soup, 'section', attrs={'id': 'numerical-index'})
    peps = find_tag(peps_by_index, 'tbody')
    peps = peps.find_all('tr')

    statuses_count = defaultdict(int)
    results = [('Статус', 'Количество')]

    for pep in tqdm(peps):
        preview_status = find_tag(pep, 'td').text[1:]
        second_column_tag = find_tag(
            pep, 'a', attrs={'class': 'pep reference internal'}
        )
        pep_url = urljoin(PEPS_URL, second_column_tag['href'])
        response = get_response(session, pep_url)
        if response is None:
            return

        card_text = find_tag(
            BeautifulSoup(response.text, features='lxml'), 'dl'
        ).text
        status = re.search(STATUS_PATTERN, card_text).groups()[0]
        statuses_count[status] += 1

        if status not in EXPECTED_STATUS[preview_status]:
            logging.info(
                f'Несовпадающие статусы:\n'
                f'{pep_url}\n'
                f'Статус в карточке: {status}\n'
                f'Ожидаемые статусы: {EXPECTED_STATUS[preview_status]}'
            )

    results.extend(sorted(statuses_count.items()))
    results.append(('Total', sum(statuses_count.values())))
    return results


MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
    'pep': pep,
}


def main():
    configure_logging()
    logging.info('Парсер запущен!')

    arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
    args = arg_parser.parse_args()
    logging.info(f'Аргументы командной строки: {args}')

    session = requests_cache.CachedSession()
    if args.clear_cache:
        session.cache.clear()

    parser_mode = args.mode
    results = MODE_TO_FUNCTION[parser_mode](session)

    if results is not None:
        control_output(results, args)
    logging.info('Парсер завершил работу.')


if __name__ == '__main__':
    main()
