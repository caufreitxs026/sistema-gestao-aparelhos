# Sistema de Gestão de Aparelhos v2.1

Uma aplicação web completa construída com Python e Streamlit para gerir o ciclo de vida de aparelhos eletrónicos (smartphones, etc.) numa empresa, desde a aquisição até à baixa, com fluxos de trabalho inteligentes para manutenção e devolução.

## Funcionalidades Principais

- **Dashboard Gerencial:** Visualização rápida dos principais indicadores (KPIs) do inventário.
- **Sistema de Login Seguro:** Acesso protegido com hashing de senhas e diferentes níveis de permissão (Administrador, etc.).
- **Gestão de Utilizadores:** Painel administrativo para criar e gerir os acessos ao sistema.
- **Interface Moderna e Editável:** A maioria das tabelas de gestão permite a edição direta dos dados, tornando as atualizações rápidas e intuitivas.

---

### Módulos e Fluxos de Trabalho Inteligentes

#### Gestão de Cadastros
- **Aparelhos, Colaboradores, Marcas, Modelos, Setores:** Controlo total sobre todas as entidades do inventário.
- **Contas Gmail:** Módulo para gerir contas de email associadas a colaboradores ou setores.

#### **Novo!** Fluxo de Devolução e Triagem
- **Processo Guiado:** Uma página dedicada para registar a devolução de um aparelho que estava em uso.
- **Checklist de Inspeção:** Registo permanente da condição de cada item do aparelho no momento da devolução.
- **Decisão de Destino Inteligente:** Com base na inspeção, o sistema guia o utilizador a:
    - **Devolver ao Estoque:** Desvinculando automaticamente o colaborador.
    - **Enviar para Manutenção:** Mantendo o vínculo com o colaborador para controlo de custos e responsabilidade.
    - **Baixar/Inutilizar:** Retirando o aparelho do inventário ativo.

#### Fluxo de Manutenção Completo
- **Integração com Devoluções:** Aparelhos designados para reparo no fluxo de devolução aparecem prontos para o próximo passo.
- **Abertura e Fecho de Ordem de Serviço (O.S.):** Controlo total sobre o envio para fornecedores, registo de custos e solução aplicada.

#### Geração de Documentos Profissionais em PDF
- **Termo de Responsabilidade (Entrega):**
    - **Checkout Flexível:** Um formulário de checkout permite editar todas as informações do termo antes de o gerar.
    - **Design Profissional:** O PDF é gerado com um layout moderno, utilizando a identidade visual da empresa (logo e cores), pronto para ser impresso e assinado.

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
