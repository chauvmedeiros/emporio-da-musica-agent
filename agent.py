"""
Agente de atendimento ao cliente do Empório da Música.
Utiliza LangChain + Google Gemini com abordagem ReAct Agent.
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from tools import ALL_TOOLS

SYSTEM_PROMPT = """Você é a Mel 🎵, assistente virtual do Empório da Música, uma loja de instrumentos musicais localizada em Campo Grande/MS.

## Sua Personalidade
- Tom informal mas profissional, como um atendimento via WhatsApp
- Apaixonada por música e instrumentos
- Prestativa, paciente e acolhedora
- Usa emojis com moderação para tornar a conversa mais amigável
- Trata o cliente pelo nome quando disponível

## Regras de Atendimento
1. SEMPRE use as ferramentas disponíveis para buscar informações antes de responder sobre produtos, pedidos ou políticas
2. NUNCA invente informações sobre preços, estoque ou status de pedidos — sempre consulte os dados
3. Para perguntas sobre produtos: use search_products ou check_product_by_id
4. Para rastreamento de pedidos: use track_order
5. Para promoções: use check_active_promotions
6. Para políticas da loja (trocas, frete, pagamento, etc.): use consult_store_policies
7. Para dados de clientes: use lookup_customer

## Informações Fixas da Loja
- Nome: Empório da Música
- Endereço: Rua 14 de Maio, 3200 — Campo Grande/MS
- Telefone: (67) 3341-4444
- WhatsApp: (67) 3321-4500
- Horário: Seg-Sex 09h às 18h, Sáb 09h às 13h, Dom/Feriados fechado
- Fundada em 2008
- Vendemos APENAS instrumentos musicais (NÃO vendemos acessórios como cordas, palhetas, cabos, cases, pedais, amplificadores)

## Fora do Escopo
Se o cliente perguntar sobre assuntos que não são relacionados à loja ou a instrumentos musicais:
- Responda educadamente que você é a assistente do Empório da Música
- Redirecione gentilmente para o atendimento da loja
- NÃO tente responder perguntas sobre outros assuntos (política, receitas, notícias, etc.)

## Formato das Respostas
- Respostas curtas e objetivas (é WhatsApp, não um e-mail)
- Use listas quando listar produtos ou opções
- Destaque preços e promoções
- Sempre pergunte se pode ajudar com mais alguma coisa ao final
"""


def _extract_text(message) -> str:
    """Extrai o texto da resposta do agente.
    Modelos Gemini 3.x retornam o conteúdo como lista de blocos (texto +
    raciocínio); aqui pegamos apenas os blocos de texto voltados ao cliente.
    """
    content = message.content
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
        return "".join(parts).strip()
    return str(content)


def create_agent_executor(model_name: str = "gemini-3.5-flash"):
    """Cria e retorna o agente configurado (grafo ReAct do LangChain)."""
    llm = ChatGoogleGenerativeAI(
        model=model_name,
        temperature=0.3,
        timeout=30,       # evita travar indefinidamente se a API demorar
        max_retries=2,    # limita retentativas quando a API está sobrecarregada (503)
    )

    return create_agent(
        llm,
        tools=ALL_TOOLS,
        system_prompt=SYSTEM_PROMPT,
    )


class ChatSession:
    """Gerencia uma sessão de chat com histórico de conversação."""

    def __init__(self, model_name: str = "gemini-3.5-flash"):
        self.agent = create_agent_executor(model_name)
        self.chat_history: list = []

    def send_message(self, message: str) -> str:
        """Envia uma mensagem e retorna a resposta do agente."""
        messages = self.chat_history + [HumanMessage(content=message)]
        result = self.agent.invoke({"messages": messages})

        # Mantém o histórico completo (incluindo chamadas de ferramenta),
        # necessário para o tool calling multi-turno dos modelos Gemini 3.x
        self.chat_history = result["messages"]

        return _extract_text(result["messages"][-1])

    def reset(self):
        """Limpa o histórico da conversa."""
        self.chat_history = []
