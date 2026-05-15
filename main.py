import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode
import av
import cv2
from pyzbar.pyzbar import decode
import queue

# 1. Inicializa o estado para controlar se o resultado já foi encontrado
if "scanned_result" not in st.session_state:
    st.session_state.scanned_result = None

st.title("Mobile Barcode Scanner")

# 2. Se já encontramos um resultado, paramos o scanner e mostramos o botão de reiniciar
if st.session_state.scanned_result:
    st.success(f"✅ Resultado: {st.session_state.scanned_result}")

    # Botão para limpar o resultado e reativar o scanner
    if st.button("🔄 Voltar a Ativar o Scanner"):
        st.session_state.scanned_result = None
        st.rerun()  # Atualiza a tela para voltar ao bloco do 'else'

else:
    # Set up a thread-safe queue to store detected barcode data
    result_queue = queue.Queue()


    def video_frame_callback(frame):
        img = frame.to_ndarray(format="bgr24")

        # Decode barcodes from the frame
        barcodes = decode(img)

        for barcode in barcodes:
            barcode_data = barcode.data.decode("utf-8")
            barcode_type = barcode.type

            # Put the data into the queue for the main thread to read
            result_queue.put(f"{barcode_type}: {barcode_data}")

            # Draw a bounding box on the video frame
            (x, y, w, h) = barcode.rect
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(img, barcode_data, (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        return av.VideoFrame.from_ndarray(img, format="bgr24")

    # 3. Gerando uma chave dinâmica única para cada tentativa (ex: "barcode-scanner-0", "barcode-scanner-1"...)
    dynamic_key = f"barcode-scanner-{st.session_state.scanner_key_counter}"

    # WebRTC Streamer configuration
    ctx = webrtc_streamer(
        key=dynamic_key,
        mode=WebRtcMode.SENDRECV,
        video_frame_callback=video_frame_callback,
        media_stream_constraints={
            "video": {"facingMode": "environment"},  # Requests back camera
            "audio": False
        },
        async_processing=True,
        rtc_configuration={
            "iceServers": [
                {"urls": ["stun:stun.l.google.com:19302"]},
                {"urls": ["stun:stun1.l.google.com:19302"]},
                {"urls": ["stun:stun2.l.google.com:19302"]},
            ]
        }
    )

    st.subheader("Scanned Results:")

    # 3. Loop modificado para salvar o estado e interromper
    while ctx.state.playing:
        try:
            # Get data from the queue without blocking
            result = result_queue.get(timeout=1.0)

            if result:
                # Salva o resultado na memória do Streamlit
                st.session_state.scanned_result = result
                # Força o recarregamento do script para esconder o scanner e mostrar o botão
                st.rerun()
                break  # Interrompe o loop while imediatamente

        except queue.Empty:
            continue