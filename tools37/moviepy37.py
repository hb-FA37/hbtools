import os
import moviepy.editor as editor
from moviepy.editor import VideoFileClip

"""
Small movie file manipulation methods.
"""


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


def cutit(movie_file, output_files, time_stamps, threads=4):
    """ Cut to the given times and write to a single file. """
    sub_clips = []
    clip = VideoFileClip(movie_file)

    for i in range(len(time_stamps) / 2):
        start = time_stamps[i * 2]
        end = time_stamps[i * 2 + 1]
        print "Cutting from {} to {}".format(start, end)
        sub_clip = clip.subclip(start, end)
        sub_clips.append(sub_clip)

    combined_clip = editor.concatenate_videoclips(sub_clips)
    combined_clip.write_videofile(output_files, preset="slower", threads=threads)


def cutit_multi(movie_file, output_path, output_files, time_stamps, threads=4):
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
        sub_clip.write_videofile(output_file, preset="medium", threads=threads)
