import streamlit as st
import cv2
import numpy as np
import zxingcpp  # Motor de alta precisão

# Configuração da Página
st.set_page_config(page_title="Scanner de Código de Barras", layout="centered")
st.title("📷 Scanner de Código de Barras de Alta Precisão")

# Inicializa o estado para guardar o resultado
if "resultado_final" not in st.session_state:
    st.session_state["resultado_final"] = None

# FLUXO A: Código processado com sucesso
if st.session_state["resultado_final"]:
    st.success("🎉 Código capturado com sucesso!")

    # Exibe o código limpo e destacado
    st.code(st.session_state["resultado_final"], language="text")

    if st.button("🔄 Escanear Próximo Código", use_container_width=True):
        st.session_state["resultado_final"] = None
        st.rerun()

# FLUXO B: Captura de Foto/Frame Estável
else:
    st.write("Tire uma foto nítida e aproximada do código de barras:")

    # Componente oficial e nativo do Streamlit para câmeras
    img_file = st.camera_input("Centralize o código de barras na tela")

    if img_file is not None:
        # Converte a imagem capturada para o formato do OpenCV
        bytes_data = img_file.getvalue()
        cv_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)

        # O ZXing lê melhor imagens coloridas ou em cinza puro, ele mesmo faz a otimização interna.
        # Chamamos o motor de leitura do ZXing (Super preciso)
        resultados = zxingcpp.read_barcodes(cv_img)

        if resultados:
            # Pegamos o primeiro código válido encontrado
            for codigo in resultados:
                texto_lido = codigo.text.strip()
                format_do_codigo = codigo.format

                if texto_lido:
                    # Salva o resultado exato e o tipo do código para conferência
                    st.session_state["resultado_final"] = texto_lido
                    st.rerun()

            # Se passou pelo loop e não achou texto válido
            st.error(
                "❌ O scanner detectou a região do código, mas não conseguiu decodificar os números. Tente focar melhor.")
        else:
            # Se falhar a detecção básica
            st.error(
                "❌ Nenhum código de barras identificado. Certifique-se de que a foto está bem focada, sem sombras fortes sobre as barras e tente novamente.")