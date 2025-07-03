#!/usr/bin/env python
import argparse
from huggingface_hub import snapshot_download as hf_snapshot_download
from modelscope import snapshot_download as ms_snapshot_download

class ModelPath:
    vlm_root_hf = "opendatalab/MinerU2.0-2505-0.9B"
    vlm_root_modelscope = "OpenDataLab/MinerU2.0-2505-0.9B"
    pipeline_root_modelscope = "OpenDataLab/PDF-Extract-Kit-1.0"
    pipeline_root_hf = "opendatalab/PDF-Extract-Kit-1.0"
    doclayout_yolo = "models/Layout/YOLO/doclayout_yolo_docstructbench_imgsz1280_2501.pt"
    yolo_v8_mfd = "models/MFD/YOLO/yolo_v8_ft.pt"
    unimernet_small = "models/MFR/unimernet_hf_small_2503"
    pytorch_paddle = "models/OCR/paddleocr_torch"
    layout_reader = "models/ReadingOrder/layout_reader"
    slanet_plus = "models/TabRec/SlanetPlus/slanet-plus.onnx"


repo_mapping = {
    'pipeline': {
        'huggingface': ModelPath.pipeline_root_hf,
        'modelscope': ModelPath.pipeline_root_modelscope,
        'default': ModelPath.pipeline_root_hf
    },
    'vlm': {
        'huggingface': ModelPath.vlm_root_hf,
        'modelscope': ModelPath.vlm_root_modelscope,
        'default': ModelPath.vlm_root_hf
    }
}
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("model_source", help="模型下载选择huggingface/modelscope")
    args = parser.parse_args()
    model_source =args.model_source

    if model_source == "huggingface":
        snapshot_download = hf_snapshot_download
    elif model_source == "modelscope":
        snapshot_download = ms_snapshot_download
    else:
        raise ValueError(f"未知的仓库类型: {model_source}")

    pipeline_model_paths = [
        ModelPath.doclayout_yolo,
        ModelPath.yolo_v8_mfd,
        ModelPath.unimernet_small,
        ModelPath.pytorch_paddle,
        ModelPath.layout_reader,
        ModelPath.slanet_plus
    ]
    pipe_mineru_patterns = [
        p.strip('/') + '/*' for p in pipeline_model_paths
    ] + [
        p.strip('/') for p in pipeline_model_paths
    ]

    pipeline_dir = snapshot_download(
        repo_mapping["pipeline"][model_source],
        allow_patterns=pipe_mineru_patterns,
        local_dir="./models2.0/pipeline",
    )

    vlm_dir = snapshot_download(
        repo_mapping["vlm"][model_source],
        local_dir="./models2.0/vlm/",
    )

    print(f"pipeline dir is: {pipeline_dir}")
    print(f"vlm dir is: {vlm_dir}")
