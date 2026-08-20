import streamlit as st
import pandas as pd
import re
import json
import os
import unicodedata
from datetime import datetime
from zoneinfo import ZoneInfo


def normalizar(texto):
    """Remove acentos, espaços extras e deixa em maiúsculas, para comparar
    textos de forma robusta (ex: 'PROSPECCAO FEIRAO' == 'PROSPECCAO FEIRAO')."""
    texto = str(texto).strip().upper()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return texto

st.set_page_config(
    page_title="Ranking de Aquecimento - Admin",
    page_icon="🔥",
    layout="wide"
)

# -----------------------------------------------------------------
# Onde o resultado processado é salvo. A página pública (em
# pages/1_Painel_Publico.py) lê esse mesmo arquivo.
# -----------------------------------------------------------------
PASTA_DADOS = os.path.join(os.path.dirname(__file__), "dados")
ARQUIVO_RESULTADO = os.path.join(PASTA_DADOS, "ultimo_resultado.json")
FUSO = ZoneInfo("America/Maceio")

os.makedirs(PASTA_DADOS, exist_ok=True)

st.title("🔥 Ranking de Aquecimento — Admin")

st.write(
    "Envie uma planilha para contar os aquecedores dos clientes com visita agendada. "
    "Ao processar, o resultado é publicado automaticamente no **Painel Público** "
    "(veja o menu à esquerda) para seus usuários."
)

arquivo = st.file_uploader(
    "📁 Selecione sua planilha Excel",
    type=["xlsx", "xls"]
)

if arquivo is not None:

    # -----------------------------------------------------------------
    # Descobrir automaticamente em qual linha está o cabeçalho real,
    # pois esta planilha tem título/linha em branco antes dele.
    # -----------------------------------------------------------------
    bruto = pd.read_excel(arquivo, header=None, nrows=15)

    linha_cabecalho = None
    for i, linha in bruto.iterrows():
        valores = [str(v).strip().lower() for v in linha.tolist()]
        if any("visita agendada" in v for v in valores) and any(
            v == "aquecimento" for v in valores
        ):
            linha_cabecalho = i
            break

    if linha_cabecalho is None:
        linha_cabecalho = 0

    arquivo.seek(0)
    df = pd.read_excel(arquivo, header=linha_cabecalho)

    df.columns = [
        re.sub(r"\s+", " ", str(col)).strip()
        for col in df.columns
    ]

    st.success("Planilha carregada com sucesso! ✅")

    coluna_agendada = None
    coluna_aquecimento = None
    coluna_tipo_evento = None

    for coluna in df.columns:
        nome = str(coluna).strip().lower()
        if nome == "visita agendada":
            coluna_agendada = coluna
        if nome == "aquecimento":
            coluna_aquecimento = coluna
        if nome == "tipo evento":
            coluna_tipo_evento = coluna

    if coluna_agendada is None or coluna_aquecimento is None:

        st.error("❌ Não consegui identificar as colunas necessárias.")
        st.write("### Colunas encontradas na planilha:")
        st.write(df.columns.tolist())

    else:

        df_filtrado = df[
            df[coluna_agendada]
            .astype(str)
            .str.strip()
            .str.upper() == "SIM"
        ].copy()

        # -----------------------------------------------------------------
        # Não contabilizar linhas cujo "Tipo Evento" seja "PROSPECCAO FEIRAO"
        # (comparação ignora acento, maiúscula/minúscula e espaços extras).
        # -----------------------------------------------------------------
        if coluna_tipo_evento is not None:
            df_filtrado = df_filtrado[
                df_filtrado[coluna_tipo_evento].apply(normalizar) != "PROSPECCAO FEIRAO"
            ]

        df_filtrado = df_filtrado.dropna(subset=[coluna_aquecimento])

        df_filtrado[coluna_aquecimento] = (
            df_filtrado[coluna_aquecimento]
            .astype(str)
            .str.strip()
        )

        ranking = (
            df_filtrado[coluna_aquecimento]
            .value_counts()
            .reset_index()
        )
        ranking.columns = ["Aquecedor", "Quantidade"]
        ranking.index = ranking.index + 1
        ranking.index.name = "Posição"

        # Métricas
        col1, col2 = st.columns(2)
        with col1:
            st.metric("📅 Total de Visitas Agendadas", len(df_filtrado))
        with col2:
            st.metric("🔥 Total de Aquecedores", len(ranking))

        st.subheader("🏆 Ranking dos Aquecedores")
        st.dataframe(ranking, use_container_width=True)

        st.subheader("📊 Visitas Agendadas por Aquecedor")
        st.bar_chart(ranking.set_index("Aquecedor"))

        # -----------------------------------------------------------------
        # Salvar o resultado + data/hora da atualização para a página
        # pública ler. Isso é o que "publica" a atualização para os
        # usuários automaticamente.
        # -----------------------------------------------------------------
        agora = datetime.now(FUSO)

        resultado = {
            "atualizado_em": agora.strftime("%d/%m/%Y %H:%M:%S"),
            "total_visitas_agendadas": int(len(df_filtrado)),
            "total_aquecedores": int(len(ranking)),
            "ranking": ranking.reset_index().to_dict(orient="records"),
        }

        with open(ARQUIVO_RESULTADO, "w", encoding="utf-8") as f:
            json.dump(resultado, f, ensure_ascii=False, indent=2)

        st.info(
            f"📤 Painel público atualizado em **{resultado['atualizado_em']}**. "
            "Seus usuários já verão os novos números."
        )