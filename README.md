# Sistema de Gestão de Aparelhos v2.0

Uma aplicação web completa construída com Python e Streamlit para gerir o ciclo de vida de aparelhos eletrónicos (smartphones, etc.) numa empresa, desde a aquisição até à baixa.

## Funcionalidades Principais

- **Dashboard Gerencial:** Visualização rápida dos principais indicadores (KPIs) do inventário, como total de aparelhos, valor total e gráficos de distribuição por status.
- **Sistema de Login Seguro:** Acesso protegido com hashing de senhas e diferentes níveis de permissão (Administrador, Editor, Leitor).
- **Gestão de Utilizadores:** Um painel administrativo dedicado para criar, visualizar e editar os utilizadores do sistema.
- **Interface Moderna e Editável:** A maioria das tabelas de gestão permite a edição direta dos dados, tornando as atualizações rápidas e intuitivas. As listas podem ser minimizadas para uma interface mais limpa.

---

### Módulos Detalhados

#### Gestão de Cadastros
- **Aparelhos:** Registo de novos equipamentos com número de série, IMEI, modelo e valor.
- **Colaboradores:** Gestão completa dos funcionários, com código, setor e contactos.
- **Itens de Referência:** Cadastro centralizado de Marcas, Modelos e Setores para manter a consistência dos dados.
- **Contas Gmail:** Módulo para gerir contas de email associadas a colaboradores ou setores.

#### ⚙Fluxo de Manutenção Completo
- **Abertura de Ordem de Serviço (O.S.):** Envie aparelhos para reparo, registando o fornecedor, o defeito e o último colaborador responsável.
- **Acompanhamento:** Visualize e edite todas as O.S. que estão em andamento.
- **Fecho de O.S.:** Registe o retorno do aparelho, a solução aplicada, o custo do reparo e defina o seu novo status no inventário (de volta ao estoque ou baixado).

#### Geração de Documentos Profissionais em PDF
- **Termo de Responsabilidade (Entrega):**
    - **Checkout Flexível:** Antes de gerar, um formulário de checkout permite editar todas as informações do termo (dados do colaborador, do aparelho, código do termo, etc.).
    - **Checklist Detalhado:** Preencha um checklist completo sobre o estado de cada item entregue.
    - **Design Profissional:** O PDF é gerado com um layout moderno, utilizando a identidade visual da empresa (logo e cores), com uma aparência limpa e profissional, pronto para ser impresso e assinado.

---

## Como Executar Localmente

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
    - **Senha Padrão:** `admin`

---
*LinkedIn: https://linkedin.com/in/cauafreitas*
*Instagram: Caufreitxs*
