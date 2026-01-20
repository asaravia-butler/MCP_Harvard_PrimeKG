# Neo4j Import Guide for PrimeKG

This guide shows how to import PrimeKG data into Neo4j for complex graph queries.

## Prerequisites

- Neo4j Desktop installed
- Python 3.x (for file conversion)
- ~2-3GB free disk space

## Step 1: Download Required Files

Download these two files from [Harvard Dataverse](https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/IXA7BM):

```bash
# Download nodes file (7.5 MB)
curl -o nodes.tab "https://dataverse.harvard.edu/api/access/datafile/6180617"

# Download edges file (368.6 MB)  
curl -o edges.csv "https://dataverse.harvard.edu/api/access/datafile/6180616"
```

## Step 2: Convert nodes.tab to CSV

Neo4j import works best with comma-delimited files. Convert `nodes.tab` to `nodes.csv`:

**Save this as `convert_nodes.py`:**

```python
#!/usr/bin/env python3
import csv

print("Converting nodes.tab to nodes.csv...")

with open('nodes.tab', 'r') as infile:
    reader = csv.reader(infile, delimiter='\t')
    with open('nodes.csv', 'w', newline='') as outfile:
        writer = csv.writer(outfile)
        for row in reader:
            writer.writerow(row)

print("✓ Created nodes.csv")
```

Run it:
```bash
python3 convert_nodes.py
```

## Step 3: Fix CSV Headers

Update both CSV headers to Neo4j's required format.

**Save this as `fix_headers.py`:**

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

Run it:
```bash
python3 fix_headers.py
```

## Step 4: Verify Headers

```bash
# Should show: node_index:ID,node_id,:LABEL,node_name,node_source
head -1 nodes.csv

# Should show: :TYPE,display_relation,:START_ID,:END_ID
head -1 edges.csv
```

## Step 5: Import into Neo4j

### Using Neo4j Desktop:

1. **Stop the database** if running
2. Click (⋯) next to your database → **"Open Folder"** → **"DBMS"**
3. Open terminal in that directory
4. Run:

```bash
./bin/neo4j-admin database import full primekg \
  --nodes=/absolute/path/to/nodes.csv \
  --relationships=/absolute/path/to/edges.csv \
  --trim-strings=true
```

**Use absolute paths!** Example:
```bash
./bin/neo4j-admin database import full primekg \
  --nodes=/Users/yourusername/Downloads/nodes.csv \
  --relationships=/Users/yourusername/Downloads/edges.csv \
  --trim-strings=true
```

Import takes ~5-10 minutes.

## Step 6: Start and Select the Database

This is critical - **you must select the correct database:**

1. **In Neo4j Desktop:**
   - Start the DBMS (the server)
   - Click **"Open"** to open Neo4j Browser

2. **In Neo4j Browser (top of page):**
   - Look for a database dropdown (usually shows "neo4j")
   - **Click the dropdown and select "primekg"**
   - This switches from the default "neo4j" database to your "primekg" database

3. **Now run verification queries:**

```cypher
// Check total nodes (should be ~129,375)
MATCH (n) RETURN count(n) as total_nodes;

// Check total relationships (should be ~4,050,249)
MATCH ()-[r]->() RETURN count(r) as total_relationships;

// View node types
MATCH (n) RETURN DISTINCT labels(n) as node_type, count(*) as count
ORDER BY count DESC;
```

**If queries return 0 or nothing:**
- ✅ Make sure you selected "primekg" in the database dropdown (step 2 above)
- ✅ Verify import completed successfully
- ✅ Check import logs for errors

## Step 7: Configure MCP Server

Add to `claude_desktop_config.json`:

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
        "INSTRUCTIONS": "Query PrimeKG for drug-disease-gene relationships."
      }
    }
  }
}
```

Replace `your_password` with your Neo4j password.

## Troubleshooting

**Query returns nothing:**
- **Most common:** Wrong database selected - select "primekg" in the dropdown!
- Database not started
- Import failed (check logs)

**Import fails:**
- Database already exists - delete it first
- Database not stopped
- Wrong file paths

## Alternative: CSV Auto-Update (Easier)

Skip Neo4j entirely and use auto-updating CSV mode:

```json
{
  "mcpServers": {
    "primekg-auto": {
      "command": "uvx",
      "args": ["mcp-primekg"],
      "env": {
        "PRIMEKG_DATA_PATH": "/Users/yourusername/primekg_data",
        "PRIMEKG_AUTO_UPDATE": "true"
      }
    }
  }
}
```

Automatically downloads and updates PrimeKG weekly!
