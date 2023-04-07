import argparse
from os import listdir, remove
from os.path import isdir, isfile, join
from pathlib import Path

import mpv
from mpv import ShutdownError

extensions = ['mkv', 'mp4', 'avi']

def isExt(fileName, exts):
  return True in map(fileName.lower().endswith, ("." + e.lower() for e in exts))

def createPlaylist(path, file, exts):
    playlist_out = [v for v in listdir(path) if isfile(join(path, v)) and isExt(v, exts)]
    if not playlist_out:
        print(f'No files with extension(s) {exts} found in folder. Playlist not created.')
        quit()
    with open(file, 'w') as playlist_f:
        data = map(lambda v: v + '\n', playlist_out)
        playlist_f.writelines(data)

parser = argparse.ArgumentParser()
parser.add_argument('path', metavar='path', type=str, help='The directory path to play')
parser.add_argument('-m', '--m3u', action="store_true", default=False, dest='m3u', help='Only create an m3u playlist.')
parser.add_argument('-e', '--ext', action="extend", default=[], dest='ext', nargs="+", type=str, help='Specify the file extension(s) to search the folder for.')
args = parser.parse_args()

current_path = args.path
if not isdir(current_path):
    print('Error: Arguments must contain a directory.')
    quit()

playlist_file = Path(join(current_path, 'playlist.m3u'))

if args.ext:
    extensions = args.ext

if args.m3u:
    createPlaylist(current_path, playlist_file, extensions)
    print('Created \'playlist.m3u\'.')
    quit()

if not playlist_file.is_file():
    createPlaylist(current_path, playlist_file, extensions)
    print('Playlist file not found in directory.\nCreated \'playlist.m3u\'.')
else:
    with open(playlist_file, 'r') as playlist_f:
        playlist = playlist_f.read().splitlines()

if not playlist:  # an empty list is a falsy value
    remove(playlist_file)
    print('No unplayed video files in directory.\nRemoved \'playlist.m3u\'.')
    quit()

player = mpv.MPV(input_default_bindings=True, input_vo_keyboard=True, osc=True)

for video in playlist:
    player.playlist_append(video)
player.playlist_pos = 0

@player.property_observer('time-pos')
def time_observer(_name, value):
    # value is either None if nothing is playing or a float containing fractional seconds since the beginning of the file.
    if value != None:
        hours, r = divmod(value, 3600)
        minutes, seconds = divmod(r, 60)
        time = f'{int(hours):01}:{int(minutes):02}:{int(seconds):02}'
        name = player.playlist[player.playlist_pos]['filename']
        print(f'Playing \'{name}\' at {time}', end='\033[K\r')

while True:
    if not playlist:
        remove(playlist_file)
        print('Playlist finished!\nRemoved \'playlist.m3u\'.')
        quit()

    try:
        player.wait_for_playback()
        print('Playing \'' + player.playlist[0]['filename'] + '\' finished.', end='\033[K\n')
        player.playlist_remove(0)
        playlist = player.playlist_filenames

    except ShutdownError:
        player.terminate()
        print('Playing \'' + playlist[0] + '\' interrupted by user.', end='\033[K')
        with open(playlist_file, 'w') as list_out:
            data = map(lambda v: v + '\n', playlist)
            list_out.writelines(data)
        quit()
