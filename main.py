import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode
import av
import cv2
from pyzbar.pyzbar import decode
import queue

st.title("Mobile Barcode Scanner")

# Containers para organizar a tela dinamicamente
container_camera = st.empty()
container_resultado = st.empty()
container_botao = st.empty()

# Criamos a fila no escopo correto para garantir a leitura em tempo real
result_queue = queue.Queue()


def video_frame_callback(frame):
    img = frame.to_ndarray(format="bgr24")
    barcodes = decode(img)

    for barcode in barcodes:
        barcode_data = barcode.data.decode("utf-8")
        barcode_type = barcode.type

        # Envia o dado para a fila local (rápido e seguro entre threads)
        result_queue.put(f"{barcode_type}: {barcode_data}")

        # Desenha na tela do player de vídeo
        (x, y, w, h) = barcode.rect
        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(img, barcode_data, (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    return av.VideoFrame.from_ndarray(img, format="bgr24")


# Renderiza o Scanner dentro de seu respectivo container
with container_camera.container():
    ctx = webrtc_streamer(
        key="barcode-scanner-static",
        mode=WebRtcMode.SENDRECV,
        video_frame_callback=video_frame_callback,
        media_stream_constraints={
            "video": {"facingMode": "environment"},
            "audio": False
        },
        async_processing=True,
        rtc_configuration={
            "iceServers": [
                {"urls": ["stun:stun.l.google.com:19302"]},
                {"urls": ["stun:stun1.l.google.com:19302"]}
            ]
        }
    )

container_resultado.subheader("Scanned Results:")

# Loop de leitura (Roda enquanto a câmera estiver ativa no navegador)
while ctx.state.playing:
    try:
        # Escuta a fila local sem bloquear o carregamento da página
        result = result_queue.get(timeout=0.5)

        if result:
            # 1. Limpa o container da câmera (desliga o vídeo na tela)
            container_camera.empty()

            # 2. Exibe o resultado de sucesso fixo na tela
            container_resultado.success(f"✅ Lido com sucesso: {result}")

            # 3. Exibe o botão para reiniciar o fluxo
            with container_botao:
                if st.button("🔄 Escanear Próximo Código"):
                    st.rerun()

            # Rompe o loop while para congelar o estado do app
            break

    except queue.Empty:
        continue