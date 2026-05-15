import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode
import av
import cv2
from pyzbar.pyzbar import decode
import queue

st.title("Mobile Barcode Scanner")

# 1. Estados essenciais na memória (Seguros e persistentes)
if "scanner_ativo" not in st.session_state:
    st.session_state["scanner_ativo"] = True

if "ultimo_resultado" not in st.session_state:
    st.session_state["ultimo_resultado"] = None


# Criamos a fila no cache para que ela nunca seja destruída entre os ciclos de render
@st.cache_resource
def obter_fila():
    return queue.Queue()


result_queue = obter_fila()

# 2. Interface de exibição do resultado se houver um código escaneado
if st.session_state["ultimo_resultado"]:
    st.success(f"✅ Lido com sucesso: {st.session_state['ultimo_resultado']}")

    if st.button("🔄 Escanear Próximo Código"):
        # Esvazia a fila antiga para não ler dados fantasmas
        while not result_queue.empty():
            try:
                result_queue.get_nowait()
            except queue.Empty:
                break

        # Limpa o resultado anterior e reativa a permissão de leitura
        st.session_state["ultimo_resultado"] = None
        st.session_state["scanner_ativo"] = True
        st.rerun()


# 3. Função de processamento de imagem
def video_frame_callback(frame):
    img = frame.to_ndarray(format="bgr24")

    # SÓ tenta ler se o scanner estiver ativamente esperando uma leitura
    if st.session_state.get("scanner_ativo", True):
        barcodes = decode(img)

        for barcode in barcodes:
            barcode_data = barcode.data.decode("utf-8")
            barcode_type = barcode.type

            # Envia para a fila
            result_queue.put(f"{barcode_type}: {barcode_data}")

            # Desenho estético do box
            (x, y, w, h) = barcode.rect
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(img, barcode_data, (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    return av.VideoFrame.from_ndarray(img, format="bgr24")


# 4. Componente estático (Chave fixa impede o colapso do asyncio no Python 3.14)
ctx = webrtc_streamer(
    key="barcode-scanner-fixed-stable",
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

# 5. Escuta de resultados sem o loop "while" agressivo
if ctx.state.playing and st.session_state["scanner_ativo"]:
    try:
        # Tenta pegar o resultado de forma imediata (sem travar a CPU do servidor)
        result = result_queue.get_nowait()
        if result:
            # Desativa o scanner para ignorar novas leituras na thread paralela
            st.session_state["scanner_ativo"] = False
            # Salva o resultado encontrado
            st.session_state["ultimo_resultado"] = result
            st.rerun()
    except queue.Empty:
        st.caption("Aguardando leitura do código de barras...")