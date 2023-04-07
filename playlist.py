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
    with open(file, 'w') as list_f:
        data = map(lambda v: v + '\n', file_list)
        list_f.writelines(data)

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
current_file = Path(join(current_path, 'current.txt'))

extensions = args.ext

playlist = findFiles(current_path, extensions)
current = 0

if not playlist:
    print(f'No files with extension(s) {extensions} found in folder. Playlist not created.')
    quit()

if args.m3u:
    if playlist and playlist_file.is_file():
        key_input = input(f'{len(playlist)} file matches found. This will overwrite existing \'playlist.m3u\', continue? ')
        if re.match('^[Y|y]e?s?', key_input):
            writePlaylist(playlist, playlist_file)
            print('Created \'playlist.m3u\'.')
    elif playlist:
        writePlaylist(playlist, playlist_file)
        print('Created \'playlist.m3u\'.')
    quit()

if current_file.is_file():
    with open(current_file, 'r') as current_f:
        current = playlist.index(current_f.readline().strip('\n'))
        print(current)

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

# have to do this weird stuff to make 'playing from partway through the playlist' work 🙃
player.loadfile(playlist[current], 'append')
for i, video in enumerate(playlist):
    if not video == playlist[current]:  # if not the file already loaded
        player.playlist_append(video)
        player.playlist_move(len(player.playlist)-1, i)  # move the newly added file around
player.playlist_pos = current

while True:
    try:
        previous_filename = player.playlist_filenames[player.playlist_pos]
        player.wait_for_playback()
        print(f'Playing \'{previous_filename}\' finished.', end='\033[K\n')
        current = player.playlist_pos
        if player.playlist_pos == -1:  # MPV returns playlist position of -1 when it reaches the end of the current playlist
            player.terminate()
            remove(current_file)
            print('Playlist finished!\nRemoved \'current.txt\'.')
            quit()

    except ShutdownError:
        player.terminate()
        print(f'\033[1APlaying \'{previous_filename}\' interrupted by user.', end='\033[K')
        writePlaylist(playlist[current:current+1], current_file)
        quit()
