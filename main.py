import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, VideoProcessorBase
import av
import cv2
from pyzbar.pyzbar import decode
import streamlit.components.v1 as components


# ==========================================
# 1. ESCOPO GLOBAL: Processador de Vídeo
# ==========================================
class BarcodeProcessor(VideoProcessorBase):
    def __init__(self):
        self.resultado = None

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        img = frame.to_ndarray(format="bgr24")

        # Só processa se ainda não capturou nada neste ciclo
        if self.resultado is None:
            barcodes = decode(img)
            for barcode in barcodes:
                barcode_data = barcode.data.decode("utf-8")
                self.resultado = barcode_data

                # Feedback visual na tela
                (x, y, w, h) = barcode.rect
                cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(img, barcode_data, (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        return av.VideoFrame.from_ndarray(img, format="bgr24")


# ==========================================
# 2. CONFIGURAÇÃO DA INTERFACE
# ==========================================
st.title("Mobile Barcode Scanner Pro")

# Inicializa as variáveis de controle no Session State
if "ultimo_resultado" not in st.session_state:
    st.session_state["ultimo_resultado"] = None
if "scanner_id" not in st.session_state:
    st.session_state["scanner_id"] = 0  # Usado para resetar o componente mudando a KEY

# FLUXO A: Código detectado com sucesso -> Para tudo e exibe
if st.session_state["ultimo_resultado"] is not None:
    st.success(f"✅ Lido com sucesso: {st.session_state['ultimo_resultado']}")
    st.json({"status": "Processado", "conteudo": st.session_state["ultimo_resultado"]})

    if st.button("🔄 Escanear Próximo Código"):
        st.session_state["ultimo_resultado"] = None
        # Incrementa o ID para forçar o Streamlit a destruir o componente velho e criar um novo do zero
        st.session_state["scanner_id"] += 1
        st.rerun()

# FLUXO B: Câmera Ativa para Escaneamento
else:
    # A KEY muda dinamicamente quando clicamos em "Próximo Código", evitando travar o WebRTC
    component_key = f"barcode-scanner-id-{st.session_state['scanner_id']}"

    ctx = webrtc_streamer(
        key=component_key,
        mode=WebRtcMode.SENDRECV,
        video_processor_factory=BarcodeProcessor,
        media_stream_constraints={
            "video": {"facingMode": "environment"},
            "audio": False
        },
        async_processing=True,
        rtc_configuration={
            "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
        }
    )

    # Monitoramento passivo seguro
    if ctx.state.playing and ctx.video_processor:
        st.info("📷 Câmera ativa. Posicione o código de barras na tela.")

        # Captura o dado gerado na thread paralela
        detectado = getattr(ctx.video_processor, "resultado", None)

        if detectado is not None:
            # Salva o resultado no estado global imediatamente
            st.session_state["ultimo_resultado"] = detectado

            # Limpa o dado do processador para garantir que ele pare de processar novos frames
            ctx.video_processor.resultado = None

            # Em vez de reload geral ou st.rerun puro de dentro do loop assíncrono,
            # usamos um clique simulado via JS em um botão invisível do Streamlit.
            # Essa é a forma mais segura de atualizar a tela sem crashar o asyncio.
            if st.button(
                    "⚠️ Clique aqui para confirmar a leitura" if st.checkbox("Mostrar botão de segurança (opcional)",
                                                                             value=False) else "Processando..."):
                st.rerun()

            # Executa o gatilho automático apenas UMA vez injetando o clique no botão acima
            components.html(
                """
                <script>
                    setTimeout(function() {
                        var buttons = window.parent.document.getElementsByTagName('button');
                        for (var i = 0; i < buttons.length; i++) {
                            if (buttons[i].innerText.includes('Processando...') || buttons[i].innerText.includes('Clique aqui')) {
                                buttons[i].click();
                                break;
                            }
                        }
                    }, 100);
                </script>
                """,
                height=0,
                width=0
            )
    else:
        st.warning("Clique no botão 'Start' acima para ligar a câmera.")