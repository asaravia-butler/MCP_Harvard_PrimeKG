# Quick Setup Guide for PrimeKG MCP Server

## Step 1: Download PrimeKG Data

Choose one of these options:

### Option A: CSV Files (Simplest)
1. Go to [PrimeKG GitHub](https://github.com/mims-harvard/PrimeKG)
2. Download `kg.csv` 
3. Create a directory: `mkdir ~/primekg_data`
4. Move the CSV file there

### Option B: Neo4j Database (Best Performance)
1. Go to [Harvard Dataverse](https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/IXA7BM)
2. Download the Neo4j database dump
3. Load into Neo4j (see README for details)

## Step 2: Add to Claude Desktop Config

Edit your `claude_desktop_config.json` and add this entry:

**For CSV version:**
```json
"primekg": {
  "command": "uvx",
  "args": ["mcp-primekg"],
  "env": {
    "PRIMEKG_DATA_PATH": "/Users/yourusername/primekg_data",
    "INSTRUCTIONS": "Query the PrimeKG precision medicine knowledge graph for drug-disease-gene relationships and biomedical insights."
  }
}
```

**For Neo4j version (recommended):**
```json
"primekg": {
  "command": "uvx",
  "args": ["mcp-genelab"],
  "env": {
    "NEO4J_URI": "bolt://localhost:7687",
    "NEO4J_USERNAME": "neo4j",
    "NEO4J_PASSWORD": "your_password",
    "NEO4J_DATABASE": "primekg",
    "INSTRUCTIONS": "Query the PrimeKG precision medicine knowledge graph for drug-disease-gene relationships and biomedical insights."
  }
}
```

## Step 3: Restart Claude Desktop

Fully quit and restart Claude Desktop.

## Step 4: Test It

Ask Claude:
- "Search for aspirin in PrimeKG"
- "What genes are associated with diabetes in PrimeKG?"
- "Find the targets of metformin in PrimeKG"

## Troubleshooting

**Server won't start:**
- Check that the data path is absolute and correct
- Verify PrimeKG data files are in the specified directory
- Check logs in Claude Desktop

**No results:**
- Ensure CSV files are properly formatted
- For Neo4j: verify database is loaded and running
- Check that database name matches your config

**Performance issues:**
- Consider using Neo4j instead of CSV files
- Neo4j provides much better performance for graph queries
- You can use the existing `mcp-genelab` server with PrimeKG data in Neo4j
