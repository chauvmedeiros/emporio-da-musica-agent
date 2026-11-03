"""
Interface CLI para o agente de atendimento do Empório da Música.
Simula uma conversa por mensagem de texto no terminal.
"""

import os
import sys
from dotenv import load_dotenv

# Garantir saída UTF-8 no terminal (Windows usa cp1252 por padrão e quebra com emojis)
for stream in (sys.stdout, sys.stderr):
    try:
        stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

# Carregar variáveis de ambiente
load_dotenv()

# Verificar API key
if not os.getenv("GOOGLE_API_KEY"):
    print("❌ Erro: GOOGLE_API_KEY não configurada!")
    print("   Crie um arquivo .env com: GOOGLE_API_KEY=sua_chave_aqui")
    print("   Ou exporte: export GOOGLE_API_KEY=sua_chave_aqui")
    print("   Obtenha sua chave em: https://aistudio.google.com/apikey")
    sys.exit(1)


def main():
    from agent import ChatSession

    print("=" * 60)
    print("🎵  Empório da Música — Atendimento Virtual  🎵")
    print("=" * 60)
    print()
    print("Olá! Eu sou a Mel, assistente virtual do Empório da Música!")
    print("Posso ajudar com informações sobre produtos, pedidos,")
    print("promoções e políticas da loja.")
    print()
    print("Digite sua mensagem ou 'sair' para encerrar.")
    print("-" * 60)

    session = ChatSession()

    while True:
        try:
            user_input = input("\n👤 Você: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\n👋 Até mais! Obrigada por visitar o Empório da Música! 🎵")
            break

        if not user_input:
            continue

        if user_input.lower() in ("sair", "exit", "quit", "tchau", "bye"):
            print("\n🎵 Mel: Até mais! Foi um prazer atender você! 😊")
            print("   Se precisar de algo, é só chamar. Boas músicas! 🎶")
            break

        try:
            response = session.send_message(user_input)
            print(f"\n🎵 Mel: {response}")
        except Exception as e:
            print(f"\n⚠️  Ops, tive um probleminha: {e}")
            print("   Pode tentar de novo, por favor?")


if __name__ == "__main__":
    main()
