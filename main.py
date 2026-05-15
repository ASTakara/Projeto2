import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, VideoProcessorBase
import av
import cv2
from pyzbar.pyzbar import decode
import queue


# 1. ESCOPO GLOBAL: Processador de Vídeo utilizando uma Fila Estável
class BarcodeProcessor(VideoProcessorBase):
    def __init__(self, result_queue):
        self.result_queue = result_queue

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        img = frame.to_ndarray(format="bgr24")

        barcodes = decode(img)
        for barcode in barcodes:
            barcode_data = barcode.data.decode("utf-8")

            # Coloca o resultado na fila se ela estiver vazia
            if self.result_queue.empty():
                self.result_queue.put(barcode_data)

            # Desenha na tela
            (x, y, w, h) = barcode.rect
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(img, barcode_data, (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        return av.VideoFrame.from_ndarray(img, format="bgr24")


# 2. INTERFACE PRINCIPAL
st.title("Mobile Barcode Scanner Pro")


# Criamos uma fila persistente usando cache do Streamlit para não reiniciar a cada render
@st.cache_resource
def obter_fila():
    return queue.Queue()


fila_resultados = obter_fila()

if "ultimo_resultado" not in st.session_state:
    st.session_state["ultimo_resultado"] = None

# Botão manual para limpar o estado anterior, se houver
if st.session_state["ultimo_resultado"]:
    st.success(f"✅ Lido com sucesso: {st.session_state['ultimo_resultado']}")
    st.json({"status": "Processado", "conteudo": st.session_state["ultimo_resultado"]})

    if st.button("🔄 Escanear Próximo Código"):
        st.session_state["ultimo_resultado"] = None
        # Limpa qualquer dado residual na fila
        while not fila_resultados.empty():
            try:
                fila_resultados.get_nowait()
            except queue.Empty:
                break
        st.rerun()

else:
    # Inicializa o webrtc streamer passando a nossa fila para a factory
    ctx = webrtc_streamer(
        key="barcode-scanner-safeloop",
        mode=WebRtcMode.SENDRECV,
        video_processor_factory=lambda: BarcodeProcessor(fila_resultados),
        media_stream_constraints={
            "video": {"facingMode": "environment"},
            "audio": False
        },
        async_processing=True,
        rtc_configuration={
            "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
        }
    )

    # Exibe informações abaixo da câmera
    status_placeholder = st.empty()

    if ctx.state.playing:
        status_placeholder.info("📷 Scanner ativo. Aproxime o código de barras...")

        # Em vez de dar rerun automático, verificamos se algo entrou na fila de forma não-bloqueante
        try:
            # Tenta pegar o resultado sem esperar (get_nowait)
            # Isso roda limpo a cada interação natural do usuário ou frame recebido, sem forçar um crash do loop assíncrono
            resultado_detectado = fila_resultados.get_nowait()
            if resultado_detectado:
                st.session_state["ultimo_resultado"] = resultado_detectado
                st.rerun()
        except queue.Empty:
            # Se a fila estiver vazia, adicionamos um pequeno botão discreto de checagem/atualização automática
            # O próprio ato de interagir ou deixar o componente ativo atualizará o frame
            if st.button("Verificar Leitura Manuscrita / Atualizar"):
                st.rerun()
    else:
        status_placeholder.warning("Clique no botão 'Start' acima para iniciar a câmera.")