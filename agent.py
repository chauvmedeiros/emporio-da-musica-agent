"""
Agente de atendimento ao cliente do Empório da Música.
Utiliza LangChain + Google Gemini com abordagem ReAct Agent.
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
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


def create_agent(model_name: str = "gemini-2.0-flash") -> AgentExecutor:
    """Cria e retorna o agente configurado."""
    llm = ChatGoogleGenerativeAI(
        model=model_name,
        temperature=0.3,
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, ALL_TOOLS, prompt)

    return AgentExecutor(
        agent=agent,
        tools=ALL_TOOLS,
        verbose=False,
        handle_parsing_errors=True,
        max_iterations=5,
    )


class ChatSession:
    """Gerencia uma sessão de chat com histórico de conversação."""

    def __init__(self, model_name: str = "gemini-2.0-flash"):
        self.agent = create_agent(model_name)
        self.chat_history: list = []

    def send_message(self, message: str) -> str:
        """Envia uma mensagem e retorna a resposta do agente."""
        response = self.agent.invoke({
            "input": message,
            "chat_history": self.chat_history,
        })

        # Atualizar histórico
        self.chat_history.append(HumanMessage(content=message))
        self.chat_history.append(AIMessage(content=response["output"]))

        return response["output"]

    def reset(self):
        """Limpa o histórico da conversa."""
        self.chat_history = []
