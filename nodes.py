"""
分辨率预设与工具节点 - 专业版
文件夹名：ComfyUI_ResolutionPresets
节点显示名：专业分辨率节点
"""
import torch
import math
from typing import Dict, Any, Tuple
from .presets import get_size_from_preset, PRESETS, CROP_METHODS, RESIZE_ALGOS
from .utils import ImageUtils

class BaseResolutionNode:
    """基础分辨率节点"""

    @classmethod
    def get_preset_inputs(cls) -> Dict[str, Any]:
        return {
            k: (["关"] + [name for name, _ in v], {"default": "关"})
            for k, v in PRESETS.items()
        }

    @staticmethod
    def validate_resolution(width: int, height: int, min_size: int = 64, max_size: int = 8192) -> Tuple[int, int]:
        width = max(min_size, min(width, max_size))
        height = max(min_size, min(height, max_size))
        return width, height


class ResolutionPresetImage(BaseResolutionNode):
    """分辨率预设 - 图像处理"""

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        return {
            "required": {
                **cls.get_preset_inputs(),
                "裁剪方式": (CROP_METHODS, {"default": "中心裁剪"}),
                "缩放算法": (RESIZE_ALGOS, {"default": "lanczos"}),
                "启用边长缩放": ("BOOLEAN", {"default": False}),
                "缩放基准": (["最长边", "最短边"], {"default": "最长边"}),
                "缩放长度": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 8}),
            },
            "optional": {
                "图像输入": ("IMAGE",),
                "遮罩输入": ("MASK",),
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK", "INT", "INT")
    RETURN_NAMES = ("图像输出", "遮罩输出", "宽度", "高度")
    FUNCTION = "process_image"
    CATEGORY = "ResolutionPresets"

    def process_image(self, 图像输入=None, 遮罩输入=None, **kwargs):
        use_edge = kwargs["启用边长缩放"]
        edge_mode = kwargs["缩放基准"]
        target_len = kwargs["缩放长度"]
        crop = kwargs["裁剪方式"]
        algo = kwargs["缩放算法"]

        if use_edge:
            if 图像输入 is not None:
                pil_img = ImageUtils.tensor_to_pil(图像输入)
                pil_img = ImageUtils.resize_by_edge(pil_img, edge_mode, target_len)
                图像输出 = ImageUtils.pil_to_tensor(pil_img)
                out_w, out_h = pil_img.size
            else:
                图像输出 = torch.zeros((1, 512, 512, 3), dtype=torch.float32)
                out_w, out_h = 512, 512

            if 遮罩输入 is not None:
                pil_msk = ImageUtils.tensor_to_pil(遮罩输入, is_mask=True)
                pil_msk = ImageUtils.resize_by_edge(pil_msk, edge_mode, target_len)
                遮罩输出 = ImageUtils.pil_to_tensor(pil_msk, is_mask=True)
            else:
                遮罩输出 = torch.zeros((1, out_h, out_w, 1), dtype=torch.float32)

            return (图像输出, 遮罩输出, out_w, out_h)

        choices = {k: kwargs[k] for k in PRESETS}
        w, h = get_size_from_preset(choices)

        if 图像输入 is not None:
            pil_img = ImageUtils.tensor_to_pil(图像输入)
            pil_img = ImageUtils.resize_with_crop(pil_img, w, h, crop, algo)
            图像输出 = ImageUtils.pil_to_tensor(pil_img)
        else:
            图像输出 = torch.zeros((1, h, w, 3), dtype=torch.float32)

        if 遮罩输入 is not None:
            pil_msk = ImageUtils.tensor_to_pil(遮罩输入, is_mask=True)
            pil_msk = ImageUtils.resize_with_crop(pil_msk, w, h, crop, algo)
            遮罩输出 = ImageUtils.pil_to_tensor(pil_msk, is_mask=True)
        else:
            遮罩输出 = torch.zeros((1, h, w, 1), dtype=torch.float32)

        return (图像输出, 遮罩输出, w, h)


class ResolutionPresetLatent(BaseResolutionNode):
    """分辨率预设 - 潜在空间"""

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        return {
            "required": {
                **cls.get_preset_inputs(),
                "启用自定义分辨率": ("BOOLEAN", {"default": False}),
                "宽度": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 8}),
                "高度": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 8}),
            }
        }

    RETURN_TYPES = ("LATENT",)
    RETURN_NAMES = ("潜在空间",)
    FUNCTION = "create_latent"
    CATEGORY = "ResolutionPresets"

    def create_latent(self, **kwargs):
        use_custom = kwargs["启用自定义分辨率"]

        if use_custom:
            w, h = kwargs["宽度"], kwargs["高度"]
        else:
            choices = {k: kwargs[k] for k in PRESETS}
            w, h = get_size_from_preset(choices)

        w, h = self.validate_resolution(w, h)
        latent = torch.zeros([1, 4, h // 8, w // 8])
        return ({"samples": latent},)


class ResolutionPresetSetter(BaseResolutionNode):
    """分辨率预设器"""

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        return {
            "required": {
                **cls.get_preset_inputs(),
                "启用自定义分辨率": ("BOOLEAN", {"default": False}),
                "宽度": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 8}),
                "高度": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 8}),
            }
        }

    RETURN_TYPES = ("INT", "INT")
    RETURN_NAMES = ("宽度", "高度")
    FUNCTION = "get_resolution"
    CATEGORY = "ResolutionPresets"

    def get_resolution(self, **kwargs):
        use_custom = kwargs["启用自定义分辨率"]

        if use_custom:
            w, h = kwargs["宽度"], kwargs["高度"]
        else:
            choices = {k: kwargs[k] for k in PRESETS}
            w, h = get_size_from_preset(choices)

        return self.validate_resolution(w, h)


class AspectRatioLock(BaseResolutionNode):
    """比例锁定器 - 支持固定比例计算或直接自定义宽高"""

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        return {
            "required": {
                "锁定比例": ([
                    "1:1 (正方形)",
                    "4:3 (传统电视)",
                    "3:2 (经典照片)",
                    "16:9 (宽屏)",
                    "2:3 (竖版照片)",
                    "3:4 (竖版传统)",
                    "9:16 (竖屏视频)",
                    "21:9 (超宽影院)",
                ], {"default": "16:9 (宽屏)"}),
                "输入类型": (["输入宽度", "输入高度"], {"default": "输入宽度"}),
                "输入值": ("INT", {"default": 1920, "min": 64, "max": 8192, "step": 8}),
                "确保8的倍数": ("BOOLEAN", {"default": True}),
                "启用自定义分辨率": ("BOOLEAN", {"default": False}),
                "自定义宽度": ("INT", {"default": 1920, "min": 64, "max": 8192, "step": 8}),
                "自定义高度": ("INT", {"default": 1080, "min": 64, "max": 8192, "step": 8}),
            }
        }

    RETURN_TYPES = ("INT", "INT", "STRING")
    RETURN_NAMES = ("宽度", "高度", "比例信息")
    FUNCTION = "calculate_by_aspect"
    CATEGORY = "ResolutionPresets"

    def calculate_by_aspect(self, **kwargs):
        use_custom = kwargs["启用自定义分辨率"]
        ensure_multiple = kwargs["确保8的倍数"]

        if use_custom:
            width = kwargs["自定义宽度"]
            height = kwargs["自定义高度"]
            ratio_desc = "自定义分辨率"
        else:
            lock_ratio = kwargs["锁定比例"]
            input_type = kwargs["输入类型"]
            input_value = kwargs["输入值"]

            ratio_part = lock_ratio.split(" ")[0]  # "16:9"
            aspect_w, aspect_h = map(int, ratio_part.split(":"))

            if input_type == "输入宽度":
                width = input_value
                height = int(width * aspect_h / aspect_w)
            else:
                height = input_value
                width = int(height * aspect_w / aspect_h)

            ratio_desc = lock_ratio

        if ensure_multiple:
            width = width - (width % 8)
            height = height - (height % 8)

        width = max(64, width)
        height = max(64, height)

        actual_ratio = width / height
        info_str = (
            f"🔒 模式: {ratio_desc}\n"
            f"📐 输出尺寸: {width} × {height}\n"
            f"📊 实际比例: {width}:{height} ≈ {actual_ratio:.3f}:1\n"
            f"📱 方向: {'横版 🌄' if width > height else '竖版 📱' if height > width else '正方形 ⬜'}"
        )

        return (width, height, info_str)


class ResolutionCalculator(BaseResolutionNode):
    """分辨率计算器 - 直接输入宽高进行缩放计算"""

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        return {
            "required": {
                "原始宽度": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 8}),
                "原始高度": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 8}),
                "缩放模式": (["按比例", "按长宽比", "固定分辨率"], {"default": "按比例"}),
                "缩放比例": ("FLOAT", {"default": 1.0, "min": 0.1, "max": 4.0, "step": 0.1}),
                "目标长宽比": (["保持原比例", "1:1", "4:3", "3:2", "16:9", "3:4", "2:3", "9:16", "21:9"], {"default": "保持原比例"}),
                "最大边长限制": ("INT", {"default": 4096, "min": 512, "max": 8192, "step": 8}),
                "确保8的倍数": ("BOOLEAN", {"default": True}),
            }
        }

    RETURN_TYPES = ("INT", "INT", "STRING")
    RETURN_NAMES = ("宽度", "高度", "分辨率信息")
    FUNCTION = "calculate_resolution"
    CATEGORY = "ResolutionPresets"

    def calculate_resolution(self, **kwargs):
        width = kwargs["原始宽度"]
        height = kwargs["原始高度"]
        mode = kwargs["缩放模式"]
        scale = kwargs["缩放比例"]
        aspect = kwargs["目标长宽比"]
        max_side = kwargs["最大边长限制"]
        ensure_multiple = kwargs["确保8的倍数"]

        if mode == "固定分辨率":
            new_width, new_height = width, height
        elif mode == "按长宽比" and aspect != "保持原比例":
            w_ratio, h_ratio = map(int, aspect.split(":"))
            new_width, new_height = ImageUtils.calculate_optimal_size(
                width, height,
                target_aspect_ratio=(w_ratio, h_ratio),
                max_side=max_side,
                multiple_of=8 if ensure_multiple else 1
            )
        else:
            new_width = int(width * scale)
            new_height = int(height * scale)
            if max(new_width, new_height) > max_side:
                scale_factor = max_side / max(new_width, new_height)
                new_width = int(new_width * scale_factor)
                new_height = int(new_height * scale_factor)

        if ensure_multiple:
            new_width = new_width - (new_width % 8)
            new_height = new_height - (new_height % 8)

        info = ImageUtils.get_resolution_info(new_width, new_height)
        info_str = (
            f"📐 分辨率: {new_width} × {new_height}\n"
            f"🔳 长宽比: {info['aspect_name']}\n"
            f"📊 像素: {info['megapixels']} MP ({info['resolution_level']})\n"
            f"📱 方向: {'横版 🌄' if info['is_landscape'] else '竖版 📱' if info['is_portrait'] else '正方形 ⬜'}"
        )

        return (new_width, new_height, info_str)


class ResolutionAnalyzer(BaseResolutionNode):
    """分辨率分析器"""

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        return {
            "required": {
                "宽度": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 8}),
                "高度": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 8}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("分辨率信息",)
    FUNCTION = "analyze_resolution"
    CATEGORY = "ResolutionPresets"

    def analyze_resolution(self, 宽度, 高度):
        info = ImageUtils.get_resolution_info(宽度, 高度)

        info_str = (
            f"分辨率: {info['width']}×{info['height']} ({info['aspect_name']})\n"
            f"像素: {info['megapixels']}MP • 等级: {info['resolution_level']}\n"
            f"方向: {'横版 🌄' if info['is_landscape'] else '竖版 📱' if info['is_portrait'] else '正方形 ⬜'}"
        )

        return (info_str,)


# 节点注册
NODE_CLASS_MAPPINGS = {
    "ResolutionPresetImage": ResolutionPresetImage,
    "ResolutionPresetLatent": ResolutionPresetLatent,
    "ResolutionPresetSetter": ResolutionPresetSetter,
    "ResolutionCalculator": ResolutionCalculator,
    "ResolutionAnalyzer": ResolutionAnalyzer,
    "AspectRatioLock": AspectRatioLock,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ResolutionPresetImage": "分辨率预设 - 图像",
    "ResolutionPresetLatent": "分辨率预设 - 潜在空间",
    "ResolutionPresetSetter": "分辨率预设器",
    "ResolutionCalculator": "分辨率计算器",
    "ResolutionAnalyzer": "分辨率分析器",
    "AspectRatioLock": "比例锁定器",
}
