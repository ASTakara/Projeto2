import streamlit as st
import cv2
import numpy as np
from pyzbar.pyzbar import decode  # Motor de altíssima precisão para fotos

# Configuração da Página
st.set_page_config(page_title="Scanner de Código de Barras", layout="centered")
st.title("📷 Scanner de Código de Barras (Alta Precisão)")

# Inicializa o estado para guardar o resultado
if "resultado_final" not in st.session_state:
    st.session_state["resultado_final"] = None

# FLUXO A: Código processado com sucesso
if st.session_state["resultado_final"]:
    st.success("🎉 Código capturado com sucesso!")

    # Exibe o código perfeitamente formatado
    st.code(st.session_state["resultado_final"], language="text")

    if st.button("🔄 Escanear Próximo Código", use_container_width=True):
        st.session_state["resultado_final"] = None
        st.rerun()

# FLUXO B: Captura de Foto Estável (Câmera Frontal)
else:
    st.write("Tire uma foto nítida e aproximada do código de barras:")

    # Componente oficial do Streamlit (Câmera frontal por padrão)
    img_file = st.camera_input("Alinhe o código de barras na tela")

    if img_file is not None:
        # Converte a imagem capturada para o formato do OpenCV
        bytes_data = img_file.getvalue()
        cv_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)

        # Converte para escala de cinza para o pyzbar trabalhar melhor
        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)

        # O pyzbar analisa a imagem e valida matematicamente o código de barras
        codigos_encontrados = decode(gray)

        codigo_valido = None

        if codigos_encontrados:
            for obj in codigos_encontrados:
                # Extrai o texto puro decodificado
                texto_lido = obj.data.decode("utf-8").strip()

                if texto_lido:
                    codigo_valido = texto_lido
                    break  # Pega o primeiro código válido

        # Validação do resultado
        if codigo_valido:
            st.session_state["resultado_final"] = codigo_valido
            st.rerun()
        else:
            # Mensagem de erro caso a foto não esteja boa o suficiente para o crivo matemático do pyzbar
            st.error(
                "❌ Não foi possível decodificar este código de barras. Certifique-se de que a foto não está tremida, muito longe ou com reflexos e tente novamente.")