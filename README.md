# AssetFlow v3.0

Uma aplicação web completa e robusta construída com Python e Streamlit para gerir todo o ciclo de vida de ativos de TI. A versão 3.0 introduz o **Flow**, um assistente de IA conversacional que revoluciona a forma como os dados são geridos.

## Funcionalidades Principais

- **Dashboard Gerencial:** Visualização rápida dos principais indicadores (KPIs) do inventário.
- **Sistema de Login Seguro:** Acesso protegido com hashing de senhas e diferentes níveis de permissão.
- **Gestão de Utilizadores:** Painel administrativo para criar e gerir os acessos ao sistema.
- **Interface Profissional e Consistente:**
    - **Identidade Visual:** Logo da aplicação e links de contacto profissionalmente integrados na interface.
    - **Layout Otimizado:** Uso de secções que podem ser minimizadas e um design limpo em todas as páginas.
    - **Usabilidade Aprimorada:** Listas suspensas com pesquisa integrada para encontrar rapidamente registos em formulários com muitos dados.
- **Edição Direta na Tabela:** A maioria das tabelas de gestão permite a edição direta e a exclusão de dados, tornando as atualizações rápidas e intuitivas.

---

### Módulos e Fluxos de Trabalho Inteligentes

#### **Novo!** Converse com o Flow (Assistente de IA)
- **Interface Conversacional:** Uma nova página de chat permite aos utilizadores interagir com o sistema usando linguagem natural.
- **Criação de Registos:** Peça ao Flow para criar novos colaboradores, aparelhos ou contas Gmail. Ele guia o utilizador sobre os dados necessários e pede confirmação antes de executar a ação.
- **Pesquisas Inteligentes:** Faça perguntas como "Quais aparelhos estão com o Cauã Freitas?" ou "Mostre o histórico do aparelho com n/s X". O Flow consulta a base de dados e apresenta os resultados diretamente no chat.
- **Gestão do Chat:** Comandos simples como `#info`, `limpar chat` e `logout` para uma experiência de utilizador completa.

#### Gestão de Cadastros
- **Controlo Total:** Gestão completa de Aparelhos, Colaboradores, Marcas, Modelos, Setores e Contas Gmail.

#### Fluxo de Devolução e Triagem
- **Processo Guiado:** Uma página dedicada para registar a devolução de um aparelho, com checklist de inspeção e decisão de destino (Estoque, Manutenção ou Baixa).
- **Integração Inteligente:** Mantém o vínculo do aparelho com o colaborador durante a manutenção para controlo de custos.

#### Fluxo de Manutenção Completo
- **Controlo de O.S.:** Abertura, acompanhamento e fecho de Ordens de Serviço, com registo de fornecedores, custos e soluções.

#### Geração de Documentos Profissionais em PDF
- **Termo de Responsabilidade:** Criação de termos de entrega com design profissional, logo da empresa e um fluxo de "checkout" para edição antes de gerar o PDF.

#### Importação de Dados em Lote
- **Página Dedicada:** Uma nova secção para importar dados em massa a partir de planilhas Excel (.xlsx).
- **Download de Modelos:** Para cada tipo de registo, o sistema oferece um modelo de planilha com exemplos.
- **Validação Inteligente:** O sistema valida os dados durante o upload, reportando sucessos e erros linha a linha.

#### Backup e Restauração
- **Painel Administrativo:** Uma página segura para criar e restaurar backups completos do sistema com um clique.
- **Restauração Segura:** Faça o upload de um ficheiro de backup para restaurar o sistema a um ponto anterior, com múltiplas confirmações para evitar a perda acidental de dados.

---

## Como Executar Localmente

1.  **Clone o repositório:**
    ```bash
    git clone [URL_DO_SEU_REPOSITORIO_AQUI]
    ```
2.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Configure os Segredos:** Crie um ficheiro `.streamlit/secrets.toml` e adicione a sua chave da API Gemini:
    ```toml
    GEMINI_API_KEY = "SUA_CHAVE_API_AQUI"
    ```
4.  **Execute a aplicação:**
    ```bash
    streamlit run app.py
    ```
5.  **Aceda à aplicação** no seu navegador, geralmente em `http://localhost:8501`.
    - **Login Padrão:** `admin`
    - **Senha Padrão:** `admin`

---
*Instagram: Caufreitxs*
