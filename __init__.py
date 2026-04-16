"""
ComfyUI Resolution Presets 🎯
专业分辨率预设与工具插件
"""

__version__ = "1.0.0"
__author__ = "fan200617120-ui"
__description__ = "专业的ComfyUI分辨率预设与工具插件，支持多种AI模型的标准分辨率预设，提供智能尺寸计算和分辨率分析功能。"

from .nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
