from ingestion.parser.adapters.adapter import GenericAdapter
from ingestion.parser.adapters.python_adapter import PythonAdapter
from ingestion.parser.adapters.typescript_adapter import TypeScriptAdapter

# Specialized adapters
ADAPTERS = {
    "python": PythonAdapter(),
    "typescript": TypeScriptAdapter(),
}

# fallback adapter
DEFAULT_ADAPTER = GenericAdapter()


def get_adapter(language):
    return ADAPTERS.get(language, DEFAULT_ADAPTER)