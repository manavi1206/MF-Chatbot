#!/usr/bin/env python3
"""
Configuration management for different environments
Supports: development, staging, production
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment-specific .env file
env = os.getenv('ENVIRONMENT', 'development')
env_file = f'.env.{env}'

if os.path.exists(env_file):
    load_dotenv(env_file)
else:
    load_dotenv('.env')  # Fallback to default .env

class Config:
    """Application configuration"""
    
    # LLM Configuration
    # Default to Gemini for production, Ollama for development
    LLM_MODEL_TYPE = os.getenv('LLM_MODEL_TYPE', 'gemini' if os.getenv('ENVIRONMENT') == 'production' else 'ollama')
    LLM_MODEL_NAME = os.getenv('LLM_MODEL_NAME', 'gemini-2.0-flash' if os.getenv('LLM_MODEL_TYPE') == 'gemini' else 'llama3.1:8b')
    
    # API Keys (only needed for cloud models)
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
    
    # Environment
    ENVIRONMENT = env
    
    # RAG Configuration
    KNOWLEDGE_BASE_PATH = os.getenv('KNOWLEDGE_BASE_PATH', 'cleaned_knowledge_base.json')
    VECTOR_STORE_PATH = os.getenv('VECTOR_STORE_PATH', './chroma_db')
    
    @classmethod
    def get_llm_config(cls) -> Dict[str, Any]:
        """Get LLM configuration based on environment"""
        config = {
            'model_type': cls.LLM_MODEL_TYPE,
            'model_name': cls.LLM_MODEL_NAME,
        }
        
        # Add API key if needed
        if cls.LLM_MODEL_TYPE == 'gemini':
            config['api_key'] = cls.GEMINI_API_KEY
        elif cls.LLM_MODEL_TYPE == 'openai':
            config['api_key'] = cls.OPENAI_API_KEY
        elif cls.LLM_MODEL_TYPE == 'anthropic':
            config['api_key'] = cls.ANTHROPIC_API_KEY
        
        return config
    
    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production"""
        return cls.ENVIRONMENT == 'production'
    
    @classmethod
    def is_development(cls) -> bool:
        """Check if running in development"""
        return cls.ENVIRONMENT == 'development'

# Production recommendations
PRODUCTION_RECOMMENDATIONS = {
    'openai': {
        'model': 'gpt-3.5-turbo',
        'cost_per_1k_tokens': 0.002,  # Average
        'rate_limit': 'High (varies by tier)',
        'quality': 'Excellent',
        'setup': 'Easy'
    },
    'anthropic': {
        'model': 'claude-3-5-sonnet-20241022',
        'cost_per_1k_tokens': 0.009,  # Average
        'rate_limit': 'High (varies by tier)',
        'quality': 'Excellent',
        'setup': 'Easy'
    },
    'gemini': {
        'model': 'gemini-2.0-flash',
        'cost_per_1k_tokens': 0.000375,  # Average
        'rate_limit': 'Medium-High (paid tier)',
        'quality': 'Very Good',
        'setup': 'Easy'
    },
    'ollama': {
        'model': 'llama3.1:8b',
        'cost_per_1k_tokens': 0,  # Server cost only
        'rate_limit': 'Unlimited',
        'quality': 'Good',
        'setup': 'Medium (requires server)'
    }
}



