import os
from moviepy.editor import VideoFileClip


def clipit(file_path, start, end, gif_name=None, resize=0.3):
    if not os.path.isfile(file_path):
        print "Invalid file path {}".format(file_path)

    clip = VideoFileClip(file_path, audio=False).subclip(
        start, end).resize(resize)
    if gif_name is None:
        export_path = os.path.splitext(file_path)[0] + ".gif"
    else:
        export_path = os.path.join(
            os.path.dirname(file_path), gif_name + ".gif")
    clip.write_gif(export_path, fps=24)


# clipit(r"C:\Users\Herbert\Videos\Overwatch\Overwatch 05.21.2017 - 23.26.08.03.mp4",
#        (1, 26, 22), (1, 26, 30))
