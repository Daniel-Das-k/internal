"""
Gemini LLM Configuration for CrewAI Agents

Configuration for Google Gemini models across different use cases in the
constraint management system.
"""

import os
from crewai import LLM
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class GeminiConfig:
    """
    Gemini model configuration for different agent roles and use cases.

    Model Selection Strategy:
    - gemini-2.5-pro-preview-05-06: Complex reasoning, planning, validation
    - gemini-2.0-flash: General purpose, balanced performance
    - gemini-1.5-flash: Fast processing, simple tasks
    - gemini-1.5-flash-8B: High-frequency operations
    """

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')

        if not self.api_key:
            print("Debug: Available env vars with 'GEMINI':", [k for k in os.environ.keys() if 'GEMINI' in k])
            raise ValueError("GEMINI_API_KEY environment variable must be set")

        print(f"✓ Gemini API key configured (starts with: {self.api_key[:10]}...)")
        logger.info("Initialized Gemini configuration with API key")

    def get_planning_llm(self) -> LLM:
        """
        High-performance model for complex planning and reasoning tasks.
        Uses Gemini 2.5 Pro for advanced thinking and reasoning.
        """
        return LLM(
            model="gemini/gemini-2.5-pro-preview-05-06",
            temperature=0.3,  # Lower temperature for consistent planning
            api_key=self.api_key
        )

    def get_general_purpose_llm(self) -> LLM:
        """
        Balanced model for general agent tasks.
        Uses Gemini 2.0 Flash for next-generation features and speed.
        """
        return LLM(
            model="gemini/gemini-2.0-flash",
            temperature=0.7,
            api_key=self.api_key
        )

    def get_fast_processing_llm(self) -> LLM:
        """
        Fast model for quick processing tasks like parsing and validation.
        Uses Gemini 1.5 Flash for balanced performance.
        """
        return LLM(
            model="gemini/gemini-1.5-flash",
            temperature=0.5,
            api_key=self.api_key
        )

    def get_high_frequency_llm(self) -> LLM:
        """
        Efficient model for high-frequency operations and monitoring.
        Uses Gemini 1.5 Flash 8B for cost efficiency.
        """
        return LLM(
            model="gemini/gemini-1.5-flash-8b",
            temperature=0.4,
            api_key=self.api_key
        )

    def get_creative_llm(self) -> LLM:
        """
        Creative model for presentation and report generation.
        Uses Gemini 1.5 Pro for creative collaboration.
        """
        return LLM(
            model="gemini/gemini-1.5-pro",
            temperature=0.8,  # Higher temperature for creativity
            api_key=self.api_key
        )

    def get_adaptive_llm(self) -> LLM:
        """
        Adaptive model for cost-efficient operations.
        Uses Gemini 2.5 Flash Preview for adaptive thinking.
        """
        return LLM(
            model="gemini/gemini-2.5-flash-preview-04-17",
            temperature=0.6,
            api_key=self.api_key
        )

    def get_llm_for_agent_role(self, role: str) -> LLM:
        """
        Get optimal LLM based on agent role.

        Args:
            role: Agent role (parser, validator, generator, presenter, planner)

        Returns:
            Configured LLM for the specific role
        """
        role_mapping = {
            'parser': self.get_fast_processing_llm,
            'validator': self.get_general_purpose_llm,
            'generator': self.get_planning_llm,  # Complex optimization needs planning
            'presenter': self.get_creative_llm,
            'planner': self.get_planning_llm,
            'monitor': self.get_high_frequency_llm,
            'memory': self.get_adaptive_llm
        }

        get_llm_func = role_mapping.get(role.lower(), self.get_general_purpose_llm)
        return get_llm_func()

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about available models and their capabilities."""
        return {
            'models': {
                'gemini-2.5-pro-preview-05-06': {
                    'context_length': '1M tokens',
                    'capabilities': 'Enhanced thinking and reasoning, multimodal understanding, advanced coding',
                    'use_case': 'Complex planning and reasoning tasks',
                    'temperature_range': '0.1-0.5'
                },
                'gemini-2.5-flash-preview-04-17': {
                    'context_length': '1M tokens',
                    'capabilities': 'Adaptive thinking, cost efficiency',
                    'use_case': 'Cost-efficient adaptive operations',
                    'temperature_range': '0.4-0.8'
                },
                'gemini-2.0-flash': {
                    'context_length': '1M tokens',
                    'capabilities': 'Next generation features, speed, thinking, and realtime streaming',
                    'use_case': 'General purpose balanced performance',
                    'temperature_range': '0.5-0.9'
                },
                'gemini-2.0-flash-lite': {
                    'context_length': '1M tokens',
                    'capabilities': 'Cost efficiency and low latency',
                    'use_case': 'High-frequency low-latency operations',
                    'temperature_range': '0.3-0.7'
                },
                'gemini-1.5-flash': {
                    'context_length': '1M tokens',
                    'capabilities': 'Balanced multimodal model, good for most tasks',
                    'use_case': 'Fast processing and validation',
                    'temperature_range': '0.4-0.8'
                },
                'gemini-1.5-flash-8b': {
                    'context_length': '1M tokens',
                    'capabilities': 'Fastest, most cost-efficient, good for high-frequency tasks',
                    'use_case': 'Monitoring and high-frequency operations',
                    'temperature_range': '0.2-0.6'
                },
                'gemini-1.5-pro': {
                    'context_length': '2M tokens',
                    'capabilities': 'Best performing, wide variety of reasoning tasks including logical reasoning, coding, and creative collaboration',
                    'use_case': 'Creative presentation and report generation',
                    'temperature_range': '0.6-1.0'
                }
            },
            'recommended_usage': {
                'constraint_parsing': 'gemini-1.5-flash (fast, accurate)',
                'constraint_validation': 'gemini-2.0-flash (balanced reasoning)',
                'schedule_generation': 'gemini-2.5-pro-preview-05-06 (complex optimization)',
                'presentation_creation': 'gemini-1.5-pro (creative collaboration)',
                'workflow_planning': 'gemini-2.5-pro-preview-05-06 (advanced planning)',
                'monitoring': 'gemini-1.5-flash-8b (high-frequency)',
                'memory_operations': 'gemini-2.5-flash-preview-04-17 (adaptive)'
            }
        }


# Global Gemini configuration instance
_gemini_config = None

def get_gemini_config() -> GeminiConfig:
    """Get global Gemini configuration instance."""
    global _gemini_config
    if _gemini_config is None:
        _gemini_config = GeminiConfig()
    return _gemini_config

def set_gemini_api_key(api_key: str):
    """Set Gemini API key and reinitialize configuration."""
    global _gemini_config
    os.environ['GEMINI_API_KEY'] = api_key
    _gemini_config = GeminiConfig(api_key)

def validate_gemini_setup() -> Dict[str, Any]:
    """Validate Gemini API setup and return status."""
    try:
        config = get_gemini_config()

        # Test with a simple model
        test_llm = config.get_high_frequency_llm()

        return {
            'status': 'success',
            'api_key_configured': bool(config.api_key),
            'models_available': list(config.get_model_info()['models'].keys()),
            'test_model': 'gemini-1.5-flash-8b',
            'message': 'Gemini configuration validated successfully'
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'message': 'Gemini configuration validation failed'
        }