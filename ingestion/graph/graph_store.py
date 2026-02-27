import os
import boto3
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from dotenv import load_dotenv
from gremlin_python.driver import client, serializer

load_dotenv()

class GraphStore:
    def __init__(self, endpoint=None, port=None, batch_size=10):
        self.endpoint = endpoint or os.getenv("NEPTUNE_WRITE_ENDPOINT")
        self.port = int(port or os.getenv("GRAPH_PORT", 8182))
        self.batch_size = batch_size
        self.region = os.getenv("AWS_REGION", "ap-south-1")

        # 1. Generate the signed headers (the "awscurl" way)
        signed_headers = self._get_signed_headers()

        # 2. Use a CLEAN wss URL (no query params)
        ws_url = f"wss://{self.endpoint}:{self.port}/gremlin"

        print(f"[GraphStore] Connecting to {self.endpoint}...")

        # 3. Pass the headers directly to the Client
        self.client = client.Client(
            ws_url,
            "g",
            message_serializer=serializer.GraphSONSerializersV2d0(),
            headers=signed_headers  # <--- This is the crucial fix
        )

        self.node_buffer = []
        self.edge_buffer = []

    def _get_signed_headers(self):
        """Generates the actual SigV4 headers Neptune needs."""
        # For Neptune (port 8182), the Host header MUST include the port
        host = f"{self.endpoint}:{self.port}"
        url = f"https://{host}/gremlin"
        
        # Create a request object
        request = AWSRequest(method='GET', url=url)
        request.headers['Host'] = host
        
        # Sign it
        session = boto3.Session()
        credentials = session.get_credentials().get_frozen_credentials()
        signer = SigV4Auth(credentials, 'neptune-db', self.region)
        signer.add_auth(request)
        
        # Return only the headers generated (Authorization, X-Amz-Date, etc.)
        return dict(request.headers)

    # ==========================================================
    # QUEUE OPERATIONS
    # ==========================================================

    def save_node(self, symbol):
        self.node_buffer.append(symbol)

        if len(self.node_buffer) >= self.batch_size:
            self.flush_nodes()

    def save_edges(self, symbol):
        for target in getattr(symbol, "resolved_calls", []):
            self.edge_buffer.append((symbol.id, target))

        if len(self.edge_buffer) >= self.batch_size:
            self.flush_edges()

    # ==========================================================
    # NODE BATCH WRITE
    # ==========================================================

    def flush_nodes(self):
        if not self.node_buffer:
            return

        query_parts = ["g"]
        # We no longer use a bindings dict

        for symbol in self.node_buffer:
            # Escape single quotes in strings to prevent query breakage
            s_id = str(symbol.id).replace("'", "\\'")
            s_name = str(symbol.name).replace("'", "\\'")
            s_type = str(symbol.type).replace("'", "\\'")
            s_file = str(symbol.file).replace("'", "\\'")
            s_desc = str(symbol.description or "").replace("'", "\\'")

            query_parts.append(f"""
            .V().has('symbol','id','{s_id}')
            .fold()
            .coalesce(
                unfold(),
                addV('symbol').property('id','{s_id}')
            )
            .property('name','{s_name}')
            .property('type','{s_type}')
            .property('file','{s_file}')
            .property('description','{s_desc}')
            """)

        query = "".join(query_parts)
        # Call submit without the bindings argument
        self.client.submit(query).all().result()
        print(f"[GraphStore] Flushed {len(self.node_buffer)} nodes")
        self.node_buffer.clear()

    def flush_edges(self):
        if not self.edge_buffer:
            return

        query_parts = ["g"]
        for source, target in self.edge_buffer:
            s_src = str(source).replace("'", "\\'")
            s_tgt = str(target).replace("'", "\\'")

            query_parts.append(f"""
            .V().has('symbol','id','{s_src}').as('a')
            .V().has('symbol','id','{s_tgt}')
            .coalesce(
                __.inE('calls').where(outV().as('a')),
                addE('calls').from('a')
            )
            """)

        query = "".join(query_parts)
        self.client.submit(query).all().result()
        print(f"[GraphStore] Flushed {len(self.edge_buffer)} edges")
        self.edge_buffer.clear()

    # ==========================================================
    # FINAL FLUSH (IMPORTANT)
    # ==========================================================

    def flush_all(self):
        self.flush_nodes()
        self.flush_edges()

    # ==========================================================

    def close(self):
        self.flush_all()
        self.client.close()