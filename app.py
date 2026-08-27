import os
import asyncio
import tempfile

import streamlit as st
from moviepy import (
    ImageClip,
    AudioFileClip,
    CompositeVideoClip,
    concatenate_videoclips,
)
from PIL import Image
import numpy as np
import edge_tts


# =========================================================
# CONFIGURACAO DO APP
# =========================================================

st.set_page_config(
    page_title="Criador de Video",
    page_icon="🎬",
    layout="centered",
)

st.title("🎬 Criador de vídeo")
st.write(
    "Envie as imagens das cenas e escolha a voz da narradora. "
    "O app cria um MP4 1280×720 com narração."
)


# =========================================================
# VOZES
# =========================================================

VOZES = {
    "👩 Feminina suave": {
        "voice": "pt-BR-FranciscaNeural",
        "rate": "-10%",
        "pitch": "+0Hz",
    },
    "👧 Feminina mais infantil": {
        "voice": "pt-BR-FranciscaNeural",
        "rate": "+5%",
        "pitch": "+15Hz",
    },
    "👩 Feminina adulta": {
        "voice": "pt-BR-FranciscaNeural",
        "rate": "-2%",
        "pitch": "-5Hz",
    },
    "👨 Masculina": {
        "voice": "pt-BR-AntonioNeural",
        "rate": "-5%",
        "pitch": "+0Hz",
    },
    "🌙 Conto calmo": {
        "voice": "pt-BR-FranciscaNeural",
        "rate": "-20%",
        "pitch": "-2Hz",
    },
    "🕯️ Dramática / sombria": {
        "voice": "pt-BR-FranciscaNeural",
        "rate": "-12%",
        "pitch": "-8Hz",
    },
}


async def gerar_narracao_async(texto, caminho_saida, voice, rate, pitch):
    comunicador = edge_tts.Communicate(
        text=texto,
        voice=voice,
        rate=rate,
        pitch=pitch,
    )
    await comunicador.save(caminho_saida)


def gerar_narracao(texto, caminho_saida, voice, rate, pitch):
    asyncio.run(
        gerar_narracao_async(
            texto=texto,
            caminho_saida=caminho_saida,
            voice=voice,
            rate=rate,
            pitch=pitch,
        )
    )


# =========================================================
# IMAGEM 16:9
# =========================================================

def preparar_imagem(imagem, largura=1280, altura=720):
    """
    Ajusta uma imagem PIL para preencher 1280x720 sem faixas brancas.
    """
    img = imagem.convert("RGB")

    proporcao_img = img.width / img.height
    proporcao_video = largura / altura

    if proporcao_img > proporcao_video:
        nova_altura = altura
        nova_largura = round(img.width * altura / img.height)
    else:
        nova_largura = largura
        nova_altura = round(img.height * largura / img.width)

    img = img.resize(
        (nova_largura, nova_altura),
        Image.Resampling.LANCZOS,
    )

    esquerda = max(0, (nova_largura - largura) // 2)
    topo = max(0, (nova_altura - altura) // 2)

    img = img.crop(
        (
            esquerda,
            topo,
            esquerda + largura,
            topo + altura,
        )
    )

    return np.array(img)


def criar_clip_com_zoom(frame, duracao, largura=1280, altura=720):
    """
    Cria um zoom suave mantendo o quadro em 1280x720.
    """
    base = ImageClip(frame).with_duration(duracao)

    zoom = base.resized(
        lambda t: 1.0 + 0.05 * (t / max(duracao, 0.001))
    ).with_position(("center", "center"))

    return CompositeVideoClip(
        [zoom],
        size=(largura, altura),
    ).with_duration(duracao)


# =========================================================
# CRIAR VIDEO
# =========================================================

def criar_video(
    imagens,
    arquivo_audio=None,
    duracao_cena=5,
    arquivo_saida="video_final.mp4",
):
    if not imagens:
        raise ValueError("Nenhuma imagem foi enviada.")

    clips = []

    for imagem in imagens:
        frame = preparar_imagem(imagem)
        clip = criar_clip_com_zoom(frame, duracao_cena)
        clips.append(clip)

    video = concatenate_videoclips(clips, method="compose")
    audio = None

    try:
        if arquivo_audio and os.path.exists(arquivo_audio):
            audio = AudioFileClip(arquivo_audio)

            # Ajusta o vídeo ao tamanho do áudio
            if audio.duration < video.duration:
                video = video.subclipped(0, audio.duration)

            if audio.duration > video.duration:
                audio = audio.subclipped(0, video.duration)

            video = video.with_audio(audio)

        video.write_videofile(
            arquivo_saida,
            fps=24,
            codec="libx264",
            audio_codec="aac",
            preset="medium",
            threads=2,
            logger=None,
        )

        return arquivo_saida

    finally:
        if audio is not None:
            audio.close()

        for clip in clips:
            clip.close()

        video.close()


# =========================================================
# INTERFACE
# =========================================================

arquivos_imagem = st.file_uploader(
    "🖼️ Escolha as imagens das cenas",
    type=["png", "jpg", "jpeg", "webp"],
    accept_multiple_files=True,
)

st.subheader("🎙️ Narração")

modo_audio = st.radio(
    "Como você quer a narração?",
    ["Gerar voz no app", "Enviar áudio pronto", "Sem narração"],
)

texto_narracao = ""
voz_escolhida = None
arquivo_audio_enviado = None

if modo_audio == "Gerar voz no app":
    texto_narracao = st.text_area(
        "Cole aqui o texto da narradora",
        height=180,
        placeholder="Era uma vez...",
    )

    voz_escolhida = st.selectbox(
        "Escolha a voz da narradora",
        list(VOZES.keys()),
    )

    st.caption(
        "A voz infantil, calma e dramática usa ajustes de velocidade "
        "e tom para mudar o estilo da narração."
    )

elif modo_audio == "Enviar áudio pronto":
    arquivo_audio_enviado = st.file_uploader(
        "Envie a narração",
        type=["mp3", "wav", "m4a", "aac"],
    )

duracao_cena = st.slider(
    "⏱️ Duração de cada cena",
    min_value=2,
    max_value=15,
    value=5,
    step=1,
)

if arquivos_imagem:
    st.write(f"✅ {len(arquivos_imagem)} imagem(ns) selecionada(s).")

    with st.expander("Ver imagens"):
        for i, arquivo in enumerate(arquivos_imagem, start=1):
            st.image(
                arquivo,
                caption=f"Cena {i}",
                use_container_width=True,
            )


if st.button("🎬 Criar vídeo final", type="primary"):
    if not arquivos_imagem:
        st.warning("Envie pelo menos uma imagem.")
        st.stop()

    if modo_audio == "Gerar voz no app" and not texto_narracao.strip():
        st.warning("Digite o texto da narração.")
        st.stop()

    imagens = []

    for arquivo in arquivos_imagem:
        arquivo.seek(0)
        imagens.append(Image.open(arquivo).copy())

    caminho_audio = None
    temp_audio = None
    caminho_video = None

    try:
        if modo_audio == "Gerar voz no app":
            temp_audio = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".mp3",
            )
            temp_audio.close()

            config_voz = VOZES[voz_escolhida]

            with st.spinner("Gerando a voz da narradora..."):
                gerar_narracao(
                    texto=texto_narracao.strip(),
                    caminho_saida=temp_audio.name,
                    voice=config_voz["voice"],
                    rate=config_voz["rate"],
                    pitch=config_voz["pitch"],
                )

            caminho_audio = temp_audio.name

        elif modo_audio == "Enviar áudio pronto" and arquivo_audio_enviado:
            extensao = os.path.splitext(
                arquivo_audio_enviado.name
            )[1] or ".mp3"

            temp_audio = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=extensao,
            )
            temp_audio.write(arquivo_audio_enviado.getbuffer())
            temp_audio.close()

            caminho_audio = temp_audio.name

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".mp4",
        ) as temp_video:
            caminho_video = temp_video.name

        with st.spinner("Montando o vídeo..."):
            criar_video(
                imagens=imagens,
                arquivo_audio=caminho_audio,
                duracao_cena=duracao_cena,
                arquivo_saida=caminho_video,
            )

        with open(caminho_video, "rb") as f:
            video_bytes = f.read()

        st.success("✅ Vídeo criado com sucesso!")
        st.video(video_bytes)

        st.download_button(
            "⬇️ Baixar vídeo MP4",
            data=video_bytes,
            file_name="video_final.mp4",
            mime="video/mp4",
        )

    except Exception as erro:
        st.error(f"Não foi possível criar o vídeo: {erro}")

    finally:
        if temp_audio is not None and os.path.exists(temp_audio.name):
            os.remove(temp_audio.name)

        if caminho_video and os.path.exists(caminho_video):
            os.remove(caminho_video)
