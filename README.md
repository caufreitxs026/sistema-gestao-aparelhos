# Sistema de Gestão de Aparelhos

Uma aplicação web completa construída com Python e Streamlit para gerir o ciclo de vida de aparelhos eletrónicos (smartphones, etc.) numa empresa.

##  Funcionalidades Principais

- **Dashboard Gerencial:** Visualização rápida dos principais indicadores (KPIs) do inventário, como total de aparelhos, valor total e gráficos de distribuição por status.
- **Sistema de Login:** Acesso seguro com diferentes níveis de permissão (Administrador, Editor, Leitor).
- **Gestão de Cadastros:**
    - **Aparelhos:** Registo de novos equipamentos com número de série, IMEI, modelo e valor.
    - **Colaboradores:** Gestão completa dos funcionários, com código, setor e contactos.
    - **Itens de Referência:** Cadastro de Marcas, Modelos e Setores para manter a consistência dos dados.
    - **Contas Gmail:** Módulo para gerir contas de email associadas a colaboradores ou setores.
- **Controlo de Movimentações:** Registo de todo o histórico de um aparelho, incluindo entregas, devoluções e envios para manutenção.
- **Geração de Documentos em PDF:**
    - Criação de **Termos de Responsabilidade** profissionais para a entrega de aparelhos.
    - Layout personalizável com logo, checklist de entrega e campos editáveis antes da geração.
- **Interface Moderna:** Tabelas com edição direta de dados e secções que podem ser minimizadas para uma melhor experiência de utilizador.

##  Como Executar Localmente

1.  **Clone o repositório:**
    ```bash
    git clone [URL_DO_SEU_REPOSITORIO_AQUI]
    ```
2.  **Navegue para a pasta do projeto:**
    ```bash
    cd sistema-gestao-aparelhos
    ```
3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Execute a aplicação:**
    ```bash
    streamlit run app.py
    ```
5.  **Aceda à aplicação** no seu navegador, geralmente em `http://localhost:8501`.
    - **Login Padrão:** `admin`
    - **Senha Padrão:** `info09@FTP`

---
*Este projeto foi desenvolvido com o auxílio do Gemini.*
