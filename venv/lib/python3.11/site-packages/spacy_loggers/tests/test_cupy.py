import pytest
from thinc.util import has_cupy_gpu, has_torch, has_tensorflow, require_gpu
from thinc.backends import use_pytorch_for_gpu_memory, use_tensorflow_for_gpu_memory

from spacy_loggers.cupy import cupy_logger_v1


@pytest.fixture
def logger():
    setup_logger = cupy_logger_v1()
    step, _ = setup_logger(None)
    return step


@pytest.mark.skipif(not has_cupy_gpu, reason="CuPy support required")
def test_cupy_allocator_source_default(logger):
    # Needs to be executed first as modifications to the memory pool
    # persist for the entire session.
    require_gpu()
    info = {}
    logger(info)
    assert info["cupy.pool.source"] == "default"


@pytest.mark.skipif(
    not has_cupy_gpu or not has_torch, reason="CuPy/PyTorch support required"
)
def test_cupy_allocator_source_torch(logger):
    require_gpu()
    use_pytorch_for_gpu_memory()
    info = {}
    logger(info)
    assert info["cupy.pool.source"] == "pytorch"


@pytest.mark.skipif(
    not has_cupy_gpu or not has_tensorflow, reason="CuPy/TensorFlow support required"
)
def test_cupy_allocator_source_tf(logger):
    require_gpu()
    use_tensorflow_for_gpu_memory()
    info = {}
    logger(info)
    assert info["cupy.pool.source"] == "tensorflow"
