# MCP Server for Harvard PrimeKG

Model Context Protocol (MCP) server for querying the [Harvard PrimeKG](https://zitniklab.hms.harvard.edu/projects/PrimeKG/) precision medicine knowledge graph.

**✨ Key Feature: Automatic Updates** - This server automatically downloads and uses the latest version of PrimeKG data from Harvard Dataverse, ensuring you always query the current version.

## About PrimeKG

PrimeKG is a comprehensive precision medicine knowledge graph containing:
- **129,375 nodes** representing genes, drugs, diseases, biological processes, and more
- **8+ million relationships** integrating 20+ biomedical databases
- Data from DrugBank, PRIMEKG, CTD, DisGeNET, GO, Reactome, SIDER, and others

## Features

This MCP server provides tools to:
- **Automatically download the latest PrimeKG data** (checks weekly by default)
- Search for nodes (genes, drugs, diseases) by name or ID
- Find relationships between entities
- Discover drug targets and disease-associated genes
- Explore drug-disease connections
- Query the knowledge graph structure

## Installation

### Prerequisites

- Python 3.10 or higher
- [uv](https://docs.astral.sh/uv/) package manager

### Install from PyPI (when published)

```bash
uvx mcp-primekg
```

### Install from Source

1. Clone this repository:
```bash
git clone https://github.com/asaravia-butler/MCP_Harvard_PrimeKG.git
cd MCP_Harvard_PrimeKG
```

2. Install dependencies:
```bash
uv sync
```

## Data Setup

### Automatic Mode (Recommended - Always Current)

The server will **automatically download the latest PrimeKG data** on first run and check for updates weekly.

**No manual data download required!** Just configure and run:

```json
{
  "mcpServers": {
    "primekg": {
      "command": "uvx",
      "args": ["mcp-primekg"],
      "env": {
        "PRIMEKG_DATA_PATH": "/Users/yourusername/primekg_data",
        "PRIMEKG_AUTO_UPDATE": "true",
        "PRIMEKG_UPDATE_INTERVAL_DAYS": "7",
        "INSTRUCTIONS": "Query the PrimeKG knowledge graph for precision medicine insights."
      }
    }
  }
}
```

The server will:
1. Create the data directory if it doesn't exist
2. Download the latest PrimeKG data from Harvard Dataverse (~600MB)
3. Check for updates every 7 days (configurable)
4. Use cached data between updates

### Manual Mode

Set `PRIMEKG_AUTO_UPDATE: "false"` and manually download data from [Harvard Dataverse](https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/IXA7BM).

### Neo4j Mode (For Complex Queries)

For advanced graph traversal and complex path queries, use Neo4j:

#### Step 1: Download Required Files

Download only these two files from [Harvard Dataverse](https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/IXA7BM):

```bash
# Download nodes file (7.5 MB)
curl -LO nodes.tab "https://dataverse.harvard.edu/api/access/datafile/6180617"

# Download edges file (368.6 MB)
curl -LO edges.csv "https://dataverse.harvard.edu/api/access/datafile/6180616"
```

#### Step 2: Modify CSV Headers for Neo4j

Neo4j requires specific header formats. Update the headers:

**For nodes.tab:**
```bash
# Change header from:
# node_index  node_id  node_type  node_name  node_source
# To:
sed -i.bak '1s/.*/node_index:ID\tnode_id\t:LABEL\tnode_name\tnode_source/' nodes.tab
```

**For edges.csv:**
```bash
# Change header from:
# relation,display_relation,x_index,y_index
# To:
sed -i.bak '1s/.*/:TYPE,display_relation,:START_ID,:END_ID/' edges.csv
```

Or manually edit the first line of each file:
- **nodes.tab**: `node_index:ID	node_id	:LABEL	node_name	node_source`
- **edges.csv**: `:TYPE,display_relation,:START_ID,:END_ID`

#### Step 3: Import into Neo4j

**Using Neo4j Desktop:**

1. Create a new database (DBMS) in Neo4j Desktop
2. Stop the database if it's running
3. Open terminal in the DBMS directory (click ⋯ → Open Folder → DBMS)
4. Run the import command:

```bash
./bin/neo4j-admin database import full primekg \
  --nodes=/full/path/to/nodes.tab \
  --relationships=/full/path/to/edges.csv \
  --delimiter-nodes=TAB \
  --delimiter-relationships=COMMA \
  --trim-strings=true
```

**Using Neo4j Server:**

```bash
neo4j-admin database import full primekg \
  --nodes=/full/path/to/nodes.tab \
  --relationships=/full/path/to/edges.csv \
  --delimiter-nodes=TAB \
  --delimiter-relationships=COMMA \
  --trim-strings=true
```

**Note:** Replace `/full/path/to/` with the actual absolute paths to your files.

#### Step 4: Start Database and Verify

1. Start the database in Neo4j Desktop
2. Open Neo4j Browser
3. Verify the import:

```cypher
// Check node count
MATCH (n) RETURN count(n) as node_count;
// Should return ~129,375 nodes

// Check edge count
MATCH ()-[r]->() RETURN count(r) as edge_count;
// Should return ~4+ million edges

// View node types
MATCH (n) RETURN DISTINCT labels(n) as node_types, count(*) as count;
```

#### Step 5: Use with MCP Server

Once imported, use the `mcp-genelab` server with your PrimeKG database by adding to your config:

```json
"primekg-neo4j": {
  "command": "uvx",
  "args": ["mcp-genelab"],
  "env": {
    "NEO4J_URI": "bolt://localhost:7687",
    "NEO4J_USERNAME": "neo4j",
    "NEO4J_PASSWORD": "your_password",
    "NEO4J_DATABASE": "primekg",
    "INSTRUCTIONS": "Query the PrimeKG precision medicine knowledge graph for drug-disease-gene relationships and biomedical insights from 20+ integrated databases."
  }
}
```

## Configuration

### For Claude Desktop

Add to your `claude_desktop_config.json`:

#### Automatic Updates (Recommended - Always Current):

**Local Development Version (primekg-auto-dev):**
```json
{
  "mcpServers": {
    "primekg-auto-dev": {
      "command": "uv",
      "args": ["run", "--directory", "/absolute/path/to/MCP_Harvard_PrimeKG", "mcp-primekg"],
      "env": {
        "PRIMEKG_DATA_PATH": "/Users/yourusername/primekg_data",
        "PRIMEKG_AUTO_UPDATE": "true",
        "PRIMEKG_UPDATE_INTERVAL_DAYS": "7",
        "INSTRUCTIONS": "Query the latest PrimeKG knowledge graph for precision medicine insights, drug-disease-gene relationships, and biomedical knowledge."
      }
    }
  }
}
```

**Production Version - After Publishing to PyPI (primekg-auto):**
```json
{
  "mcpServers": {
    "primekg-auto": {
      "command": "uvx",
      "args": ["mcp-primekg"],
      "env": {
        "PRIMEKG_DATA_PATH": "/Users/yourusername/primekg_data",
        "PRIMEKG_AUTO_UPDATE": "true",
        "PRIMEKG_UPDATE_INTERVAL_DAYS": "7",
        "INSTRUCTIONS": "Query the latest PrimeKG knowledge graph for precision medicine insights."
      }
    }
  }
}
```

**Configuration Options:**
- `PRIMEKG_DATA_PATH`: Directory to store PrimeKG data (default: `~/primekg_data`)
- `PRIMEKG_AUTO_UPDATE`: Enable automatic updates (default: `true`)
- `PRIMEKG_UPDATE_INTERVAL_DAYS`: Days between update checks (default: `7`)

**Note:** 
- Use `primekg-auto-dev` with the `--directory` flag when developing locally or before publishing
- Use `primekg-auto` after publishing to PyPI for simpler configuration
- Replace `/absolute/path/to/MCP_Harvard_PrimeKG` with the actual path where you cloned this repository

#### Using Neo4j (for better performance with complex queries):
```json
{
  "mcpServers": {
    "primekg-neo4j": {
      "command": "uvx",
      "args": ["mcp-genelab"],
      "env": {
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USERNAME": "neo4j",
        "NEO4J_PASSWORD": "your_password",
        "NEO4J_DATABASE": "primekg",
        "INSTRUCTIONS": "Query the PrimeKG knowledge graph for precision medicine insights."
      }
    }
  }
}
```

## Available Tools

### `search_nodes`
Search for nodes by name or ID
- **Input**: query (string), node_type (optional), limit (default: 10)
- **Example**: Search for "aspirin" or "breast cancer"

### `get_node_relationships`
Get all relationships for a specific node
- **Input**: node_id (string), relationship_type (optional), limit (default: 50)

### `find_drug_targets`
Find gene/protein targets for a drug
- **Input**: drug_name (string)
- **Example**: Find targets for "metformin"

### `find_disease_genes`
Find genes associated with a disease
- **Input**: disease_name (string), limit (default: 50)
- **Example**: Find genes for "Alzheimer's disease"

### `find_drug_disease_paths`
Find connections between drugs and diseases
- **Input**: drug_name, disease_name, max_path_length (default: 3)

### `get_node_details`
Get detailed information about a specific node
- **Input**: node_id (string)

## Example Usage

Once configured in Claude Desktop, you can ask:

- "What are the protein targets of aspirin in PrimeKG?"
- "Find genes associated with Parkinson's disease in PrimeKG"
- "Search for drugs that target EGFR in PrimeKG"
- "What are the relationships between metformin and diabetes in PrimeKG?"
- "Show me the biological processes associated with TP53 in PrimeKG"

## Development

### Running Tests
```bash
uv run pytest
```

### Code Formatting
```bash
uv run black src/
```

### Type Checking
```bash
uv run mypy src/
```

## Data Sources

PrimeKG integrates data from 20+ biomedical resources:
- DrugBank, ChEMBL (drugs)
- DisGeNET, OMIM (diseases)
- STRING, BioGRID (protein interactions)
- Gene Ontology (biological processes)
- Reactome, KEGG (pathways)
- SIDER (side effects)
- And many more...

## Citation

If you use PrimeKG in your research, please cite:

```bibtex
@article{chandak2023building,
  title={Building a knowledge graph to enable precision medicine},
  author={Chandak, Payal and Huang, Kexin and Zitnik, Marinka},
  journal={Scientific Data},
  volume={10},
  number={1},
  pages={67},
  year={2023},
  publisher={Nature Publishing Group UK London}
}
```

## License

This MCP server is released under the MIT License.

PrimeKG data is released under CC BY 4.0 License by Harvard Medical School.

## Links

- [PrimeKG Project Page](https://zitniklab.hms.harvard.edu/projects/PrimeKG/)
- [PrimeKG GitHub](https://github.com/mims-harvard/PrimeKG)
- [PrimeKG Paper](https://www.nature.com/articles/s41597-023-01960-3)
- [Harvard Dataverse](https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/IXA7BM)
- [NSF Proto-OKN Project Page](https://www.proto-okn.net/)
- [SPOKE-OKN Project Page](https://spoke.ucsf.edu/prototype-open-knowledge-network-proto-okn-spoke-space-health)
- [MCP-GeneLab GitHub](https://github.com/sbl-sdsc/mcp-genelab)
- [MCP-Proto-OKN GitHub](https://github.com/sbl-sdsc/mcp-proto-okn)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions:
- Open an issue on GitHub
- Check the [PrimeKG documentation](https://github.com/mims-harvard/PrimeKG)
- Review the [MCP documentation](https://modelcontextprotocol.io/)
