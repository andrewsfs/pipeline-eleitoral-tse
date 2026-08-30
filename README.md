\# Pipeline ETL: Inteligência Territorial com Dados do TSE



\## O Problema

Campanhas políticas frequentemente carecem de inteligência geográfica baseada em dados reais. Os dados públicos do Tribunal Superior Eleitoral (TSE) oferecem um raio-X detalhado das votações, mas são disponibilizados em arquivos brutos massivos (gigabytes de CSVs) com granularidade por seção eleitoral, dificultando a análise direta por aplicações web.



\## A Solução

Este projeto implementa um pipeline ETL local utilizando Python e Pandas para processar os microdados do TSE. A arquitetura foi desenhada para:

1\. \*\*Extrair\*\* os dados brutos de votação e locais de seção.

2\. \*\*Transformar\*\* e cruzar (Join) essas informações, consolidando os votos em nível de bairro e coordenadas geográficas.

3\. \*\*Carregar\*\* apenas o fragmento essencial (dados limpos e agregados) em um banco de dados relacional na nuvem (Supabase/PostgreSQL).



\*\*Trade-off Arquitetural:\*\* Optou-se por rodar o processamento pesado localmente e subir apenas os dados agregados para a nuvem. Isso reduz o volume de armazenamento no Supabase em mais de 90% e garante que a aplicação front-end (Mapa de Calor) consuma a API com respostas em milissegundos, reduzindo custos de infraestrutura.



\## Tecnologias Utilizadas

\* \*\*Python 3 \& Pandas:\*\* Processamento em lote e manipulação de DataFrames.

\* \*\*Supabase (PostgreSQL):\*\* Banco de dados relacional em nuvem.

\* \*\*Git/GitHub:\*\* Controle de versão e governança de código.



\## Como Reproduzir Localmente

1\. Clone este repositório.

2\. Crie um ambiente virtual: `python -m venv venv`

3\. Ative o ambiente e instale as dependências: `pip install -r requirements.txt`

4\. Baixe os arquivos do TSE e coloque na pasta `/data`.

5\. Crie um arquivo `.env` com suas credenciais do Supabase.

6\. Execute o script principal: `python src/main.py`

