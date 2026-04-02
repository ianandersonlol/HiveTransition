"""
Monkey-patch openfold's attention_core to avoid requiring the compiled CUDA kernel.

Import this before importing ESMFold to make it work without attn_core_inplace_cuda.

Usage:
    import patch_attention  # patches openfold
    import esm
    model = esm.pretrained.esmfold_v1()
"""
import torch
import importlib
import sys
from functools import reduce
from operator import mul


# Create a fake attn_core_inplace_cuda module with pure-torch implementations
class FakeAttnCoreModule:
    @staticmethod
    def forward_(attention_logits, flat_size, last_dim):
        """In-place softmax along last dimension."""
        attention_logits.copy_(torch.softmax(attention_logits, dim=-1))

    @staticmethod
    def backward_(attention_logits, grad_output, v, flat_size, last_dim, v_dim):
        """In-place backward pass for softmax attention."""
        # attention_logits contains softmax output at this point
        # grad_attn = softmax * (grad_output @ v^T - sum(grad_output * (softmax @ v), dim=-1, keepdim=True))
        dv = torch.matmul(attention_logits.transpose(-1, -2), grad_output)
        grad_attn = torch.matmul(grad_output, v.transpose(-1, -2))
        grad_attn -= (grad_attn * attention_logits).sum(dim=-1, keepdim=True)
        grad_attn *= attention_logits
        attention_logits.copy_(grad_attn)


# Register fake module so importlib.import_module finds it
sys.modules["attn_core_inplace_cuda"] = FakeAttnCoreModule()
