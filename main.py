import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode
import av
import cv2
from pyzbar.pyzbar import decode
import queue

st.title("Mobile Barcode Scanner")

# 1. Estados estáveis na memória
if "scanner_ativo" not in st.session_state:
    st.session_state["scanner_ativo"] = True

if "ultimo_resultado" not in st.session_state:
    st.session_state["ultimo_resultado"] = None


# Garante que a fila persista sem reiniciar
@st.cache_resource
def obter_fila_estavel():
    return queue.Queue()


result_queue = obter_fila_estavel()

# 2. SE JÁ LERU: Exibe o resultado e pausa a câmera
if st.session_state["ultimo_resultado"]:
    st.success(f"✅ Lido com sucesso: {st.session_state['ultimo_resultado']}")

    if st.button("🔄 Escanear Próximo Código"):
        # Limpa restos que ficaram na fila antes de reativar
        while not result_queue.empty():
            try:
                result_queue.get_nowait()
            except queue.Empty:
                break
        st.session_state["ultimo_resultado"] = None
        st.session_state["scanner_ativo"] = True
        st.rerun()

# 3. SE NÃO LEU: Mantém o Scanner ativo na tela
else:
    def video_frame_callback(frame):
        img = frame.to_ndarray(format="bgr24")

        # Só processa se o estado do app permitir leitura
        if st.session_state.get("scanner_ativo", True):
            barcodes = decode(img)
            for barcode in barcodes:
                barcode_data = barcode.data.decode("utf-8")

                # Alimenta a fila compartilhada
                result_queue.put(barcode_data)

                # Feedback visual direto no frame do vídeo
                (x, y, w, h) = barcode.rect
                cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(img, barcode_data, (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        return av.VideoFrame.from_ndarray(img, format="bgr24")


    # Chave 100% estática para blindar o asyncio contra o bug do Python 3.14
    ctx = webrtc_streamer(
        key="barcode-scanner-engine-fixed",
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

    st.subheader("Scanned Results:")
    status_placeholder = st.empty()

    # O segredo: Ouvinte seguro da fila que respeita a conexão do webrtc
    if ctx.state.playing:
        status_placeholder.info("📷 Scanner ativo. Aproxime o código de barras...")

        # Um loop simples interno, limitado apenas enquanto o player de vídeo estiver aberto
        while ctx.state.playing:
            try:
                # Aguarda até 0.5 segundos por um dado na fila sem travar a thread principal
                resultado_capturado = result_queue.get(timeout=0.5)

                if resultado_capturado:
                    st.session_state["scanner_ativo"] = False
                    st.session_state["ultimo_resultado"] = resultado_capturado
                    st.rerun()
                    break
            except queue.Empty:
                continue
    else:
        status_placeholder.warning("Clique no botão 'Start' acima para ligar a câmera.")