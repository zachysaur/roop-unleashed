import os
import gradio as gr
import roop.utilities as util
import roop.util_ffmpeg as ffmpeg
import roop.globals
from subprocess import getoutput

def runcc(command):
    out = getoutput(f"{command}")
    return out

def extras_tab():
    with gr.Tab("🎉 Extras"):
        with gr.Row():
            command = gr.Textbox(show_label=False, max_lines=1, placeholder="command")
            out_text1 = gr.Textbox(show_label=False)
            btn_run = gr.Button("run command")
            btn_run.click(runcc, inputs=command, outputs=out_text1)
            files_to_process = gr.Files(label='File(s) to process', file_count="multiple", file_types=["image", "video"])
        # with gr.Row(variant='panel'):
        #     with gr.Accordion(label="Post process", open=False):
        #         with gr.Column():
        #             selected_post_enhancer = gr.Dropdown(["None", "Codeformer", "GFPGAN"], value="None", label="Select post-processing")
        #         with gr.Column():
        #             gr.Button("Start").click(fn=lambda: gr.Info('Not yet implemented...'))
        with gr.Row(variant='panel'):
            with gr.Accordion(label="Video/GIF", open=False):
                with gr.Row(variant='panel'):
                    with gr.Column():
                        gr.Markdown("""
                                    # Cut video
                                    Be aware that this means re-encoding the video which might take a longer time.
                                    Encoding uses your configuration from the Settings Tab.
    """)
                    with gr.Column():
                        cut_start_time = gr.Slider(0, 1000000, value=0, label="Start Frame", step=1.0, interactive=True)
                    with gr.Column():
                        cut_end_time = gr.Slider(1, 1000000, value=1, label="End Frame", step=1.0, interactive=True)
                    with gr.Column():
                        start_cut_video = gr.Button("Cut video")
                        start_extract_frames = gr.Button("Extract frames")

                with gr.Row(variant='panel'):
                    with gr.Column():
                        gr.Markdown("""
                                    # Join videos
    """)
                    with gr.Column():
                        extras_chk_encode = gr.Checkbox(label='Re-encode video (necessary for videos with different codecs)', value=False)
                        start_join_videos = gr.Button("Start")
                with gr.Row(variant='panel'):
                    with gr.Column():
                        gr.Markdown("""
                                    # Create video/gif from images
    """)
                    with gr.Column():
                        extras_fps = gr.Slider(minimum=0, maximum=120, value=30, label="Video FPS", step=1.0, interactive=True)
                        extras_images_folder = gr.Textbox(show_label=False, placeholder="/content/", interactive=True)
                    with gr.Column():
                        extras_chk_creategif = gr.Checkbox(label='Create GIF from video', value=False)
                        extras_create_video=gr.Button("Create")
        with gr.Row():
            gr.Button("👀 Open Output Folder", size='sm').click(fn=lambda: util.open_folder(roop.globals.output_path))
        with gr.Row():
            extra_files_output = gr.Files(label='Resulting output files', file_count="multiple")

    start_cut_video.click(fn=on_cut_video, inputs=[files_to_process, cut_start_time, cut_end_time], outputs=[extra_files_output])
    start_extract_frames.click(fn=on_extras_extract_frames, inputs=[files_to_process], outputs=[extra_files_output])
    start_join_videos.click(fn=on_join_videos, inputs=[files_to_process, extras_chk_encode], outputs=[extra_files_output])
    extras_create_video.click(fn=on_extras_create_video, inputs=[extras_images_folder, extras_fps, extras_chk_creategif], outputs=[extra_files_output])


def on_cut_video(files, cut_start_frame, cut_end_frame):
    if files is None:
        return None
    
    resultfiles = []
    for tf in files:
        f = tf.name
        destfile = util.get_destfilename_from_path(f, roop.globals.output_path, '_cut')
        ffmpeg.cut_video(f, destfile, cut_start_frame, cut_end_frame)
        if os.path.isfile(destfile):
            resultfiles.append(destfile)
        else:
            gr.Error('Cutting video failed!')
    return resultfiles


def on_join_videos(files, chk_encode):
    if files is None:
        return None
    
    filenames = []
    for f in files:
        filenames.append(f.name)
    destfile = util.get_destfilename_from_path(filenames[0], roop.globals.output_path, '_join')
    sorted_filenames = util.sort_filenames_ignore_path(filenames)        
    ffmpeg.join_videos(sorted_filenames, destfile, not chk_encode)
    resultfiles = []
    if os.path.isfile(destfile):
        resultfiles.append(destfile)
    else:
        gr.Error('Joining videos failed!')
    return resultfiles



def on_extras_create_video(images_path,fps, create_gif):
    util.sort_rename_frames(os.path.dirname(images_path))
    destfilename = os.path.join(roop.globals.output_path, "img2video." + roop.globals.CFG.output_video_format)
    ffmpeg.create_video('', destfilename, fps, images_path)
    resultfiles = []
    if os.path.isfile(destfilename):
        resultfiles.append(destfilename)
    else:
        return None
    if create_gif:
        gifname = util.get_destfilename_from_path(destfilename, './output', '.gif')
        ffmpeg.create_gif_from_video(destfilename, gifname)
        if os.path.isfile(destfilename):
            resultfiles.append(gifname)
    return resultfiles
    

def on_extras_extract_frames(files):
    if files is None:
        return None
    
    resultfiles = []
    for tf in files:
        f = tf.name
        resfolder = ffmpeg.extract_frames(f)
        for file in os.listdir(resfolder):
            outfile = os.path.join(resfolder, file)
            if os.path.isfile(outfile):
                resultfiles.append(outfile)
    return resultfiles

