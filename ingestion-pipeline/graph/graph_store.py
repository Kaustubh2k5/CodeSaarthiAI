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
        # 1. Process Function/Method Calls
        for target in getattr(symbol, "calls", []):
            self.edge_buffer.append((symbol.id, target, 'calls'))

        # 2. Process File/Module Imports
        for imp in getattr(symbol, "imports", []):
            self.edge_buffer.append((symbol.id, imp, 'imports'))

        if len(self.edge_buffer) >= self.batch_size:
            self.flush_edges()

    # ==========================================================
    # NODE BATCH WRITE
    # ==========================================================

    def flush_nodes(self):
        if not self.node_buffer: return
        query_parts = ["g"]
        
        for symbol in self.node_buffer:
            s_id = str(symbol.id).replace("'", "\\'")
            
            # Upsert the Symbol Node with expanded properties
            query_parts.append(f"""
            .V('{s_id}').fold().coalesce(unfold(), addV('symbol').property(T.id, '{s_id}'))
            .property(single, 'name', '{symbol.name}')
            .property(single, 'type', '{symbol.type}')
            .property(single, 'language', '{symbol.language}')
            .property(single, 'file', '{symbol.file}')
            """)

            # Add Framework Tags as secondary nodes
            for tag in getattr(symbol, "framework_tags", []):
                tag_id = f"tag:{tag.lower()}"
                query_parts.append(f"""
                .V('{tag_id}').fold().coalesce(unfold(), addV('framework').property(T.id, '{tag_id}').property('name', '{tag}'))
                .addE('tagged_with').from(V('{s_id}'))
                """)
        
        self.client.submit("".join(query_parts)).all().result()
        self.node_buffer.clear()

    def flush_edges(self):
        if not self.edge_buffer: return
        query_parts = ["g"]
        
        for item in self.edge_buffer:
            # Defensive unpacking
            source = item[0]
            target = item[1]
            label = item[2] if len(item) > 2 else 'calls'

            s_src = str(source).replace("'", "\\'")
            s_tgt = str(target).replace("'", "\\'")

            query_parts.append(f"""
            .V('{s_src}').as('src').V('{s_tgt}').as('tgt')
            .coalesce(
                __.select('src').outE('{label}').where(inV().as('tgt')),
                __.select('src').addE('{label}').to(__.select('tgt'))
            )
            """)

        self.client.submit("".join(query_parts)).all().result()
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