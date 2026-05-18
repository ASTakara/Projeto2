import streamlit as st
import cv2
import numpy as np
from pyzbar.pyzbar import decode
import streamlit.components.v1 as components
import requests

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Inovaçao - Coleta de Produtos", layout="centered")
# st.title("📦 Coleta de Produtos")
st.markdown("<h1 style='font-size: 25px;'>📦 Coleta de Produtos</h1>", unsafe_allow_html=True)


# =====================================================================
# FUNÇÕES DE INTEGRAÇÃO COM AS SUAS APIS (SUBSTITUA PELOS SEUS ENDEREÇOS)
# =====================================================================

def consultar_api_endereco(codigo_endereco):
    """Valida se o endereço existe no sistema"""
    try:
        if codigo_endereco.isalnum():
            return True, f"Setor Logístico - Rua 4 (Código: {codigo_endereco})"
        else:
            return False, "Endereço não localizado no sistema."
    except Exception:
        return False, "Erro de conexão com o servidor da API."


def consultar_api_produto(codigo_barras):
    """Consulta a API para verificar se o produto existe e trazer seu Título"""
    try:
        if 8 <= len(codigo_barras) <= 14:
            titulo_produto = f"Produto Exemplo SKU-{codigo_barras[:4]}"
            return True, titulo_produto
        else:
            return False, "Produto não cadastrado no catálogo."
    except Exception:
        return False, "Erro ao conectar na API de produtos."


def gravar_dados_inventario(endereco, codigo_barras, quantidade):
    """Envia o payload final via POST para salvar no banco de dados"""
    try:
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

    # Tentativa 1: Em pé
    codigos = decode(gray)
    if codigos:
        for obj in codigos:
            texto = obj.data.decode("utf-8").strip()
            if texto: return texto

    # Tentativa 2: Deitado
    gray_rotated = cv2.rotate(gray, cv2.ROTATE_90_CLOCKWISE)
    codigos_rotacionados = decode(gray_rotated)
    if codigos_rotacionados:
        for obj in codigos_rotacionados:
            texto = obj.data.decode("utf-8").strip()
            if texto: return texto
    return None


# --- NOVA FUNÇÃO REUTILIZÁVEL PARA PROCESSAR PRODUTO ---
def processar_codigo_produto(codigo_prod, quantidade_input):
    """Encapsula a lógica de validação e gravação para reaproveitar no scanner e na digitação"""
    sucesso_prod, resultado_prod = consultar_api_produto(codigo_prod)

    if sucesso_prod:
        sucesso_gravacao = gravar_dados_inventario(
            endereco=st.session_state["prateleira_atual"],
            codigo_barras=codigo_prod,
            quantidade=quantidade_input
        )

        if sucesso_gravacao:
            st.session_state["produto_codigo"] = codigo_prod
            st.session_state["produto_titulo"] = resultado_prod
            st.session_state["produto_quantidade"] = quantidade_input
            st.session_state["produto_escanear"] = False
            st.rerun()
        else:
            st.error("❌ O produto é válido, mas ocorreu um erro ao gravar os dados no servidor.")
    else:
        st.error(f"❌ Erro no Produto: {resultado_prod}")


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
# FLUXO DE SAÍDA: SE O OPERADOR CLICOU EM ENCERRAR
# =====================================================================
if st.session_state["encerrado"]:
    st.warning("⚠️ O processo foi encerrado. Você já pode fechar esta aba do navegador.")
    components.html("""
        <script>
            window.close();
            setTimeout(function() {
                document.body.innerHTML = '<h2 style="color: gray; text-align: center; font-family: sans-serif; margin-top: 50px;">Sessão encerrada com segurança. Pode fechar o aplicativo.</h2>';
            }, 300);
        </script>
    """, height=100)
    st.stop()

# =====================================================================
# BLOCO 1: GROUP BOX - DADOS DA LOCALIZAÇÃO (ORDEM CORRIGIDA)
# =====================================================================
st.write("")
with st.container(border=True):
    # st.markdown("### 📍 Dados do Endereço")
    st.markdown("<h1 style='font-size: 25px;'>📍 Dados do Endereço</h1>", unsafe_allow_html=True)

    # Coluna 1 dedicada às informações textuais, Coluna 2 dedicada ao botão de ação
    col_informacoes, col_acao = st.columns([2.5, 1.5], vertical_alignment="bottom")

    with col_informacoes:
        st.text_input(
            "Endereço Ativo:",
            value=st.session_state["prateleira_atual"],
            disabled=True,
            placeholder="Aguardando leitura do código...",
        )

        # O label com o local consultado na API fica aqui, logo após o endereço e antes do botão
        if st.session_state["label_api_prateleira"]:
            st.info(f"**Local:** {st.session_state['label_api_prateleira']}")

    with col_acao:
        botao_fechar_desabilitado = not bool(st.session_state["prateleira_atual"])
        if st.button("Fechar Endereço", type="primary", disabled=botao_fechar_desabilitado, use_container_width=True):
            st.toast(f"🔒 Endereço {st.session_state['prateleira_atual']} fechado com sucesso!")
            st.session_state["prateleira_atual"] = ""
            st.session_state["label_api_prateleira"] = ""
            st.session_state["produto_codigo"] = None
            st.session_state["produto_titulo"] = ""
            st.session_state["produto_quantidade"] = 1
            st.session_state["produto_escanear"] = True
            st.rerun()

# =====================================================================
# BLOCO 2: FLUXO DINÂMICO DE PRODUTOS
# =====================================================================
st.write("")

# PASSO A: Escanear Prateleira
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
                st.error(f"❌ Erro na validação do endereço: {resultado_api}")
        else:
            st.error("❌ Endereço não reconhecido. Tente novamente.")

# PASSO B: Prateleira ativa, libera os produtos
else:
    with st.container(border=True):
        # st.markdown("### 📦 Coleta de Produtos")
        st.markdown("<h1 style='font-size: 25px;'>📦 Coleta de Produtos</h1>", unsafe_allow_html=True)

        # Caso 1: Tela de Sucesso após gravação dos dados
        if not st.session_state["produto_escanear"] and st.session_state["produto_codigo"]:
            st.success("🎉 Dados gravados com sucesso no sistema!")

            col_p1, col_p2 = st.columns(2)
            with col_p1:
                st.metric(label="Código do Produto", value=st.session_state["produto_codigo"])
                st.markdown(f"**🏷️ Título:** {st.session_state['produto_titulo']}")
            with col_p2:
                st.metric(label="Quantidade", value=f"{st.session_state['produto_quantidade']} un")

            st.write("")
            if st.button("🔄 Escanear Próximo Produto", use_container_width=True):
                st.session_state["produto_codigo"] = None
                st.session_state["produto_titulo"] = ""
                st.session_state["produto_quantidade"] = 1
                st.session_state["produto_escanear"] = True
                st.rerun()

        # Caso 2: Tela de Captura (Campos de entrada e Câmera do Produto)
        else:
            quantidade_input = st.number_input(
                "1. Informe a Quantidade do Produto:",
                min_value=1, value=1, step=1,
                key="campo_quantidade",
            )

            st.write("2. Tire a foto do Código de Barras do **Produto**:")
            img_produto = st.camera_input("Escanear Código do Produto", key="cam_produto")

            # Fluxo via Câmera (Inalterado)
            if img_produto is not None:
                codigo_prod = escanear_codigo(img_produto)
                if codigo_prod:
                    processar_codigo_produto(codigo_prod, quantidade_input)
                else:
                    st.error("❌ Código do produto não reconhecido fisicamente. Verifique o enquadramento.")

            # --- NOVA SEÇÃO: ALTERNATIVA DE DIGITAÇÃO MANUAL ---
            st.markdown("---")
            st.write("⌨️ **Não conseguiu escanear?** Digite o código manualmente:")

            col_input, col_btn = st.columns([2.5, 1.5], vertical_alignment="bottom")

            with col_input:
                codigo_digitado = st.text_input(
                    "Código de Barras Manual:",
                    placeholder="Ex: 7891234567890",
                    label_visibility="collapsed"
                ).strip()

            with col_btn:
                if st.button("Confirmar Código", use_container_width=True, type="secondary"):
                    if codigo_digitado:
                        processar_codigo_produto(codigo_digitado, quantidade_input)
                    else:
                        st.warning("⚠️ Por favor, digite um código antes de confirmar.")

# =====================================================================
# BLOCO 3: BOTÃO FIXO NO FIM DA TELA PARA ENCERRAR O NAVEGADOR
# =====================================================================
st.write("")

if st.button("❌ Encerrar Processo e Sair", type="secondary", use_container_width=True):
    st.session_state["prateleira_atual"] = ""
    st.session_state["label_api_prateleira"] = ""
    st.session_state["produto_codigo"] = None
    st.session_state["produto_titulo"] = ""
    st.session_state["encerrado"] = True
    st.rerun()