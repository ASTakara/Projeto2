import streamlit as st
import cv2
import numpy as np
from pyzbar.pyzbar import decode
import streamlit.components.v1 as components

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Inovação - Coleta de Produtos", layout="centered")
st.markdown("<h2 style='text-align: center; font-size: 24px;'>📦 Coleta de Produtos</h2>", unsafe_allow_html=True)


# =====================================================================
# FUNÇÕES DE INTEGRAÇÃO COM AS SUAS APIS
# =====================================================================

def consultar_api_endereco(codigo_endereco):
    try:
        if codigo_endereco.isalnum():
            return True, f"Setor Logístico - Rua 4 (Código: {codigo_endereco})"
        return False, "Endereço não localizado no sistema."
    except Exception:
        return False, "Erro de conexão com o servidor da API."


def consultar_api_produto(codigo_barras):
    try:
        if 8 <= len(codigo_barras) <= 14:
            return True, f"Produto Exemplo SKU-{codigo_barras[:4]}"
        return False, "Produto não cadastrado no catálogo."
    except Exception:
        return False, "Erro ao conectar na API de produtos."


def gravar_dados_inventario(endereco, codigo_barras, quantidade):
    try:
        # Simulação de requisição POST bem-sucedida
        return True
    except Exception:
        return False


# --- FUNÇÃO AUXILIAR DE LEITURA (OPENCV + PYZBAR) ---
def escanear_codigo(img_file):
    if img_file is None:
        return None
    bytes_data = img_file.getvalue()
    cv_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)

    # Tentativa 1: Normal
    codigos = decode(gray)
    if codigos:
        return codigos[0].data.decode("utf-8").strip()

    # Tentativa 2: Rotação 90º para códigos verticais
    gray_rotated = cv2.rotate(gray, cv2.ROTATE_90_CLOCKWISE)
    codigos_rotacionados = decode(gray_rotated)
    if codigos_rotacionados:
        return codigos_rotacionados[0].data.decode("utf-8").strip()

    return None


# --- INICIALIZAÇÃO DO ESTADO (SESSION STATE) ---
if "prateleira_atual" not in st.session_state:
    st.session_state["prateleira_atual"] = ""
if "label_api_prateleira" not in st.session_state:
    st.session_state["label_api_prateleira"] = ""
if "produto_escanear" not in st.session_state:
    st.session_state["produto_escanear"] = True
if "produto_codigo" not in st.session_state:
    st.session_state["produto_codigo"] = None
if "produto_titulo" not in st.session_state:
    st.session_state["produto_titulo"] = ""
if "produto_quantidade" not in st.session_state:
    st.session_state["produto_quantidade"] = 1
if "encerrado" not in st.session_state:
    st.session_state["encerrado"] = False

# =====================================================================
# FLUXO DE ENCERRAMENTO
# =====================================================================
if st.session_state["encerrado"]:
    st.warning("⚠️ O processo foi encerrado. Você já pode fechar esta aba do navegador.")
    components.html("""
        <script>
            window.close();
            setTimeout(function() {
                document.body.innerHTML = '<h3 style="color: gray; text-align: center; font-family: sans-serif; margin-top: 50px;">Sessão encerrada com segurança. Pode fechar o aplicativo.</h3>';
            }, 300);
        </script>
    """, height=100)
    st.stop()

# =====================================================================
# BLOCO 1: STATUS DO ENDEREÇO ATUAL
# =====================================================================
st.write("")
with st.container(border=True):
    st.markdown("<h4 style='margin:0;'>📍 Endereço Logístico</h4>", unsafe_allow_html=True)

    col_informacoes, col_acao = st.columns([2.5, 1.5], vertical_alignment="bottom")

    with col_informacoes:
        st.text_input(
            "Endereço Ativo:",
            value=st.session_state["prateleira_atual"] if st.session_state[
                "prateleira_atual"] else "Nenhum endereço selecionado",
            disabled=True,
        )
        if st.session_state["label_api_prateleira"]:
            st.info(f"**Local:** {st.session_state['label_api_prateleira']}")

    with col_acao:
        botao_fechar_desabilitado = not bool(st.session_state["prateleira_atual"])
        if st.button("Fechar Endereço", type="primary", disabled=botao_fechar_desabilitado, use_container_width=True):
            st.session_state["prateleira_atual"] = ""
            st.session_state["label_api_prateleira"] = ""
            st.session_state["produto_codigo"] = None
            st.session_state["produto_titulo"] = ""
            st.session_state["produto_quantidade"] = 1
            st.session_state["produto_escanear"] = True
            st.toast("🔒 Endereço fechado com sucesso!")
            st.rerun()

# =====================================================================
# BLOCO 2: FLUXO DINÂMICO DE CAPTURA
# =====================================================================
st.write("")

# PASSO A: Escanear Prateleira (Só exibe se não houver prateleira ativa)
if not st.session_state["prateleira_atual"]:
    st.info("👋 Para iniciar, aponte a câmera para a Etiqueta do **Endereço**.")
    img_prateleira = st.camera_input("Escanear Etiqueta do Endereço", key="cam_prateleira")

    if img_prateleira is not None:
        codigo_prat = escanear_codigo(img_prateleira)
        if codigo_prat:
            sucesso, resultado_api = consultar_api_endereco(codigo_prat)
            if sucesso:
                st.session_state["prateleira_atual"] = codigo_prat
                st.session_state["label_api_prateleira"] = resultado_api
                st.rerun()
            else:
                st.error(f"❌ {resultado_api}")
        else:
            st.error("❌ Endereço não reconhecido. Tente focar melhor no código de barras.")

# PASSO B: Coleta de Produtos Ativa
else:
    with st.container(border=True):
        st.markdown("<h4 style='margin:0;'>📦 Coleta de Itens</h4>", unsafe_allow_html=True)

        # CASO B1: Tela de Sucesso (Visualização do último item coletado)
        if not st.session_state["produto_escanear"] and st.session_state["produto_codigo"]:
            st.success("🎉 Dados gravados com sucesso no sistema!")

            col_p1, col_p2 = st.columns(2)
            with col_p1:
                st.metric(label="Código do Produto", value=st.session_state["produto_codigo"])
                st.markdown(f"**🏷️ Título:** {st.session_state['produto_titulo']}")
            with col_p2:
                st.metric(label="Quantidade Registrada", value=f"{st.session_state['produto_quantidade']} un")

            st.write("")
            if st.button("🔄 Escanear Próximo Produto", type="secondary", use_container_width=True):
                st.session_state["produto_codigo"] = None
                st.session_state["produto_titulo"] = ""
                st.session_state["produto_quantidade"] = 1
                st.session_state["produto_escanear"] = True
                st.rerun()

        # CASO B2: Formulário de Entrada e Câmera do Produto
        else:
            quantidade_input = st.number_input(
                "1. Informe a Quantidade Antes de Escanear:",
                min_value=1, value=st.session_state["produto_quantidade"], step=1,
                key="campo_quantidade",
            )

            # Atualiza o estado da quantidade dinamicamente sem quebrar o fluxo
            st.session_state["produto_quantidade"] = quantidade_input

            st.write("2. Aponte para o Código de Barras do **Produto**:")
            img_produto = st.camera_input("Escanear Código do Produto", key="cam_produto")

            if img_produto is not None:
                codigo_prod = escanear_codigo(img_produto)
                if codigo_prod:
                    sucesso_prod, resultado_prod = consultar_api_produto(codigo_prod)

                    if sucesso_prod:
                        # Envia os dados para a API passando a variável atualizada do input
                        sucesso_gravacao = gravar_dados_inventario(
                            endereco=st.session_state["prateleira_atual"],
                            codigo_barras=codigo_prod,
                            quantidade=st.session_state["produto_quantidade"]
                        )

                        if sucesso_gravacao:
                            st.session_state["produto_codigo"] = codigo_prod
                            st.session_state["produto_titulo"] = resultado_prod
                            st.session_state["produto_escanear"] = False
                            st.rerun()
                        else:
                            st.error("❌ Erro interno ao gravar dados no servidor.")
                    else:
                        st.error(f"❌ {resultado_prod}")
                else:
                    st.error("❌ Código do produto não reconhecido. Verifique a iluminação.")

# =====================================================================
# BLOCO 3: BOTÃO FIXO DE SAÍDA
# =====================================================================
st.write("")
if st.button("❌ Encerrar Processo e Sair", type="secondary", use_container_width=True):
    st.session_state["prateleira_atual"] = ""
    st.session_state["label_api_prateleira"] = ""
    st.session_state["produto_codigo"] = None
    st.session_state["produto_titulo"] = ""
    st.session_state["encerrado"] = True
    st.rerun()