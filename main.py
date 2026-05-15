import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode
import av
import cv2
from pyzbar.pyzbar import decode
import queue

st.title("Mobile Barcode Scanner")

# Criamos containers vazios para controlar a ordem visual da tela de forma fixa
container_camera = st.empty()
container_resultado = st.empty()
container_botao = st.empty()

# Inicializa as filas e variáveis apenas uma vez na sessão
if "fila_resultados" not in st.session_state:
    st.session_state["fila_resultados"] = queue.Queue()


# Função de callback da câmera
def video_frame_callback(frame):
    img = frame.to_ndarray(format="bgr24")
    barcodes = decode(img)

    for barcode in barcodes:
        barcode_data = barcode.data.decode("utf-8")
        barcode_type = barcode.type

        # Envia para a fila global da sessão
        st.session_state["fila_resultados"].put(f"{barcode_type}: {barcode_data}")

        (x, y, w, h) = barcode.rect
        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(img, barcode_data, (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    return av.VideoFrame.from_ndarray(img, format="bgr24")


# Renderiza o Scanner dentro do container de câmera
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

# Loop de escuta ativo enquanto a câmera estiver ligada
while ctx.state.playing:
    try:
        # Puxa o dado da fila armazenada na sessão
        result = st.session_state["fila_resultados"].get(timeout=1.0)

        if result:
            # 1. Mostra o resultado imediatamente na tela
            container_resultado.success(f"✅ Encontrado: {result}")

            # 2. Desliga visualmente a câmera limpando o container dela
            container_camera.empty()

            # 3. Cria o botão de reiniciar dentro do container de botões
            with container_botao:
                if st.button("🔄 Ativar Scanner Novamente"):
                    # Limpa a fila antiga
                    st.session_state["fila_resultados"] = queue.Queue()
                    st.rerun()

            # Interrompe o loop do código atual
            break

    except queue.Empty:
        continue