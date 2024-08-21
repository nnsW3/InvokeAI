# Copyright (c) 2024, Brandon W. Rising and the InvokeAI Development Team
"""Class for Flux model loading in InvokeAI."""

from dataclasses import fields
from pathlib import Path
from typing import Any, Optional

import accelerate
import torch
import yaml
from safetensors.torch import load_file
from transformers import CLIPTextModel, CLIPTokenizer, T5EncoderModel, T5Tokenizer

from invokeai.app.services.config.config_default import get_config
from invokeai.backend.flux.model import Flux, FluxParams
from invokeai.backend.flux.modules.autoencoder import AutoEncoder, AutoEncoderParams
from invokeai.backend.model_manager import (
    AnyModel,
    AnyModelConfig,
    BaseModelType,
    ModelFormat,
    ModelType,
    SubModelType,
)
from invokeai.backend.model_manager.config import (
    CheckpointConfigBase,
    CLIPEmbedDiffusersConfig,
    MainBnbQuantized4bCheckpointConfig,
    MainCheckpointConfig,
    T5Encoder8bConfig,
    T5EncoderConfig,
    VAECheckpointConfig,
)
from invokeai.backend.model_manager.load.model_loader_registry import ModelLoaderRegistry
from invokeai.backend.model_manager.load.model_loaders.generic_diffusers import GenericDiffusersLoader
from invokeai.backend.quantization.bnb_nf4 import quantize_model_nf4
from invokeai.backend.quantization.fast_quantized_transformers_model import FastQuantizedTransformersModel
from invokeai.backend.util.silence_warnings import SilenceWarnings

app_config = get_config()


@ModelLoaderRegistry.register(base=BaseModelType.Flux, type=ModelType.VAE, format=ModelFormat.Checkpoint)
class FluxVAELoader(GenericDiffusersLoader):
    """Class to load VAE models."""

    def _load_model(
        self,
        config: AnyModelConfig,
        submodel_type: Optional[SubModelType] = None,
    ) -> AnyModel:
        if isinstance(config, VAECheckpointConfig):
            model_path = Path(config.path)
            load_class = AutoEncoder
            legacy_config_path = app_config.legacy_conf_path / config.config_path
            config_path = legacy_config_path.as_posix()
            with open(config_path, "r") as stream:
                try:
                    flux_conf = yaml.safe_load(stream)
                except:
                    raise

            dataclass_fields = {f.name for f in fields(AutoEncoderParams)}
            filtered_data = {k: v for k, v in flux_conf["params"].items() if k in dataclass_fields}
            params = AutoEncoderParams(**filtered_data)

            with SilenceWarnings():
                model = load_class(params)
                sd = load_file(model_path)
                model.load_state_dict(sd, strict=False, assign=True)

            return model
        else:
            return super()._load_model(config, submodel_type)


@ModelLoaderRegistry.register(base=BaseModelType.Any, type=ModelType.CLIPEmbed, format=ModelFormat.Diffusers)
class ClipCheckpointModel(GenericDiffusersLoader):
    """Class to load main models."""

    def _load_model(
        self,
        config: AnyModelConfig,
        submodel_type: Optional[SubModelType] = None,
    ) -> AnyModel:
        if not isinstance(config, CLIPEmbedDiffusersConfig):
            raise Exception("Only CLIPEmbedDiffusersConfig models are currently supported here.")

        match submodel_type:
            case SubModelType.Tokenizer:
                return CLIPTokenizer.from_pretrained(config.path, max_length=77)
            case SubModelType.TextEncoder:
                return CLIPTextModel.from_pretrained(config.path)

        raise Exception("Only Tokenizer and TextEncoder submodels are currently supported.")


@ModelLoaderRegistry.register(base=BaseModelType.Any, type=ModelType.T5Encoder, format=ModelFormat.T5Encoder8b)
class T5Encoder8bCheckpointModel(GenericDiffusersLoader):
    """Class to load main models."""

    def _load_model(
        self,
        config: AnyModelConfig,
        submodel_type: Optional[SubModelType] = None,
    ) -> AnyModel:
        if not isinstance(config, T5Encoder8bConfig):
            raise Exception("Only T5Encoder8bConfig models are currently supported here.")

        match submodel_type:
            case SubModelType.Tokenizer2:
                return T5Tokenizer.from_pretrained(Path(config.path) / "tokenizer_2", max_length=512)
            case SubModelType.TextEncoder2:
                return FastQuantizedTransformersModel.from_pretrained(Path(config.path) / "text_encoder_2")

        raise Exception("Only Tokenizer and TextEncoder submodels are currently supported.")


@ModelLoaderRegistry.register(base=BaseModelType.Any, type=ModelType.T5Encoder, format=ModelFormat.T5Encoder)
class T5EncoderCheckpointModel(GenericDiffusersLoader):
    """Class to load main models."""

    def _load_model(
        self,
        config: AnyModelConfig,
        submodel_type: Optional[SubModelType] = None,
    ) -> AnyModel:
        if not isinstance(config, T5EncoderConfig):
            raise Exception("Only T5EncoderConfig models are currently supported here.")

        match submodel_type:
            case SubModelType.Tokenizer2:
                return T5Tokenizer.from_pretrained(Path(config.path) / "tokenizer_2", max_length=512)
            case SubModelType.TextEncoder2:
                return T5EncoderModel.from_pretrained(
                    Path(config.path) / "text_encoder_2"
                )  # TODO: Fix hf subfolder install

        raise Exception("Only Tokenizer and TextEncoder submodels are currently supported.")


@ModelLoaderRegistry.register(base=BaseModelType.Flux, type=ModelType.Main, format=ModelFormat.Checkpoint)
class FluxCheckpointModel(GenericDiffusersLoader):
    """Class to load main models."""

    def _load_model(
        self,
        config: AnyModelConfig,
        submodel_type: Optional[SubModelType] = None,
    ) -> AnyModel:
        if not isinstance(config, CheckpointConfigBase):
            raise Exception("Only CheckpointConfigBase models are currently supported here.")
        legacy_config_path = app_config.legacy_conf_path / config.config_path
        config_path = legacy_config_path.as_posix()
        with open(config_path, "r") as stream:
            try:
                flux_conf = yaml.safe_load(stream)
            except:
                raise

        match submodel_type:
            case SubModelType.Transformer:
                return self._load_from_singlefile(config, flux_conf)

        raise Exception("Only Transformer submodels are currently supported.")

    def _load_from_singlefile(
        self,
        config: AnyModelConfig,
        flux_conf: Any,
    ) -> AnyModel:
        assert isinstance(config, MainCheckpointConfig)
        load_class = Flux
        params = None
        model_path = Path(config.path)
        dataclass_fields = {f.name for f in fields(FluxParams)}
        filtered_data = {k: v for k, v in flux_conf["params"].items() if k in dataclass_fields}
        params = FluxParams(**filtered_data)

        with SilenceWarnings():
            model = load_class(params)
            sd = load_file(model_path)
            model.load_state_dict(sd, strict=False, assign=True)
        return model


@ModelLoaderRegistry.register(base=BaseModelType.Flux, type=ModelType.Main, format=ModelFormat.BnbQuantizednf4b)
class FluxBnbQuantizednf4bCheckpointModel(GenericDiffusersLoader):
    """Class to load main models."""

    def _load_model(
        self,
        config: AnyModelConfig,
        submodel_type: Optional[SubModelType] = None,
    ) -> AnyModel:
        if not isinstance(config, CheckpointConfigBase):
            raise Exception("Only CheckpointConfigBase models are currently supported here.")
        legacy_config_path = app_config.legacy_conf_path / config.config_path
        config_path = legacy_config_path.as_posix()
        with open(config_path, "r") as stream:
            try:
                flux_conf = yaml.safe_load(stream)
            except:
                raise

        match submodel_type:
            case SubModelType.Transformer:
                return self._load_from_singlefile(config, flux_conf)

        raise Exception("Only Transformer submodels are currently supported.")

    def _load_from_singlefile(
        self,
        config: AnyModelConfig,
        flux_conf: Any,
    ) -> AnyModel:
        assert isinstance(config, MainBnbQuantized4bCheckpointConfig)
        load_class = Flux
        params = None
        model_path = Path(config.path)
        dataclass_fields = {f.name for f in fields(FluxParams)}
        filtered_data = {k: v for k, v in flux_conf["params"].items() if k in dataclass_fields}
        params = FluxParams(**filtered_data)

        with SilenceWarnings():
            with accelerate.init_empty_weights():
                model = load_class(params)
                model = quantize_model_nf4(model, modules_to_not_convert=set(), compute_dtype=torch.bfloat16)
            sd = load_file(model_path)
            model.load_state_dict(sd, strict=False, assign=True)
        return model