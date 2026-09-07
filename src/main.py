import basedosdados as bd
import pandas as pd
import os
from dotenv import load_dotenv

def extrair_votos_nuvem():
    load_dotenv()
    project_id = os.environ.get("GCP_PROJECT_ID")
    
    municipio_alvo = 'DUQUE DE CAXIAS'
    ano_alvo = 2024
    
    # A query SQL executa o Join no BigQuery e retorna apenas os dados agregados.
    # Utilizamos o id_municipio da Base dos Dados (TSE) ou filtramos pelo nome para simplificar.
    query = f"""
        SELECT 
            v.ano,
            v.sigla_uf,
            l.nome_municipio,
            l.bairro,
            v.cargo,
            v.numero_candidato,
            SUM(v.votos) as total_votos
        FROM `basedosdados.br_tse_eleicoes.votacao_secao` AS v
        INNER JOIN `basedosdados.br_tse_eleicoes.local_votacao` AS l
            ON v.ano = l.ano 
            AND v.sigla_uf = l.sigla_uf 
            AND v.id_municipio_tse = l.id_municipio_tse 
            AND v.zona = l.zona 
            AND v.secao = l.secao
        WHERE v.ano = {ano_alvo} 
          AND v.sigla_uf = 'RJ' 
          AND l.nome_municipio = '{municipio_alvo}'
        GROUP BY 1, 2, 3, 4, 5, 6
    """
    
    print(f"Executando processamento em nuvem para {municipio_alvo} ({ano_alvo})...")
    
    # A primeira vez que este comando rodar, ele abrirá uma aba no navegador 
    # pedindo para você fazer login com sua conta Google e autorizar o acesso.
    df_consolidado = bd.read_sql(query, billing_project_id=project_id)
    
    print(f"Processamento concluído. Total de registros: {len(df_consolidado)}")
    
    # Exibe as 5 primeiras linhas para conferência
    print(df_consolidado.head())
    
    return df_consolidado

if __name__ == "__main__":
    df_final = extrair_votos_nuvem()