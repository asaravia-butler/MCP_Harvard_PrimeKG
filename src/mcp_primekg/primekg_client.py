"""
PrimeKG Client - handles data loading and querying of the PrimeKG knowledge graph
"""

import json
import logging
from pathlib import Path
from typing import Optional, Dict, List, Any
import pandas as pd
import requests
from datetime import datetime, timedelta
import os

logger = logging.getLogger("mcp-primekg")


class PrimeKGClient:
    """Client for querying the PrimeKG knowledge graph."""
    
    # PrimeKG GitHub raw data URLs
    PRIMEKG_KG_URL = "https://dataverse.harvard.edu/api/access/datafile/6180620"
    PRIMEKG_NODES_URL = "https://raw.githubusercontent.com/mims-harvard/PrimeKG/main/data/nodes.csv"
    
    def __init__(self, data_path: str, auto_update: bool = True, update_interval_days: int = 7):
        """Initialize the PrimeKG client.
        
        Args:
            data_path: Path to directory containing PrimeKG data files
            auto_update: If True, automatically download latest data if cache is stale
            update_interval_days: Number of days before checking for updates
        """
        self.data_path = Path(data_path)
        self.data_path.mkdir(parents=True, exist_ok=True)
        self.auto_update = auto_update
        self.update_interval_days = update_interval_days
        self.nodes_df = None
        self.edges_df = None
        self._load_data()
    
    def _should_update(self) -> bool:
        """Check if data should be updated based on age."""
        timestamp_file = self.data_path / ".last_update"
        
        if not timestamp_file.exists():
            return True
        
        try:
            with open(timestamp_file, 'r') as f:
                last_update = datetime.fromisoformat(f.read().strip())
            
            age = datetime.now() - last_update
            return age.days >= self.update_interval_days
        except Exception as e:
            logger.warning(f"Error reading timestamp: {e}")
            return True
    
    def _mark_updated(self):
        """Mark data as updated."""
        timestamp_file = self.data_path / ".last_update"
        with open(timestamp_file, 'w') as f:
            f.write(datetime.now().isoformat())
    
    def _download_file(self, url: str, destination: Path) -> bool:
        """Download a file from URL to destination.
        
        Args:
            url: URL to download from
            destination: Path to save the file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Downloading from {url}...")
            response = requests.get(url, stream=True, timeout=300)
            response.raise_for_status()
            
            with open(destination, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Successfully downloaded to {destination}")
            return True
            
        except Exception as e:
            logger.error(f"Error downloading {url}: {e}")
            return False
    
    def _download_primekg_data(self) -> bool:
        """Download the latest PrimeKG data.
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("Downloading latest PrimeKG data...")
        
        # Download main knowledge graph file
        kg_file = self.data_path / "kg.csv"
        if not self._download_file(self.PRIMEKG_KG_URL, kg_file):
            logger.error("Failed to download kg.csv")
            return False
        
        logger.info("PrimeKG data download complete")
        self._mark_updated()
        return True
    
    def _load_data(self):
        """Load PrimeKG data from CSV files."""
        # Check if we should update
        if self.auto_update and self._should_update():
            logger.info("PrimeKG data is stale or missing, downloading latest version...")
            if not self._download_primekg_data():
                logger.warning("Failed to download data, attempting to use cached version")
        
        try:
            # Try to load main knowledge graph file
            kg_file = self.data_path / "kg.csv"
            if kg_file.exists():
                logger.info(f"Loading PrimeKG data from {kg_file}...")
                df = pd.read_csv(kg_file)
                
                # The kg.csv file contains edges with columns like:
                # x_id, x_type, x_name, relation, y_id, y_type, y_name, etc.
                self.edges_df = df
                
                # Create nodes dataframe from unique x and y entities
                x_nodes = df[['x_id', 'x_type', 'x_name']].rename(
                    columns={'x_id': 'node_id', 'x_type': 'node_type', 'x_name': 'node_name'}
                )
                y_nodes = df[['y_id', 'y_type', 'y_name']].rename(
                    columns={'y_id': 'node_id', 'y_type': 'node_type', 'y_name': 'node_name'}
                )
                self.nodes_df = pd.concat([x_nodes, y_nodes]).drop_duplicates(subset=['node_id'])
                
                logger.info(f"Loaded {len(self.nodes_df)} nodes and {len(self.edges_df)} edges")
            else:
                logger.warning(f"PrimeKG data file not found at {kg_file}")
                logger.info("Download PrimeKG data from: https://github.com/mims-harvard/PrimeKG")
                
        except Exception as e:
            logger.error(f"Error loading PrimeKG data: {e}")
            logger.info("PrimeKG data not loaded. Download from: https://github.com/mims-harvard/PrimeKG")
    
    def get_schema(self) -> str:
        """Get the schema of the PrimeKG knowledge graph."""
        schema_info = """
PrimeKG Schema:

Node Types:
- gene/protein
- drug
- disease
- biological_process
- molecular_function
- cellular_component
- pathway
- anatomy
- phenotype
- exposure

Relationship Types:
- drug-protein interactions
- gene-disease associations
- gene-gene interactions
- protein-pathway associations
- disease-phenotype associations
- drug-disease indications
- and many more...

Data Sources: 20+ biomedical databases including:
- DrugBank, PRIMEKG, CTD, DisGeNET, GO, Reactome, SIDER, etc.

Total: ~129,375 nodes and ~8+ million relationships
"""
        return schema_info
    
    def get_statistics(self) -> str:
        """Get statistics about the loaded PrimeKG data."""
        if self.nodes_df is None or self.edges_df is None:
            return "PrimeKG data not loaded. Please download from: https://github.com/mims-harvard/PrimeKG"
        
        stats = f"""
PrimeKG Statistics:

Nodes: {len(self.nodes_df):,}
Edges: {len(self.edges_df):,}

Node Type Distribution:
{self.nodes_df['node_type'].value_counts().to_string() if 'node_type' in self.nodes_df.columns else 'Node type information not available'}

Relationship Type Distribution:
{self.edges_df['relation'].value_counts().head(20).to_string() if 'relation' in self.edges_df.columns else 'Relationship type information not available'}
"""
        return stats
    
    def search_nodes(self, query: str, node_type: Optional[str] = None, limit: int = 10) -> str:
        """Search for nodes by name or ID."""
        if self.nodes_df is None:
            return "PrimeKG data not loaded. Please download from: https://github.com/mims-harvard/PrimeKG"
        
        # Search in node name or ID columns
        mask = self.nodes_df.apply(lambda row: query.lower() in str(row).lower(), axis=1)
        
        if node_type:
            mask &= (self.nodes_df['node_type'].str.lower() == node_type.lower())
        
        results = self.nodes_df[mask].head(limit)
        
        if len(results) == 0:
            return f"No nodes found matching query: {query}"
        
        return f"Found {len(results)} nodes:\n\n{results.to_string()}"
    
    def get_node_relationships(self, node_id: str, relationship_type: Optional[str] = None, limit: int = 50) -> str:
        """Get all relationships for a specific node."""
        if self.edges_df is None:
            return "PrimeKG data not loaded. Please download from: https://github.com/mims-harvard/PrimeKG"
        
        # Find edges where the node is either source or target
        mask = (self.edges_df['x_id'] == node_id) | (self.edges_df['y_id'] == node_id)
        
        if relationship_type:
            mask &= (self.edges_df['relation'].str.lower() == relationship_type.lower())
        
        results = self.edges_df[mask].head(limit)
        
        if len(results) == 0:
            return f"No relationships found for node: {node_id}"
        
        return f"Found {len(results)} relationships:\n\n{results.to_string()}"
    
    def find_drug_targets(self, drug_name: str) -> str:
        """Find gene/protein targets for a given drug."""
        if self.nodes_df is None or self.edges_df is None:
            return "PrimeKG data not loaded. Please download from: https://github.com/mims-harvard/PrimeKG"
        
        # Find drug node
        drug_mask = (self.nodes_df['node_type'] == 'drug') & \
                    (self.nodes_df['node_name'].str.contains(drug_name, case=False, na=False))
        drugs = self.nodes_df[drug_mask]
        
        if len(drugs) == 0:
            return f"Drug not found: {drug_name}"
        
        drug_id = drugs.iloc[0]['node_id']
        
        # Find protein targets
        target_mask = (self.edges_df['x_id'] == drug_id) & \
                     (self.edges_df['relation'].str.contains('target|protein', case=False, na=False))
        targets = self.edges_df[target_mask]
        
        if len(targets) == 0:
            return f"No targets found for drug: {drug_name}"
        
        return f"Found {len(targets)} targets for {drug_name}:\n\n{targets.to_string()}"
    
    def find_disease_genes(self, disease_name: str, limit: int = 50) -> str:
        """Find genes associated with a disease."""
        if self.nodes_df is None or self.edges_df is None:
            return "PrimeKG data not loaded. Please download from: https://github.com/mims-harvard/PrimeKG"
        
        # Find disease node
        disease_mask = (self.nodes_df['node_type'] == 'disease') & \
                      (self.nodes_df['node_name'].str.contains(disease_name, case=False, na=False))
        diseases = self.nodes_df[disease_mask]
        
        if len(diseases) == 0:
            return f"Disease not found: {disease_name}"
        
        disease_id = diseases.iloc[0]['node_id']
        
        # Find associated genes
        gene_mask = ((self.edges_df['x_id'] == disease_id) | (self.edges_df['y_id'] == disease_id)) & \
                   (self.edges_df['relation'].str.contains('gene|associated', case=False, na=False))
        genes = self.edges_df[gene_mask].head(limit)
        
        if len(genes) == 0:
            return f"No genes found for disease: {disease_name}"
        
        return f"Found {len(genes)} genes for {disease_name}:\n\n{genes.to_string()}"
    
    def find_drug_disease_paths(self, drug_name: str, disease_name: str, max_path_length: int = 3) -> str:
        """Find potential connections between a drug and disease."""
        if self.nodes_df is None or self.edges_df is None:
            return "PrimeKG data not loaded. Please download from: https://github.com/mims-harvard/PrimeKG"
        
        # This is a simplified version - full path finding would require graph traversal
        return f"Path finding between {drug_name} and {disease_name} requires graph traversal algorithms. " \
               f"Consider using Neo4j backend for complex path queries."
    
    def get_node_details(self, node_id: str) -> str:
        """Get detailed information about a specific node."""
        if self.nodes_df is None:
            return "PrimeKG data not loaded. Please download from: https://github.com/mims-harvard/PrimeKG"
        
        node = self.nodes_df[self.nodes_df['node_id'] == node_id]
        
        if len(node) == 0:
            # Try searching by name
            node = self.nodes_df[self.nodes_df['node_name'].str.contains(node_id, case=False, na=False)]
            
        if len(node) == 0:
            return f"Node not found: {node_id}"
        
        return f"Node details:\n\n{node.to_string()}"
