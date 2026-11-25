# Faça sua primeira chamada MCP

[Voltar ao projeto](../README.md) · [Ver arquitetura](architecture.md)

O cliente Python inicia o servidor como um subprocesso e conversa com ele pela
entrada e saída padrão (`stdio`). Neste exemplo, ele lê um arquivo UTF-8 que o
próprio exercício cria. Você só precisa de Python 3.11+ e das dependências do
projeto instaladas.

## Preparar e executar

Ative o ambiente virtual conforme o [README](../README.md#2-criar-um-ambiente-virtual).
Na raiz do clone, instale o servidor.

```bash
python -m pip install -e .
```

Salve o exemplo como `mcp_example.py` e rode `python mcp_example.py` no mesmo
ambiente virtual.

```python
import asyncio
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import TextContent


async def main() -> None:
    with TemporaryDirectory() as directory:
        workspace = Path(directory).resolve()
        (workspace / "exemplo.txt").write_text("Olá, MCP!", encoding="utf-8")
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "developer_toolbox_mcp.server"],
            env={"TOOLBOX_WORKSPACE_ROOT": str(workspace)},
        )

        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    "read_file", arguments={"path": "exemplo.txt"}
                )
                if result.isError:
                    raise RuntimeError(result.content)

                for item in result.content:
                    if isinstance(item, TextContent):
                        print(item.text)


if __name__ == "__main__":
    asyncio.run(main())
```

O conteúdo esperado em `stdout` é este.

```text
Olá, MCP!
```

A pasta temporária contém apenas o arquivo criado para o exercício.
Ela é removida ao terminar a execução.

## Acompanhar no código

1. Em [`server.py`](../src/developer_toolbox_mcp/server.py), localize
   `@mcp.tool()` sobre `read_file`. O registro torna essa função disponível ao cliente.
2. Em [`config.py`](../src/developer_toolbox_mcp/config.py), veja como a variável
   `TOOLBOX_WORKSPACE_ROOT` define a pasta de trabalho.
3. Em [`security.py`](../src/developer_toolbox_mcp/security.py), siga
   `resolve_safe_path` e `validate_text_file` para ver as checagens feitas
   antes da leitura em UTF-8.

**Experimente** mudar o conteúdo de `exemplo.txt` no script. Observe o novo retorno.
Para ver como um cliente descobre as ferramentas, chame `await session.list_tools()`
depois de inicializar a sessão e inspecione os nomes retornados.
