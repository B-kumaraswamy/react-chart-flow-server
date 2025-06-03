from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json

app = FastAPI(title="Pipeline Builder API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PipelineAnalysis(BaseModel):
    num_nodes: int
    num_edges: int
    is_dag: bool

@app.get("/")
def read_root():
    return {"message": "Pipeline Builder API is running!", "status": "healthy"}

@app.post("/pipelines/parse")
async def parse_pipeline(request: Request):
    """
    RAW JSON endpoint - no Pydantic validation
    """
    try:
        # Get raw JSON data directly
        raw_data = await request.json()
        
        print(f"\n{'='*60}")
        print(f"📊 RAW JSON RECEIVED:")
        print(f"{'='*60}")
        print(json.dumps(raw_data, indent=2))
        print(f"{'='*60}")
        
        # Extract data
        nodes = raw_data.get('nodes', [])
        edges = raw_data.get('edges', [])
        
        print(f"\n📊 EXTRACTED DATA:")
        print(f"Nodes: {len(nodes)}")
        print(f"Edges: {len(edges)}")
        
        if edges:
            first_edge = edges[0]
            print(f"\n🔗 FIRST EDGE DETAILS:")
            print(f"- source: {first_edge.get('source')}")
            print(f"- target: {first_edge.get('target')}")
            print(f"- sourceHandle: {first_edge.get('sourceHandle')}")  # Note: sourceHandle, not sourceHandleId
            print(f"- targetHandle: {first_edge.get('targetHandle')}")  # Note: targetHandle, not targetHandleId
        
        # Calculate stats
        num_nodes = len(nodes)
        num_edges = len(edges)
        is_dag = check_is_dag_raw(nodes, edges)
        
        result = {
            "num_nodes": num_nodes,
            "num_edges": num_edges,
            "is_dag": is_dag
        }
        
        print(f"\n✅ RESULT:")
        print(json.dumps(result, indent=2))
        print(f"{'='*60}\n")
        
        # Return raw dictionary (FastAPI will convert to JSON)
        return result
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return {"error": str(e)}, 400

def check_is_dag_raw(nodes, edges):
    """
    Check if graph is DAG using raw data
    """
    if not edges:
        return True
    
    # Build adjacency list
    graph = {}
    node_ids = {node.get('id') for node in nodes if node.get('id')}
    
    for node_id in node_ids:
        graph[node_id] = []
    
    # Add edges
    for edge in edges:
        source = edge.get('source')
        target = edge.get('target')
        if source and target and source in graph and target in graph:
            graph[source].append(target)
    
    # DFS cycle detection
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {node_id: WHITE for node_id in node_ids}
    
    def has_cycle(node):
        color[node] = GRAY
        for neighbor in graph[node]:
            if color[neighbor] == GRAY:
                return True
            if color[neighbor] == WHITE and has_cycle(neighbor):
                return True
        color[node] = BLACK
        return False
    
    for node_id in node_ids:
        if color[node_id] == WHITE:
            if has_cycle(node_id):
                return False
    
    return True

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)