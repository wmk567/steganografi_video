import os
import ffmpeg
from PIL import Image

def extract_frames(video_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    (
        ffmpeg
        .input(video_path)
        .output(os.path.join(output_dir, 'frame_%04d.png'), pix_fmt='rgb24')
        .run()
    )

def extract_audio(input_video_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    stream = ffmpeg.input(input_video_path)
    audio = stream.audio
    audio = ffmpeg.output(audio, os.path.join(output_dir, 'audio_0.mp3'), acodec='libmp3lame')
    ffmpeg.run(audio)

def encode_image(cover_image_path, secret_image_path, output_image_path):
    cover_image = Image.open(cover_image_path)
    secret_image = Image.open(secret_image_path)

    cover_image = cover_image.convert("RGB")
    secret_image = secret_image.convert("RGB")

    secret_image = secret_image.resize(cover_image.size)

    encoded_image = Image.new("RGB", cover_image.size)

    for x in range(cover_image.width):
        for y in range(cover_image.height):
            cover_pixel = cover_image.getpixel((x, y))
            secret_pixel = secret_image.getpixel((x, y))

            encoded_pixel = (
                (cover_pixel[0] & 0b11111110) | (secret_pixel[0] >> 7),
                (cover_pixel[1] & 0b11111110) | (secret_pixel[1] >> 7),
                (cover_pixel[2] & 0b11111110) | (secret_pixel[2] >> 7)
            )

            encoded_image.putpixel((x, y), encoded_pixel)

    encoded_image.save(output_image_path)

def decode_image(encoded_image_path, output_image_path):
    encoded_image = Image.open(encoded_image_path)
    decoded_image = Image.new("RGB", encoded_image.size)

    for x in range(encoded_image.width):
        for y in range(encoded_image.height):
            encoded_pixel = encoded_image.getpixel((x, y))

            decoded_pixel = (
                encoded_pixel[0] & 0b00000001,
                encoded_pixel[1] & 0b00000001,
                encoded_pixel[2] & 0b00000001
            )

            decoded_pixel = (
                decoded_pixel[0] << 7,
                decoded_pixel[1] << 7,
                decoded_pixel[2] << 7
            )

            decoded_image.putpixel((x, y), decoded_pixel)

    decoded_image.save(output_image_path)

def embed_video(cover_video, secret_video, output_video):
    cover_frames_path = 'cover_frames/'
    secret_frames_path = 'secret_frames/'
    embedded_frames_path = 'embedded_frames/'
    audio_path = 'audio/'

    extract_frames(cover_video, cover_frames_path)
    extract_frames(secret_video, secret_frames_path)
    extract_audio(cover_video, audio_path)

    os.makedirs(embedded_frames_path, exist_ok=True)

    cover_frames = sorted(os.listdir(cover_frames_path))
    secret_frames = sorted(os.listdir(secret_frames_path))

    for i, (cover_frame, secret_frame) in enumerate(zip(cover_frames, secret_frames)):
        cover_frame_path = os.path.join(cover_frames_path, cover_frame)
        secret_frame_path = os.path.join(secret_frames_path, secret_frame)
        
        embedded_image = encode_image(cover_frame_path, secret_frame_path, embedded_frames_path + f'frame_{i:04d}.png')

    video_stream = ffmpeg.input(os.path.join(embedded_frames_path, 'frame_%04d.png'), framerate=12.5)
    audio_stream = ffmpeg.input(os.path.join(audio_path, 'audio_0.mp3'))

    ffmpeg.output(video_stream, audio_stream, output_video, vcodec='ffv1', pix_fmt='bgr0', acodec='copy', shortest=None).run()

def extract_video(output_video, hidden_video):
    hidden_frames_path = 'hidden_frames/'
    output_frames_path = 'output_frames/'

    extract_frames(output_video, output_frames_path)
    os.makedirs(hidden_frames_path, exist_ok=True)

    output_frames = sorted(os.listdir(output_frames_path))

    for i, output_frame in enumerate(output_frames):
        output_frame_path = os.path.join(output_frames_path, output_frame)
        
        hidden_image = decode_image(output_frame_path, hidden_frames_path + f'frame_{i:04d}.png')

    (
        ffmpeg
        .input(os.path.join(hidden_frames_path, 'frame_%04d.png'), framerate=30)
        .output(hidden_video, vcodec='ffv1', pix_fmt='bgr0')  
        .run()
    )

cover_video_path = 'cover-video.mkv'
secret_video_path = 'secret-video.mkv'
output_video_path = 'output_video.mkv'
hidden_video_path = 'hidden_video.mkv'

embed_video(cover_video_path, secret_video_path, output_video_path)
extract_video(output_video_path, hidden_video_path)