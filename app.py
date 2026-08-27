import streamlit as st
import os
import tempfile
from pathlib import Path

from moviepy import (
    ImageClip,
    AudioFileClip,
    concatenate_videoclips,
    concatenate_audioclips,
    CompositeAudioClip,
)

# ==========================================
# CONFIGURAÇÃO
# ==========================================

st.set_page_config(
    page_title="Montador de Vídeo IA",
    page_icon="🎬",
    layout="centered"
)

st.title("🎬 Montador de Vídeo com Imagens e Som")

st.write(
    "Envie suas imagens e os áudios das falas. "
    "O app monta as cenas e cria um vídeo MP4."
)


# ==========================================
# FORMATO DO VÍDEO
# ==========================================

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


# ==========================================
# UPLOAD DAS IMAGENS
# ==========================================

imagens = st.file_uploader(
    "📷 Envie as imagens das cenas",
    type=[
        "png",
        "jpg",
        "jpeg",
        "webp"
    ],
    accept_multiple_files=True
)


# ==========================================
# UPLOAD DOS ÁUDIOS
# ==========================================

audios = st.file_uploader(
    "🎤 Envie as falas/áudios das cenas",
    type=[
        "mp3",
        "wav",
        "m4a",
        "aac"
    ],
    accept_multiple_files=True
)


# ==========================================
# MÚSICA DE FUNDO
# ==========================================

musica = st.file_uploader(
    "🎵 Música de fundo (opcional)",
    type=[
        "mp3",
        "wav",
        "m4a",
        "aac"
    ]
)

volume_musica = st.slider(
    "🔊 Volume da música de fundo",
    min_value=0,
    max_value=100,
    value=15
)


# ==========================================
# DURAÇÃO SEM ÁUDIO
# ==========================================

duracao_sem_audio = st.slider(
    "⏱️ Duração da imagem quando não houver fala",
    min_value=2,
    max_value=15,
    value=5
)


st.info(
    "💡 Para manter tudo na ordem, use nomes como: "
    "01.jpg + 01.mp3, "
    "02.jpg + 02.mp3, "
    "03.jpg + 03.mp3."
)


# ==========================================
# ORDENAR ARQUIVOS
# ==========================================

def ordenar_arquivos(arquivos):

    if not arquivos:
        return []

    return sorted(
        arquivos,
        key=lambda arquivo: arquivo.name.lower()
    )


# ==========================================
# AJUSTAR IMAGEM
# ==========================================

def ajustar_imagem(
    clip,
    largura,
    altura
):

    proporcao_video = largura / altura
    proporcao_imagem = clip.w / clip.h

    if proporcao_imagem > proporcao_video:

        clip = clip.resized(
            height=altura
        )

    else:

        clip = clip.resized(
            width=largura
        )

    x1 = max(
        0,
        (clip.w - largura) / 2
    )

    y1 = max(
        0,
        (clip.h - altura) / 2
    )

    clip = clip.cropped(
        x1=x1,
        y1=y1,
        width=largura,
        height=altura
    )

    return clip


# ==========================================
# CRIAR VÍDEO
# ==========================================

if st.button(
    "🎬 CRIAR VÍDEO",
    type="primary",
    use_container_width=True
):

    if not imagens:

        st.error(
            "❌ Envie pelo menos uma imagem."
        )

        st.stop()


    # ======================================
    # PASTA TEMPORÁRIA
    # ======================================

    temp_dir = tempfile.mkdtemp()


    try:

        # ==================================
        # ORDENAR
        # ==================================

        imagens_ordenadas = ordenar_arquivos(
            imagens
        )

        audios_ordenados = ordenar_arquivos(
            audios
        )


        # ==================================
        # SALVAR IMAGENS
        # ==================================

        caminhos_imagens = []

        for i, arquivo in enumerate(
            imagens_ordenadas
        ):

            extensao = Path(
                arquivo.name
            ).suffix.lower()

            caminho = os.path.join(
                temp_dir,
                f"imagem_{i:03d}{extensao}"
            )

            with open(
                caminho,
                "wb"
            ) as f:

                f.write(
                    arquivo.getbuffer()
                )

            caminhos_imagens.append(
                caminho
            )


        # ==================================
        # SALVAR ÁUDIOS
        # ==================================

        caminhos_audios = []

        for i, arquivo in enumerate(
            audios_ordenados
        ):

            extensao = Path(
                arquivo.name
            ).suffix.lower()

            caminho = os.path.join(
                temp_dir,
                f"audio_{i:03d}{extensao}"
            )

            with open(
                caminho,
                "wb"
            ) as f:

                f.write(
                    arquivo.getbuffer()
                )

            caminhos_audios.append(
                caminho
            )


        # ==================================
        # MONTAGEM
        # ==================================

        st.write(
            "⏳ Montando as cenas..."
        )

        progresso = st.progress(0)

        clips = []

        total = len(
            caminhos_imagens
        )


        # ==================================
        # CRIAR CENAS
        # ==================================

        for i, caminho_imagem in enumerate(
            caminhos_imagens
        ):

            audio_clip = None


            # ==============================
            # ÁUDIO DA CENA
            # ==============================

            if i < len(
                caminhos_audios
            ):

                audio_clip = AudioFileClip(
                    caminhos_audios[i]
                )

                duracao = (
                    audio_clip.duration
                    + 0.3
                )

            else:

                duracao = (
                    duracao_sem_audio
                )


            # ==============================
            # IMAGEM
            # ==============================

            imagem_clip = ImageClip(
                caminho_imagem
            )

            imagem_clip = (
                imagem_clip
                .with_duration(
                    duracao
                )
            )

            imagem_clip = ajustar_imagem(
                imagem_clip,
                largura,
                altura
            )


            # ==============================
            # COLOCAR VOZ NA IMAGEM
            # ==============================

            if audio_clip is not None:

                imagem_clip = (
                    imagem_clip
                    .with_audio(
                        audio_clip
                    )
                )


            clips.append(
                imagem_clip
            )


            porcentagem = int(
                ((i + 1) / total)
                * 70
            )

            progresso.progress(
                porcentagem
            )


        # ==================================
        # JUNTAR TODAS AS CENAS
        # ==================================

        video = concatenate_videoclips(
            clips,
            method="compose"
        )

        progresso.progress(75)


        # ==================================
        # MÚSICA DE FUNDO
        # ==================================

        musica_original = None
        musica_final = None

        if musica:

            extensao = Path(
                musica.name
            ).suffix.lower()

            caminho_musica = os.path.join(
                temp_dir,
                f"musica{extensao}"
            )

            with open(
                caminho_musica,
                "wb"
            ) as f:

                f.write(
                    musica.getbuffer()
                )


            musica_original = AudioFileClip(
                caminho_musica
            )


            # ==============================
            # REPETIR MÚSICA SE NECESSÁRIO
            # ==============================

            if (
                musica_original.duration
                < video.duration
            ):

                repeticoes = int(
                    video.duration
                    / musica_original.duration
                ) + 1

                partes_musica = []

                for _ in range(
                    repeticoes
                ):

                    partes_musica.append(
                        musica_original
                    )


                musica_final = (
                    concatenate_audioclips(
                        partes_musica
                    )
                )

            else:

                musica_final = (
                    musica_original
                )


            # ==============================
            # CORTAR NO TAMANHO DO VÍDEO
            # ==============================

            musica_final = (
                musica_final
                .subclipped(
                    0,
                    video.duration
                )
            )


            # ==============================
            # VOLUME DA MÚSICA
            # ==============================

            musica_final = (
                musica_final
                .with_volume_scaled(
                    volume_musica
                    / 100
                )
            )


            # ==============================
            # MISTURAR VOZ + MÚSICA
            # ==============================

            if video.audio is not None:

                audio_final = (
                    CompositeAudioClip(
                        [
                            video.audio,
                            musica_final
                        ]
                    )
                )

            else:

                audio_final = (
                    musica_final
                )


            video = video.with_audio(
                audio_final
            )


        progresso.progress(80)


        # ==================================
        # ARQUIVO FINAL
        # ==================================

        saida = os.path.join(
            temp_dir,
            "video_final.mp4"
        )


        st.write(
            "🎞️ Criando o arquivo MP4..."
        )


        video.write_videofile(
            saida,
            fps=24,
            codec="libx264",
            audio_codec="aac",
            preset="medium",
            threads=2,
            logger=None
        )


        progresso.progress(100)


        # ==================================
        # SUCESSO
        # ==================================

        st.success(
            "✅ Vídeo criado com sucesso!"
        )


        # ==================================
        # MOSTRAR VÍDEO
        # ==================================

        st.video(
            saida
        )


        # ==================================
        # DOWNLOAD
        # ==================================

        with open(
            saida,
            "rb"
        ) as arquivo_video:

            dados_video = (
                arquivo_video.read()
            )


        st.download_button(
            label="⬇️ BAIXAR VÍDEO MP4",
            data=dados_video,
            file_name="video_final.mp4",
            mime="video/mp4",
            use_container_width=True
        )


    except Exception as erro:

        st.error(
            "❌ Não foi possível criar o vídeo."
        )

        st.exception(
            erro
        )
