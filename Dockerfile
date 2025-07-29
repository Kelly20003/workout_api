# Usar uma imagem base oficial do Python
FROM python:3.11-slim

# Definir o diretório de trabalho dentro do contêiner
WORKDIR /app

# Copiar o arquivo de dependências e instalar as libs
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo o resto do código do projeto para o contêiner
COPY . .