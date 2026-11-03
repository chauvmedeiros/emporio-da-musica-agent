# 🎵 Empório da Música - Agente de Atendimento ao Cliente

Agente conversacional inteligente para atendimento ao cliente do **Empório da Música**, uma loja de instrumentos musicais em Campo Grande/MS. O agente simula um atendimento via WhatsApp, respondendo perguntas sobre produtos, pedidos, promoções e políticas da loja.

## 📋 Índice

- [Como Executar](#-como-executar)
- [Arquitetura](#-arquitetura)
- [Decisões Técnicas](#-decisões-técnicas)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Exemplos de Interação](#-exemplos-de-interação)
- [Limitações Conhecidas](#-limitações-conhecidas)
- [Uso de IA no Desenvolvimento](#-uso-de-ia-no-desenvolvimento)

## 🚀 Como Executar

### Pré-requisitos

- Python 3.10+
- Chave de API do Google Gemini (gratuita)

### Passo a passo

1. **Clone o repositório:**
```bash
git clone https://github.com/chauvmedeiros/emporio-da-musica-agent.git
cd emporio-da-musica-agent
```

2. **Crie e ative um ambiente virtual:**
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows
```

3. **Instale as dependências:**
```bash
pip install -r requirements.txt
```

4. **Configure a API key:**

Obtenha uma chave gratuita em [Google AI Studio](https://aistudio.google.com/apikey) e crie o arquivo `.env`:
```bash
cp .env.example .env
# Edite o .env e coloque sua chave
```

5. **Execute:**
```bash
python main.py
```

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────┐
│                    CLI (main.py)                 │
│              Interface do Usuário                │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────┐
│              ChatSession (agent.py)              │
│         Histórico de Conversa (memória)          │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────┐
│          ReAct Agent (LangChain)                 │
│      Google Gemini 3.5 Flash + Tool Calling      │
└──────────┬───────┬───────┬───────┬──────────────┘
           │       │       │       │
     ┌─────▼──┐ ┌──▼───┐ ┌▼─────┐ ┌▼──────────┐
     │Produtos│ │Pedidos│ │Promos│ │ Políticas  │
     │ (CSV)  │ │ (CSV) │ │(CSV) │ │  (PDF)     │
     └────────┘ └──────┘ └──────┘ └────────────┘
```

O agente utiliza a abordagem **ReAct** (Reasoning + Acting): a cada mensagem do cliente, o modelo decide quais ferramentas acionar, analisa os resultados e compõe uma resposta contextualizada.

## 🔧 Decisões Técnicas

### 1. Framework: LangChain com Tool Calling

**Escolha:** LangChain 1.x (`create_agent`)

**Justificativa:** O `create_agent` do LangChain oferece uma abstração madura para construir agentes com ferramentas, com suporte nativo a tool calling (function calling) do Gemini. Isso permite que o modelo decida autonomamente quais ferramentas acionar com base na pergunta do cliente, sem necessidade de lógica condicional manual. Por baixo dos panos ele monta um agente ReAct sobre o LangGraph, o que mantém o código simples para este caso de uso (um agente de atendimento com ferramentas de consulta) e já deixa o caminho aberto para fluxos com estados mais complexos no futuro.

**Alternativas consideradas:**
- **LangGraph "na mão":** Montar o grafo manualmente dá mais controle sobre estados e roteamento condicional, mas adiciona complexidade desnecessária para este caso
- **Implementação manual com Gemini SDK:** Menor abstração, mais controle, mas requer reimplementar o loop ReAct e a gestão de ferramentas
- **RAG puro:** Limitado para consultas estruturadas (CSV); melhor para documentos longos não estruturados

### 2. Modelo: Google Gemini 3.5 Flash

**Escolha:** `gemini-3.5-flash` via Google AI Studio (tier gratuito)

**Justificativa:** Oferece excelente relação custo-performance para agentes conversacionais. Suporta tool calling nativo (fundamental para a abordagem ReAct), compreende bem português brasileiro, e o tier gratuito é suficiente para desenvolvimento e demonstração. A baixa latência do Flash é ideal para simulação de atendimento em tempo real.

**Alternativas consideradas:**
- **GPT-4o (OpenAI):** Excelente qualidade, mas custo por token significativamente maior
- **Claude (Anthropic):** Ótimo em português e raciocínio, mas sem tier gratuito para API
- **Modelos open-source (Llama, Mistral):** Requerem infraestrutura de hosting e têm desempenho inferior em tool calling

### 3. Abordagem: ReAct Agent com Tools

**Escolha:** Agente ReAct com 6 ferramentas especializadas

**Justificativa:** Cada ferramenta encapsula uma consulta específica aos dados da loja:
- `search_products` - Busca por nome, categoria ou descrição
- `check_product_by_id` - Detalhes de um produto específico
- `check_active_promotions` - Lista promoções vigentes
- `track_order` - Rastreamento por ID, código, nome ou e-mail
- `lookup_customer` - Busca dados cadastrais do cliente
- `consult_store_policies` - Consulta o PDF de políticas

Esta separação permite que o modelo decida quais fontes consultar com base no contexto, podendo combinar múltiplas ferramentas em uma única resposta (ex: buscar produto + verificar promoção).

**Alternativas consideradas:**
- **SQL Agent:** Converter CSVs em banco SQLite e usar queries SQL. Mais flexível para consultas complexas, mas adiciona camada de complexidade e risco de SQL injection/erros de sintaxe
- **RAG com vector store:** Ideal para grandes volumes de texto, mas os CSVs são estruturados e pequenos o suficiente para consulta direta com Pandas

### 4. Interface: CLI (Command Line Interface)

**Escolha:** Interface de terminal com loop de conversação

**Justificativa:** A CLI é a interface mais direta para demonstrar a funcionalidade do agente sem dependências adicionais de frontend. O foco do desafio está na lógica do agente, não na interface. O formato simula uma conversa por mensagem, alinhado com o cenário WhatsApp proposto.

**Alternativas consideradas:**
- **API REST (FastAPI/Flask):** Mais profissional para produção, mas adiciona complexidade sem agregar à avaliação do agente
- **Streamlit/Gradio:** Interface visual rápida, mas mascara a interação real com o agente
- **Jupyter Notebook:** Bom para demonstração, mas menos reprodutível

### 5. Histórico de Conversação: Em Memória

**Escolha:** Lista de mensagens (`HumanMessage`/`AIMessage`) em memória

**Justificativa:** Para uma sessão de atendimento via mensagem, o histórico em memória é suficiente. O contexto do atendimento é de curta duração (uma sessão de chat), não sendo necessário persistência entre execuções. A implementação é simples e leve.

**Alternativas consideradas:**
- **SQLite/Redis:** Necessário para produção com múltiplos atendentes, mas overkill para demonstração
- **ConversationBufferWindowMemory:** Útil para limitar tokens em conversas longas, mas o Gemini Flash tem janela de contexto generosa (1M tokens)

### 6. Tratamento dos Dados: Pandas + Texto Direto

**Escolha:** CSVs carregados em DataFrames Pandas; PDF extraído como texto

**Justificativa:** Os dados são pequenos (64 produtos, 50 clientes, 20 pedidos) e estruturados. Pandas permite filtros eficientes e joins entre tabelas sem necessidade de banco de dados. O PDF de políticas (8 páginas) é pequeno o suficiente para ser passado integralmente ao modelo quando necessário, dispensando chunking e vector store.

**Alternativas consideradas:**
- **SQLite:** Mais robusto para queries complexas, mas adiciona etapa de ETL
- **Vector store (FAISS/Chroma):** Essencial para grandes volumes de documentos, mas overkill para 8 páginas de políticas

## 📁 Estrutura do Projeto

```
emporio-da-musica-agent/
├── data/
│   ├── products.csv          # Catálogo de produtos
│   ├── categories.csv        # Categorias de instrumentos
│   ├── customers.csv         # Base de clientes
│   ├── orders.csv            # Pedidos
│   ├── order_items.csv       # Itens dos pedidos
│   ├── promotions.csv        # Promoções
│   └── politicas_da_loja.pdf # Políticas da loja
├── examples/
│   ├── exemplo_01_produtos.md
│   ├── exemplo_02_pedido.md
│   ├── exemplo_03_promocoes.md
│   ├── exemplo_04_politicas.md
│   └── exemplo_05_fora_escopo.md
├── agent.py                  # Configuração do agente e sessão de chat
├── data_loader.py            # Carregamento e preparação dos dados
├── tools.py                  # Ferramentas do agente
├── main.py                   # Interface CLI
├── requirements.txt          # Dependências Python
├── .env.example              # Template de variáveis de ambiente
├── .gitignore
└── README.md
```

## 💬 Exemplos de Interação

Os exemplos completos estão na pasta `examples/`. Resumo dos cenários cobertos:

1. **Busca e recomendação de produtos** - Cliente procurando um violão para iniciante
2. **Rastreamento de pedido** - Cliente verificando status de entrega
3. **Promoções ativas** - Cliente perguntando sobre ofertas e descontos
4. **Políticas da loja** - Cliente com dúvidas sobre troca/devolução e frete
5. **Fora do escopo** - Agente lidando com perguntas não relacionadas à loja

## ⚠️ Limitações Conhecidas

1. **Sem persistência entre sessões:** O histórico de conversa é perdido ao encerrar o programa. Em produção, seria necessário um banco de dados para manter contexto entre sessões.

2. **Dados estáticos:** Os CSVs são carregados uma vez na inicialização. Alterações nos dados requerem reiniciar o agente. Em produção, seria conectado a um banco de dados ou API em tempo real.

3. **Sem autenticação de cliente:** O agente não verifica a identidade do cliente antes de mostrar informações de pedidos. Em produção, seria necessário um fluxo de verificação (ex: CPF + e-mail).

4. **Limite do tier gratuito:** O Google Gemini gratuito tem limites de requisições por minuto. Para uso em produção, seria necessário um plano pago.

5. **Políticas como texto integral:** O PDF de políticas é passado integralmente ao modelo a cada consulta. Com documentos maiores, seria necessário implementar RAG com chunking e vector store.

6. **Sem integração real com WhatsApp:** O agente simula o atendimento via CLI. A integração com WhatsApp Business API requer infraestrutura adicional (webhook, servidor, certificação Meta).

## 🚀 O que Faria com Mais Tempo

Se houvesse mais tempo disponível, o próximo passo natural seria evoluir este agente para uma **plataforma completa de atendimento ao cliente** - um sistema web onde os atendentes não precisariam usar o WhatsApp Web diretamente. A visão inclui:

### Plataforma de Gestão de Atendimentos

- **Painel web para atendentes:** Interface própria para gerenciar conversas sem depender do WhatsApp Web (que consome muita memória e limita o controle). Múltiplos atendentes poderiam acessar o sistema simultaneamente com suas próprias credenciais.

- **Handoff inteligente IA ↔ Humano:** O atendente poderia, a qualquer momento, assumir uma conversa que a IA estava conduzindo ("stop IA → atendimento humano"), e depois devolver para a IA continuar. A IA também sinalizaria automaticamente quando detectasse que o cliente precisa de atendimento humano (reclamações, situações sensíveis, perguntas muito fora do escopo).

- **Catálogo visual de produtos:** Galeria com fotos e vídeos dos instrumentos, integrada às ferramentas do agente para enviar mídia durante o atendimento.

- **Relatórios e analytics:** Dashboard com métricas de atendimento - tempo médio de resposta, taxa de resolução por IA vs. humano, produtos mais consultados, horários de pico.

- **Envio de mensagens em massa:** Campanhas segmentadas para clientes cadastrados (promoções, novidades, restock de produtos populares).

- **CRM integrado:** Histórico completo de cada cliente - todas as conversas, compras, preferências - para atendimento personalizado e follow-up proativo.

### Stack que Utilizaria

Para essa evolução, a stack que escolheria com base na minha experiência:
- **Frontend:** React/Next.js ou Lovable para prototipação rápida
- **Backend:** Supabase (PostgreSQL + Auth + Realtime) para dados e autenticação em tempo real
- **Automações:** n8n para orquestração de workflows (webhooks do WhatsApp, notificações, relatórios agendados)
- **WhatsApp:** Integração via WhatsApp Business API oficial da Meta com webhook
- **IA:** Mesmo agente LangChain, adaptado para processar mensagens do webhook e responder via API

Essa visão reflete o tipo de sistema que já construo profissionalmente - agentes de IA integrados com WhatsApp Business API, dashboards de gestão e automações com n8n - e seria a evolução natural deste protótipo para um produto real.

## 🤖 Uso de IA no Desenvolvimento

Transparência é importante: este projeto foi desenvolvido em parceria com **Claude (Anthropic)**, utilizado como assistente de desenvolvimento ao longo de todo o processo. Especificamente, a IA auxiliou em:

- **Arquitetura:** Discussão e validação da estrutura do projeto, escolha de padrões (ReAct, tool calling) e definição do fluxo do agente
- **Implementação:** Geração do código-base dos módulos, com iterações de refinamento
- **Documentação:** Elaboração do README, exemplos de interação e justificativas técnicas
- **Revisão:** Code review, identificação de edge cases e melhorias na robustez das ferramentas

**O que é meu neste projeto:**
- As **decisões de arquitetura** foram baseadas na minha experiência construindo agentes de IA com LangChain, WhatsApp Business API e n8n profissionalmente
- A **escolha do Gemini 3.5 Flash** como modelo, a abordagem de dados com Pandas (sem vector store para dados pequenos) e o design da persona "Mel" refletem decisões pragmáticas que tomo no dia a dia
- A **visão de produto** (seção "O que faria com mais tempo") vem diretamente da minha atuação profissional com sistemas de atendimento via WhatsApp
- Todo o código foi **revisado, compreendido e validado** - não aceitei output da IA sem entender o que cada parte faz e por quê
