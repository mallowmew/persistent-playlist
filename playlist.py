from os import listdir, remove
from os.path import isfile, isdir, join 
from pathlib import Path
import sys
import subprocess
import argparse

extensions = ['mkv', 'mp4']

def isExt(fileName, ext):
  return True in map(fileName.lower().endswith, ("." + e.lower() for e in ext))

def play_video(path):
    player = subprocess.Popen(['C:\\Program Files\\mpv\\mpv.exe', video_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = player.communicate()

def remove_first_line_of_playlist():
    with open(playlist_path, 'r') as list_in:
        data = list_in.read().splitlines(True)
    with open(playlist_path, 'w') as list_out:
        list_out.writelines(data[1:])

parser = argparse.ArgumentParser()
parser.add_argument('path', metavar='path', type=str, help='The directory path to play')
parser.add_argument('-a', '--auto', action='store_true', default=False)
args = parser.parse_args()

print(args)

current_path = args.path
if not isdir(current_path):
    print('Error: Arguments must contain a directory.')
    quit()

playlist_path = Path(join(current_path, 'playlist.txt'))

if not playlist_path.is_file():
    print('Playlist file not found in directory. Creating playlist.txt')
    with open(playlist_path, 'x') as playlist:
        videofiles = [v for v in listdir(current_path) if isfile(join(current_path, v)) and isExt(v, extensions)]
        videofiles = map(lambda v: v + '\n', videofiles)
        playlist.writelines(videofiles)

while True:
    with open(playlist_path, 'r') as playlist:
        video_filename = playlist.readline().rstrip('\n')

    if video_filename == '':
        print('No unplayed video files in directory.')
        remove(playlist_path)
        print('Playlist file deleted.')
        quit()
    else:
        video_path = join(current_path, video_filename)

    print('Now playing: ' + video_filename)
    play_video(video_path)
    remove_first_line_of_playlist()

    if ('--auto' in sys.argv) or ('-a' in sys.argv):
        continue

    key_input = input('Play next? ')
    if key_input == 'y':
        continue
    else:
        quit()
