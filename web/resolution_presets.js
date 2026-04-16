/**
 * ComfyUI Resolution Presets Web Extension
 * 提供更好的UI体验和预览功能
 */

import { app } from "../../scripts/app.js";

// 前端预设表（与后端 presets.py 同步）
const PRESETS_JS = {
    "SD1.5": [
        ["512×512 (1:1)", 512, 512],
        ["768×512 (3:2)", 768, 512],
        ["512×768 (2:3)", 512, 768],
        ["768×576 (4:3)", 768, 576],
        ["576×768 (3:4)", 576, 768]
    ],
    "SDXL": [
        ["1024×1024 (1:1)", 1024, 1024],
        ["1152×896 (9:7)", 1152, 896],
        ["896×1152 (7:9)", 896, 1152],
        ["1344×768 (7:4)", 1344, 768],
        ["768×1344 (4:7)", 768, 1344],
        ["1216×832 (19:13)", 1216, 832],
        ["832×1216 (13:19)", 832, 1216],
        ["1280×768 (5:3)", 1280, 768],
        ["768×1280 (3:5)", 768, 1280],
        ["1536×640 (12:5)", 1536, 640],
        ["640×1536 (5:12)", 640, 1536],
        ["1600×640 (5:2)", 1600, 640],
        ["640×1600 (2:5)", 640, 1600]
    ],
    "FLUX": [
        ["1024×1024 (1:1)", 1024, 1024],
        ["1280×720 (16:9)", 1280, 720],
        ["720×1280 (9:16)", 720, 1280],
        ["1536×640 (12:5)", 1536, 640],
        ["640×1536 (5:12)", 640, 1536],
        ["1920×1080 (16:9) 2K", 1920, 1080],
        ["1080×1920 (9:16) 2K竖版", 1080, 1920],
        ["2048×1080 (17:9) 2K DCI", 2048, 1080],
        ["2560×1440 (16:9) 2.5K", 2560, 1440],
        ["1440×2560 (9:16) 2.5K竖版", 1440, 2560],
        ["3072×1728 (16:9) 3K", 3072, 1728],
        ["1728×3072 (9:16) 3K竖版", 1728, 3072],
        ["3840×2160 (16:9) 4K UHD", 3840, 2160],
        ["2160×3840 (9:16) 4K竖版", 2160, 3840],
        ["4096×2160 (17:9) 4K DCI", 4096, 2160],
        ["5120×2880 (16:9) 5K", 5120, 2880],
        ["6144×3456 (16:9) 6K", 6144, 3456]
    ],
    "WAN": [
        ["832×480 (16:9)", 832, 480],
        ["480×832 (9:16)", 480, 832],
        ["896×512 (7:4)", 896, 512],
        ["512×896 (4:7)", 512, 896],
        ["1280×720 (16:9)", 1280, 720],
        ["720×1280 (9:16)", 720, 1280],
        ["640×480 (4:3)", 640, 480],
        ["1024×576 (16:9)", 1024, 576],
        ["576×1024 (9:16)", 576, 1024]
    ],
    "QWEN": [
        ["1328×1328 (1:1)", 1328, 1328],
        ["928×1664 (9:16)", 928, 1664],
        ["1664×928 (16:9)", 1664, 928],
        ["1104×1472 (3:4)", 1104, 1472],
        ["1472×1104 (4:3)", 1472, 1104],
        ["1056×1584 (2:3)", 1056, 1584],
        ["1584×1056 (3:2)", 1584, 1056]
    ]
};

app.registerExtension({
    name: "ComfyUI.ResolutionPresets.WebExtension",

    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "ResolutionPresetImage") {
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function() {
                const r = onNodeCreated ? onNodeCreated.apply(this) : undefined;

                if (this.widgets) {
                    this.addWidget("button", "预览尺寸", null, () => {
                        this.showPreview();
                    });
                }

                return r;
            };

            nodeType.prototype.showPreview = function() {
                let width = 512, height = 512;
                let isEdgeMode = false;

                // 1. 检查是否启用边长缩放
                if (this.widgets) {
                    const edgeWidget = this.widgets.find(w => w.name === "启用边长缩放");
                    if (edgeWidget && edgeWidget.value === true) {
                        isEdgeMode = true;
                    }
                }

                // 2. 获取预设宽高
                if (this.widgets) {
                    for (const key in PRESETS_JS) {
                        const widget = this.widgets.find(w => w.name === key);
                        if (widget && widget.value !== "关") {
                            const found = PRESETS_JS[key].find(p => p[0] === widget.value);
                            if (found) {
                                width = found[1];
                                height = found[2];
                                break;
                            }
                        }
                    }
                }

                // 3. 如果启用了边长缩放，根据缩放设置重新计算宽高
                if (isEdgeMode) {
                    const edgeModeWidget = this.widgets.find(w => w.name === "缩放基准");
                    const targetLenWidget = this.widgets.find(w => w.name === "缩放长度");
                    const mode = edgeModeWidget ? edgeModeWidget.value : "最长边";
                    const targetLen = targetLenWidget ? targetLenWidget.value : 1024;

                    const aspect = width / height;
                    if (mode === "最长边") {
                        if (width >= height) {
                            width = targetLen;
                            height = Math.round(targetLen / aspect);
                        } else {
                            height = targetLen;
                            width = Math.round(targetLen * aspect);
                        }
                    } else { // 最短边
                        if (width <= height) {
                            width = targetLen;
                            height = Math.round(targetLen / aspect);
                        } else {
                            height = targetLen;
                            width = Math.round(targetLen * aspect);
                        }
                    }

                    // 确保 8 的倍数（与后端行为一致）
                    width = width - (width % 8);
                    height = height - (height % 8);
                    width = Math.max(64, width);
                    height = Math.max(64, height);
                }

                // 4. 打开预览窗口
                const previewWindow = window.open('', '_blank');
                previewWindow.document.write(`
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>分辨率预览 - ${width}×${height}</title>
                        <style>
                            body {
                                margin: 0;
                                padding: 20px;
                                font-family: 'Segoe UI', Arial, sans-serif;
                                background: #f0f2f5;
                            }
                            .container {
                                max-width: 800px;
                                margin: 0 auto;
                                background: white;
                                padding: 24px;
                                border-radius: 12px;
                                box-shadow: 0 4px 12px rgba(0,0,0,0.08);
                            }
                            h1 {
                                margin-top: 0;
                                color: #1a1a1a;
                                font-weight: 500;
                            }
                            .preview-area {
                                width: 100%;
                                height: 400px;
                                border: 2px dashed #d0d7de;
                                margin: 20px 0;
                                display: flex;
                                align-items: center;
                                justify-content: center;
                                position: relative;
                                background: linear-gradient(45deg, #f6f8fa 25%, transparent 25%, transparent 75%, #f6f8fa 75%, #f6f8fa),
                                            linear-gradient(45deg, #f6f8fa 25%, transparent 25%, transparent 75%, #f6f8fa 75%, #f6f8fa);
                                background-size: 20px 20px;
                                background-position: 0 0, 10px 10px;
                                border-radius: 8px;
                            }
                            .preview-box {
                                background: #2da44e;
                                opacity: 0.7;
                                position: absolute;
                                border-radius: 4px;
                                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                            }
                            .info {
                                background: #f6f8fa;
                                padding: 16px;
                                border-radius: 8px;
                                margin: 12px 0;
                            }
                            .info h3 {
                                margin-top: 0;
                                color: #0969da;
                            }
                            .dimensions {
                                font-size: 28px;
                                font-weight: 600;
                                color: #1f2328;
                            }
                            .ratio {
                                font-size: 16px;
                                color: #57606a;
                                margin-top: 4px;
                            }
                            .suggestion {
                                color: #1f2328;
                            }
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <h1>📐 分辨率预览</h1>
                            <div class="info">
                                <h3>尺寸信息</h3>
                                <div class="dimensions">${width} × ${height}</div>
                                <div class="ratio">长宽比: ${(width/height).toFixed(2)}:1</div>
                                <div>总像素: ${(width*height).toLocaleString()}</div>
                                <div>百万像素: ${((width*height)/1000000).toFixed(2)} MP</div>
                            </div>
                            <div class="preview-area" id="previewArea">
                                <div id="previewBox" class="preview-box"></div>
                            </div>
                            <div class="info">
                                <h3>使用建议</h3>
                                <div id="suggestion" class="suggestion">计算中...</div>
                            </div>
                        </div>
                        <script>
                            const area = document.getElementById('previewArea');
                            const box = document.getElementById('previewBox');
                            const suggestion = document.getElementById('suggestion');

                            const w = ${width};
                            const h = ${height};

                            const areaWidth = area.clientWidth;
                            const areaHeight = area.clientHeight;
                            const aspect = w / h;

                            let previewWidth, previewHeight;
                            if (aspect > 1) {
                                previewWidth = Math.min(areaWidth * 0.8, areaHeight * 0.8 * aspect);
                                previewHeight = previewWidth / aspect;
                            } else {
                                previewHeight = Math.min(areaHeight * 0.8, areaWidth * 0.8 / aspect);
                                previewWidth = previewHeight * aspect;
                            }

                            box.style.width = previewWidth + 'px';
                            box.style.height = previewHeight + 'px';
                            box.style.left = (areaWidth - previewWidth) / 2 + 'px';
                            box.style.top = (areaHeight - previewHeight) / 2 + 'px';

                            const mp = (w * h) / 1000000;
                            let suggestionText = '';
                            if (mp < 0.5) suggestionText = '适合图标、小图、预览图';
                            else if (mp < 2) suggestionText = '适合社交媒体、网页图片';
                            else if (mp < 5) suggestionText = '适合高清壁纸、小尺寸印刷';
                            else if (mp < 10) suggestionText = '适合4K显示、中等尺寸印刷';
                            else suggestionText = '适合大幅面印刷、专业摄影';

                            suggestion.textContent = suggestionText;
                        </script>
                    </body>
                    </html>
                `);
                previewWindow.document.close();
            };
        }
    }
});
