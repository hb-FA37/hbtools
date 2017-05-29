import os
import moviepy.editor as editor
from moviepy.editor import VideoFileClip


def clipit(file_path, start, end, name=None, webm=False, resize=0.3):
    """ Clip to gif. """
    if not os.path.isfile(file_path):
        print "Invalid file path {}".format(file_path)

    clip = VideoFileClip(file_path, audio=False).subclip(
        start, end).resize(resize)

    extension = ".gif"
    if webm:
        extension = ".webm"

    if name is None:
        export_path = os.path.splitext(file_path)[0] + extension
    else:
        export_path = os.path.join(
            os.path.dirname(file_path), name + extension)

    clip.write_gif(export_path, fps=30)


def cutit(movie_file, output_files, time_stamps):
    """ Cut to the given times and write to a single file. """
    sub_clips = []
    clip = VideoFileClip(movie_file)

    for i in range(len(time_stamps) / 2):
        start = time_stamps[i * 2]
        end = time_stamps[i * 2 + 1]
        print "Cutting from {} to {}".format(start, end)
        sub_clip = clip.subclip(start, end)
        sub_clips.append(clip)

    combined_clip = editor.concatenate_videoclips(sub_clips)
    combined_clip.write_videofile(output_files, preset="slower", threads=12)


def cutit_multi(movie_file, output_path, output_files, time_stamps):
    """ Cut to the given times and writes each section to a different file. """
    sub_clips = []
    clip = VideoFileClip(movie_file)

    if len(output_files) != len(time_stamps) / 2:
        error = "Not enough output files for the given amount of subclips ({})".format(
            len(time_stamps) / 2)
        raise ValueError(error)

    for i in range(len(time_stamps) / 2):
        start = time_stamps[i * 2]
        end = time_stamps[i * 2 + 1]
        print "Cutting from {} to {}".format(start, end)
        sub_clip = clip.subclip(start, end)
        sub_clips.append(clip)

    for index, sub_clip in enumerate(sub_clips):
        output_file = os.path.join(output_path, output_files[index])
        sub_clip.write_videofile(output_file, preset="medium", threads=12)


# Example Usage #

"""
from Tools37.moviepy37 import clipit
file_name = r"C:\Users.mp4"
clipit(file_name, (0, 54, 10), (0, 54, 37), gif_name='symmetra')
"""

"""
from Tools37.moviepy37 import cutit
movie_file = r"C:\Users.mp4"
output_file = r"C:\Users_clipped.mp4"
#output_file = r"C:\Users_clipped.webm"
time_stamps = [(0, 0, 0), (0, 23, 0), (0, 28, 14), (0, 46, 58), (0, 50, 40), (1, 8, 28), (1, 14, 18), (1, 40, 33)]
cutit(movie_file, output_file, time_stamps)

from Tools37.moviepy37 import cutit_multi
movie_file = r"C:\Users.mp4"
output_path = r"C:\Users\Videos"
output_files = ["a1.mp4", "b1.mp4", "c3.mp4", "d4.mp4"]
#output_files = ["a1.webm", "b1.webm", "c3.webm", "d4.webm"]
time_stamps = [(0, 0, 0), (0, 23, 0), (0, 28, 14), (0, 46, 58), (0, 50, 40), (1, 8, 28), (1, 14, 18), (1, 40, 33)]
cutit_multi(movie_file, output_path, output_files, time_stamps)
"""
