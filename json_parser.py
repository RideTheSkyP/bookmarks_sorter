import re
import json
import copy

from bookmarks_converter import BookmarksConverter


filename = 'Bookmarks'

try:
    with open(filename, 'r', encoding='utf8') as f:
        bookmarks_list = json.load(f)
        bookmarks_list = bookmarks_list.get('roots').get('bookmark_bar').get('children')
        bookmarks_list = [bookmark for bookmark in bookmarks_list]
except Exception as e:
    print(f'Error: {e}')
    exit(1)


def get_folders(bookmarks_folders):
    folders_dict = {}
    for bookmark_folder in bookmarks_folders:
        if bookmark_folder.get('type') == 'folder':
            bookmark_folder.pop('children')
            folders_dict[bookmark_folder.get('name')] = bookmark_folder
        else:
            print('TYPE NOT FOLDER', bookmark_folder)
    return folders_dict


folders_dict = get_folders(copy.deepcopy(bookmarks_list))


def delete_duplicates(bookmarks_folders):
    seen = set()
    result = []
    for bookmarks_folder in bookmarks_folders:
        for bookmark in bookmarks_folder.get('children'):
            bookmark.pop('meta_info')
            b = bookmark.copy()
            if not b.get('url'):
                continue
            url = b.get('url')
            if url not in seen:
                result.append(bookmark)
                seen.add(url)
            else:
                print(f'Detected duplicate: {b}')
    return result


bookmarks_dict_no_dupe_list = delete_duplicates(bookmarks_list)


def normalize_bookmark_title(folder_name, bookmark_title):
    normalized_bookmark = re.sub(r'[._\-]', ' ', bookmark_title)

    # Split both folder name and normalized filename into words
    folder_words = folder_name.split()
    bookmark_words = normalized_bookmark.split()

    # Check if all words in the folder name are present in the filename
    return all(word in bookmark_words for word in folder_words)


def organize_by_folders(bookmarks):
    res = {folder_title: [] for folder_title in folders_dict.keys()}
    seen = []
    for bookmark in bookmarks:
        bookmark_url = bookmark.get('url')
        bookmark_name = bookmark.get('name').lower()
        for folder in folders_dict:
            if normalize_bookmark_title(folder.lower(), bookmark_name):
                print(f'Found: {bookmark_name} in {folder}')
                if bookmark_url not in seen:
                    seen.append(bookmark_url)
                else:
                    print(f'Already seen: {bookmark}')
                    bookmark = bookmark.copy()
                res[folder].append(bookmark)
    return res


organized_by_folders_bookmarks_dict = organize_by_folders(bookmarks_dict_no_dupe_list)
organized_bookmarks_list = [bookmark for bookmarks_list in organized_by_folders_bookmarks_dict.values() for bookmark in bookmarks_list]
all_bookmarks_list = [bookmark for item in bookmarks_list for bookmark in item.get('children', [])]
not_organized_by_folders_bookmarks_list = [x for x in all_bookmarks_list if (x not in organized_bookmarks_list)]
all_bookmarks_list_by_folders = {}
all_bookmarks_list_by_folders.update(organized_by_folders_bookmarks_dict)

google_bookmarks = {
    'checksum': '0',
    'roots': {
        'bookmark_bar': {
            'children': [
                {
                    'name': folder_name,
                    'type': 'folder',
                    'id': 0,
                    'date_added': '0',
                    'children': [
                        bookmark for bookmark in bookmarks
                    ]
                }
                for folder_name, bookmarks in all_bookmarks_list_by_folders.items()
            ],
            'date_added': '0',
            'date_modified': '0',
            'id': '1',
            'name': 'Bookmarks bar',
            'type': 'folder'
        },
        'other': {
                'children': [
                    bookmark for bookmark in not_organized_by_folders_bookmarks_list
                ],
                'date_added': '0',
                'date_modified': '0',
                'id': '2',
                'name': 'Other bookmarks',
                'type': 'folder',
        },
         'synced': {
            'children': [],
            'date_added': '0',
            'date_modified': '0',
            'id': '3',
            'name': 'Mobile bookmarks',
            'type': 'folder'
         }
    },
    'version': 1
}

with open('Bookmarks1', 'w') as f:
    f.write(json.dumps(google_bookmarks, indent=4))

bookmarks = BookmarksConverter('Bookmarks1')
bookmarks.parse('json')
bookmarks.convert('html')
bookmarks.save()
