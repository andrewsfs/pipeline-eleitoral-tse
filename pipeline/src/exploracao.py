import pandas as pd

def explorar_arquivos():
    # Caminhos ajustados para rodar a partir da raiz do projeto (pipeline_tse)
    arquivo_votos = 'data/2022/votacao_secao_2022_RJ.csv'
    arquivo_locais = 'data/2022/eleitorado_local_votacao_2022.csv'
    
    print("--- 1. Análise do Arquivo de Votos ---")
    try:
        df_votos = pd.read_csv(arquivo_votos, sep=';', encoding='latin1', nrows=5)
        colunas_votos = ['NM_MUNICIPIO', 'NR_ZONA', 'NR_SECAO', 'DS_CARGO', 'NM_VOTAVEL', 'QT_VOTOS']
        colunas_existentes_votos = [c for c in colunas_votos if c in df_votos.columns]
        print(df_votos[colunas_existentes_votos])
    except FileNotFoundError:
        print(f"Erro: Arquivo {arquivo_votos} não encontrado.")

    print("\n--- 2. Análise do Arquivo de Locais (O Mapa) ---")
    try:
        df_locais = pd.read_csv(arquivo_locais, sep=';', encoding='latin1', nrows=5)
        
        colunas_locais = ['NM_MUNICIPIO', 'NR_ZONA', 'NR_SECAO', 'NM_BAIRRO', 'DS_TIPO_SECAO_AGREGADA', 'NR_SECAO_PRINCIPAL']
        colunas_existentes_locais = [c for c in colunas_locais if c in df_locais.columns]
        
        print(df_locais[colunas_existentes_locais])
        
        print("\nVerificando se Latitude e Longitude vieram preenchidas:")
        lat_lon = [c for c in ['NR_LATITUDE', 'NR_LONGITUDE'] if c in df_locais.columns]
        print(df_locais[lat_lon])
        
    except FileNotFoundError:
        print(f"Erro: Arquivo {arquivo_locais} não encontrado.")

if __name__ == "__main__":
    explorar_arquivos()