#!/usr/bin/env python3
"""
Master script to update the entire knowledge base
This script:
1. Fetches all fund data
2. Fetches all regulatory/help data
3. Cleans and structures all data
4. Updates the cleaned knowledge base

Run this script weekly via cron to keep data fresh.
"""

import sys
import os
import json
import logging
from datetime import datetime
from pathlib import Path

# Add current directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)
os.chdir(script_dir)  # Change to script directory

# Setup logging first
log_dir = Path(__file__).parent / 'logs'
log_dir.mkdir(exist_ok=True)

log_file = log_dir / f'update_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Import our modules
try:
    from fetch_fund_data import FundDataFetcher
    from fetch_regulatory_sources import RegulatorySourceFetcher
    from clean_and_structure_data import DataCleaner
except ImportError as e:
    logger.error(f"Import error: {e}")
    logger.error("Make sure all required scripts are in the same directory")
    sys.exit(1)

class KnowledgeBaseUpdater:
    def __init__(self):
        self.start_time = datetime.now()
        self.errors = []
        self.warnings = []
        
    def update_fund_data(self):
        """Update fund-specific data"""
        logger.info("="*80)
        logger.info("STEP 1: UPDATING FUND DATA")
        logger.info("="*80)
        
        try:
            fetcher = FundDataFetcher()
            fetcher.fetch_all_data()
            comprehensive_data = fetcher.compile_comprehensive_dataset()
            fetcher.save_dataset(comprehensive_data)
            
            logger.info("✓ Fund data updated successfully")
            return True
        except Exception as e:
            error_msg = f"Error updating fund data: {str(e)}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            return False
    
    def update_regulatory_data(self):
        """Update regulatory and help data"""
        logger.info("\n" + "="*80)
        logger.info("STEP 2: UPDATING REGULATORY & HELP DATA")
        logger.info("="*80)
        
        try:
            fetcher = RegulatorySourceFetcher()
            fetcher.fetch_all_regulatory_sources()
            fetcher.save_regulatory_data()
            
            logger.info("✓ Regulatory and help data updated successfully")
            return True
        except Exception as e:
            error_msg = f"Error updating regulatory data: {str(e)}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            return False
    
    def clean_and_structure_data(self):
        """Clean and structure all data"""
        logger.info("\n" + "="*80)
        logger.info("STEP 3: CLEANING AND STRUCTURING DATA")
        logger.info("="*80)
        
        try:
            cleaner = DataCleaner()
            cleaner.clean_all_data()
            
            logger.info("✓ Data cleaned and structured successfully")
            return True
        except Exception as e:
            error_msg = f"Error cleaning data: {str(e)}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            return False
    
    def create_update_summary(self):
        """Create a summary of the update"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        summary = {
            'update_timestamp': end_time.isoformat(),
            'duration_seconds': duration,
            'status': 'success' if not self.errors else 'partial',
            'errors': self.errors,
            'warnings': self.warnings,
            'files_updated': [
                'comprehensive_fund_dataset.json',
                'comprehensive_fund_dataset.csv',
                'regulatory_knowledge_base.json',
                'regulatory_knowledge_base_summary.json',
                'cleaned_knowledge_base.json'
            ]
        }
        
        # Save summary
        summary_file = Path(__file__).parent / 'update_summary.json'
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        logger.info("\n" + "="*80)
        logger.info("UPDATE SUMMARY")
        logger.info("="*80)
        logger.info(f"Status: {summary['status']}")
        logger.info(f"Duration: {duration:.2f} seconds")
        logger.info(f"Errors: {len(self.errors)}")
        logger.info(f"Warnings: {len(self.warnings)}")
        logger.info(f"Summary saved to: {summary_file}")
        
        return summary
    
    def run_full_update(self):
        """Run the complete update process"""
        logger.info("="*80)
        logger.info("KNOWLEDGE BASE UPDATE STARTED")
        logger.info(f"Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("="*80)
        
        results = {
            'fund_data': self.update_fund_data(),
            'regulatory_data': self.update_regulatory_data(),
            'cleaning': self.clean_and_structure_data()
        }
        
        summary = self.create_update_summary()
        
        # Check if all steps succeeded
        if all(results.values()):
            logger.info("\n✅ ALL UPDATES COMPLETED SUCCESSFULLY")
            return 0
        else:
            logger.warning("\n⚠️  UPDATE COMPLETED WITH ERRORS")
            return 1

def main():
    """Main entry point"""
    updater = KnowledgeBaseUpdater()
    exit_code = updater.run_full_update()
    sys.exit(exit_code)

if __name__ == '__main__':
    main()

