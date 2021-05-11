from os import listdir, remove
from os.path import isfile, isdir, join 
from pathlib import Path
import argparse
import re
import mpv
from mpv import ShutdownError
import datetime

extensions = ['mkv', 'mp4']

def isExt(fileName, exts):
  return True in map(fileName.lower().endswith, ("." + e.lower() for e in exts))

def remove_first_line_of_playlist():
    with open(playlist_path, 'r') as list_in:
        data = list_in.read().splitlines(True)
    with open(playlist_path, 'w') as list_out:
        list_out.writelines(data[1:])

parser = argparse.ArgumentParser()
parser.add_argument('path', metavar='path', type=str, help='The directory path to play')
parser.add_argument('-a', '--auto', action='store_true', default=False, help='In auto mode the script will not ask for confirmation before moving onto the next file in the playlist')
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

    player = mpv.MPV(input_default_bindings=True, input_vo_keyboard=True, osc=True)

    @player.property_observer('time-pos')
    def time_observer(_name, value):
        # value is either None if nothing is playing or a float containing fractional seconds since the beginning of the file.
        if value != None:
            time = str(datetime.timedelta(seconds=value))
            print('Now playing ' + video_filename + ' at ' + time + '\033[K', end='\r')

    prompt_string = 0

    try:
        player.play(video_path)
        player.wait_for_playback()
        remove_first_line_of_playlist()
        prompt_string = 'Play next? '

    except ShutdownError:
        print('\nPlayback ended by user.', end='')
        prompt_string = 'Retry? '

    finally:
        player.terminate()

    if (args.auto):
        continue
        
    key_input = input('\n' + prompt_string)
    if re.match('^[Y|y]e?s?', key_input):
        continue
    else:
        quit()
