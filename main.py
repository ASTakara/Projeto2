import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode
import av
import cv2
from pyzbar.pyzbar import decode
import queue
import time

st.title("Mobile Barcode Scanner")

# 1. Gerencia o estado do resultado e a chave única do scanner
if "scanned_result" not in st.session_state:
    st.session_state["scanned_result"] = None

if "scanner_session_id" not in st.session_state:
    st.session_state["scanner_session_id"] = int(time.time())

# Containers fixos na tela
container_camera = st.empty()
container_resultado = st.empty()
container_botao = st.empty()

# 2. SE JÁ FOI ESCANEADO: Mostra resultado e botão de reset
if st.session_state["scanned_result"]:
    container_resultado.success(f"✅ Lido com sucesso: {st.session_state['scanned_result']}")

    with container_botao:
        if st.button("🔄 Escanear Próximo Código"):
            # Limpa o resultado anterior
            st.session_state["scanned_result"] = None
            # Força uma ID de conexão WebRTC totalmente nova
            st.session_state["scanner_session_id"] = int(time.time())
            st.rerun()

# 3. SE NÃO FOI ESCANEADO: Ativa o scanner normalmente
else:
    result_queue = queue.Queue()


    def video_frame_callback(frame):
        img = frame.to_ndarray(format="bgr24")
        barcodes = decode(img)

        for barcode in barcodes:
            barcode_data = barcode.data.decode("utf-8")
            barcode_type = barcode.type

            result_queue.put(f"{barcode_type}: {barcode_data}")

            (x, y, w, h) = barcode.rect
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(img, barcode_data, (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # LINHA CORRIGIDA: Agora está dentro da função video_frame_callback
        return av.VideoFrame.from_ndarray(img, format="bgr24")


    # A key muda a cada clique de reiniciar para limpar o cache do navegador
    unique_key = f"barcode-scanner-{st.session_state['scanner_session_id']}"

    with container_camera.container():
        ctx = webrtc_streamer(
            key=unique_key,
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

    # Loop de escuta ativo
    while ctx.state.playing:
        try:
            result = result_queue.get(timeout=0.5)

            if result:
                # Salva o resultado no estado global do Streamlit
                st.session_state["scanned_result"] = result
                # Limpa a câmera da tela imediatamente
                container_camera.empty()
                # Recarrega o app para entrar no bloco do 'if' (destruindo o webrtc antigo)
                st.rerun()
                break

        except queue.Empty:
            continue