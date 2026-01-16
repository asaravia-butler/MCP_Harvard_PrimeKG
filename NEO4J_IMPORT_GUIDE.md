# PrimeKG Neo4j Import Guide

Complete guide for importing PrimeKG into Neo4j for use with the MCP server.

## Why Use Neo4j?

- **Better performance** for complex graph queries
- **Path finding** between drugs, diseases, and genes
- **Multi-hop relationships** and graph traversal
- **Integration** with other Neo4j databases you may have

## Prerequisites

- Neo4j Desktop or Neo4j Server installed
- ~2GB disk space for the imported database
- Java JDK 17 or 21 (required for neo4j-admin)

## Step 1: Download PrimeKG Data

Download the two required files from Harvard Dataverse:

### Option A: Using curl (recommended)

```bash
# Create a directory for PrimeKG data
mkdir -p ~/primekg_neo4j
cd ~/primekg_neo4j

# Download nodes file (7.5 MB)
curl -L -o nodes.tab "https://dataverse.harvard.edu/api/access/datafile/6180617"

# Download edges file (368.6 MB)
curl -L -o edges.csv "https://dataverse.harvard.edu/api/access/datafile/6180616"
```

### Option B: Manual download

1. Go to: https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/IXA7BM
2. Download:
   - `nodes.tab` (7.5 MB)
   - `edges.csv` (368.6 MB)
3. Save to a known directory

## Step 2: Prepare Headers for Neo4j

Neo4j's import tool requires specific header formats with special markers like `:ID`, `:LABEL`, `:TYPE`, `:START_ID`, and `:END_ID`.

### Option A: Using sed (macOS/Linux)

```bash
# Modify nodes.tab header
sed -i.bak '1s/.*/node_index:ID\tnode_id\t:LABEL\tnode_name\tnode_source/' nodes.tab

# Modify edges.csv header  
sed -i.bak '1s/.*/:TYPE,display_relation,:START_ID,:END_ID/' edges.csv
```

**Note for macOS:** Use `sed -i '' '1s/...` instead of `sed -i.bak '1s/...`

### Option B: Manual editing

Open each file in a text editor:

**nodes.tab** - Change first line to (use TABS between fields):
```
node_index:ID	node_id	:LABEL	node_name	node_source
```

**edges.csv** - Change first line to (use COMMAS between fields):
```
:TYPE,display_relation,:START_ID,:END_ID
```

### Verify Headers

Check that headers are correct:

```bash
# Check nodes.tab header
head -n 1 nodes.tab

# Should output:
# node_index:ID	node_id	:LABEL	node_name	node_source

# Check edges.csv header
head -n 1 edges.csv

# Should output:
# :TYPE,display_relation,:START_ID,:END_ID
```

## Step 3: Import into Neo4j

### Using Neo4j Desktop

1. **Open Neo4j Desktop**

2. **Create or select a project**

3. **Add a new DBMS** (or use an existing one)
   - Name it something like "PrimeKG Server"
   - Set a password you'll remember

4. **Stop the database** if it's running
   - Click "Stop" button

5. **Open terminal in DBMS directory**
   - Click the three dots (⋯) next to your DBMS
   - Select "Open Folder" → "DBMS"
   - Open terminal/command prompt in that directory

6. **Run the import command:**

```bash
# macOS/Linux
./bin/neo4j-admin database import full primekg \
  --nodes=/absolute/path/to/nodes.tab \
  --relationships=/absolute/path/to/edges.csv \
  --delimiter-nodes=TAB \
  --delimiter-relationships=COMMA \
  --trim-strings=true \
  --skip-bad-relationships=true \
  --skip-duplicate-nodes=true

# Windows
bin\neo4j-admin.bat database import full primekg ^
  --nodes="C:\absolute\path\to\nodes.tab" ^
  --relationships="C:\absolute\path\to\edges.csv" ^
  --delimiter-nodes=TAB ^
  --delimiter-relationships=COMMA ^
  --trim-strings=true ^
  --skip-bad-relationships=true ^
  --skip-duplicate-nodes=true
```

**Important:**
- Replace `/absolute/path/to/` with your actual file paths
- Use **absolute paths**, not relative paths
- The database name will be `primekg`

7. **Wait for import to complete** (~5-10 minutes)
   - You'll see progress output
   - Final message should indicate success

8. **Set file permissions** (macOS/Linux only):

```bash
# From the DBMS directory
sudo chown -R $(whoami) data/databases/primekg
sudo chown -R $(whoami) data/transactions/primekg
```

### Using Neo4j Server (Command Line)

If you have Neo4j installed as a server:

```bash
# Stop Neo4j if running
neo4j stop

# Run import
neo4j-admin database import full primekg \
  --nodes=/absolute/path/to/nodes.tab \
  --relationships=/absolute/path/to/edges.csv \
  --delimiter-nodes=TAB \
  --delimiter-relationships=COMMA \
  --trim-strings=true \
  --skip-bad-relationships=true \
  --skip-duplicate-nodes=true

# Start Neo4j
neo4j start
```

## Step 4: Verify the Import

1. **Start the database** in Neo4j Desktop

2. **Open Neo4j Browser**
   - Click "Open" button next to your DBMS
   - Or go to http://localhost:7474

3. **Select the primekg database:**
   - In the top dropdown, select "primekg"
   - Or run: `:use primekg`

4. **Run verification queries:**

```cypher
// Check total nodes (should be ~129,375)
MATCH (n) RETURN count(n) as total_nodes;

// Check total relationships (should be ~4,050,249)
MATCH ()-[r]->() RETURN count(r) as total_relationships;

// View distribution of node types
MATCH (n) 
RETURN DISTINCT labels(n)[0] as node_type, count(*) as count
ORDER BY count DESC;

// Check for drugs
MATCH (n:drug) RETURN n.node_name as drug_name LIMIT 10;

// Check for diseases
MATCH (n:disease) RETURN n.node_name as disease_name LIMIT 10;

// Check for genes
MATCH (n) WHERE 'gene/protein' IN labels(n) 
RETURN n.node_name as gene_name LIMIT 10;

// Sample a drug-disease relationship
MATCH (d:drug)-[r]->(dis:disease)
RETURN d.node_name as drug, type(r) as relationship, dis.node_name as disease
LIMIT 5;
```

### Expected Results

- **Nodes:** ~129,375
- **Relationships:** ~4,050,249
- **Node types:** disease, drug, gene/protein, biological_process, molecular_function, cellular_component, pathway, anatomy, phenotype, exposure
- **Relationship types:** ~30 different types including drug-disease associations, gene-disease associations, protein-protein interactions, etc.

## Step 5: Configure Claude Desktop

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
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
  }
}
```

Replace `your_password_here` with the password you set for your Neo4j database.

## Step 6: Test with Claude

1. **Fully quit and restart Claude Desktop**

2. **Test queries:**
   - "Find all drugs that target EGFR in the PrimeKG database"
   - "What genes are associated with Alzheimer's disease in PrimeKG?"
   - "Show me drugs used to treat diabetes in PrimeKG"
   - "Find the path between metformin and type 2 diabetes in PrimeKG"

## Troubleshooting

### Import fails with "permission denied"

**Solution:** Ensure database is stopped before import:
```bash
# In Neo4j Desktop, click "Stop" button
# Or for server:
neo4j stop
```

### Import fails with "file not found"

**Solution:** Use absolute paths, not relative:
```bash
# Get absolute path
cd ~/primekg_neo4j
pwd
# Use the full path shown in the import command
```

### "Database primekg already exists"

**Solution:** Delete existing database first:
```bash
# Stop Neo4j
neo4j stop

# Delete existing database
rm -rf data/databases/primekg
rm -rf data/transactions/primekg

# Re-run import
```

### Neo4j Browser shows "Database not found"

**Solution:** Create/start the database:
```cypher
// In Neo4j Browser
:use system
CREATE DATABASE primekg;
START DATABASE primekg;
:use primekg
```

### Import is very slow

**Solution:** This is normal! The import processes 4+ million relationships. Expect:
- ~5-10 minutes on modern hardware
- ~15-20 minutes on older hardware

### Claude can't connect to Neo4j

**Solutions:**
1. Verify Neo4j is running
2. Check password is correct in config
3. Verify database name is "primekg"
4. Test connection manually:
```bash
cypher-shell -u neo4j -p your_password -d primekg "MATCH (n) RETURN count(n);"
```

## Optional: Add Feature Data

After importing the basic graph, you can optionally add detailed clinical features for drugs and diseases:

### Download feature files

```bash
# Drug features
curl -L -o drug_features.tab "https://dataverse.harvard.edu/api/access/datafile/6180619"

# Disease features  
curl -L -o disease_features.tab "https://dataverse.harvard.edu/api/access/datafile/6180618"
```

### Load into Neo4j

Place files in Neo4j import directory, then in Neo4j Browser:

```cypher
// Load drug features
LOAD CSV WITH HEADERS FROM 'file:///drug_features.tab' AS row FIELDTERMINATOR '\t'
MATCH (d:drug {node_index: toInteger(row.node_index)})
SET d.drug_description = row.description,
    d.indications = row.indications,
    d.pharmacodynamics = row.pharmacodynamics;

// Load disease features
LOAD CSV WITH HEADERS FROM 'file:///disease_features.tab' AS row FIELDTERMINATOR '\t'
MATCH (dis:disease {node_index: toInteger(row.node_index)})
SET dis.disease_description = row.description,
    dis.symptoms = row.symptoms,
    dis.treatment = row.treatment;
```

## Performance Tips

### Create indexes for faster queries

```cypher
// Create indexes on commonly queried properties
CREATE INDEX drug_name IF NOT EXISTS FOR (n:drug) ON (n.node_name);
CREATE INDEX disease_name IF NOT EXISTS FOR (n:disease) ON (n.node_name);
CREATE INDEX gene_name IF NOT EXISTS FOR (n) ON (n.node_name) WHERE 'gene/protein' IN labels(n);
```

### Increase memory allocation

In Neo4j Desktop:
1. Click ⋯ → Settings
2. Increase these values:
```
dbms.memory.heap.max_size=4G
dbms.memory.pagecache.size=2G
```

## Next Steps

- Explore the graph structure with Cypher queries
- Use Claude to ask questions about the data
- Combine PrimeKG with other knowledge graphs in Neo4j
- Build custom queries for your research questions

## Resources

- PrimeKG Paper: https://www.nature.com/articles/s41597-023-01960-3
- PrimeKG GitHub: https://github.com/mims-harvard/PrimeKG
- Neo4j Cypher Manual: https://neo4j.com/docs/cypher-manual/current/
- Neo4j Import Tool Docs: https://neo4j.com/docs/operations-manual/current/tools/neo4j-admin/neo4j-admin-import/
