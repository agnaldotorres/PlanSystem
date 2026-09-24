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
    textos de forma robusta (ex: 'Prospecção Feirão' == 'PROSPECCAO FEIRAO')."""
    texto = str(texto).strip().upper()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return texto


# -----------------------------------------------------------------
# Metas por empresa. A comparação ignora acento/maiúscula/espaço.
#
# Para cada empresa, listamos "palavras-chave" que identificam ela no
# texto da coluna "Empresa" da planilha:
#   - Se a palavra-chave tiver mais de uma palavra (ex: "VIVA VOLKS"),
#     a frase inteira precisa aparecer dentro do texto da célula.
#   - Se for uma palavra só (ex: "FORD", "MG"), ela precisa bater com
#     uma palavra INTEIRA do texto, para não confundir com outro nome
#     que apenas contenha essas letras por acaso.
#
# Ajuste as palavras-chave abaixo para bater exatamente com o que
# aparece na coluna "Empresa" da sua planilha.
# -----------------------------------------------------------------
METAS = {
    "MITSUBISHI": (["MITSUBISHI", "AKANE"], 30),
    "FORD": (["FORD"], 15),
    "SEMINOVOS": (["SEMINOVOS", "JRCA"], 35),
    "BYD": (["BYD"], 65),
    "DENZA": (["DENZA"], 11),
    "VIVA VOLKS": (["VIVA VOLKS", "VOLKSWAGEN", "VW"], 30),
    "BAJAJ": (["BAJAJ"], 30),
    "NIKAI": (["NIKAI"], 35),
    "TRIUMPH": (["TRIUMPH"], 14),
    "MG": (["MG"], 14),
}


def obter_meta(empresa):
    """Recebe o texto da coluna Empresa e devolve (nome_padronizado, meta)
    ou (None, None) se não reconhecer a empresa."""
    if pd.isna(empresa) or not str(empresa).strip():
        return None, None
    texto = normalizar(empresa)
    tokens = set(texto.split())
    for chave, (palavras, meta) in METAS.items():
        for p in palavras:
            p_norm = normalizar(p)
            if " " in p_norm:
                if p_norm in texto:
                    return chave, meta
            else:
                if p_norm in tokens:
                    return chave, meta
    return None, None


st.set_page_config(
    page_title="Ranking de Visita em Loja - Admin",
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
    coluna_empresa = None

    for coluna in df.columns:
        nome = normalizar(coluna)
        if nome == "VISITA AGENDADA":
            coluna_agendada = coluna
        if nome == "AQUECIMENTO":
            coluna_aquecimento = coluna
        if "TIPO EVENTO" in nome or "TIPO DE EVENTO" in nome:
            coluna_tipo_evento = coluna
        if nome == "EMPRESA":
            coluna_empresa = coluna

    if coluna_tipo_evento is None:
        st.warning(
            "⚠️ Não encontrei a coluna 'Tipo Evento' nesta planilha — "
            "o filtro de 'PROSPECÇÃO FEIRÃO' não será aplicado. "
            "Colunas encontradas: " + ", ".join(df.columns.tolist())
        )

    if coluna_empresa is None:
        st.warning(
            "⚠️ Não encontrei a coluna 'Empresa' nesta planilha — "
            "o destaque de metas não será aplicado."
        )

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
        # Regra confirmada: só exclui FEIRÃO, mantém CRM contabilizado.
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

        # -----------------------------------------------------------------
        # Descobrir a empresa de cada aquecedor (pega a mais frequente,
        # caso existam inconsistências na planilha) e comparar a
        # quantidade de visitas dele com a meta daquela empresa.
        # -----------------------------------------------------------------
        if coluna_empresa is not None:
            empresa_por_aquecedor = df_filtrado.groupby(coluna_aquecimento)[coluna_empresa].agg(
                lambda s: s.mode().iat[0] if not s.mode().empty else None
            )

            ranking["Empresa"] = ranking["Aquecedor"].map(empresa_por_aquecedor)

            metas_info = ranking["Empresa"].apply(obter_meta)
            ranking["Meta"] = metas_info.apply(lambda x: x[1])
            ranking["Atingiu Meta"] = ranking.apply(
                lambda r: bool(pd.notna(r["Meta"]) and r["Quantidade"] >= r["Meta"]),
                axis=1,
            )

            nao_reconhecidos = ranking.loc[ranking["Meta"].isna(), "Empresa"].dropna().unique()
            if len(nao_reconhecidos) > 0:
                st.warning(
                    "⚠️ Não reconheci a meta destas empresas (ajuste o dicionário METAS): "
                    + ", ".join(map(str, nao_reconhecidos))
                )

        # Métricas
        col1, col2 = st.columns(2)
        with col1:
            st.metric("📅 Total de Visitas Agendadas", len(df_filtrado))
        with col2:
            st.metric("🔥 Total de Aquecedores", len(ranking))

        st.subheader("🏆 Ranking dos Aquecedores")

        if "Atingiu Meta" in ranking.columns:

            def destacar_meta(row):
                estilos = [""] * len(row)
                if row.get("Atingiu Meta"):
                    idx = row.index.get_loc("Aquecedor")
                    estilos[idx] = "color: #16a34a; font-weight: 800;"
                return estilos

            st.dataframe(
                ranking.style.apply(destacar_meta, axis=1),
                width="stretch",
            )
        else:
            st.dataframe(ranking, width="stretch")

        st.subheader("📊 Visitas Agendadas por Aquecedor")
        st.bar_chart(ranking.set_index("Aquecedor")["Quantidade"])

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