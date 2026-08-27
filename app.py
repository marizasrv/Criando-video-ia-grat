from moviepy import ImageClip, AudioFileClip, concatenate_videoclips
from PIL import Image
import numpy as np
import os


def preparar_imagem(imagem, largura=1280, altura=720):
    """
    Coloca a imagem em 1280x720 sem deixar faixas brancas.
    """
    img = imagem.convert("RGB")

    proporcao_img = img.width / img.height
    proporcao_video = largura / altura

    if proporcao_img > proporcao_video:
        nova_altura = altura
        nova_largura = int(img.width * altura / img.height)
    else:
        nova_largura = largura
        nova_altura = int(img.height * largura / img.width)

    img = img.resize((nova_largura, nova_altura))

    esquerda = (nova_largura - largura) // 2
    topo = (nova_altura - altura) // 2

    img = img.crop(
        (
            esquerda,
            topo,
            esquerda + largura,
            topo + altura
        )
    )

    return np.array(img)


def criar_video(imagens, arquivo_audio=None, duracao_cena=5):
    clips = []

    for imagem in imagens:

        frame = preparar_imagem(imagem)

        clip = ImageClip(frame).with_duration(duracao_cena)

        # Zoom suave
        clip = clip.resized(
            lambda t: 1 + (0.04 * t / duracao_cena)
        )

        clips.append(clip)

    video = concatenate_videoclips(
        clips,
        method="compose"
    )

    # Adicionar narracao
    if arquivo_audio and os.path.exists(arquivo_audio):

        audio = AudioFileClip(arquivo_audio)

        video = video.with_audio(audio)

        # Ajusta o vídeo ao tamanho do áudio
        if audio.duration < video.duration:
            video = video.subclipped(0, audio.duration)

    arquivo_saida = "video_final.mp4"

    video.write_videofile(
        arquivo_saida,
        fps=24,
        codec="libx264",
        audio_codec="aac"
    )

    return arquivo_saida
