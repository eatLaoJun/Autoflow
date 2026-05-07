import os
import json
import logging

logger = logging.getLogger(__name__)

class PRDAgent(BaseAgent):
    """PRD Generation Agent"""
    
    def __init__(self):
        super().__init__()
