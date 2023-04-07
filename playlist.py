import argparse
import re
from os import listdir, remove
from os.path import isdir, isfile, join
from pathlib import Path

import mpv
from mpv import ShutdownError

def isExt(fileName, exts):
  return True in map(fileName.lower().endswith, ("." + e.lower() for e in exts))

def findFiles(path, exts):
    return [v for v in listdir(path) if isfile(join(path, v)) and isExt(v, exts)]

def writePlaylist(file_list, file):
    with open(file, 'w') as playlist_f:
        data = map(lambda v: v + '\n', file_list)
        playlist_f.writelines(data)

parser = argparse.ArgumentParser()
parser.add_argument('path', metavar='path', type=str, help='The directory path to play')
parser.add_argument('-m', '--m3u', action="store_true", default=False, dest='m3u', help='Only create an m3u playlist.')
parser.add_argument('-e', '--ext', action="extend", default=['mkv', 'mp4', 'avi'], dest='ext', nargs="+", type=str, help='Specify the file extension(s) to search the folder for.')
args = parser.parse_args()

current_path = args.path
if not isdir(current_path):
    print('Error: Arguments must contain a directory.')
    quit()

playlist_file = Path(join(current_path, 'playlist.m3u'))

extensions = args.ext

if args.m3u:
    file_list = findFiles(current_path, extensions)
    if file_list and playlist_file.is_file():
        key_input = input(f'{len(file_list)} file matches found. This will overwrite existing \'playlist.m3u\', continue? ')
        if re.match('^[Y|y]e?s?', key_input):
            writePlaylist(file_list, playlist_file)
            print('Created \'playlist.m3u\'.')
    elif file_list:
        writePlaylist(file_list, playlist_file)
        print('Created \'playlist.m3u\'.')
    else:
        print(f'No files with extension(s) {extensions} found in folder. Playlist not created.')
    quit()

if not playlist_file.is_file():
    playlist = findFiles(current_path, extensions)
    if not playlist:
        print(f'No files with extension(s) {extensions} found in folder. Playlist not created.')
        quit()
    writePlaylist(playlist, playlist_file)
    print('Playlist file not found in directory.\nCreated \'playlist.m3u\'.')
else:
    with open(playlist_file, 'r') as playlist_f:
        playlist = playlist_f.read().splitlines()

if not playlist:  # an empty list is a falsy value
    remove(playlist_file)
    print('No unplayed video files in directory.\nRemoved \'playlist.m3u\'.')
    quit()

player = mpv.MPV(input_default_bindings=True, input_vo_keyboard=True, osc=True)

@player.property_observer('time-pos')
def time_observer(_name, value):
    # value is either None if nothing is playing or a float containing fractional seconds since the beginning of the file.
    if value != None:
        hours, r = divmod(value, 3600)
        minutes, seconds = divmod(r, 60)
        time = f'{int(hours):01}:{int(minutes):02}:{int(seconds):02}'
        name = player.playlist_filenames[player.playlist_pos]
        print(f'Playing \'{name}\' at {time}', end='\033[K\r')

for video in playlist:
    player.playlist_append(video)
player.playlist_pos = 0  # also starts MPV

while True:
    try:
        previous_filename = player.playlist_filenames[player.playlist_pos]
        player.wait_for_playback()
        print(f'Playing \'{previous_filename}\' finished.', end='\033[K\n')
        playlist = player.playlist_filenames[player.playlist_pos:]
        if player.playlist_pos == -1:  # MPV returns playlist position of -1 when it reaches the end of the current playlist
            player.terminate()
            remove(playlist_file)
            print('Playlist finished!\nRemoved \'playlist.m3u\'.')
            quit()

    except ShutdownError:
        player.terminate()
        print(f'\033[1APlaying \'{previous_filename}\' interrupted by user.', end='\033[K')
        writePlaylist(playlist, playlist_file)
        quit()
