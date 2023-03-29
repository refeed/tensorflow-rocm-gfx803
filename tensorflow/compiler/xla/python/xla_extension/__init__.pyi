# Copyright 2021 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

import enum
import inspect
import types
import typing
from typing import Any, Callable, ClassVar, Dict, List, Optional, Sequence, Tuple, Type, TypeVar, Union, overload

import numpy as np

from . import ops
from . import jax_jit
from . import mlir
from . import outfeed_receiver
from . import pmap_lib
from . import profiler
from . import pytree
from . import transfer_guard_lib

_LiteralSlice = Any
_Status = Any
_Dtype = Any
_XlaOpMetadata = Any

_T = TypeVar("_T")

class XlaRuntimeError(RuntimeError):
  pass

class PrimitiveType(enum.IntEnum):
  PRIMITIVE_TYPE_INVALID: PrimitiveType
  PRED: PrimitiveType
  S8: PrimitiveType
  S16: PrimitiveType
  S32: PrimitiveType
  S64: PrimitiveType
  U8: PrimitiveType
  U16: PrimitiveType
  U32: PrimitiveType
  U64: PrimitiveType
  F8_E4M3FN: PrimitiveType
  F8_E5M2: PrimitiveType
  BF16: PrimitiveType
  F16: PrimitiveType
  F32: PrimitiveType
  F64: PrimitiveType
  C64: PrimitiveType
  C128: PrimitiveType
  TUPLE: PrimitiveType
  OPAQUE_TYPE: PrimitiveType
  TOKEN: PrimitiveType

def bfloat16_dtype() -> Type[Any]: ...
def float8_e4m3fn_dtype() -> Type[Any]: ...
def float8_e5m2_dtype() -> Type[Any]: ...

# === BEGIN xla_compiler.cc

class Shape:
  def __init__(self, s: str): ...
  @staticmethod
  def tuple_shape(shapes: Sequence[Shape]) -> Shape: ...
  @staticmethod
  def array_shape(
      type: Union[np.dtype, PrimitiveType],
      dims_seq: Any = ...,
      layout_seq: Any = ...,
      dynamic_dimensions: Optional[List[bool]] = ...) -> Shape: ...
  @staticmethod
  def token_shape() -> Shape: ...
  @staticmethod
  def scalar_shape(type: Union[np.dtype, PrimitiveType]) -> Shape: ...
  def dimensions(self) -> Tuple[int, ...]: ...
  def xla_element_type(self) -> PrimitiveType: ...
  def element_type(self) -> np.dtype: ...
  def numpy_dtype(self) -> np.dtype: ...
  def is_tuple(self) -> bool: ...
  def is_array(self) -> bool: ...
  def is_token(self) -> bool: ...
  def is_static(self) -> bool: ...
  def is_dynamic(self) -> bool: ...
  def is_dynamic_dimension(self, dimension: int) -> bool: ...
  def set_dynamic_dimension(self, dimension: int, is_dynamic: bool) -> None: ...
  def rank(self) -> int: ...
  def to_serialized_proto(self) -> bytes: ...
  def tuple_shapes(self) -> List[Shape]: ...
  def leaf_count(self) -> int: ...
  def with_major_to_minor_layout_if_absent(self) -> Shape: ...
  def __eq__(self, other: Shape) -> bool: ...
  def __ne__(self, other: Shape) -> bool: ...
  def __hash__(self) -> int: ...
  def __repr__(self) -> str: ...

class Layout:
  def minor_to_major(self) -> Tuple[int, ...]: ...
  def to_string(self) -> str: ...
  def __eq__(self, other: Layout) -> bool: ...
  def __ne__(self, other: Layout) -> bool: ...
  def __hash__(self) -> int: ...

class ProgramShape:
  def __init__(self, params: Sequence[Shape], result: Shape) -> None: ...
  def parameter_shapes(self) -> List[Shape]: ...
  def result_shape(self) -> Shape: ...
  def __repr__(self) -> str: ...

class ShapeIndex:
  def __init__(self, indices: List[int]) -> ShapeIndex: ...
  def __eq__(self, other: Shape) -> bool: ...
  def __ne__(self, other: Shape) -> bool: ...
  def __hash__(self) -> int: ...
  def __repr__(self) -> str: ...

class Literal:
  def __repr__(self) -> str: ...

class XlaComputation:
  def __init__(self, serialized_hlo_module_proto: bytes) -> None: ...
  def get_hlo_module(self) -> HloModule: ...
  def program_shape(self) -> ProgramShape: ...
  def as_serialized_hlo_module_proto(self) -> bytes: ...
  def as_hlo_text(self, print_large_constants: bool=False) -> str: ...
  def as_hlo_dot_graph(self) -> str: ...
  def hash(self) -> int: ...
  def as_hlo_module(self) -> HloModule: ...

class HloPrintOptions:
  def __init__(self) -> None: ...
  @staticmethod
  def short_parsable() -> HloPrintOptions: ...
  @staticmethod
  def canonical() -> HloPrintOptions: ...
  @staticmethod
  def fingerprint() -> HloPrintOptions: ...
  print_large_constants: bool
  print_metadata: bool
  print_backend_config: bool
  print_result_shape: bool
  print_operand_shape: bool
  print_operand_names: bool
  print_ids: bool
  print_extra_attributes: bool
  print_program_shape: bool
  print_percent: bool
  print_control_dependencies: bool
  compact_operands: bool
  include_layout_in_shapes: bool
  canonicalize_instruction_names: bool
  canonicalize_computations: bool
  indent_amount: int
  is_in_nested_computation: bool

class HloModule:
  spmd_output_sharding: Optional[OpSharding]
  spmd_parameters_shardings: Optional[List[OpSharding]]
  @property
  def name(self) -> str: ...
  def to_string(self, options: HloPrintOptions = ...) -> str: ...
  def as_serialized_hlo_module_proto(self)-> bytes: ...
  @staticmethod
  def from_serialized_hlo_module_proto(
    serialized_hlo_module_proto: bytes) -> HloModule: ...

class HloModuleGroup:
  def __init__(self, name: str, modules: List[HloModule]) -> None: ...
  @property
  def name(self) -> str: ...
  def to_string(self) -> str: ...
  def to_modules(self) -> List[HloModule]: ...

def hlo_module_to_dot_graph(hlo_module: HloModule) -> str: ...
def hlo_module_from_text(hlo_module_text: str) -> HloModule: ...

def hlo_module_cost_analysis(
    client: Client,
    module: HloModule) -> Dict[str, float]: ...

class XlaOp: ...

class XlaBuilder:
  def __init__(self, name: str) -> None: ...
  def Build(self, root: Optional[XlaOp] = ...) -> XlaComputation: ...
  def GetShape(self, __op: XlaOp) -> Shape: ...
  build = Build
  def clear_op_metadata(self) -> None: ...
  get_shape = GetShape
  def get_program_shape(self, root: Optional[XlaOp] = ...) -> ProgramShape: ...
  def is_constant(self, __op: XlaOp) -> bool: ...
  def set_op_metadata(self, metadata: _XlaOpMetadata) -> None: ...
  def set_sharding(self, sharding: OpSharding_Type) -> None: ...
  def clear_sharding(self) -> None: ...
  def setup_alias(
      self,
      __output_index: Sequence[int],
      __param_number: int,
      __param_index: Sequence[int]) -> None: ...

class DeviceAssignment:
  @staticmethod
  def create(array: np.ndarray) -> DeviceAssignment: ...
  def replica_count(self) -> int: ...
  def computation_count(self) -> int: ...
  def __repr__(self) -> str: ...
  def serialize(self) -> bytes: ...

class CompileOptions:
  @staticmethod
  def ParseFromString(s: bytes) -> CompileOptions: ...
  def __init__(self) -> None: ...
  def SerializeAsString(self) -> bytes: ...
  argument_layouts: Optional[List[Shape]]
  parameter_is_tupled_arguments: bool
  executable_build_options: ExecutableBuildOptions
  tuple_arguments: bool
  num_replicas: int
  num_partitions: int
  profile_version: int
  device_assignment: Optional[DeviceAssignment]
  compile_portable_executable: bool

def register_custom_call_target(fn_name: str, capsule: Any, platform: str) -> _Status: ...
def register_custom_call_partitioner(name: str, prop_user_sharding: Callable,
                                     partition: Callable, infer_sharding_from_operands: Callable,
                                     can_side_effecting_have_replicated_sharding: bool) -> None: ...

class DebugOptions:
  def __repr__(self) -> str: ...
  xla_cpu_enable_fast_math: bool
  xla_cpu_fast_math_honor_infs: bool
  xla_cpu_fast_math_honor_nans: bool
  xla_cpu_fast_math_honor_division: bool
  xla_cpu_fast_math_honor_functions: bool
  xla_gpu_enable_fast_min_max: bool
  xla_backend_optimization_level: int
  xla_cpu_enable_xprof_traceme: bool
  xla_llvm_disable_expensive_passes: bool
  xla_test_all_input_layouts: bool

class CompiledMemoryStats:
  generated_code_size_in_bytes: int
  argument_size_in_bytes: int
  output_size_in_bytes: int
  alias_size_in_bytes: int
  temp_size_in_bytes: int
  serialized_hlo_proto: bytes
  def __str__(self) -> str: ...


class ExecutableBuildOptions:
  def __init__(self) -> None: ...
  def __repr__(self) -> str: ...
  result_layout: Optional[Shape]
  num_replicas: int
  num_partitions: int
  debug_options: DebugOptions
  device_assignment: Optional[DeviceAssignment]
  use_spmd_partitioning: bool
  use_auto_spmd_partitioning: bool
  auto_spmd_partitioning_mesh_shape: List[int]
  auto_spmd_partitioning_mesh_ids: List[int]

class PrecisionConfig_Precision(enum.IntEnum):
  DEFAULT: int
  HIGH: int
  HIGHEST: int

class OpSharding_Type(enum.IntEnum):
  REPLICATED: int
  MAXIMAL: int
  TUPLE: int
  OTHER: int
  MANUAL: int

class OpSharding:
  Type: typing.Type[OpSharding_Type]
  type: OpSharding_Type
  replicate_on_last_tile_dim: bool
  last_tile_dims: Sequence[Type]
  tile_assignment_dimensions: Sequence[int]
  tile_assignment_devices: Sequence[int]
  tuple_shardings: Sequence[OpSharding]
  def ParseFromString(self, s: bytes) -> None: ...
  def SerializeToString(self) -> bytes: ...
  def clone(self) -> OpSharding: ...

class HloSharding:
  @staticmethod
  def from_proto(proto: OpSharding) -> HloSharding: ...
  def __eq__(self, other: HloSharding) -> bool: ...
  def __hash__(self) -> int: ...
  def __repr__(self) -> str: ...
  def tile(self, shape: Shape) -> Shape: ...
  def is_replicated() -> bool: ...
  def to_proto() -> OpSharding: ...

class ChannelHandle_ChannelType(enum.IntEnum):
  CHANNEL_TYPE_INVALID: int
  DEVICE_TO_DEVICE: int
  DEVICE_TO_HOST: int
  HOST_TO_DEVICE: int

class ChannelHandle:
  type: ChannelHandle_ChannelType
  handle: int
  def __repr__(self) -> str: ...

class FftType(enum.IntEnum):
  FFT: int
  IFFT: int
  RFFT: int
  IRFFT: int

# === END xla_compiler.cc

class Device:
  id: int
  host_id: int
  process_index: int
  platform: str
  device_kind: str
  client: Client
  def __repr__(self) -> str: ...
  def __str__(self) -> str: ...
  def transfer_to_infeed(self, literal: _LiteralSlice): ...
  def transfer_from_outfeed(self, shape: Shape): ...
  def live_buffers(self) -> List[Buffer]: ...
  def __getattr__(self, name: str) -> Any: ...

class _GpuAllocatorKind(enum.IntEnum):
    DEFAULT: int
    PLATFORM: int
    BFC: int
    CUDA_ASYNC: int

class GpuAllocatorConfig:
  # TODO(b/194673104): Remove once pytype correctly resolves a nested enum.
  Kind = _GpuAllocatorKind

  def __init__(
      self,
      kind: _GpuAllocatorKind = ...,
      memory_fraction: float = ...,
      preallocate: bool = ...) -> None: ...

class HostBufferSemantics(enum.IntEnum):
  IMMUTABLE_ONLY_DURING_CALL: HostBufferSemantics
  IMMUTABLE_UNTIL_TRANSFER_COMPLETES: HostBufferSemantics
  ZERO_COPY: HostBufferSemantics

class Client:
  platform: str
  platform_version: str
  runtime_type: str
  def device_count(self) -> int: ...
  def local_device_count(self) -> int: ...
  def devices(self) -> List[Device]: ...
  def local_devices(self) -> List[Device]: ...
  def live_buffers(self) -> List[Buffer]: ...
  def live_arrays(self) -> List[ArrayImpl]: ...
  def live_executables(self) -> List[LoadedExecutable]: ...
  def host_id(self) -> int: ...
  def process_index(self) -> int: ...
  @overload
  def get_default_device_assignment(
      self,
      num_replicas: int,
      num_partitions: int) -> List[List[Device]]: ...
  @overload
  def get_default_device_assignment(
      self,
      num_replicas: int) -> List[Device]: ...
  def create_channel_handle(self) -> ChannelHandle: ...
  def create_device_to_host_channel_handle(self) -> ChannelHandle: ...
  def create_host_to_device_channel_handle(self) -> ChannelHandle: ...
  def buffer_from_pyval(
      self,
      argument: Any,
      device: Optional[Device] = ...,
      force_copy: bool = ...,
      host_buffer_semantics: HostBufferSemantics = ...) -> Buffer: ...
  def make_cross_host_receive_buffers(
      self,
      shapes: Sequence[Shape],
      device: Device) -> List[Tuple[Buffer, bytes]]: ...
  def compile(
      self,
      computation: Union[str, bytes],
      compile_options: CompileOptions = ..., host_callbacks: Sequence[Any] = ...) -> LoadedExecutable: ...
  def serialize_executable(self, executable: LoadedExecutable) -> bytes: ...
  def deserialize_executable(
      self, serialized: bytes,
      options: CompileOptions, host_callbacks: Sequence[Any] = ...) -> LoadedExecutable: ...
  # TODO(skyewm): remove when jax stop providing hlo_module
  def deserialize_executable(
      self, serialized: bytes,
      hlo_module: HloModule,
      options: CompileOptions, host_callbacks: Sequence[Any] = ...) -> LoadedExecutable: ...
  def heap_profile(self) -> bytes: ...
  def defragment(self) -> _Status: ...
  def get_emit_python_callback_descriptor(
      self, callable: Callable, operand_shapes: Sequence[Shape],
      results_shapes: Sequence[Shape]) -> Tuple[Any, Any]: ...
  def emit_python_callback(
      self, callable: Callable, builder: XlaBuilder, operands: Sequence[XlaOp],
      results_shapes: Sequence[Shape],
      operand_layouts: Optional[Sequence[Shape]] = ...,
      has_side_effects: bool = ...) -> Tuple[XlaOp, Any]: ...
  def make_python_callback_from_host_send_and_recv(
      self, callable: Callable, operand_shapes: Sequence[Shape],
      result_shapes: Sequence[Shape], send_channel_ids: Sequence[int],
      recv_channel_ids: Sequence[int]) -> Any: ...
  def get_python_callback_from_host_send(callable: Any,
                                         operand_shapes: Any, send_channel_ids: Any, recv_channel_ids: Any) -> Any: ...


def get_tfrt_cpu_client(asynchronous: bool = ...) -> Client: ...
def get_interpreter_client() -> Client: ...
def get_gpu_client(
    asynchronous: bool = ...,
    allocator_config: GpuAllocatorConfig = ...,
    distributed_client: Optional[DistributedRuntimeClient] = ...,
    node_id: int = ...,
    allowed_devices: Optional[Any] = ...,
    platform_name: Optional[str] = ...) -> Client:...
def get_tpu_client(max_inflight_computations: int = ...) -> Client: ...
def get_c_api_client(platform_name: str, options: Dict[str, Union[str, int, List[int], float]]) -> Client: ...
def load_pjrt_plugin(platform_name: str, library_path: str) -> _Status: ...

class DeviceArrayBase: ...

class DeviceArray(DeviceArrayBase):
  __array_priority__: int
  _device: Optional[Device]
  aval: Any
  weak_type: Optional[bool]
  @property
  def device_buffer(self: _T) -> _T: ...
  shape: Tuple[int, ...]
  dtype: np.dtype
  size: int
  ndim: int
  _value: np.ndarray
  def __array__(self, dtype=None, context=None) -> np.ndarray: ...
  def copy_to_device(self, dst_device: Device) -> DeviceArray: ...
  def copy_to_remote_device(self,
                            descriptor: bytes) -> Tuple[_Status, bool]: ...
  def on_device_size_in_bytes(self) -> int: ...
  def delete(self) -> None: ...
  def is_ready(self) -> bool: ...
  def is_known_ready(self) -> bool: ...
  def block_until_ready(self) -> DeviceArray: ...
  def copy_to_host_async(self) -> _Status: ...
  def xla_shape(self) -> Shape: ...
  def xla_dynamic_shape(self) -> Shape: ...
  client: Client
  def device(self) -> Device: ...
  def platform(self) -> str: ...
  def is_deleted(self) -> bool: ...
  def unsafe_buffer_pointer(self) -> Any: ...
  __cuda_array_interface__: Dict[str, Any]
  traceback: Traceback
  def clone(self) -> DeviceArray: ...

PyLocalBuffer = DeviceArray
Buffer = DeviceArray

ArrayImpl = Any

# TODO(phawkins): this type is problematic because it is not a subtype of
# jax.Array, and pytype notices.
# class ArrayImpl:
#   def __init__(self,
#                aval: Any,
#                sharding: Any,
#                arrays: Sequence[DeviceArray],
#                committed: bool,
#                _skip_checks: bool = ...): ...
#   def block_until_ready(self) -> ArrayImpl: ...
#   def is_deleted(self) -> bool: ...
#   # TODO(yashkatariya): remove this once the transition completes.
#   def _init_with_fastpath_disabled(self) -> None: ...
#   def is_ready(self) -> bool: ...
#   def delete(self): ...
#   def unsafe_buffer_pointer(self) -> Any: ...
#   def clone(self) -> ArrayImpl: ...
#   def _copy_single_device_array_to_host_async(self): ...
#   def _single_device_array_to_np_array(self) -> np.ndarray: ...
#   def on_device_size_in_bytes(self) -> int: ...
#   __cuda_array_interface__: Dict[str, Any]
#   dtype: np.dtype
#   shape: Tuple[int, ...]
#   _arrays: Any
#   _npy_value: Any
#   traceback: Traceback
#   _HAS_DYNAMIC_ATTRIBUTES: bool = ...


def copy_array_to_devices_with_sharding(self: ArrayImpl, devices: List[Device], sharding: Any) -> ArrayImpl: ...


def batched_device_put(
    aval: Any, sharding: Any, shards: Sequence[Any], devices: List[Device],
    committed: bool = True,
) -> ArrayImpl:
  ...


def array_result_handler(
               aval: Any,
               sharding: Any,
               committed: bool,
               _skip_checks: bool = ...) -> Callable:
  ...

class Token:
  def block_until_ready(self): ...

class ShardedToken:
  def block_until_ready(self): ...
  def get_token(self, device_id: int): ...

class ExecuteResults:
  def __len__(self) -> int: ...
  def disassemble_into_single_device_arrays(self) -> List[List[DeviceArray]]: ...
  def disassemble_prefix_into_single_device_arrays(self, n: int) -> List[List[DeviceArray]]: ...
  def consume_with_handlers(self, handlers: List[Callable]) -> List[Any]: ...
  def consume_token(self) -> ShardedToken: ...

class LoadedExecutable:
  client: Client
  def local_logical_device_ids(self) -> List[Tuple[int, int]]: ...
  def local_devices(self) -> List[Device]: ...
  def size_of_generated_code_in_bytes(self) -> int: ...
  def delete(self) -> None: ...
  def execute(self, arguments: Sequence[DeviceArray]) -> List[DeviceArray]: ...
  def execute_with_token(
      self,
      arguments: Sequence[DeviceArray]) -> Tuple[List[DeviceArray], Token]:
    ...
  def execute_sharded_on_local_devices(
      self,
      arguments: Sequence[List[DeviceArray]]) -> List[List[DeviceArray]]: ...
  def execute_sharded_on_local_devices_with_tokens(
      self,
      arguments: Sequence[List[DeviceArray]]) -> Tuple[List[List[DeviceArray]], ShardedToken]: ...
  def execute_sharded(
      self,
      arguments: Sequence[List[DeviceArray]], with_tokens: bool = ...) -> ExecuteResults: ...
  def hlo_modules(self) -> List[HloModule]: ...
  def get_compiled_memory_stats(self) -> CompiledMemoryStats: ...
  def keep_alive(self) -> None: ...
  def compile_options(self) -> CompileOptions: ...
  traceback: Traceback
  fingerprint: Optional[bytes]

class Executable:
  def hlo_modules(self) -> List[HloModule]: ...
  def get_output_shardings(self) -> Optional[List[OpSharding]]: ...
  def get_parameter_shardings(self) -> Optional[List[OpSharding]]: ...
  def get_compiled_memory_stats(self) -> CompiledMemoryStats: ...
  def serialize(self) -> str: ...
  def compile_options(self) -> CompileOptions: ...

class DeviceTopology:
  platform: str

def compile(topology: DeviceTopology, mlir_module: str) -> Executable: ...

def buffer_to_dlpack_managed_tensor(
    buffer: ArrayImpl,
    take_ownership: bool = ...) -> Any: ...
def dlpack_managed_tensor_to_buffer(
    tensor: Any, cpu_backend: Optional[Client] = ...,
    gpu_backend: Optional[Client] = ...) -> ArrayImpl: ...

# === BEGIN py_traceback.cc

class Frame:
  file_name: str
  function_name: str
  function_line_start: int
  line_num: int
  def __repr__(self) -> str: ...

class Traceback:
  enabled: ClassVar[bool]
  @staticmethod
  def get_traceback() -> Traceback: ...
  frames: Sequence[Frame]
  def __str__(self) -> str: ...
  def as_python_traceback(self) -> Any: ...
  def raw_frames(self) -> Tuple[List[types.CodeType], List[int]]: ...

  @staticmethod
  def code_addr2line(code: types.CodeType, lasti: int) -> int: ...
  @staticmethod
  def code_addr2location(code: types.CodeType,
                         lasti: int) -> Tuple[int, int, int, int]: ...

def replace_thread_exc_traceback(traceback: Any): ...

# === END py_traceback.cc

class DistributedRuntimeService:
  def shutdown(self) -> None: ...
class DistributedRuntimeClient:
  def connect(self) -> _Status: ...
  def shutdown(self) -> _Status: ...
  def blocking_key_value_get(self, key: str, timeout_in_ms: int) -> _Status: ...
  def blocking_key_value_get_bytes(self, key: str, timeout_in_ms: int) -> _Status: ...
  def key_value_dir_get(self, key: str) -> _Status: ...
  def key_value_dir_get_bytes(self, key: str) -> _Status: ...
  def key_value_set(self, key: str, value: str) -> _Status: ...
  def key_value_delete(self, key:str) -> _Status: ...
  def wait_at_barrier(self, barrier_id: str, timeout_in_ms: int) -> _Status: ...
def get_distributed_runtime_service(
    address: str,
    num_nodes: int,
    use_coordination_service: bool = ...,
    heartbeat_interval: Optional[int] = ...,
    max_missing_heartbeats: Optional[int] = ...,
    enumerate_devices_timeout: Optional[int] = ...,
    shutdown_timeout: Optional[int] = ...) -> DistributedRuntimeService: ...
def get_distributed_runtime_client(
    address: str,
    node_id: int,
    use_coordination_service: bool = ...,
    rpc_timeout: Optional[int] = ...,
    init_timeout: Optional[int] = ...,
    shutdown_timeout: Optional[int] = ...,
    heartbeat_interval: Optional[int] = ...,
    max_missing_heartbeats: Optional[int] = ...,
    missed_heartbeat_callback: Optional[Any] = ...,
    shutdown_on_destruction: Optional[bool] = ...) -> DistributedRuntimeClient: ...

class PreemptionSyncManager:
  def initialize(self, client: DistributedRuntimeClient) -> _Status: ...
  def reached_sync_point(self, step_counter: int) -> bool: ...
def create_preemption_sync_manager() -> PreemptionSyncManager: ...

def collect_garbage() -> None: ...

def is_optimized_build() -> bool: ...

def json_to_pprof_profile(json: str) -> bytes: ...
def pprof_profile_to_json(proto: bytes) -> str: ...


CompiledFunction = Any


class PmapFunction:
  def __call__(self, *args, **kwargs) -> Any: ...
  def __getstate__(self) -> Any: ...
  def __setstate__(self, Any): ...
  __signature__: inspect.Signature
  def _cache_size(self) -> int: ...
  def _clear_cache(self) -> None: ...

def weakref_lru_cache(cache_context_fn: Callable, call: Callable, maxsize=...):
  ...

class Sharding: ...

class XLACompatibleSharding(Sharding): ...

class NamedSharding(XLACompatibleSharding):
  def __init__(self, mesh: Any, spec: Any, _parsed_pspec: Any = None): ...
  mesh: Any
  spec: Any
  _parsed_pspec: Any

class SingleDeviceSharding(XLACompatibleSharding):
  def __init__(self, device: Device): ...
  _device: Device

class PmapSharding(XLACompatibleSharding):
  def __init__(self, devices: Sequence[Any], sharding_spec: pmap_lib.ShardingSpec): ...
  devices: List[Any]
  sharding_spec: pmap_lib.ShardingSpec

class GSPMDSharding(XLACompatibleSharding):
  def __init__(self, devices: Sequence[Device], op_sharding: OpSharding): ...
  _devices: Tuple[Device, ...]
  _op_sharding: OpSharding

class PjitFunction:
  def __call__(self, *args, **kwargs) -> Any: ...

class PjitFunctionCache:
  def __init__(self, capacity: int = ...): ...
  def __getstate__(self) -> Any: ...
  def __setstate__(self, Any): ...
  def size(self) -> int: ...
  def capacity(self) -> int: ...
  def clear(self): ...
  @staticmethod
  def clear_all(): ...

def pjit(function_name: str, fun: Optional[Callable], cache_miss: Callable,
         static_argnums: Sequence[int], static_argnames: Sequence[str],
         donate_argnums: Sequence[int],
         cache: Optional[PjitFunctionCache] = ...) -> PjitFunction: ...

class HloPassInterface:
  @property
  def name(self) -> str: ...
  def is_pass_pipeline(self) -> bool: ...
  def run(self, module: HloModule) -> bool: ...
  def run_on_module_group(self, module_group: HloModuleGroup) -> bool: ...

class HloDCE(HloPassInterface):
  def __init__(self) -> None: ...

class CallInliner(HloPassInterface):
  def __init__(self) -> None: ...

class FlattenCallGraph(HloPassInterface):
  def __init__(self) -> None: ...

class TupleSimplifer(HloPassInterface):
  def __init__(self) -> None: ...


def is_asan() -> bool: ...

def is_msan() -> bool: ...

def is_tsan() -> bool: ...

def is_sanitized() -> bool: ...
