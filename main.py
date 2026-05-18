import streamlit as st
import cv2
import numpy as np
from pyzbar.pyzbar import decode

# Configuração da Página
st.set_page_config(page_title="Scanner de Inventário", layout="centered")
st.title("📷 Scanner de Inventário")


# --- FUNÇÃO AUXILIAR DE LEITURA ---
def escanear_codigo(img_file):
    """Recebe o arquivo de imagem do Streamlit e tenta decodificar o código de barras"""
    if img_file is None:
        return None

    # Converte para o formato do OpenCV
    bytes_data = img_file.getvalue()
    cv_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)

    # Tentativa 1: Posição original
    codigos = decode(gray)
    if codigos:
        for obj in codigos:
            texto = obj.data.decode("utf-8").strip()
            if texto:
                return texto

    # Tentativa 2: Rotacionado 90°
    gray_rotated = cv2.rotate(gray, cv2.ROTATE_90_CLOCKWISE)
    codigos_rotacionados = decode(gray_rotated)
    if codigos_rotacionados:
        for obj in codigos_rotacionados:
            texto = obj.data.decode("utf-8").strip()
            if texto:
                return texto

    return None


# --- INICIALIZAÇÃO DO ESTADO (SESSION STATE) ---
if "endereco_prateleira" not in st.session_state:
    st.session_state["endereco_prateleira"] = None
if "resultado_final" not in st.session_state:
    st.session_state["resultado_final"] = None
if "quantidade_final" not in st.session_state:
    st.session_state["quantidade_final"] = 1


# --- FLUXO C: Exibe Resultado Final Consolidado ---
if st.session_state["endereco_prateleira"] and st.session_state["resultado_final"]:
    st.success("🎉 Dados capturados com sucesso!")

    # Exibe as métricas em 3 colunas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            label="📍 Endereço Prateleira",
            value=st.session_state["endereco_prateleira"],
        )
    with col2:
        st.metric(
            label="📦 Código do Produto",
            value=st.session_state["resultado_final"],
        )
    with col3:
        st.metric(
            label="🔢 Quantidade",
            value=f"{st.session_state['quantidade_final']} un",
        )

    # Opções para continuar
    st.write("---")
    if st.button("🔄 Escanear Próximo Produto (Mesma Prateleira)", use_container_width=True):
        st.session_state["resultado_final"] = None
        st.session_state["quantidade_final"] = 1
        st.rerun()

    if st.button("📍 Mudar de Prateleira", type="secondary", use_container_width=True):
        st.session_state["endereco_prateleira"] = None
        st.session_state["resultado_final"] = None
        st.session_state["quantidade_final"] = 1
        st.rerun()


# --- FLUXO A: Escanear Endereço da Prateleira ---
elif not st.session_state["endereco_prateleira"]:
    st.subheader("Passo 1: Identificar a Prateleira")
    st.write("Tire a foto do código de barras da **prateleira/posição**:")

    img_endereco = st.camera_input("Alinhe o código do endereço na tela", key="cam_endereco")

    if img_endereco is not None:
        codigo_endereco = escanear_codigo(img_endereco)
        if codigo_endereco:
            st.session_state["endereco_prateleira"] = codigo_endereco
            st.rerun()
        else:
            st.error(
                "❌ Não foi possível ler o código do endereço. Verifique o foco e tente novamente."
            )


# --- FLUXO B: Informar Quantidade e Escanear Produto ---
else:
    # Mostra em qual prateleira o usuário está trabalhando atualmente
    st.info(f"📍 Prateleira Atual: **{st.session_state['endereco_prateleira']}**")

    st.subheader("Passo 2: Escanear Produto")

    quantidade_input = st.number_input(
        "1. Insira a quantidade deste produto:",
        min_value=1,
        value=1,
        step=1,
        key="campo_quantidade",
    )

    st.write("2. Tire a foto do código de barras do **produto**:")
    img_produto = st.camera_input("Alinhe o código do produto na tela", key="cam_produto")

    if img_produto is not None:
        codigo_produto = escanear_codigo(img_produto)
        if codigo_produto:
            st.session_state["resultado_final"] = codigo_produto
            st.session_state["quantidade_final"] = quantidade_input
            st.rerun()
        else:
            st.error(
                "❌ Não foi possível ler o código do produto. Verifique o foco e tente novamente."
            )

    # Botão de escape caso ele queira mudar a prateleira antes de bipar um produto
    if st.button("⬅️ Voltar / Mudar Prateleira", type="secondary"):
        st.session_state["endereco_prateleira"] = None
        st.rerun()