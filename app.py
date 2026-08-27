import streamlit as st
import os
import tempfile
from pathlib import Path

from moviepy import (
    ImageClip,
    AudioFileClip,
    concatenate_videoclips,
    CompositeAudioClip,
)

st.set_page_config(
    page_title="Montador de Vídeo IA",
    page_icon="🎬",
    layout="centered"
)

st.title("🎬 Montador de Vídeo com Imagens e Som")
st.write(
    "Envie as imagens e as falas prontas. "
    "O app monta tudo e cria um vídeo MP4."
)

formato = st.selectbox(
    "Formato do vídeo",
    [
        "YouTube Horizontal 16:9",
        "YouTube Shorts / TikTok 9:16"
    ]
)

if formato == "YouTube Horizontal 16:9":
    largura = 1280
    altura = 720
else:
    largura = 720
    altura = 1280


def ordenar_arquivos(arquivos):
    return sorted(
        arquivos,
        key=lambda x: x.name.lower()
    )


imagens = st.file_uploader(
    "📷 Envie as imagens das cenas",
    type=["png", "jpg", "jpeg", "webp"],
    accept_multiple_files=True
)

audios = st.file_uploader(
    "🎤 Envie as falas/áudios das cenas",
    type=["mp3", "wav", "m4a", "aac"],
    accept_multiple_files=True
)

musica = st.file_uploader(
    "🎵 Música de fundo (opcional)",
    type=["mp3", "wav", "m4a", "aac"]
)

volume_musica = st.slider(
    "Volume da música de fundo",
    min_value=0,
    max_value=100,
    value=15
)

duracao_sem_audio = st.slider(
    "Duração da imagem quando não houver fala",
    min_value=2,
    max_value=15,
    value=5
)

st.info(
    "💡 Para facilitar, nomeie os arquivos assim: "
    "01.jpg + 01.mp3, 02.jpg + 02.mp3, 03.jpg + 03.mp3..."
)


def ajustar_imagem(clip, largura, altura):
    proporcao_video = largura / altura
    proporcao_img = clip.w / clip.h

    if proporcao_img > proporcao_video:
        clip = clip.resized(height=altura)
    else:
        clip = clip.resized(width=largura)

    x1 = max(0, (clip.w - largura) / 2)
    y1 = max(0, (clip.h - altura) / 2)

    clip = clip.cropped(
        x1=x1,
        y1=y1,
        width=largura,
        height=altura
    )

    return clip


if st.button("🎬 CRIAR VÍDEO", type="primary"):

    if not imagens:
        st.error("Envie pelo menos uma imagem.")
        st.stop()

    temp_dir = tempfile.mkdtemp()

    try:
        imagens = ordenar_arquivos(imagens)

        if audios:
            audios = ordenar_arquivos(audios)

        caminhos_imagens = []

        for i, arquivo in enumerate(imagens):
            extensao = Path(arquivo.name).suffix
            caminho = os.path.join(
                temp_dir,
                f"imagem_{i:03d}{extensao}"
            )

            with open(caminho, "wb") as f:
                f.write(arquivo.getbuffer())

            caminhos_imagens.append(caminho)

        caminhos_audios = []

        if audios:
            for i, arquivo in enumerate(audios):
                extensao = Path(arquivo.name).suffix
                caminho = os.path.join(
                    temp_dir,
                    f"audio_{i:03d}{extensao}"
                )

                with open(caminho, "wb") as f:
                    f.write(arquivo.getbuffer())

                caminhos_audios.append(caminho)

        st.write("⏳ Montando as cenas...")

        progresso = st.progress(0)

        clips = []
        audios_abertos = []

        total = len(caminhos_imagens)

        for i, caminho_imagem in enumerate(caminhos_imagens):

            audio_clip = None

            if i < len(caminhos_audios):
                audio_clip = AudioFileClip(
                    caminhos_audios[i]
                )

                audios_abertos.append(audio_clip)

                duracao = audio_clip.duration + 0.3

            else:
                duracao = duracao_sem_audio

            imagem_clip = ImageClip(
                caminho_imagem
            ).with_duration(duracao)

            imagem_clip = ajustar_imagem(
                imagem_clip,
                largura,
                altura
            )

            if audio_clip:
                imagem_clip = imagem_clip.with_audio(
                    audio_clip
                )

            clips.append(imagem_clip)

            progresso.progress(
                int(((i + 1) / total) * 70)
            )

        video = concatenate_videoclips(
            clips,
            method="compose"
        )

        progresso.progress(75)

        musica_clip = None

        if musica:

            extensao = Path(musica.name).suffix
            caminho_musica = os.path.join(
                temp_dir,
                f"musica{extensao}"
            )

            with open(caminho_musica, "wb") as f:
                f.write(musica.getbuffer())

            musica_clip = AudioFileClip(
                caminho_musica
            )

            if musica_clip.duration < video.duration:
                repeticoes = int(
                    video.duration /
                    musica_clip.duration
                ) + 1

                musica_partes = [
                    musica_clip
                    for _ in range(repeticoes)
                ]

                musica_clip = concatenate_videoclips(
                    musica_partes
                )

            musica_clip = (
                musica_clip
                .subclipped(0, video.duration)
                .with_volume_scaled(
                    volume_musica / 100
                )
            )

            if video.audio:
                audio_final = CompositeAudioClip(
                    [
                        video.audio,
                        musica_clip
                    ]
                )
            else:
                audio_final = musica_clip

            video = video.with_audio(
                audio_final
            )

        progresso.progress(80)

        saida = os.path.join(
            temp_dir,
            "video_final.mp4"
        )

        video.write_videofile(
            saida,
            fps=24,
            codec="libx264",
            audio_codec="aac",
            preset="medium",
            threads=2
        )

        progresso.progress(100)

        st.success("✅ Vídeo criado!")

        st.video(saida)

        with open(saida, "rb") as arquivo_video:
            st.download_button(
                "⬇️ BAIXAR VÍDEO MP4",
                arquivo_video,
                file_name="video_final.mp4",
                mime="video/mp4"
            )

        video.close()

        for clip in clips:
            clip.close()

        for audio in audios_abertos:
            audio.close()

        if musica_clip:
            musica_clip.close()

    except Exception as erro:
        st.error("❌ Não foi possível criar o vídeo.")
        st.exception(erro)
