# Pacote de execução LFAM para Claude Code — V2

**Conteúdo:** prompt mestre, enunciado estruturado, documentos técnicos, apresentações, desenhos Ladder, seis referências SCADA, fluxograma e scripts legados de geração gráfica.

## Como instalar no seu repositório
1. Extraia **o conteúdo inteiro deste ZIP** diretamente em `C:\Users\rafael\Desktop\github\lfam-automation` (o arquivo `.project` existente fica onde está; este pacote não contém nem substitui esse projeto).
2. O workspace deve conter `LFAM_Automacao.project`, `PROMPT_CLAUDE_CODE_LFAM_V2.md`, `README_REFERENCIAS.md` e a pasta `references/`.
3. Abra o CODESYS com o `.project` existente e confirme `Ferramentas > Ativar servidor MCP`. No Claude Code conectado a este workspace, use a instrução:

> Leia `PROMPT_CLAUDE_CODE_LFAM_V2.md` integralmente; leia os arquivos em `references/` e a documentação já existente em `docs/`; siga o prompt como instrução de execução, iniciando pela inspeção real do projeto com o MCP `codesys-ide` e por uma POC Ladder compilada. Não confunda imagens com código LD executável.

4. No Windows, para conferir MCP: `claude mcp list`. Dentro de uma sessão do Claude Code, use `/mcp`.

## Organização
- `references/ENUNCIADO_PROFESSORA.md`: rubric obrigatório.
- `references/documents/`: documentos originais (DOCX e PPTX).
- `references/visual/scada/`: seis telas e mosaico de referência.
- `references/visual/ladder/`: quatro pranchas estáticas.
- `references/visual/fluxograma_funcional.png`: diagrama estático.
- `references/legacy/`: **prompts/scripts antigos**; usar somente para comparar desenhos, não executar cegamente.

## Cuidados
- O repositório GitHub está **privado**. Antes de commitar `references/`, confirme permissão do grupo para compartilhar estes materiais com serviço de IA e GitHub, ainda que o repo seja privado. Se necessário, mantenha referências locais com exclusão local do Git e commite apenas código/documentação própria sem dados sensíveis.
- Arquivos da pasta `references/` não devem ser confundidos com um trabalho pronto e testado.
- Não sobrescreva `LFAM_Automacao.project` nem recrie redes que já possam ter sido alteradas no CODESYS sem inspeção/backup.
- Os scripts legados representam **desenhos Python**, não Ladder compilável.
- As imagens SCADA são **maquetes estáticas com dados simulados**, não SCADA online.
