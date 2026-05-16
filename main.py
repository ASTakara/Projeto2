import streamlit as st
import cv2
import numpy as np
from pyzbar.pyzbar import decode

# Configuração da Página
st.set_page_config(page_title="Scanner de Código de Barras", layout="centered")
st.title("📷 Scanner de Código de Barras")

# Inicializa o estado para guardar o resultado e a quantidade
if "resultado_final" not in st.session_state:
    st.session_state["resultado_final"] = None
if "quantidade_final" not in st.session_state:
    st.session_state["quantidade_final"] = 1

# FLUXO A: Código processado com sucesso (Exibe Resultado + Quantidade)
if st.session_state["resultado_final"]:
    st.success("🎉 Produto escaneado com sucesso!")

    # Cria duas colunas para mostrar as informações organizadas
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Código de Barras", value=st.session_state["resultado_final"])
    with col2:
        st.metric(label="Quantidade Informada", value=f"{st.session_state['quantidade_final']} un")

    if st.button("🔄 Escanear Próximo Código", use_container_width=True):
        st.session_state["resultado_final"] = None
        # Reseta para 1 para o próximo produto
        st.session_state["quantidade_final"] = 1
        st.rerun()

# FLUXO B: Escolha da Quantidade e Captura da Foto
else:
    # Caixa de texto numérica para inserir a quantidade desejada
    quantidade_input = st.number_input(
        "1. Insira a quantidade deste produto:",
        min_value=1,
        value=1,
        step=1,
        key="campo_quantidade"
    )

    st.write("2. Tire a foto do código de barras (funciona em pé ou deitado):")

    # Componente oficial do Streamlit (Câmera frontal por padrão)
    img_file = st.camera_input("Alinhe o código de barras na tela")

    if img_file is not None:
        # Converte a imagem capturada para o formato do OpenCV
        bytes_data = img_file.getvalue()
        cv_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)

        # Converte para escala de cinza
        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)

        # --- TENTATIVA 1: Posição original (em pé) ---
        codigos_encontrados = decode(gray)
        codigo_valido = None

        if codigos_encontrados:
            for obj in codigos_encontrados:
                texto_lido = obj.data.decode("utf-8").strip()
                if texto_lido:
                    codigo_valido = texto_lido
                    break

        # --- TENTATIVA 2: Se falhar, rotaciona 90° (deitado) ---
        if not codigo_valido:
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
            # Salva o código de barras e a quantidade definida pelo usuário
            st.session_state["resultado_final"] = codigo_valido
            st.session_state["quantidade_final"] = quantidade_input
            st.rerun()
        else:
            st.error(
                "❌ Não foi possível decodificar. Certifique-se de que a foto não está muito borrada e que o código está totalmente visível dentro do enquadramento.")