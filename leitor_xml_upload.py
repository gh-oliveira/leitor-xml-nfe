# VERSÃO 01 DA AUTOMAÇÃO PARA UPLOAD DE ARQUIVOS XML

import streamlit as st
import pandas as pd
import xmltodict
import io

def infos_xml(arquivo_xml):
    dic_arquivo = xmltodict.parse(arquivo_xml)
    dados_nf = dic_arquivo["nfeProc"]["NFe"]["infNFe"]
    dados_item = dados_nf["det"]

    # Normaliza sempre para lista
    if not isinstance(dados_item, list):
        dados_item = [dados_item]

    conteudo_itens = []
    for item in dados_item:
        numero_nf = dados_nf["ide"]["nNF"]
        natureza_op = dados_nf["ide"]["natOp"]
        nome_fornecedor = dados_nf["emit"]["xNome"]
        uf_fornecedor = dados_nf["emit"]["enderEmit"]["UF"]
        nome_destinatario = dados_nf["dest"]["xNome"]
        cnpj_destinatario = dados_nf["dest"]["CNPJ"]
        uf_destinatario = dados_nf["dest"]["enderDest"]["UF"]
        vlr_icms_destino = float(dados_nf["total"]["ICMSTot"].get("vICMSUFDest", 0))

        numero_item = item.get("@nItem", "")
        descricao_item = item["prod"]["xProd"]
        ncm_item = item["prod"]["NCM"]
        cfop_item = item["prod"]["CFOP"]
        
        pis = list(item["imposto"].get("PIS", {}).values())[0] if "PIS" in item["imposto"] else {}
        cst_pis = pis.get("CST", "")
        cofins = list(item["imposto"].get("COFINS", {}).values())[0] if "COFINS" in item["imposto"] else {}
        cst_cofins = cofins.get("CST", "")

        icms = list(item["imposto"]["ICMS"].values())[0]
        origem_cst = icms.get("orig", "")
        cst_item = origem_cst + icms.get("CST", icms.get("CSOSN", ""))
        bc_icms_item = float(icms.get("vBC", 0))
        alq_icms_item = icms.get("pICMS", 0)
        vlr_icms_item = float(icms.get("vICMS", 0))
        vlr_st_item = float(icms.get("vICMSST", 0))

        vlr_icms_destino_item = float(item["imposto"].get("ICMSUFDest", {}).get("vBCFCPUFDest", 0))
        inf_comp = dados_nf.get("infAdic", {}).get("infCpl", "")

        conteudo_itens.append({
            "Número NF": numero_nf,
            "Natureza da Operação": natureza_op,
            "Fornecedor": nome_fornecedor,
            "UF Fornecedor": uf_fornecedor,
            "Destinatário": nome_destinatario,
            "CNPJ Destinatário": cnpj_destinatario,
            "UF Destinatário": uf_destinatario,
            "Valor ICMS Destino (Total)": vlr_icms_destino,
            "Item": numero_item,
            "Descrição": descricao_item,
            "NCM": ncm_item,
            "CST": cst_item,
            "CFOP": cfop_item,
            "CST PIS": cst_pis,
            "CST COFINS": cst_cofins,
            "Base ICMS": bc_icms_item,
            "Alíquota ICMS": alq_icms_item,
            "Valor ICMS": vlr_icms_item,
            "Valor ICMS Destino Item": vlr_icms_destino_item,
            "Valor ST": vlr_st_item,
            "Info Complementar": inf_comp
        })

    return pd.DataFrame(conteudo_itens)


# ==========================
# Streamlit App
# ==========================
st.title("📑 Leitor de XML NFe")
st.write("Faça upload de **um ou mais arquivos XML** da Nota Fiscal para gerar um Excel consolidado.")

uploaded_files = st.file_uploader(
    "Selecione arquivos XML",
    type="xml",
    accept_multiple_files=True
)

if uploaded_files:
    try:
        conteudo_total = []
        for file in uploaded_files:
            tabela = infos_xml(file)
            conteudo_total.append(tabela)

        # Juntar tudo em um único DataFrame
        resultado_final = pd.concat(conteudo_total, ignore_index=True)

        st.success(f"{len(uploaded_files)} arquivos processados com sucesso! ✅")
        st.dataframe(resultado_final)

        # Gerar Excel em memória
        output = io.BytesIO()
        resultado_final.to_excel(output, index=False)
        output.seek(0)

        st.download_button(
            label="📥 Baixar Relatório",
            data=output,
            file_name="dados_xml_NFe.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"Erro ao processar os arquivos: {e}")