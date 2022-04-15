from typing import List, NamedTuple, Optional
import ctypes
import glm
from ..formats.buffer_types import Float3, Float4
from .node import Node
from .mesh_renderer import MeshRenderer
from ..formats.humanoid_bones import HumanoidBone


def vec3_to_float3(v: glm.vec3) -> Float3:
    return Float3(v.x, v.y, v.z)


def get_normal(p0: Float3, p1: Float3, p2: Float3) -> Float3:
    pp0 = glm.vec3(*p0)
    pp1 = glm.vec3(*p1)
    pp2 = glm.vec3(*p2)
    n = glm.cross(glm.normalize(pp2-pp1), glm.normalize(pp0-pp1))
    return vec3_to_float3(n)


SHADER = "assets/skeleton"


class Vertex(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ('position', Float3),
        ('normal', Float3),
        ('color', Float3),
        ('bone', Float4),
        ('weight', Float4),
    ]


class Bone(NamedTuple):
    head: Node
    tail: Node
    color: Float3
    up: Optional[glm.vec3] = None
    width: float = 0
    height: float = 0

    def __str__(self) -> str:
        return f'{self.head.humanoid_bone} => {self.tail.humanoid_bone}'


class Skeleton:
    def __init__(self, root: Node) -> None:
        self.nodes: List[Node] = []
        self.vertices = []
        self.indices = []

        bones: List[Bone] = []

        def find_tail(node: Node) -> Optional[Node]:
            if len(node.children) > 1:
                match node.name:
                    case '上半身2':
                        return next(iter(node for node, _ in node.traverse_node_and_parent() if node.name == '首'))
                    case '下半身':
                        node.find_tail()
                    case '右手首':
                        return next(iter(node for node, _ in node.traverse_node_and_parent() if node.name == '右中指１'))
                    case '左手首':
                        return next(iter(node for node, _ in node.traverse_node_and_parent() if node.name == '左中指１'))
                    case _:
                        pass

            return node.find_tail()

        for node, _ in root.traverse_node_and_parent():
            if node.humanoid_bone:
                tail = find_tail(node)
                if tail:
                    color = Float3(1, 1, 1)
                    up = None
                    width = 0.005
                    height = 0.001
                    if node.humanoid_bone.is_finger():
                        if 'Index' in node.humanoid_bone.name or 'Ring' in node.humanoid_bone.name:
                            if node.humanoid_bone.name.endswith("Intermediate"):
                                color = Float3(0.1, 0.4, 0.8)
                            else:
                                color = Float3(0.2, 0.7, 0.9)
                        else:
                            if node.humanoid_bone.name.endswith("Intermediate"):
                                color = Float3(0.8, 0.4, 0.1)
                            else:
                                color = Float3(0.9, 0.7, 0.2)
                        if 'Thumb' in node.humanoid_bone.name:
                            up = glm.vec3(0, 0, 1)
                        else:
                            up = glm.vec3(0, 1, 0)
                        width = 0.005
                    else:
                        match node.humanoid_bone:
                            case (
                                HumanoidBone.leftUpperArm | HumanoidBone.leftLowerArm |
                                HumanoidBone.leftUpperArm | HumanoidBone.leftLowerArm
                            ):
                                color = Float3(0.3, 0.6, 0.1) if 'Lower' in node.humanoid_bone.name else Float3(
                                    0.7, 0.9, 0.2)
                                up = glm.vec3(0, 0, -1)
                                width = 0.01
                                height = 0.005
                            case (HumanoidBone.leftHand | HumanoidBone.leftHand):
                                color = Float3(0.8, 0.8, 0.8)
                                up = glm.vec3(0, 1, 0)
                                width = 0.005
                                height = 0.002
                    bones.append(
                        Bone(node, tail, color, up=up, width=width, height=height))

        for bone in bones:
            print(bone)
            self._add_node(bone)

        vertices = (Vertex * len(self.vertices))(*self.vertices)
        indices = (ctypes.c_uint16 * len(self.indices))(*self.indices)

        self.renderer = MeshRenderer(SHADER,
                                     vertices, indices, joints=self.nodes)

    def _add_node(self, bone: Bone):
        p0 = bone.head.bind_matrix[3]
        p1 = bone.tail.bind_matrix[3]
        if bone.up:
            self._push_cube(len(self.nodes), bone.color, glm.vec3(p0.x, p0.y, p0.z), glm.vec3(p1.x, p1.y, p1.z),
                            bone.up, bone.width, bone.height)
        else:
            self._push_triangle(len(self.nodes), bone.color,
                                Float3(p0.x, p0.y, p0.z),
                                Float3(p1.x, p1.y, p1.z),
                                Float3(p0.x, p0.y, p0.z + 0.01),
                                )
            self._push_triangle(len(self.nodes), bone.color,
                                Float3(p0.x, p0.y, p0.z),
                                Float3(p0.x, p0.y, p0.z + 0.01),
                                Float3(p1.x, p1.y, p1.z),
                                )
        self.nodes.append(bone.head)

    def _push_triangle(self, bone_index: int, color: Float3, p0: Float3, p1: Float3, p2: Float3):
        vertex_index = len(self.vertices)
        n = get_normal(p0, p1, p2)
        self.vertices.append(
            Vertex(p0, n, color,
                   Float4(bone_index, 0, 0, 0), Float4(1, 0, 0, 0)))
        self.vertices.append(
            Vertex(p1, n, color,
                   Float4(bone_index, 0, 0, 0), Float4(1, 0, 0, 0)))
        self.vertices.append(
            Vertex(p2, n, color,
                   Float4(bone_index, 0, 0, 0), Float4(1, 0, 0, 0)))

        self.indices.append(vertex_index)
        self.indices.append(vertex_index+1)
        self.indices.append(vertex_index+2)

    def _push_quad(self, bone_index: int, color: Float3, p0: Float3, p1: Float3, p2: Float3, p3: Float3):
        vertex_index = len(self.vertices)
        n = get_normal(p0, p1, p2)
        self.vertices.append(
            Vertex(p0, n, color,
                   Float4(bone_index, 0, 0, 0), Float4(1, 0, 0, 0)))
        self.vertices.append(
            Vertex(p1, n, color,
                   Float4(bone_index, 0, 0, 0), Float4(1, 0, 0, 0)))
        self.vertices.append(
            Vertex(p2, n, color,
                   Float4(bone_index, 0, 0, 0), Float4(1, 0, 0, 0)))
        self.vertices.append(
            Vertex(p3, n, color,
                   Float4(bone_index, 0, 0, 0), Float4(1, 0, 0, 0)))

        self.indices.append(vertex_index)
        self.indices.append(vertex_index+1)
        self.indices.append(vertex_index+2)

        self.indices.append(vertex_index+2)
        self.indices.append(vertex_index+3)
        self.indices.append(vertex_index)

    def _push_cube(self, bone_index: int, color: Float3, p0: glm.vec3, p1: glm.vec3,
                   y: glm.vec3, w: float, h: float):
        z = glm.normalize(p1 - p0)
        x = glm.cross(z, y)
        y = glm.cross(x, z)
        # 3 2
        # 0 1
        p0_0 = p0-x*w-y*h
        p0_1 = p0+x*w-y*h
        p0_2 = p0+x*w+y*h
        p0_3 = p0-x*w+y*h
        p1_0 = p1-x*w-y*h
        p1_1 = p1+x*w-y*h
        p1_2 = p1+x*w+y*h
        p1_3 = p1-x*w+y*h
        # cap
        self._push_quad(bone_index, color,
                        vec3_to_float3(p1_0),
                        vec3_to_float3(p1_3),
                        vec3_to_float3(p1_2),
                        vec3_to_float3(p1_1))
        # top
        self._push_quad(bone_index, color,
                        vec3_to_float3(p0_3),
                        vec3_to_float3(p0_2),
                        vec3_to_float3(p1_2),
                        vec3_to_float3(p1_3))
        # bottom
        self._push_quad(bone_index, color * Float3(0.9, 0.2, 0.2),
                        vec3_to_float3(p0_1),
                        vec3_to_float3(p0_0),
                        vec3_to_float3(p1_0),
                        vec3_to_float3(p1_1))
        # left
        self._push_quad(bone_index, color,
                        vec3_to_float3(p0_0),
                        vec3_to_float3(p0_3),
                        vec3_to_float3(p1_3),
                        vec3_to_float3(p1_0))
        # right
        self._push_quad(bone_index, color,
                        vec3_to_float3(p0_2),
                        vec3_to_float3(p0_1),
                        vec3_to_float3(p1_1),
                        vec3_to_float3(p1_2))