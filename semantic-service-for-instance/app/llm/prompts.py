from app.config import settings


def build_context(symbol):

    imports = symbol.imports[:settings.MAX_IMPORTS]
    calls = symbol.calls[:settings.MAX_CALLS]

    imports_str = ", ".join(imports) if imports else "none"
    calls_str = ", ".join(calls) if calls else "none"

    context = (
        "SYMBOL_CONTEXT\n"
        f"name: {symbol.name}\n"
        f"type: {symbol.type}\n"
        f"language: {symbol.language}\n"
        f"file: {symbol.file}\n"
        f"imports: {imports_str}\n"
        f"calls: {calls_str}\n"
    )

    return context