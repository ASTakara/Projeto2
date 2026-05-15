import streamlit as st
import cv2
import numpy as np

# Configuração da Página
st.set_page_config(page_title="Scanner de Código de Barras", layout="centered")
st.title("📷 Scanner de Código de Barras")

# Inicializa o estado para guardar o resultado
if "resultado_final" not in st.session_state:
    st.session_state["resultado_final"] = None

# FLUXO A: Código processado com sucesso
if st.session_state["resultado_final"]:
    st.success("🎉 Código capturado com sucesso!")
    st.info(f"**Conteúdo do Código:** {st.session_state['resultado_final']}")

    if st.button("🔄 Escanear Próximo Código", use_container_width=True):
        st.session_state["resultado_final"] = None
        st.rerun()

# FLUXO B: Captura de Foto/Frame Estável
else:
    st.write("Tire uma foto nítida e aproximada do código de barras usando o botão abaixo:")

    # Componente oficial e nativo do Streamlit para câmeras (Mobile e Desktop)
    # Abre diretamente o app de câmera nativo do celular com foco automático
    img_file = st.camera_input("Alinhe o código de barras na linha horizontal")

    if img_file is not None:
        # Converte a imagem capturada para o formato do OpenCV
        bytes_data = img_file.getvalue()
        cv_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)

        # Converte para escala de cinza para otimizar
        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)

        # Inicializa o detector nativo e robusto do OpenCV
        detector = cv2.barcode.BarcodeDetector()
        retval, decoded_info, decoded_type, points = detector.detectAndDecode(gray)

        if retval and decoded_info[0]:
            # Sucesso absoluto na leitura!
            st.session_state["resultado_final"] = decoded_info[0]
            st.rerun()
        else:
            # Se falhar, dá uma dica visual sem quebrar o sistema
            st.error(
                "❌ Código de barras não identificado na imagem. Certifique-se de que a foto não ficou tremida ou com reflexos e tente novamente.")