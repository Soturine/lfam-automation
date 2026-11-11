# Política de segurança

Este é um projeto **educacional e de simulação**. **Não é** software de segurança certificado e **não deve** controlar máquina real. A parada de emergência é, e deve ser, um circuito de **hardware independente**.

## Reportar uma vulnerabilidade
Se encontrar algo que exponha **credenciais, acesso indevido ao CLP/OPC UA ou execução de código** (por exemplo: senha em log, escrita em variável que o backend não deveria escrever), **não abra uma Issue pública**. Use [Reportar uma vulnerabilidade](../../security/advisories/new) (canal privado) com: o que é, como reproduzir e o impacto.

## Já tratado (não é novidade)
- Credenciais só em variáveis de ambiente; logs do `asyncua` em `WARNING` (em `DEBUG` ele imprimia a senha).
- OPC UA com canal assinado e cifrado; o backend escreve só em entradas da lista branca.
- Avaliador de expressões com lista branca (sem `eval`).

Detalhes: [LIGACAO_BACKEND_CODESYS](docs/entender/LIGACAO_BACKEND_CODESYS.md).
