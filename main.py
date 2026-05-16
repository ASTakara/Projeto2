import streamlit as st
import cv2
import numpy as np
from pyzbar.pyzbar import decode

# Configuração da Página
st.set_page_config(page_title="Scanner de Código de Barras", layout="centered")
st.title("📷 Scanner de Código de Barras Omni-Direcional")

# Inicializa o estado para guardar o resultado
if "resultado_final" not in st.session_state:
    st.session_state["resultado_final"] = None

# FLUXO A: Código processado com sucesso
if st.session_state["resultado_final"]:
    st.success("🎉 Código capturado com sucesso!")
    st.code(st.session_state["resultado_final"], language="text")

    if st.button("🔄 Escanear Próximo Código", use_container_width=True):
        st.session_state["resultado_final"] = None
        st.rerun()

# FLUXO B: Captura de Foto Estável (Câmera Frontal)
else:
    st.write("Tire uma foto do código de barras (funciona em pé ou deitado):")

    # Componente oficial do Streamlit (Câmera frontal por padrão)
    img_file = st.camera_input("Alinhe o código de barras na tela")

    if img_file is not None:
        # Converte a imagem capturada para o formato do OpenCV
        bytes_data = img_file.getvalue()
        cv_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)

        # Converte para escala de cinza
        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)

        # --- TENTATIVA 1: Tenta ler na posição original (em pé) ---
        codigos_encontrados = decode(gray)
        codigo_valido = None

        if codigos_encontrados:
            for obj in codigos_encontrados:
                texto_lido = obj.data.decode("utf-8").strip()
                if texto_lido:
                    codigo_valido = texto_lido
                    break

        # --- TENTATIVA 2: Se falhar, rotaciona 90° para ler o código deitado ---
        if not codigo_valido:
            # Rotaciona a imagem em escala de cinza em 90 graus no sentido horário
            gray_rotated = cv2.rotate(gray, cv2.ROTATE_90_CLOCKWISE)
            codigos_encontrados_rotacionados = decode(gray_rotated)

            if codigos_encontrados_rotacionados:
                for obj in codigos_encontrados_rotacionados:
                    texto_lido = obj.data.decode("utf-8").strip()
                    if texto_lido:
                        codigo_valido = texto_lido
                        break

        # Validação do resultado final
        if codigo_valido:
            st.session_state["resultado_final"] = codigo_valido
            st.rerun()
        else:
            st.error(
                "❌ Não foi possível decodificar. Certifique-se de que a foto não está muito borrada e que o código está totalmente visível dentro do enquadramento.")