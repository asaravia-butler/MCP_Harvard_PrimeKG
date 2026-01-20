# Adding PrimeKG to Your Claude Desktop Configuration

This guide shows how to add PrimeKG queries to your existing [Proto-OKN MCP](https://github.com/sbl-sdsc/mcp-proto-okn) server setup.

## Your Updated Configuration

Add this entry to your existing `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "spoke-genelab": {
      "command": "uvx",
      "args": ["mcp-proto-okn", "--endpoint", "https://frink.apps.renci.org/spoke-genelab/sparql"]
    },
    "spoke-okn": {
      "command": "uvx",
      "args": ["mcp-proto-okn", "--endpoint", "https://frink.apps.renci.org/spoke-okn/sparql"]
    },
    "genelab-local": {
      "command": "uvx",
      "args": ["mcp-genelab"],
      "env": {
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USERNAME": "neo4j",
        "NEO4J_PASSWORD": "myPassword",
        "NEO4J_DATABASE": "spoke-genelab-v0.1.0",
        "INSTRUCTIONS": "Query the GeneLab KG to identify NASA spaceflight experiments containing omics datasets, specifically differential gene expression (transcriptomics) and DNA 
methylation (epigenomics) data."
      }
    },
    "genelab-dev": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/mcp-genelab", "mcp-genelab"],
      "env": {
        "NEO4J_URI": "neo4j+s://bolt.matebioservices-spoke.com:443",
        "NEO4J_USERNAME": "username",
        "NEO4J_PASSWORD": "mypassword",
        "NEO4J_DATABASE": "spoke-genelab-v0.1.0",
        "INSTRUCTIONS": "Query the GeneLab KG to identify NASA spaceflight experiments containing omics datasets, specifically differential gene expression (transcriptomics) and DNA 
methylation (epigenomics) data."
      }
    },    
    "primekg-auto-dev": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/MCP_Harvard_PrimeKG", "mcp-primekg"],
      "env": {
        "PRIMEKG_DATA_PATH": "/Users/username/primekg_data",
        "PRIMEKG_AUTO_UPDATE": "true",
        "PRIMEKG_UPDATE_INTERVAL_DAYS": "7",
        "INSTRUCTIONS": "Query the latest version of PrimeKG precision medicine knowledge graph containing 129,375 nodes (genes, drugs, diseases, biological processes) and 8+ million 
relationships from 20+ biomedical databases for drug discovery and precision medicine insights."
      }
    },    
    "primekg-auto": {
      "command": "uvx",
      "args": ["mcp-primekg"],
      "env": {
        "PRIMEKG_DATA_PATH": "/Users/username/primekg_data",
        "PRIMEKG_AUTO_UPDATE": "true",
        "PRIMEKG_UPDATE_INTERVAL_DAYS": "7",
        "INSTRUCTIONS": "Query the latest version of PrimeKG precision medicine knowledge graph containing 129,375 nodes (genes, drugs, diseases, biological processes) and 8+ million 
relationships from 20+ biomedical databases for drug discovery and precision medicine insights."
      }
    }
  }
}
```

## What This Adds

**Two server options are provided:**

### `primekg-auto-dev` (Local Development)
Use this while developing or before publishing to PyPI:
- Points to your local repository with `--directory` flag
- Requires you to have cloned the MCP_Harvard_PrimeKG repository
- Update the path to match where you cloned the repository

### `primekg-auto` (Production/Published)
Use this after publishing the package to PyPI:
- Automatically downloads from PyPI using `uvx`
- No local repository needed
- Simpler configuration

Both servers will:

✅ **Automatically download the latest PrimeKG data** from Harvard Dataverse on first run  
✅ **Check for updates every 7 days** to ensure you always query current data  
✅ **Cache data locally** at `/Users/username/primekg_data` (change path as needed)  
✅ **Provide specialized PrimeKG query tools** for drugs, diseases, and genes

## Setup Steps

1. **Add the configuration** above to your `claude_desktop_config.json`
   - Use **`primekg-auto-dev`** if you're developing locally or before publishing
   - Use **`primekg-auto`** if the package is published on PyPI

2. **Create the data directory** (optional - server creates it automatically):
   ```bash
   mkdir -p /Users/username/primekg_data
   ```

3. **Restart Claude Desktop** completely (Cmd+Q, then reopen)

4. **First run will download data** (~600MB, takes a few minutes)

5. **Test it** by asking Claude:
   - "Search for metformin in PrimeKG"
   - "What are the targets of aspirin in PrimeKG?"
   - "Find genes associated with Alzheimer's disease in PrimeKG"

## Alternative: Use Neo4j for PrimeKG

If you prefer to use your existing Neo4j setup (better for complex queries):

### Step-by-Step Neo4j Setup

#### 1. Download Required Files

Download only these two files from Harvard Dataverse:

```bash
# Download nodes file (7.5 MB)
curl -o nodes.tab "https://dataverse.harvard.edu/api/access/datafile/6180617"

# Download edges file (368.6 MB)
curl -o edges.csv "https://dataverse.harvard.edu/api/access/datafile/6180616"
```

Or download manually from: https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/IXA7BM

#### 2. Convert nodes.tab to CSV

Neo4j works best with comma-delimited files. Create `convert_nodes.py`:

```python
#!/usr/bin/env python3
import csv

with open('nodes.tab', 'r') as infile:
    reader = csv.reader(infile, delimiter='\t')
    with open('nodes.csv', 'w', newline='') as outfile:
        writer = csv.writer(outfile)
        for row in reader:
            writer.writerow(row)
print("✓ Created nodes.csv")
```

Run: `python3 convert_nodes.py`

#### 3. Prepare Files for Neo4j Import

Update headers for both CSV files. Create `fix_headers.py`:

```python
#!/usr/bin/env python3

# Fix nodes.csv
with open('nodes.csv', 'r') as f:
    lines = f.readlines()
lines[0] = 'node_index:ID,node_id,:LABEL,node_name,node_source\n'
with open('nodes.csv', 'w') as f:
    f.writelines(lines)
print("✓ Fixed nodes.csv header")

# Fix edges.csv  
with open('edges.csv', 'r') as f:
    lines = f.readlines()
lines[0] = ':TYPE,display_relation,:START_ID,:END_ID\n'
with open('edges.csv', 'w') as f:
    f.writelines(lines)
print("✓ Fixed edges.csv header")
```

Run: `python3 fix_headers.py`

#### 4. Import into Neo4j

**Using Neo4j Desktop:**

1. Open Neo4j Desktop
2. Create a new database (or use existing DBMS)
3. **Stop the database** (must be stopped for import)
4. Click the three dots (⋯) next to your database
5. Select "Open Folder" → "DBMS"
6. Open terminal in that directory
7. Run the import command:

```bash
./bin/neo4j-admin database import full primekg \
  --nodes=/absolute/path/to/nodes.csv \
  --relationships=/absolute/path/to/edges.csv \
  --trim-strings=true
```

**Using Neo4j Server (command line):**

```bash
neo4j-admin database import full primekg \
  --nodes=/absolute/path/to/nodes.csv \
  --relationships=/absolute/path/to/edges.csv \
  --trim-strings=true
```

**Important Notes:**
- Use **absolute paths** to your files (e.g., `/Users/yourusername/Downloads/nodes.csv`)
- The database must be **stopped** during import
- Import creates a new database named "primekg"
- This takes ~5-10 minutes depending on your hardware

#### 5. Verify the Import

1. Start the "primekg" database in Neo4j Desktop
2. Open Neo4j Browser
3. **CRITICAL: Select the correct database**
   - Look for the database dropdown at the top of Neo4j Browser (usually shows "neo4j")
   - Click the dropdown and **select "primekg"**
   - Without this step, your queries will return no results!
4. Run these queries to verify:

```cypher
// Check total nodes (should be ~129,375)
MATCH (n) RETURN count(n) as total_nodes;

// Check total relationships (should be ~4+ million)
MATCH ()-[r]->() RETURN count(r) as total_relationships;

// View node types and counts
MATCH (n) RETURN DISTINCT labels(n) as node_type, count(*) as count
ORDER BY count DESC;

// Sample some drug nodes
MATCH (n:drug) RETURN n LIMIT 5;

// Sample some disease nodes
MATCH (n:disease) RETURN n LIMIT 5;
```

Expected results:
- ~129,375 nodes
- ~4,050,249 relationships
- Node types: disease, drug, gene/protein, biological_process, etc.

**If queries return 0 or nothing:**
- ✅ Make sure you selected "primekg" database in the dropdown (step 3 above)
- ✅ Verify the database is running (shows "Active")
- ✅ Check import logs for errors

#### 6. Configure Claude Desktop

Add this to your `claude_desktop_config.json`:

```json
"primekg-neo4j": {
  "command": "uvx",
  "args": ["mcp-genelab"],
  "env": {
    "NEO4J_URI": "bolt://localhost:7687",
    "NEO4J_USERNAME": "neo4j",
    "NEO4J_PASSWORD": "your_password_here",
    "NEO4J_DATABASE": "primekg",
    "INSTRUCTIONS": "Query the PrimeKG precision medicine knowledge graph for drug-disease-gene relationships and biomedical insights from 20+ integrated databases."
  }
}
```

Replace `your_password_here` with the password you set for your Neo4j database.

#### 7. Test with Claude

After restarting Claude Desktop, test queries like:
- "Find all drugs that target EGFR in PrimeKG"
- "What are the genes associated with Alzheimer's disease in PrimeKG?"
- "Show me the path between metformin and diabetes in PrimeKG"

## Comparison

| Feature | CSV (primekg-auto/primekg-auto-dev) | Neo4j (primekg-neo4j) |
|---------|-------------------|-------|
| **Setup Complexity** | ⭐ Easy - automatic | ⭐⭐⭐ Manual download & import |
| **Always Current** | ✅ Yes - auto-updates weekly | ❌ Manual updates needed |
| **Query Performance** | ⭐⭐ Good for simple queries | ⭐⭐⭐ Excellent for complex queries |
| **Disk Space** | ~600MB | ~2-3GB |
| **Best For** | Quick setup, simple queries | Complex path finding, advanced analytics |

## Recommendations

**Start with CSV Auto-Update** (`primekg-auto-dev` or `primekg-auto`) because:
- Zero manual setup
- Always queries the latest PrimeKG version
- Good enough for most drug/disease/gene queries

**Switch to Neo4j** (`primekg-neo4j`) later if you need:
- Complex multi-hop path queries
- Better performance for large result sets
- Integration with your other Neo4j databases

## Troubleshooting

**Download fails:**
- Check internet connection
- Verify you have ~1GB free space
- Check logs in Claude Desktop

**Server won't start:**
- Verify the data path is correct and writable
- Check Claude Desktop logs
- Try running `uvx mcp-primekg` in terminal to see errors

**Want to force an update:**
- Delete the `.last_update` file in your data directory
- Restart Claude Desktop

**Disable auto-updates:**
- Set `"PRIMEKG_AUTO_UPDATE": "false"` in config
- Manually update data as needed

