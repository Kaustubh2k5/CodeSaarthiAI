# graph/resolver.py

def resolve_symbols(symbols):
    """
    Resolve call relationships between symbols.
    Converts call names into graph edges.
    """

    # name → symbols (multiple allowed)
    name_index = {}

    for s in symbols:
        name_index.setdefault(s.name, []).append(s)

    for symbol in symbols:
        symbol.resolved_calls = []

        for call in getattr(symbol, "calls", []):
            targets = name_index.get(call, [])

            for target in targets:
                # avoid self-links
                if target.id != symbol.id:
                    symbol.resolved_calls.append(target.id)

    return symbols