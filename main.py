import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode
import av
import cv2
from pyzbar.pyzbar import decode
import queue
import time

st.title("Mobile Barcode Scanner")

# Inicialização segura do estado
if "scanned_result" not in st.session_state:
    st.session_state["scanned_result"] = None

if "scanner_session_id" not in st.session_state:
    st.session_state["scanner_session_id"] = int(time.time())

container_camera = st.empty()
container_resultado = st.empty()
container_botao = st.empty()

# 1. SE JÁ FOI ESCANEADO: Mostra o resultado e o botão
if st.session_state.get("scanned_result"):
    container_resultado.success(f"✅ Lido com sucesso: {st.session_state['scanned_result']}")

    with container_botao:
        if st.button("🔄 Escanear Próximo Código"):
            st.session_state["scanned_result"] = None
            st.session_state["scanner_session_id"] = int(time.time())
            st.rerun()

# 2. SE NÃO FOI ESCANEADO: Abre o scanner
else:
    # Usamos o st.cache_resource para garantir que a fila não se perca entre renders rápidos
    @st.cache_resource
    def get_queue():
        return queue.Queue()


    result_queue = get_queue()


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

        return av.VideoFrame.from_ndarray(img, format="bgr24")


    session_id = st.session_state.get("scanner_session_id", int(time.time()))

    with container_camera.container():
        ctx = webrtc_streamer(
            key=f"barcode-scanner-{session_id}",
            mode=WebRtcMode.SENDRECV,
            video_frame_callback=video_frame_callback,
            media_stream_constraints={
                "video": {"facingMode": "environment"},
                "audio": False
            },
            async_processing=True,
            rtc_configuration={
                "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
            }
        )

    container_resultado.subheader("Scanned Results:")

    # Checagem passiva (sem loop while infinito bloqueando a CPU)
    if ctx.state.playing:
        try:
            # Tenta pegar um resultado de forma direta e rápida
            result = result_queue.get_nowait()
            if result:
                st.session_state["scanned_result"] = result
                container_camera.empty()
                st.rerun()
        except queue.Empty:
            # Se a fila estiver vazia, adicionamos um pequeno botão de "Atualizar Interface"
            # ou simplesmente deixamos o webrtc atualizar nativamente
            st.caption("Aguardando leitura do código de barras...")